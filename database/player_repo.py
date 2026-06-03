# database/player_repo.py
from __future__ import annotations

import sqlite3
from database.connection import get_connection
from models import Player


class PlayerRepository:
    def get(self) -> Player:
        with get_connection() as conn:
            r = conn.execute("SELECT * FROM player WHERE id=1").fetchone()
            if not r:
                conn.execute(
                    """
                    INSERT INTO player (id, username, level, xp, xp_for_next_level, completed_tasks)
                    VALUES (1, 'Umut', 1, 0, 100, 0)
                    """
                )
                conn.commit()
                r = conn.execute("SELECT * FROM player WHERE id=1").fetchone()

            return Player(
                username=r["username"],
                level=int(r["level"]),
                xp=int(r["xp"]),
                xp_for_next_level=int(r["xp_for_next_level"]),
                completed_tasks=int(r["completed_tasks"]),
                badges=[],
                badge_history=[],
                task_history=[],
            )

    def upsert(self, p: Player, conn: sqlite3.Connection | None = None) -> None:
        def _do_upsert(c: sqlite3.Connection) -> None:
            c.execute(
                """
                INSERT INTO player (id, username, level, xp, xp_for_next_level, completed_tasks)
                VALUES (1, ?, ?, ?, ?, ?)
                ON CONFLICT(id) DO UPDATE SET
                    username=excluded.username,
                    level=excluded.level,
                    xp=excluded.xp,
                    xp_for_next_level=excluded.xp_for_next_level,
                    completed_tasks=excluded.completed_tasks
                """,
                (p.username, p.level, p.xp, p.xp_for_next_level, p.completed_tasks),
            )

        if conn is None:
            with get_connection() as conn2:
                _do_upsert(conn2)
                conn2.commit()
                return

        _do_upsert(conn)
