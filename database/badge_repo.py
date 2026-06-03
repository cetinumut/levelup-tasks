# database/badge_repo.py
from __future__ import annotations

import sqlite3
from typing import List, Dict, Any

from database.connection import get_connection


class BadgeRepository:
    def list_earned_ids(self, conn: sqlite3.Connection | None = None) -> List[str]:
        def _do(c: sqlite3.Connection) -> List[str]:
            rows = c.execute("SELECT badge_id FROM badge_earned").fetchall()
            return [r["badge_id"] for r in rows]

        if conn is None:
            with get_connection() as conn2:
                return _do(conn2)
        return _do(conn)

    def insert_earned(
        self,
        *,
        badge_id: str,
        badge_name: str,
        awarded_at: str,
        context: Dict[str, Any],
        conn: sqlite3.Connection | None = None,
    ) -> None:
        def _do(c: sqlite3.Connection) -> None:
            c.execute(
                """
                INSERT INTO badge_earned (badge_id, badge_name, awarded_at, task_id, task_title, task_type, gained_xp)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    badge_id,
                    badge_name,
                    awarded_at,
                    context.get("task_id"),
                    context.get("task_title"),
                    context.get("task_type"),
                    context.get("gained_xp"),
                ),
            )

        if conn is None:
            with get_connection() as conn2:
                _do(conn2)
                conn2.commit()
                return

        _do(conn)

    def list_timeline(self, limit: int | None = None, conn: sqlite3.Connection | None = None) -> List[Dict[str, Any]]:
        def _do(c: sqlite3.Connection) -> List[Dict[str, Any]]:
            sql = "SELECT * FROM badge_earned ORDER BY id DESC"
            params: tuple[Any, ...] = ()
            if limit:
                sql += " LIMIT ?"
                params = (int(limit),)
            rows = c.execute(sql, params).fetchall()
            return [dict(r) for r in rows]

        if conn is None:
            with get_connection() as conn2:
                return _do(conn2)
        return _do(conn)
