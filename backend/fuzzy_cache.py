import threading
from db_connection import get_connection, release_connection
import time
from rapidfuzz import process, fuzz
import re

class FuzzyCache:
    def __init__(self, cache_size: int = 1000, max_cache_age: int = 3600):
        self.player_names = []
        self.player_name_set = set()
        self.cache_lock = threading.Lock()
        self.max_cache_age = max_cache_age
        self.start_background_refresh()

    def fetch_player_names(self):
        try:
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT player_name FROM players")
            names = [row[0] for row in cursor.fetchall()]
            return names
        finally:
            if conn:
                release_connection(conn)

    def refresh(self):
        names = self.fetch_player_names()
        with self.cache_lock:
            self.player_names = names
            self.player_name_set = set(names)
            self.last_refresh = time.time()

    def start_background_refresh(self):
        def refresh_loop():
            while True:
                self.refresh()
                time.sleep(self.max_cache_age)
        threading.Thread(target=refresh_loop, daemon=True).start()

 
    def fuzzy_match(self, name, threshold=80):
        if name in self.player_name_set:
            return name

        best_match = process.extractOne(name, self.player_names, scorer=fuzz.ratio)
        if best_match and best_match[1] >= threshold:
            return best_match[0]
        return name
        
    def correct_names(self, text):
        pattern = re.compile(r"\*\*\*(.*?)\*\*\*")

        def _repl(match: re.Match) -> str:
            raw_name = match.group(1)
            with self.cache_lock:
                corrected = self.fuzzy_match(raw_name)
            return f"***{corrected}***"

        return pattern.sub(_repl, text)

    
            