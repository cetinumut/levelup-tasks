# gui/dialogs/task_form.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Dict, Optional


class TaskFormDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, *, title: str = "Task", initial: Optional[Dict[str, Any]] = None):
        super().__init__(master)
        self.title(title)
        self.resizable(False, False)
        self.result: Optional[Dict[str, Any]] = None

        initial = initial or {}

        self.var_title = tk.StringVar(value=initial.get("title", ""))
        self.var_desc = tk.StringVar(value=initial.get("description", ""))
        self.var_cat = tk.StringVar(value=initial.get("category", ""))
        self.var_priority = tk.StringVar(value=initial.get("priority", "medium"))
        self.var_type = tk.StringVar(value=initial.get("task_type", "daily"))
        self.var_diff = tk.IntVar(value=int(initial.get("difficulty", 2) or 2))

        self._build()
        self.transient(master)
        self.grab_set()
        self._center(master)

        self.bind("<Return>", lambda _e: self._on_save())
        self.bind("<Escape>", lambda _e: self._on_cancel())

    def _build(self) -> None:
        pad = 10
        frm = ttk.Frame(self, padding=pad)
        frm.pack(fill="both", expand=True)

        # title
        ttk.Label(frm, text="Title").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self.var_title, width=45).grid(row=0, column=1, sticky="we", padx=(8, 0))

        # desc
        ttk.Label(frm, text="Description").grid(row=1, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.var_desc, width=45).grid(row=1, column=1, sticky="we", padx=(8, 0), pady=(8, 0))

        # category
        ttk.Label(frm, text="Category").grid(row=2, column=0, sticky="w", pady=(8, 0))
        ttk.Entry(frm, textvariable=self.var_cat, width=45).grid(row=2, column=1, sticky="we", padx=(8, 0), pady=(8, 0))

        # priority
        ttk.Label(frm, text="Priority").grid(row=3, column=0, sticky="w", pady=(8, 0))
        pri = ttk.Combobox(frm, textvariable=self.var_priority, values=["low", "medium", "high"], state="readonly", width=42)
        pri.grid(row=3, column=1, sticky="we", padx=(8, 0), pady=(8, 0))

        # diff
        ttk.Label(frm, text="Difficulty").grid(row=4, column=0, sticky="w", pady=(8, 0))
        diff = ttk.Combobox(frm, textvariable=self.var_diff, values=[1, 2, 3], state="readonly", width=42)
        diff.grid(row=4, column=1, sticky="we", padx=(8, 0), pady=(8, 0))

        # type
        ttk.Label(frm, text="Type").grid(row=5, column=0, sticky="w", pady=(8, 0))
        typ = ttk.Combobox(frm, textvariable=self.var_type, values=["daily", "weekly", "monthly", "epic"], state="readonly", width=42)
        typ.grid(row=5, column=1, sticky="we", padx=(8, 0), pady=(8, 0))

        # buttons
        btns = ttk.Frame(frm)
        btns.grid(row=6, column=0, columnspan=2, sticky="e", pady=(12, 0))

        ttk.Button(btns, text="Cancel", command=self._on_cancel).pack(side="right", padx=(8, 0))
        ttk.Button(btns, text="Save", command=self._on_save).pack(side="right")

        frm.columnconfigure(1, weight=1)

    def _on_save(self) -> None:
        title = self.var_title.get().strip()
        if not title:
            messagebox.showwarning("Validation", "Title cannot be empty.")
            return

        self.result = {
            "title": title,
            "description": self.var_desc.get().strip(),
            "category": self.var_cat.get().strip(),
            "priority": self.var_priority.get().strip() or "medium",
            "difficulty": int(self.var_diff.get() or 2),
            "task_type": self.var_type.get().strip() or "daily",
        }
        self.destroy()

    def _on_cancel(self) -> None:
        self.result = None
        self.destroy()

    def _center(self, master: tk.Widget) -> None:
        self.update_idletasks()
        mw = master.winfo_width()
        mh = master.winfo_height()
        mx = master.winfo_rootx()
        my = master.winfo_rooty()
        w = self.winfo_width()
        h = self.winfo_height()
        x = mx + (mw - w) // 2
        y = my + (mh - h) // 2
        self.geometry(f"+{x}+{y}")
