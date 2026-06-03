# stats.py  (DB tabanlı)
import datetime
from typing import Any, Dict, List, Optional, Tuple

from database.tasklog_repo import TaskLogRepository

_tasklog_repo = TaskLogRepository()


def _parse_dt(dt_str: Optional[str]) -> Optional[datetime.datetime]:
    if not dt_str:
        return None
    try:
        return datetime.datetime.fromisoformat(dt_str)
    except ValueError:
        return None


def _get_logs(limit: Optional[int] = None) -> List[Dict[str, Any]]:
    """
    Tek kaynak: DB (task_log).
    """
    items = _tasklog_repo.list_timeline(limit=limit)
    return items or []


def stats_overview(_player=None, verbose: bool = True) -> Dict[str, int]:
    logs = _get_logs(limit=None)
    total_logs = len(logs)
    total_xp = sum(int(h.get("gained_xp", 0) or 0) for h in logs)

    if verbose:
        print("\n--- STATS OVERVIEW ---")
        print(f"Total completions (logs): {total_logs}")
        print(f"Total XP earned (from logs): {total_xp}")
        print()

    return {"total_logs": total_logs, "total_xp": total_xp}


def top_xp_tasks(_player=None, n: int = 5, verbose: bool = True) -> List[Dict[str, Any]]:
    logs = _get_logs(limit=None)

    logs.sort(key=lambda h: int(h.get("gained_xp", 0) or 0), reverse=True)
    top = logs[: max(n, 0)]

    if verbose:
        print(f"\n--- TOP {n} XP COMPLETIONS ---")
        if not top:
            print("(none)\n")
        else:
            for h in top:
                print(f"- {h.get('task_title')} | xp={h.get('gained_xp')} | {h.get('completed_at')}")
            print()

    return top


def last_n_days_summary(_player=None, days: int = 30, verbose: bool = True) -> Dict[str, Any]:
    logs = _get_logs(limit=None)
    now = datetime.datetime.now()
    cutoff = now - datetime.timedelta(days=days)

    total_xp = 0
    total_tasks = 0
    by_type: Dict[str, int] = {}

    for h in logs:
        dt = _parse_dt(h.get("completed_at"))
        if not dt:
            continue
        if dt >= cutoff:
            total_tasks += 1
            xp = int(h.get("gained_xp", 0) or 0)
            total_xp += xp
            ttype = h.get("task_type", "unknown") or "unknown"
            by_type[ttype] = by_type.get(ttype, 0) + 1

    if verbose:
        print(f"\n--- LAST {days} DAYS SUMMARY ---")
        print(f"Completed: {total_tasks}")
        print(f"Total XP: {total_xp}")
        print("By type:")
        if not by_type:
            print("  (none)")
        else:
            for k, v in sorted(by_type.items(), key=lambda x: x[0]):
                print(f"  - {k}: {v}")
        print()

    return {"days": days, "total_tasks": total_tasks, "total_xp": total_xp, "by_type": by_type}


def most_completed_task(_player=None, verbose: bool = True) -> Optional[Dict[str, Any]]:
    logs = _get_logs(limit=None)

    counts: Dict[str, int] = {}
    for h in logs:
        title = h.get("task_title") or "unknown"
        counts[title] = counts.get(title, 0) + 1

    if not counts:
        if verbose:
            print("\n--- MOST COMPLETED TASK ---\n(none)\n")
        return None

    best_title = max(counts, key=counts.get)
    best_count = counts[best_title]

    if verbose:
        print("\n--- MOST COMPLETED TASK ---")
        print(f"{best_title} -> {best_count} times\n")

    return {"task_title": best_title, "count": best_count}
