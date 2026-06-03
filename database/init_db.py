# database/init_db.py
from __future__ import annotations

from typing import Callable, List, Tuple
from database.connection import get_connection
from database.migrations import migrate

Migration = Tuple[int, Callable[[], None]]  # (target_version, fn)


def _ensure_schema_version_table(conn) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
    """)
    conn.execute("""
        INSERT INTO schema_version (id, version)
        VALUES (1, 0)
        ON CONFLICT(id) DO NOTHING
    """)


def _get_version(conn) -> int:
    _ensure_schema_version_table(conn)
    r = conn.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
    return int(r["version"]) if r else 0


def _set_version(conn, v: int) -> None:
    conn.execute("UPDATE schema_version SET version=? WHERE id=1", (int(v),))


# -------------------------
# Migrations
# -------------------------

def _migrate_v1_create_core_tables() -> None:
    with get_connection() as conn:
        # TASKS
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tasks (
                id INTEGER PRIMARY KEY,
                title TEXT NOT NULL,
                description TEXT,
                category TEXT,
                priority TEXT,
                difficulty INTEGER,
                task_type TEXT,
                status INTEGER DEFAULT 0,
                created_at TEXT,
                due_date TEXT,
                streak INTEGER DEFAULT 0,
                best_streak INTEGER DEFAULT 0,
                completed_at TEXT
            )
        """)

        # PLAYER
        conn.execute("""
            CREATE TABLE IF NOT EXISTS player (
                id INTEGER PRIMARY KEY CHECK (id = 1),
                username TEXT NOT NULL,
                level INTEGER NOT NULL,
                xp INTEGER NOT NULL,
                xp_for_next_level INTEGER NOT NULL,
                completed_tasks INTEGER NOT NULL
            )
        """)

        # BADGE EARNED
        conn.execute("""
            CREATE TABLE IF NOT EXISTS badge_earned (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                badge_id TEXT NOT NULL,
                badge_name TEXT NOT NULL,
                awarded_at TEXT NOT NULL,
                task_id INTEGER,
                task_title TEXT,
                task_type TEXT,
                gained_xp INTEGER
            )
        """)

        # TASK LOG
        conn.execute("""
            CREATE TABLE IF NOT EXISTS task_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id INTEGER,
                task_title TEXT,
                task_type TEXT,
                priority TEXT,
                difficulty INTEGER,
                gained_xp INTEGER,
                completed_at TEXT NOT NULL,
                period TEXT
            )
        """)

        # default player row (id=1)
        conn.execute("""
            INSERT INTO player (id, username, level, xp, xp_for_next_level, completed_tasks)
            VALUES (1, 'Umut', 1, 0, 100, 0)
            ON CONFLICT(id) DO NOTHING
        """)

        conn.commit()


def _migrate_v2_indexes_and_uniques() -> None:
    """
    Stabilite + performans:
    - badge_id için duplicate önleme (unique index)
    - timeline sorguları için index
    """
    with get_connection() as conn:
        # 1) badge_earned badge_id duplicate varsa temizle (unique index aksi halde patlar)
        # aynı badge_id için en küçük id kalsın:
        conn.execute("""
            DELETE FROM badge_earned
            WHERE id NOT IN (
                SELECT MIN(id)
                FROM badge_earned
                GROUP BY badge_id
            )
        """)

        # 2) unique index: aynı badge_id bir daha yazılamasın
        conn.execute("""
            CREATE UNIQUE INDEX IF NOT EXISTS ux_badge_earned_badge_id
            ON badge_earned(badge_id)
        """)

        # 3) timeline index’leri
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_badge_earned_awarded_at
            ON badge_earned(awarded_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_task_log_completed_at
            ON task_log(completed_at)
        """)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS ix_task_log_period
            ON task_log(period)
        """)

        conn.commit()


MIGRATIONS: List[Migration] = [
    (1, _migrate_v1_create_core_tables),
    (2, _migrate_v2_indexes_and_uniques),
]




def init_db(verbose: bool = True) -> None:
    with get_connection() as conn:
        # tek transaction
        conn.execute("BEGIN")
        try:
            migrate(conn, verbose=verbose)
            conn.commit()
        except Exception:
            conn.rollback()
            raise


if __name__ == "__main__":
    init_db(verbose=True)



if __name__ == "__main__":
    init_db()
    print("✅ DB initialized (migrations applied).")
