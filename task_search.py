# task_search.py

from typing import List, Optional, Tuple, Any


def _norm(s: Any) -> str:
    return str(s or "").strip().lower()


def _matches_text(task, q: str, fields: List[str]) -> bool:
    q = _norm(q)
    if not q:
        return True

    for f in fields:
        val = _norm(getattr(task, f, ""))
        if q in val:
            return True
    return False


def filter_tasks(
    task_manager,
    *,
    text: Optional[str] = None,
    fields: Optional[List[str]] = None,
    status: Optional[bool] = None,            # True=Done, False=Pending, None=All
    task_type: Optional[str] = None,          # daily/weekly/monthly/epic
    priority: Optional[str] = None,           # low/medium/high
    category: Optional[str] = None,           # any string
) -> List:
    """
    Tek fonksiyonla hem SEARCH hem FILTER.
    text + fields: arama
    diğer parametreler: filtre
    """
    fields = fields or ["title", "description", "category"]

    tt = _norm(task_type) if task_type else None
    pr = _norm(priority) if priority else None
    cat = _norm(category) if category else None

    results = []
    for t in task_manager.tasks:
        if status is not None and t.status is not status:
            continue
        if tt and _norm(getattr(t, "task_type", "")) != tt:
            continue
        if pr and _norm(getattr(t, "priority", "")) != pr:
            continue
        if cat and _norm(getattr(t, "category", "")) != cat:
            continue
        if text and not _matches_text(t, text, fields):
            continue

        results.append(t)

    return results


def sort_tasks(tasks: List, sort_key: Optional[str] = None) -> List:
    """
    sort_key:
      - "priority": high -> medium -> low
      - "type": daily/weekly/monthly/epic
      - "title": A->Z
      - "streak": high->low
      - "id": ascending
    """
    sort_key = _norm(sort_key)

    if not sort_key or sort_key == "id":
        return sorted(tasks, key=lambda t: getattr(t, "id", 0))

    if sort_key == "title":
        return sorted(tasks, key=lambda t: _norm(getattr(t, "title", "")))

    if sort_key == "priority":
        order = {"high": 3, "medium": 2, "low": 1}
        return sorted(tasks, key=lambda t: order.get(_norm(getattr(t, "priority", "")), 0), reverse=True)

    if sort_key == "type":
        order = {"daily": 1, "weekly": 2, "monthly": 3, "epic": 4}
        return sorted(tasks, key=lambda t: order.get(_norm(getattr(t, "task_type", "")), 99))

    if sort_key == "streak":
        return sorted(tasks, key=lambda t: int(getattr(t, "streak", 0) or 0), reverse=True)

    # bilinmeyen -> id
    return sorted(tasks, key=lambda t: getattr(t, "id", 0))


def print_tasks(tasks: List, *, title: str = "RESULTS") -> None:
    print(f"\n--- {title} ({len(tasks)}) ---")
    if not tasks:
        print("No results.\n")
        return
    for t in tasks:
        print(t)
    print()
