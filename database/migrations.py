# database/migrations.py
from __future__ import annotations

import sqlite3
from typing import Callable, List, Tuple

LATEST_SCHEMA_VERSION = 1  # yeni migration ekledikçe artır

MigrationFn = Callable[[sqlite3.Connection], None]


def _table_exists(conn: sqlite3.Connection, name: str) -> bool:
    r = conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name=?",
        (name,),
    ).fetchone()
    return r is not None


def _ensure_schema_version_table(conn: sqlite3.Connection) -> None:
    conn.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            version INTEGER NOT NULL
        )
    """)
    # satır yoksa ekle
    conn.execute("""
        INSERT INTO schema_version (id, version)
        VALUES (1, 0)
        ON CONFLICT(id) DO NOTHING
    """)


def get_schema_version(conn: sqlite3.Connection) -> int:
    _ensure_schema_version_table(conn)
    r = conn.execute("SELECT version FROM schema_version WHERE id=1").fetchone()
    return int(r["version"]) if r else 0


def set_schema_version(conn: sqlite3.Connection, version: int) -> None:
    conn.execute("UPDATE schema_version SET version=? WHERE id=1", (int(version),))


# -------------------------
# MIGRATIONS
# -------------------------

def _m001_baseline(conn: sqlite3.Connection) -> None:
    """
    v1: Mevcut tabloları 'IF NOT EXISTS' ile garantiye al.
    (Senin init_db zaten yapıyor ama migration tarafında da "tek kaynak" olsun.)
    """
    # tasks
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

    # player
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

    # badge_earned
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

    # task_log
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

    # default player row
    conn.execute("""
        INSERT INTO player (id, username, level, xp, xp_for_next_level, completed_tasks)
        VALUES (1, 'Umut', 1, 0, 100, 0)
        ON CONFLICT(id) DO NOTHING
    """)

    # (opsiyonel ama iyi) temel indexler
    conn.execute("CREATE INDEX IF NOT EXISTS idx_task_log_completed_at ON task_log(completed_at)")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_badge_earned_awarded_at ON badge_earned(awarded_at)")


MIGRATIONS: List[Tuple[int, MigrationFn]] = [
    (1, _m001_baseline),
]


def migrate(conn: sqlite3.Connection, *, verbose: bool = True) -> int:
    """
    Tek transaction içinde, eksik migration'ları sırayla uygular.
    Başarıyla biterse schema_version günceller.
    """
    _ensure_schema_version_table(conn)
    current = get_schema_version(conn)

    if current >= LATEST_SCHEMA_VERSION:
        if verbose:
            print(f"✅ DB schema up-to-date (v{current}).")
        return current

    # sıraya koy
    pending = [(v, fn) for (v, fn) in MIGRATIONS if v > current]
    pending.sort(key=lambda x: x[0])

    if verbose:
        versions = ", ".join(f"v{v}" for v, _ in pending)
        print(f"🛠️ Applying migrations: {versions}")

    for v, fn in pending:
        fn(conn)
        set_schema_version(conn, v)

    if verbose:
        print(f"✅ Migrations applied. Current schema v{get_schema_version(conn)}")

    return get_schema_version(conn)
