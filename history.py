# history.py
from __future__ import annotations

import datetime
import sqlite3

from database.tasklog_repo import TaskLogRepository
from time_utils import period_key

_tasklog_repo = TaskLogRepository()


def _safe_task_history(player):
    if not hasattr(player, "task_history") or player.task_history is None:
        player.task_history = []
    return player.task_history


def log_task_completion(player, task, gained_xp: int, now=None, conn: sqlite3.Connection | None = None):
    now = now or datetime.datetime.now()
    hist = _safe_task_history(player)

    task_type = getattr(task, "task_type", None)
    pkey = None
    if task_type and task_type != "epic":
        try:
            pkey = period_key(task_type, now)
        except Exception:
            pkey = None

    entry = {
        "task_id": getattr(task, "id", None),
        "task_title": getattr(task, "title", None),
        "task_type": task_type,
        "priority": getattr(task, "priority", None),
        "difficulty": getattr(task, "difficulty", None),
        "gained_xp": int(gained_xp or 0),
        "completed_at": now.isoformat(),
        "period": pkey,
    }

    # in-memory (opsiyonel, geri uyumluluk)
    hist.append(entry)

    # DB log (aynı transaction içinde çalışabilsin)
    _tasklog_repo.insert_log(entry, conn=conn)

    return entry


def show_task_timeline(player=None, limit=None, verbose=True):
    items = _tasklog_repo.list_timeline(limit=limit)
    if verbose:
        print("\n--- TASK TIMELINE ---")
        if not items:
            print("No task history yet.\n")
            return items
        for h in items:
            print(
                f"- {h.get('completed_at')} | id={h.get('task_id')} | {h.get('task_title')} | "
                f"{h.get('task_type')} | xp={h.get('gained_xp')}"
                + (f" | period={h.get('period')}" if h.get("period") else "")
            )
        print()
    return items


def weekly_summary(player, iso_year: int, iso_week: int, verbose=True):
    period = f"{iso_year}-W{iso_week:02d}"
    result = _tasklog_repo.weekly_summary(period)

    if verbose:
        print("\n--- WEEKLY SUMMARY ---")
        print(f"Week: {period}")
        print(f"Completed tasks: {result['total_tasks']}")
        print(f"Total XP: {result['total_xp']}")
        print("By type:")
        if not result["by_type"]:
            print("  (none)")
        else:
            for k, v in sorted(result["by_type"].items(), key=lambda x: x[0]):
                print(f"  - {k}: {v}")
        print()

    return {
        "iso_year": iso_year,
        "iso_week": iso_week,
        "total_tasks": result["total_tasks"],
        "total_xp": result["total_xp"],
        "by_type": result["by_type"],
    }
