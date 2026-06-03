# exporter.py

import csv
import json
import datetime
from typing import Optional
from models import Task, Player


def _ts() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def export_tasks_csv(task_manager, filename: Optional[str] = None) -> str:
    """
    tasks -> CSV (Excel friendly)
    """
    if filename is None:
        filename = f"tasks_export_{_ts()}.csv"

    fieldnames = [
        "id",
        "title",
        "description",
        "category",
        "priority",
        "difficulty",
        "task_type",
        "status",
        "created_at",
        "due_date",
        "streak",
        "best_streak",
        "completed_at",
    ]

    with open(filename, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for t in task_manager.tasks:
            row = {
                "id": getattr(t, "id", ""),
                "title": getattr(t, "title", ""),
                "description": getattr(t, "description", ""),
                "category": getattr(t, "category", ""),
                "priority": getattr(t, "priority", ""),
                "difficulty": getattr(t, "difficulty", ""),
                "task_type": getattr(t, "task_type", ""),
                "status": getattr(t, "status", ""),
                "created_at": getattr(t, "created_at", ""),
                "due_date": getattr(t, "due_date", ""),
                "streak": getattr(t, "streak", ""),
                "best_streak": getattr(t, "best_streak", ""),
                "completed_at": getattr(t, "completed_at", ""),
            }
            writer.writerow(row)

    return filename


def export_snapshot_json(player, task_manager, filename: Optional[str] = None) -> str:
    """
    Full snapshot: player + tasks (tek dosyada yedek)
    """
    if filename is None:
        filename = f"snapshot_{_ts()}.json"

    payload = {
        "meta": {
            "created_at": datetime.datetime.now().isoformat(),
            "app": "LevelUp Tasks",
            "version": "1.0",
        },
        "player": player.to_dict() if hasattr(player, "to_dict") else {},
        "tasks": [t.to_dict() for t in task_manager.tasks],
    }

    with open(filename, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)

    return filename


def restore_from_snapshot(snapshot_file: str, tasks_filename: str = "tasks.json", player_filename: str = "player.json") -> bool:
    """
    snapshot json -> tasks.json + player.json olarak geri yükler.
    Güvenli: önce mevcut dosyaları yedekler.
    """
    # 1) snapshot oku
    try:
        with open(snapshot_file, "r", encoding="utf-8") as f:
            payload = json.load(f)
    except FileNotFoundError:
        print("Snapshot file not found.")
        return False
    except json.JSONDecodeError:
        print("Snapshot file is corrupted/unreadable.")
        return False

    # 2) doğrula
    player_data = payload.get("player")
    tasks_data = payload.get("tasks")
    if not isinstance(player_data, dict) or not isinstance(tasks_data, list):
        print("Snapshot format invalid (missing player/tasks).")
        return False

    # 3) mevcut dosyaları yedekle
    stamp = _ts()
    try:
        # tasks.json backup
        try:
            with open(tasks_filename, "r", encoding="utf-8") as f:
                old_tasks = f.read()
            with open(f"{tasks_filename}.bak_{stamp}", "w", encoding="utf-8") as f:
                f.write(old_tasks)
        except FileNotFoundError:
            pass

        # player.json backup
        try:
            with open(player_filename, "r", encoding="utf-8") as f:
                old_player = f.read()
            with open(f"{player_filename}.bak_{stamp}", "w", encoding="utf-8") as f:
                f.write(old_player)
        except FileNotFoundError:
            pass
    except Exception:
        print("Backup failed. Restore cancelled for safety.")
        return False

    # 4) snapshot'ı kalıcı jsonlara yaz
    try:
        # tasks.json -> list[dict]
        with open(tasks_filename, "w", encoding="utf-8") as f:
            json.dump(tasks_data, f, indent=4, ensure_ascii=False)

        # player.json -> dict
        with open(player_filename, "w", encoding="utf-8") as f:
            json.dump(player_data, f, indent=4, ensure_ascii=False)
    except Exception:
        print("Restore write failed.")
        return False

    print("✅ Restore completed. (Backups created with .bak_ timestamp)")
    return True