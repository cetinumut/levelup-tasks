# menus.py
from __future__ import annotations

from typing import Any, Callable, Dict, Optional
from database.connection import get_connection
from database.tasklog_repo import TaskLogRepository
from database.badge_repo import BadgeRepository
from services.complete_task_service import complete_task_service
from database.task_repo import TaskRepository




from badges import (
    check_and_award_badges,
    list_badges,
    show_badge_details,
    search_badges,
    list_badges_filtered,
    show_badge_timeline,
)

from history import (
    log_task_completion,
    show_task_timeline,
    weekly_summary,
)

from stats import (
    stats_overview,
    top_xp_tasks,
    last_n_days_summary,
    most_completed_task,
)

# ------------------------------------------------------------
# Core input helpers (23 + 24)
# ------------------------------------------------------------

def _read_choice(prompt: str, *, allow_empty: bool = False) -> str | int | None:
    """
    Kullanıcıdan seçim alır:
    - "1", "2" gibi sayı -> int döner
    - "t", "b", "h", "s", "q", "back", "?" gibi -> str döner (lower)
    - boş bırakma (allow_empty=True) -> "" döner
    - invalid -> None
    """
    raw = input(prompt).strip()
    if raw == "" and allow_empty:
        return ""
    if raw.isdigit():
        return int(raw)
    if raw == "":
        return None
    return raw.lower()


def _read_int(prompt: str, *, allow_empty: bool = False) -> Optional[int]:
    raw = input(prompt).strip()
    if raw == "" and allow_empty:
        return None
    if not raw.isdigit():
        return None
    return int(raw)


def _print_help(title: str, shortcuts: Dict[str, str]) -> None:
    print(f"\n--- HELP: {title} ---")
    for k, v in shortcuts.items():
        print(f"{k}: {v}")
    print()


def _run_menu(
    title: str,
    options: Dict[int, str],
    actions: Dict[int, Callable[[], None]],
    *,
    shortcuts: Dict[str, Callable[[], None]] | None = None,
    help_shortcuts: Dict[str, str] | None = None,
) -> None:
    """
    Generic menu runner:
    - options: {1:"...", 2:"..."}
    - actions: {1: fn, 2: fn}
    - shortcuts: {"?": help_fn, "b": back_fn ...}
    """
    shortcuts = shortcuts or {}
    help_shortcuts = help_shortcuts or {}

    while True:
        print(f"\n--- {title} ---")
        for k in sorted(options.keys()):
            print(f"{k}) {options[k]}")
        print("0) Back")
        print("?) Help")

        ch = _read_choice("Select: ")
        if ch is None:
            print("Invalid input.")
            continue

        # built-ins
        if ch == 0 or ch == "0" or ch == "back":
            return
        if ch == "?":
            _print_help(title, help_shortcuts)
            continue

        # shortcuts
        if isinstance(ch, str) and ch in shortcuts:
            shortcuts[ch]()
            continue

        # numeric action
        if isinstance(ch, int):
            fn = actions.get(ch)
            if not fn:
                print("Invalid option.")
                continue
            fn()
        else:
            print("Invalid option.")


# ------------------------------------------------------------
# MAIN MENU (24: shortcut)
# ------------------------------------------------------------

