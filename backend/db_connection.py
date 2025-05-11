import psycopg2
from psycopg2 import pool
# from config import Config
from typing import Dict, List, Tuple, Any, Optional
import threading

# Global connection pool
connection_pool = None
pool_lock = threading.Lock()

def initialize_connection_pool(min_conn=2, max_conn=10):
###   Initialize the connection pool if it doesn't exist
    global connection_pool
    
    with pool_lock:
        if connection_pool is None:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn=min_conn,
                maxconn=max_conn,
                host=Config.DATABASE_HOST,
                port=5432,
                user='postgres',
                password=Config.DATABASE_PASSWORD,
                database='postgres',
                sslmode='require'
            )
    return connection_pool

def get_connection():
    global connection_pool
    if connection_pool is None:
        initialize_connection_pool()
    
    return connection_pool.getconn()

def release_connection(conn):
    global connection_pool
    if connection_pool is not None and conn is not None:
        connection_pool.putconn(conn)

def get_data_text(query, conn=None):
###   Execute a query and return the results, with automatic connection management
    connection_provided = conn is not None
    
    try:
        if not connection_provided:
            conn = get_connection()
        
        cursor = conn.cursor()
        cursor.execute(query)
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        return columns, rows, None
    except Exception as e:
        return [], [], str(e)
    finally:
        if conn is not None and not connection_provided:
            release_connection(conn)

def close_all_connections():
    global connection_pool
    if connection_pool is not None:
        connection_pool.closeall()
        connection_pool = None


