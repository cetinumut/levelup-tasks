# gui/main_window.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk

from gui.screens.tasks_screen import TasksScreen
from gui.screens.badges_screen import BadgesScreen
from gui.screens.history_screen import HistoryScreen
from gui.screens.stats_screen import StatsScreen


class MainWindow(tk.Frame):
    def __init__(self, master: tk.Tk, *, service):
        super().__init__(master)
        self.service = service

        self._current_screen: tk.Widget | None = None
        self._active_key: str = "tasks"

        self._build_layout()
        self._bind_shortcuts()

        self._show_tasks()  # default

    # ---------- layout ----------
    def _build_layout(self) -> None:
        # root grid: sidebar + content
        self.columnconfigure(0, weight=0)
        self.columnconfigure(1, weight=1)
        self.rowconfigure(0, weight=1)

        # styles (selected sidebar button)
        self._init_styles()

        # Sidebar
        sidebar = tk.Frame(self, padx=10, pady=10)
        sidebar.grid(row=0, column=0, sticky="ns")

        ttk.Label(sidebar, text="LevelUp Tasks", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 12))

        # Keep references to buttons for active styling
        self._nav_buttons: dict[str, ttk.Button] = {}

        self._nav_buttons["tasks"] = ttk.Button(
            sidebar, text="Tasks", command=self._show_tasks, width=18, style="Nav.TButton"
        )
        self._nav_buttons["tasks"].pack(anchor="w", pady=4)

        self._nav_buttons["badges"] = ttk.Button(
            sidebar, text="Badges", command=self._show_badges, width=18, style="Nav.TButton"
        )
        self._nav_buttons["badges"].pack(anchor="w", pady=4)

        self._nav_buttons["history"] = ttk.Button(
            sidebar, text="History", command=self._show_history, width=18, style="Nav.TButton"
        )
        self._nav_buttons["history"].pack(anchor="w", pady=4)

        self._nav_buttons["stats"] = ttk.Button(
            sidebar, text="Stats", command=self._show_stats, width=18, style="Nav.TButton"
        )
        self._nav_buttons["stats"].pack(anchor="w", pady=4)

        ttk.Separator(sidebar, orient="horizontal").pack(fill="x", pady=12)

        self.status_var = tk.StringVar(value="")
        ttk.Label(sidebar, textvariable=self.status_var, foreground="#555").pack(anchor="w")

        # Content
        self.content = tk.Frame(self, padx=12, pady=12)
        self.content.grid(row=0, column=1, sticky="nsew")
        self.content.rowconfigure(0, weight=1)
        self.content.columnconfigure(0, weight=1)

    def _init_styles(self) -> None:
        style = ttk.Style()
        # Default style for nav buttons
        style.configure("Nav.TButton", anchor="w", padding=(10, 6))
        # Selected style
        style.configure("NavSelected.TButton", anchor="w", padding=(10, 6))
        # Some ttk themes ignore background; still OK, at least "pressed" look changes on many themes.
        # We also set a slightly bolder font.
        style.configure("NavSelected.TButton", font=("Segoe UI", 10, "bold"))

    # ---------- shortcuts ----------
    def _bind_shortcuts(self) -> None:
        # Bind to top-level window
        root = self.winfo_toplevel()
        root.bind("<F5>", self._on_refresh_shortcut)
        root.bind("<Control-r>", self._on_refresh_shortcut)
        root.bind("<Control-R>", self._on_refresh_shortcut)

    def _on_refresh_shortcut(self, _evt=None) -> None:
        # If current screen has refresh(), call it.
        if self._current_screen is None:
            return
        fn = getattr(self._current_screen, "refresh", None)
        if callable(fn):
            fn()
            self._set_status("Refreshed (F5).")

    # ---------- helpers ----------
    def _set_status(self, text: str) -> None:
        self.status_var.set(text)

    def _swap_screen(self, widget: tk.Widget, *, key: str) -> None:
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = widget
        self._current_screen.grid(row=0, column=0, sticky="nsew")

        self._active_key = key
        self._update_nav_styles()

    def _update_nav_styles(self) -> None:
        for k, btn in self._nav_buttons.items():
            btn.configure(style="NavSelected.TButton" if k == self._active_key else "Nav.TButton")

    # ---------- screens ----------
    def _show_tasks(self) -> None:
        screen = TasksScreen(self.content, service=self.service, set_status=self._set_status)
        self._swap_screen(screen, key="tasks")
        self._set_status("Tasks loaded.")

    def _show_badges(self) -> None:
        screen = BadgesScreen(self.content, service=self.service, set_status=self._set_status)
        self._swap_screen(screen, key="badges")
        self._set_status("Badges loaded.")

    def _show_history(self) -> None:
        screen = HistoryScreen(self.content, service=self.service, set_status=self._set_status)
        self._swap_screen(screen, key="history")
        self._set_status("History loaded.")

    def _show_stats(self) -> None:
        screen = StatsScreen(self.content, service=self.service, set_status=self._set_status)
        self._swap_screen(screen, key="stats")
        self._set_status("Stats loaded.")