def main_menu_loop(player: Any, tm: Any,player_repo: Any) -> None:
    def go_tasks(): tasks_menu(player, tm, player_repo)
    def go_badges(): badges_menu(player, tm, player_repo)
    def go_history(): history_menu(player, tm, player_repo)
    def go_stats(): stats_menu(player, tm, player_repo)
    def go_system(): system_menu(player, tm, player_repo)

    options = {
        1: "Tasks",
        2: "Badges",
        3: "History",
        4: "Stats",
        5: "System",
    }

    actions = {
        1: go_tasks,
        2: go_badges,
        3: go_history,
        4: go_stats,
        5: go_system,
    }

    shortcuts = {
        "t": go_tasks,
        "b": go_badges,
        "h": go_history,
        "s": go_stats,
        "sys": go_system,
        "q": lambda: (_exit_menu_loop(),),
    }

    help_shortcuts = {
        "0/back": "Go back (Exit app from main menu)",
        "?": "Show help",
        "t": "Tasks menu",
        "b": "Badges menu",
        "h": "History menu",
        "s": "Stats menu",
        "sys": "System menu",
        "q": "Exit",
    }

    while True:
        print("\n========== LevelUp Tasks ==========")
        for k in sorted(options.keys()):
            print(f"{k}) {options[k]}")
        print("0) Exit")
        print("?) Help")
        print("Shortcuts: t/b/h/s/sys, q")

        ch = _read_choice("Select: ")
        if ch is None:
            print("Invalid input.")
            continue

        if ch == 0 or ch == "0" or ch == "q":
            break

        if ch == "?":
            _print_help("MAIN MENU", help_shortcuts)
            continue

        if isinstance(ch, str):
            if ch in shortcuts:
                # q zaten break yaptı, burada diğerleri:
                if ch != "q":
                    shortcuts[ch]()
                continue
            else:
                print("Invalid option.")
                continue

        # numeric
        fn = actions.get(ch)
        if not fn:
            print("Invalid option.")
            continue
        fn()


def _exit_menu_loop():
    # sadece placeholder; main_menu_loop içinde break ile çıkıyoruz
    return


# ------------------------------------------------------------
# TASKS MENU (23: dispatch)
# ------------------------------------------------------------


