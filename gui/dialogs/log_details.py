# gui/dialogs/log_details.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Dict


class LogDetailsDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, *, title: str, data: Dict[str, Any]):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.transient(master.winfo_toplevel())
        self.grab_set()

        body = tk.Frame(self, padx=12, pady=12)
        body.pack(fill="both", expand=True)

        ttk.Label(body, text=title, font=("Segoe UI", 12, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        grid = tk.Frame(body)
        grid.grid(row=1, column=0, sticky="nsew")

        grid.columnconfigure(0, weight=0)
        grid.columnconfigure(1, weight=1)

        # key ordering (güzel görünüm)
        order = [
            "id",
            "completed_at",
            "period",
            "task_id",
            "task_title",
            "task_type",
            "priority",
            "difficulty",
            "gained_xp",
        ]

        items = []
        seen = set()
        for k in order:
            if k in data:
                items.append((k, data.get(k)))
                seen.add(k)
        for k, v in data.items():
            if k not in seen:
                items.append((k, v))

        r = 0
        for k, v in items:
            ttk.Label(grid, text=str(k), foreground="#555").grid(row=r, column=0, sticky="w", padx=(0, 10), pady=2)
            ttk.Label(grid, text="" if v is None else str(v)).grid(row=r, column=1, sticky="w", pady=2)
            r += 1

        btns = tk.Frame(body)
        btns.grid(row=2, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Close", command=self.destroy).pack()

        self._center()

    def _center(self):
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()
        parent = self.master.winfo_toplevel()
        px = parent.winfo_rootx()
        py = parent.winfo_rooty()
        pw = parent.winfo_width()
        ph = parent.winfo_height()
        x = px + (pw - w) // 2
        y = py + (ph - h) // 2
        self.geometry(f"+{x}+{y}")
