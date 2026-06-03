# migrate_tasks_to_db.py
import json
from pathlib import Path

from database.schema import init_db
from database.task_repo import TaskRepository
from models import Task

def main():
    init_db()
    repo = TaskRepository()

    src = Path("tasks.json")
    if not src.exists():
        print("tasks.json not found. Nothing to migrate.")
        return

    try:
        data = json.loads(src.read_text(encoding="utf-8"))
    except Exception:
        print("tasks.json unreadable/corrupted. Migration aborted.")
        return

    if not isinstance(data, list):
        print("tasks.json format invalid (expected list).")
        return

    migrated = 0
    for item in data:
        if not isinstance(item, dict):
            continue
        t = Task.from_dict(item)
        repo.upsert(t)
        migrated += 1

    print(f"✅ Migrated {migrated} tasks to levelup.db")

if __name__ == "__main__":
    main()