def tasks_menu(player: Any, tm: Any, player_repo: Any) -> None:
    def add_task():
        baslik = input("Task title: ").strip()
        tanim = input("Description: ").strip()
        kategori = input("Category: ").strip()
        oncelik = input("Priority (low/medium/high): ").strip().lower()
        zorluk = _read_int("Difficulty (1,2,3): ")
        gorev_turu = input("Type (daily/weekly/monthly/epic): ").strip().lower()

        if zorluk not in (1, 2, 3):
            print("Difficulty invalid.")
            return

        yeni = tm.gorev_ekle(baslik, tanim, kategori, oncelik, zorluk, gorev_turu)
        print("Created:", yeni)

    def list_all():
        tm.tum_gorevleri_listele()



    def complete_task():
        gid = _read_int("Task ID to complete: ")
        if gid is None:
            print("Invalid ID.")
            return

        # repo nesnesi lazımsa: tm.repo zaten TaskRepository
        task_repo = tm.repo if tm.repo is not None else TaskRepository()

        result = complete_task_service(
            task_id=gid,
            player=player,
            tm=tm,
            task_repo=task_repo,
            player_repo=player_repo,
            verbose=True,
        )

        if not result["ok"]:
            # service zaten uygun message döndürüyor
            print(result.get("message", "Failed."))
            return

        task = result["task"]
        gained = result["gained_xp"]
        print(f"Done: {task.title} | +{gained} XP | Level: {player.level} | XP: {player.xp}")

    def list_pending():
        tm.bekleyen_gorevleri_listele()

    def list_completed():
        tm.tamamlanan_gorevleri_listele()

    def sort_priority():
        tm.gorevleri_oncelige_gore_listele()

    def list_by_type():
        tur = input("Type (daily/weekly/monthly/epic): ").strip().lower()
        tm.gorevleri_ture_gore_listele(tur)

    def delete_task():
        gid = _read_int("Task ID to delete: ")
        if gid is None:
            print("Invalid ID.")
            return

        task = tm.id_ile_gorev_bul(gid)
        if task is None:
            print("No such task.")
            return

        if task.status:
            ok = input("Task completed. Delete anyway? (y/n): ").strip().lower()
            if ok != "y":
                print("Cancelled.")
                return

        if tm.gorev_sil(gid):
            print("Deleted.")
        else:
            print("Delete failed.")

    def edit_task():
        gid = _read_int("Task ID to edit: ")
        if gid is None:
            print("Invalid ID.")
            return

        task = tm.id_ile_gorev_bul(gid)
        if task is None:
            print("No such task.")
            return

        yeni_title = input(f"Title [{task.title}]: ").strip()
        if yeni_title:
            task.title = yeni_title

        yeni_desc = input(f"Description [{task.description}]: ").strip()
        if yeni_desc:
            task.description = yeni_desc

        yeni_cat = input(f"Category [{task.category}]: ").strip()
        if yeni_cat:
            task.category = yeni_cat

        yeni_pri = input(f"Priority [{task.priority}] (low/medium/high): ").strip().lower()
        if yeni_pri:
            if yeni_pri in ("low", "medium", "high"):
                task.priority = yeni_pri
            else:
                print("Priority invalid. Not changed.")

        yeni_diff = input(f"Difficulty [{task.difficulty}] (1/2/3): ").strip()
        if yeni_diff:
            if yeni_diff.isdigit() and int(yeni_diff) in (1, 2, 3):
                task.difficulty = int(yeni_diff)
            else:
                print("Difficulty invalid. Not changed.")

        yeni_type = input(f"Type [{task.task_type}] (daily/weekly/monthly/epic): ").strip().lower()
        if yeni_type:
            if yeni_type in ("daily", "weekly", "monthly", "epic"):
                task.task_type = yeni_type
            else:
                print("Type invalid. Not changed.")

        tm.gorev_guncelle(task)
        print("Updated:", task)

    def details():
        gid = _read_int("Task ID: ")
        if gid is None:
            print("Invalid.")
            return
        task = tm.id_ile_gorev_bul(gid)
        if task is None:
            print("No task found.")
        else:
            task.detay_yazdir()

    options = {
        1: "Add task",
        2: "List all tasks",
        3: "Complete task",
        4: "List pending",
        5: "List completed",
        6: "Sort by priority",
        7: "List by type",
        8: "Delete task",
        9: "Edit task",
        10: "Task details (by ID)",
    }

    actions = {
        1: add_task,
        2: list_all,
        3: complete_task,
        4: list_pending,
        5: list_completed,
        6: sort_priority,
        7: list_by_type,
        8: delete_task,
        9: edit_task,
        10: details,
    }

    help_shortcuts = {
        "0/back": "Back to main menu",
        "?": "Show help",
    }

    _run_menu("TASKS MENU", options, actions, help_shortcuts=help_shortcuts)




# BADGES MENU (23: dispatch + 24: extra)
# ------------------------------------------------------------

def badges_menu(player: Any, tm: Any, player_repo: Any) -> None:
    def show_all():
        list_badges(player, task_manager=tm, verbose=True)

    def details():
        bid = input("Badge ID: ").strip()
        show_badge_details(player, bid, task_manager=tm, verbose=True)

    def search():
        q = input("Search: ").strip()
        results = search_badges(q)
        if not results:
            print("No results.")
            return
        print("\n--- RESULTS ---")
        for b in results:
            print(f"- {b['id']} | {b['name']} — {b['description']}")
        print()

    def filter_():
        r = input("Rarity (common/rare/epic/legendary or empty): ").strip()
        c2 = input("Category (progress/streak/xp/misc or empty): ").strip()
        r = r if r else None
        c2 = c2 if c2 else None
        list_badges_filtered(player, tm, rarity=r, category=c2, verbose=True)

    def timeline():
        lim = _read_int("How many latest? (empty=all): ", allow_empty=True)
        show_badge_timeline(player, limit=lim, verbose=True)

    options = {
        1: "Show my badges (owned + locked)",
        2: "Badge details (by badge ID)",
        3: "Search badges",
        4: "Filter badges (rarity/category)",
        5: "Badge timeline",
    }

    actions = {
        1: show_all,
        2: details,
        3: search,
        4: filter_,
        5: timeline,
    }

    help_shortcuts = {
        "0/back": "Back to main menu",
        "?": "Show help",
    }

    _run_menu("BADGES MENU", options, actions, help_shortcuts=help_shortcuts)


