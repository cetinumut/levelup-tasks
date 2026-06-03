# database/tasklog_repo.py
from __future__ import annotations

import sqlite3
from typing import Any, Dict, List, Optional, Tuple

from database.connection import get_connection


class TaskLogRepository:
    def insert_log(self, entry: Dict[str, Any], conn: sqlite3.Connection | None = None) -> None:
        def _do_insert(c: sqlite3.Connection) -> None:
            c.execute(
                """
                INSERT INTO task_log (
                    task_id, task_title, task_type, priority, difficulty, gained_xp, completed_at, period
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    entry.get("task_id"),
                    entry.get("task_title"),
                    entry.get("task_type"),
                    entry.get("priority"),
                    entry.get("difficulty"),
                    entry.get("gained_xp"),
                    entry.get("completed_at"),
                    entry.get("period"),
                ),
            )

        if conn is None:
            with get_connection() as conn2:
                _do_insert(conn2)
                conn2.commit()
                return
        _do_insert(conn)

    def list_timeline(
        self,
        limit: int | None = None,
        *,
        task_type: str | None = None,
        min_xp: int | None = None,
        query: str | None = None,
        conn: sqlite3.Connection | None = None,
    ) -> List[Dict[str, Any]]:
        """
        task_type: 'daily' | 'weekly' | 'monthly' | 'epic' | None
        min_xp: minimum gained_xp
        query: title içinde arama (LIKE)
        """
        def _do_list(c: sqlite3.Connection) -> List[Dict[str, Any]]:
            sql = "SELECT * FROM task_log"
            where: List[str] = []
            params: List[Any] = []

            if task_type and task_type.lower() != "all":
                where.append("task_type = ?")
                params.append(task_type)

            if min_xp is not None:
                where.append("COALESCE(gained_xp, 0) >= ?")
                params.append(int(min_xp))

            q = (query or "").strip()
            if q:
                where.append("(LOWER(COALESCE(task_title,'')) LIKE ? OR CAST(COALESCE(task_id,'') AS TEXT) LIKE ?)")
                like = f"%{q.lower()}%"
                params.extend([like, like])

            if where:
                sql += " WHERE " + " AND ".join(where)

            sql += " ORDER BY id DESC"

            if limit is not None:
                sql += " LIMIT ?"
                params.append(int(limit))

            rows = c.execute(sql, tuple(params)).fetchall()
            return [dict(r) for r in rows]

        if conn is None:
            with get_connection() as conn2:
                return _do_list(conn2)
        return _do_list(conn)

    def weekly_summary(self, period: str, conn: sqlite3.Connection | None = None) -> Dict[str, Any]:
        """
        period format: 'YYYY-Www'  (ör: 2026-W04)
        """
        def _do_summary(c: sqlite3.Connection) -> Dict[str, Any]:
            r = c.execute(
                """
                SELECT
                    COUNT(*) AS total_tasks,
                    COALESCE(SUM(gained_xp), 0) AS total_xp
                FROM task_log
                WHERE period = ?
                """,
                (period,),
            ).fetchone()

            rows = c.execute(
                """
                SELECT task_type, COUNT(*) AS cnt
                FROM task_log
                WHERE period = ?
                GROUP BY task_type
                ORDER BY task_type ASC
                """,
                (period,),
            ).fetchall()

            by_type = {row["task_type"] or "unknown": int(row["cnt"]) for row in rows}

            return {
                "total_tasks": int(r["total_tasks"] or 0),
                "total_xp": int(r["total_xp"] or 0),
                "by_type": by_type,
            }

        if conn is None:
            with get_connection() as conn2:
                return _do_summary(conn2)
        return _do_summary(conn)
