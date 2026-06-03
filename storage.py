# storage.py
import json
from json import JSONDecodeError
import os
import glob

from models import Player
from database.task_repo import TaskRepository

_task_repo = TaskRepository()


# -----------------------
# TASKS (DB is source of truth)
# -----------------------

def load_tasks(task_manager) -> None:
    """Tasks -> DB’den yükle"""
    task_manager.tasks.clear()
    task_manager.tasks.extend(_task_repo.list_all())


def save_tasks(task_manager, filename: str = "tasks.json", *, export_backup: bool = False) -> None:
    """
    Artık tasks DB’ye menü/repo üzerinden yazıldığı için burada DB yazımı yapmıyoruz.
    İstersen export_backup=True ile tasks.json yedeği alır.
    """
    if not export_backup:
        return

    task_dict_list = [t.to_dict() for t in task_manager.tasks]
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(task_dict_list, f, indent=4, ensure_ascii=False)


# -----------------------
# PLAYER (still JSON for now)
# -----------------------

def save_player(player, filename: str = "player.json") -> None:
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(player.to_dict(), f, indent=4, ensure_ascii=False)


def load_player(filename: str = "player.json", default_username: str = "Umut") -> Player:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
    except FileNotFoundError:
        return Player(default_username)
    except JSONDecodeError:
        print("player.json Broken/unreadable. New player created.")
        return Player(default_username)

    return Player.from_dict(data)


# -----------------------
# JSON health/repair helpers (player.json için anlamlı)
# tasks.json artık backup ise anlamı azalır ama kalsın
# -----------------------

def _latest_backup(filename: str) -> str | None:
    pattern = f"{filename}.bak_*"
    backups = glob.glob(pattern)
    if not backups:
        return None
    backups.sort(reverse=True)
    return backups[0]


def _restore_backup_to_file(backup_path: str, filename: str) -> bool:
    try:
        with open(backup_path, "r", encoding="utf-8") as src:
            content = src.read()
        with open(filename, "w", encoding="utf-8") as dst:
            dst.write(content)
        return True
    except Exception:
        return False


def health_check_and_repair(
    tasks_filename: str = "tasks.json",
    player_filename: str = "player.json",
    verbose: bool = True
) -> dict:
    result = {
        "tasks_ok": True,
        "player_ok": True,
        "tasks_repaired": False,
        "player_repaired": False,
        "tasks_backup_used": None,
        "player_backup_used": None,
    }

    # --- tasks.json check (sadece backup dosyasıysa çok kritik değil) ---
    try:
        if os.path.exists(tasks_filename):
            with open(tasks_filename, "r", encoding="utf-8") as f:
                json.load(f)
    except Exception:
        result["tasks_ok"] = False
        b = _latest_backup(tasks_filename)
        if b and _restore_backup_to_file(b, tasks_filename):
            result["tasks_repaired"] = True
            result["tasks_backup_used"] = b
            try:
                with open(tasks_filename, "r", encoding="utf-8") as f:
                    json.load(f)
                result["tasks_ok"] = True
            except Exception:
                result["tasks_ok"] = False

    # --- player.json check (kritik) ---
    try:
        if os.path.exists(player_filename):
            with open(player_filename, "r", encoding="utf-8") as f:
                json.load(f)
    except Exception:
        result["player_ok"] = False
        b = _latest_backup(player_filename)
        if b and _restore_backup_to_file(b, player_filename):
            result["player_repaired"] = True
            result["player_backup_used"] = b
            try:
                with open(player_filename, "r", encoding="utf-8") as f:
                    json.load(f)
                result["player_ok"] = True
            except Exception:
                result["player_ok"] = False

    if verbose:
        print("\n--- HEALTH CHECK ---")
        print(f"tasks.json: {'OK' if result['tasks_ok'] else 'BROKEN'}")
        if result["tasks_repaired"]:
            print(f"  ✅ repaired using: {result['tasks_backup_used']}")
        print(f"player.json: {'OK' if result['player_ok'] else 'BROKEN'}")
        if result["player_repaired"]:
            print(f"  ✅ repaired using: {result['player_backup_used']}")
        print()

    return result
