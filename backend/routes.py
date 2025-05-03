from flask import Blueprint, request, jsonify, session
from flask_cors import CORS
from db_connection import get_connection, release_connection, get_data_text
from openai_response import break_down_query, get_response, get_sql_query, get_error_response
import uuid
from user_session import UserSession
from fuzzy_cache import FuzzyCache
import re
import time as tm
import threading

fuzzy_cache = FuzzyCache()

# create a Blueprint for the app
bp = Blueprint('api', __name__)
# wrap in CORS to allow cross-origin requests
CORS(bp, resources={r"/*": {"origins": "*"}})

active_sessions = {}

def session_cleanup_thread():
    while True:
        tm.sleep(7200)  # Run every 2 hours
        current_time = tm.time()
        expired_sessions = []
        
        for session_id, user_session in active_sessions.items():
            # Remove sessions inactive for more than 24 hours
            if not user_session.chat_history or current_time - user_session.chat_history[-1]['timestamp'] > 86400:
                expired_sessions.append(session_id)
        
        for session_id in expired_sessions:
            del active_sessions[session_id]

# Start session cleanup thread
cleanup_thread = threading.Thread(target=session_cleanup_thread, daemon=True)
cleanup_thread.start()

# register query function to handle posts at /api/query
@bp.route('/api/query', methods=['POST'])
def query():
    # get the query from the request body
    query = request.json['query']

    # get or create session
    session_id = session.get('session_id')
    if not session_id or session_id not in active_sessions:
        session_id = str(uuid.uuid4())
        session['session_id'] = session_id
        active_sessions[session_id] = UserSession()
    
    user_session = active_sessions[session_id]
    # get the breakdown of the query
    breakdown = break_down_query(query, user_session)
    breakdown = fuzzy_cache.correct_names(breakdown)
    print("Updated Breakdown:", breakdown)

    # get the sql query
    sql_query = get_sql_query(query, breakdown)
    
    # If the query generator couldn't create a valid SQL query
    if sql_query is None:
        error = "I couldn't understand your question. Could you please rephrase it or provide more specific details about the NBA statistics you're looking for?"
        user_session.add_interaction(query = query, sql_query = sql_query, error = error)
        return jsonify({
            "success": False,
            "response": error
        })
    
    # connect to database
    conn = get_connection()
    
    try:
        # get the data text
        columns, rows, error = get_data_text(sql_query, conn)
        
        if error:
            # Get a user-friendly error message
            error_response = get_error_response(query, error)
            user_session.add_interaction(query = query, sql_query = sql_query, error = error_response)
            return jsonify({
                "success": False,
                "response": error_response
            })
        
        # If no results were found but query executed successfully
        if len(rows) == 0:
            error_response = "No results found for your query. Try asking about different NBA players, teams, or time periods, or check your spelling of player names or teams."
            user_session.add_interaction(query = query, sql_query = sql_query, data_table = "", error = error_response)
            return jsonify({
                "success": True,
                "response": error_response,
                "table": ""
            })
        
        # get the response
        formatted_table, llm_response = get_response(query, columns, rows)
        user_session.add_interaction(query = query, sql_query = sql_query, data_table = formatted_table, response = llm_response)
        return jsonify({
            "success": True,
            "response": llm_response,
            "table": formatted_table
        })
    finally:
        release_connection(conn)

# GET endpoint to verify health of service
@bp.route('/api/health', methods=['GET'])
def health():
    return jsonify({"status": "OK"})