# database/connection.py
import sqlite3
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent  # proje kökü
DB_PATH = str(BASE_DIR / "levelup.db")

def get_connection(db_path: str = DB_PATH) -> sqlite3.Connection:
    # timeout: DB kilitliyken hemen patlamasın (busy_timeout’a ek olarak)
    conn = sqlite3.connect(db_path, timeout=5)
    conn.row_factory = sqlite3.Row

    # --- SQLite pragmas (stability/perf) ---
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA journal_mode = WAL;")      # daha stabil eşzamanlı okuma/yazma
    conn.execute("PRAGMA synchronous = NORMAL;")    # WAL ile iyi denge
    conn.execute("PRAGMA busy_timeout = 5000;")     # 5sn bekle, sonra hata ver

    return conn