# ------------------------------------------------------------
# HISTORY MENU (23: dispatch)
# ------------------------------------------------------------

def history_menu(player: Any, tm: Any, player_repo: Any) -> None:
    def timeline():
        lim = _read_int("How many latest? (empty=all): ", allow_empty=True)
        show_task_timeline(player, limit=lim, verbose=True)

    def weekly():
        y = _read_int("ISO Year (example 2026): ")
        w = _read_int("ISO Week (example 4): ")
        if y is None or w is None:
            print("Invalid input.")
            return
        weekly_summary(player, y, w, verbose=True)

    options = {
        1: "Show task timeline",
        2: "Weekly summary (ISO week)",
    }

    actions = {
        1: timeline,
        2: weekly,
    }

    help_shortcuts = {
        "0/back": "Back to main menu",
        "?": "Show help",
    }

    _run_menu("HISTORY MENU", options, actions, help_shortcuts=help_shortcuts)


# ------------------------------------------------------------
# STATS MENU (23: dispatch)
# ------------------------------------------------------------

def stats_menu(player: Any, tm: Any, player_repo: Any) -> None:
    def overview():
        stats_overview(verbose=True)

    def topxp():
        n = _read_int("How many? (default 5): ", allow_empty=True)
        n = n if n is not None else 5
        top_xp_tasks(n=n, verbose=True)

    def lastdays():
        d = _read_int("Days? (default 30): ", allow_empty=True)
        d = d if d is not None else 30
        last_n_days_summary(days=d, verbose=True)

    def mostdone():
        most_completed_task(verbose=True)

    options = {
        1: "Overview",
        2: "Top XP completions",
        3: "Last N days summary",
        4: "Most completed task",
    }

    actions = {
        1: overview,
        2: topxp,
        3: lastdays,
        4: mostdone,
    }

    help_shortcuts = {
        "0/back": "Back to main menu",
        "?": "Show help",
    }

    _run_menu("STATS MENU", options, actions, help_shortcuts=help_shortcuts)


# ------------------------------------------------------------
# SYSTEM MENU (placeholder now, but dispatch-ready)
# ------------------------------------------------------------

def system_menu(player: Any, tm: Any, player_repo: Any) -> None:
    from storage import health_check_and_repair
    from exporter import export_tasks_csv, export_snapshot_json, restore_from_snapshot

    def save_now():
        player_repo.upsert(player)
        print("Saved.")

    def health_check():
        health_check_and_repair(verbose=True)

    def backup_snapshot():
        fn = export_snapshot_json(player, tm)
        print(f"Snapshot created: {fn}")

    def export_csv():
        fn = export_tasks_csv(tm)
        print(f"CSV exported: {fn}")

    def restore_snapshot():
        snap = input("Snapshot file name (example: snapshot_20260121_235959.json): ").strip()
        if not snap:
            print("Cancelled.")
            return
        ok = restore_from_snapshot(snap)
        if ok:
            print("Restore done. Restart app recommended.")
        else:
            print("Restore failed.")

    options = {
        1: "Save now",
        2: "Health check & repair (JSON)",
        3: "Backup snapshot (player+tasks)",
        4: "Export tasks CSV",
        5: "Restore from snapshot",
    }

    actions = {
        1: save_now,
        2: health_check,
        3: backup_snapshot,
        4: export_csv,
        5: restore_snapshot,
    }

    help_shortcuts = {
        "0/back": "Back to main menu",
        "?": "Show help",
    }

    _run_menu("SYSTEM MENU", options, actions, help_shortcuts=help_shortcuts)
