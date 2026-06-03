# gui/app.py
from __future__ import annotations

import tkinter as tk

from database.init_db import init_db
from database.player_repo import PlayerRepository
from database.task_repo import TaskRepository
from models import TaskManager
from gui.main_window import MainWindow
from services.app_service import AppService


def bootstrap() -> AppService:
    # init_db bazı sürümlerde verbose paramı yoksa patlamasın
    try:
        init_db(verbose=False)
    except TypeError:
        init_db()

    task_repo = TaskRepository()
    player_repo = PlayerRepository()

    tm = TaskManager(repo=task_repo)
    tm.tasks = task_repo.list_all()

    player = player_repo.get()

    # ✅ Tek dönüş: AppService
    return AppService(
        tm=tm,
        player=player,
        task_repo=task_repo,
        player_repo=player_repo,
    )


def run() -> None:
    service = bootstrap()   # ✅ tuple değil, AppService

    root = tk.Tk()
    root.title("LevelUp Tasks")
    root.geometry("1100x650")
    # gui/app.py içinde run() -> root oluşturduktan sonra
    root.minsize(1000, 600)
    try:
        # center
        root.update_idletasks()
        w, h = 1100, 650
        x = (root.winfo_screenwidth() // 2) - (w // 2)
        y = (root.winfo_screenheight() // 2) - (h // 2)
        root.geometry(f"{w}x{h}+{x}+{y}")
    except Exception:
        pass

    app = MainWindow(root, service=service)
    app.pack(fill="both", expand=True)

    root.mainloop()


if __name__ == "__main__":
    run()
