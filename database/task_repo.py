# database/task_repo.py
from __future__ import annotations

import sqlite3
from typing import Optional, List

from database.connection import get_connection
from models import Task


def _row_to_task(r) -> Task:
    return Task(
        id=r["id"],
        title=r["title"],
        description=r["description"] or "",
        category=r["category"] or "",
        priority=r["priority"] or "medium",
        difficulty=int(r["difficulty"] or 2),
        task_type=r["task_type"] or "daily",
        status=bool(r["status"]),
        created_at=r["created_at"],
        due_date=r["due_date"],
        streak=int(r["streak"] or 0),
        completed_at=r["completed_at"],
        best_streak=int(r["best_streak"] or 0),
    )


class TaskRepository:
    # ---------- READ ----------
    def list_all(self, conn: sqlite3.Connection | None = None) -> List[Task]:
        if conn is None:
            with get_connection() as conn2:
                rows = conn2.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
                return [_row_to_task(r) for r in rows]
        rows = conn.execute("SELECT * FROM tasks ORDER BY id ASC").fetchall()
        return [_row_to_task(r) for r in rows]

    def get_by_id(self, task_id: int, conn: sqlite3.Connection | None = None) -> Optional[Task]:
        if conn is None:
            with get_connection() as conn2:
                r = conn2.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
                return _row_to_task(r) if r else None
        r = conn.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        return _row_to_task(r) if r else None

    # ---------- WRITE ----------
    def insert(self, task: Task, conn: sqlite3.Connection | None = None) -> Task:
        """
        task.id None veya 0 ise insert eder.
        transaction dışarıdan yönetilebilir.
        """
        def _do_insert(c: sqlite3.Connection) -> Task:
            cur = c.execute(
                """
                INSERT INTO tasks (
                    title, description, category, priority, difficulty, task_type,
                    status, created_at, due_date, streak, best_streak, completed_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.priority,
                    task.difficulty,
                    task.task_type,
                    1 if task.status else 0,
                    task.created_at,
                    task.due_date,
                    task.streak,
                    task.best_streak,
                    task.completed_at,
                ),
            )
            task.id = int(cur.lastrowid)
            return task

        if conn is None:
            with get_connection() as conn2:
                out = _do_insert(conn2)
                conn2.commit()
                return out

        return _do_insert(conn)

    def update(self, task: Task, conn: sqlite3.Connection | None = None) -> None:
        """
        task.id zorunlu ve pozitif olmalı.
        """
        if not task.id:  # None veya 0
            raise ValueError("update() requires a valid task.id (non-zero)")

        def _do_update(c: sqlite3.Connection) -> None:
            c.execute(
                """
                UPDATE tasks SET
                    title=?,
                    description=?,
                    category=?,
                    priority=?,
                    difficulty=?,
                    task_type=?,
                    status=?,
                    created_at=?,
                    due_date=?,
                    streak=?,
                    best_streak=?,
                    completed_at=?
                WHERE id=?
                """,
                (
                    task.title,
                    task.description,
                    task.category,
                    task.priority,
                    task.difficulty,
                    task.task_type,
                    1 if task.status else 0,
                    task.created_at,
                    task.due_date,
                    task.streak,
                    task.best_streak,
                    task.completed_at,
                    task.id,
                ),
            )

        if conn is None:
            with get_connection() as conn2:
                _do_update(conn2)
                conn2.commit()
                return

        _do_update(conn)

    def upsert(self, task: Task, conn: sqlite3.Connection | None = None) -> Task:
        """
        id None veya 0 -> insert
        aksi -> update
        """
        if not task.id:
            return self.insert(task, conn=conn)
        self.update(task, conn=conn)
        return task

    def delete(self, task_id: int, conn: sqlite3.Connection | None = None) -> bool:
        def _do_delete(c: sqlite3.Connection) -> bool:
            cur = c.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
            return cur.rowcount > 0

        if conn is None:
            with get_connection() as conn2:
                ok = _do_delete(conn2)
                conn2.commit()
                return ok

        return _do_delete(conn)
