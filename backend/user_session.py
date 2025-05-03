import time as tm

class UserSession:
    def __init__(self):
        self.chat_history = []
        self.messages = []

    def add_interaction(self, query, sql_query = None, data_table = None, response = None, error = None):
        self.chat_history.append({'timestamp': tm.time(),
                                  'query': query,
                                  'sql_query': sql_query,
                                  'data_table': data_table,
                                  'response': response,
                                  'error': error})
        self.messages.append(f'User: {query}')
        if response:
            self.messages.append(f'Assistant: {response}')
        elif error:
            self.messages.append(f'Assistant: {error}')
    