# database/schema.py
from database.connection import get_connection

def init_db() -> None:
    with get_connection() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                difficulty INTEGER,
                task_type TEXT,
                status INTEGER NOT NULL DEFAULT 0,
                created_at TEXT,
                due_date TEXT,
                streak INTEGER NOT NULL DEFAULT 0,
                best_streak INTEGER NOT NULL DEFAULT 0,
                completed_at TEXT
            );
            """
        )
