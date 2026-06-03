# gui/screens/history_screen.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, Dict, List, Optional

from gui.dialogs.log_details import LogDetailsDialog


def _safe_int(x, default: int = 0) -> int:
    try:
        return int(x)
    except Exception:
        return default


class HistoryScreen(tk.Frame):
    def __init__(self, master, *, service: Any, set_status: Callable[[str], None]):
        super().__init__(master)
        self.service = service
        self.set_status = set_status

        self._rows_by_iid: Dict[str, Dict[str, Any]] = {}
        self._debounce_after_id: str | None = None

        self._build_ui()
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        # Top bar
        top = tk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="History", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        # Filters row
        filters = tk.Frame(self)
        filters.pack(fill="x")

        ttk.Label(filters, text="Type:").pack(side="left", padx=(0, 6))
        self.type_var = tk.StringVar(value="All")
        self.type_cb = ttk.Combobox(
            filters,
            textvariable=self.type_var,
            values=["All", "daily", "weekly", "monthly", "epic"],
            state="readonly",
            width=10,
        )
        self.type_cb.pack(side="left", padx=(0, 14))
        self.type_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(filters, text="Min XP:").pack(side="left", padx=(0, 6))
        self.minxp_var = tk.StringVar(value="0")
        self.minxp_cb = ttk.Combobox(
            filters,
            textvariable=self.minxp_var,
            values=["0", "10", "50", "200", "1000"],
            state="readonly",
            width=8,
        )
        self.minxp_cb.pack(side="left", padx=(0, 14))
        self.minxp_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(filters, text="Search:").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar(value="")
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var, width=26)
        self.search_entry.pack(side="left", padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._debounced_refresh)

        ttk.Label(filters, text="Show:").pack(side="left", padx=(0, 6))
        self.limit_var = tk.StringVar(value="200")
        self.limit_cb = ttk.Combobox(
            filters,
            textvariable=self.limit_var,
            values=["100", "200", "500", "1000"],
            state="readonly",
            width=8,
        )
        self.limit_cb.pack(side="left", padx=(0, 14))
        self.limit_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Button(filters, text="Clear", command=self._clear_filters).pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        # Table
        columns = ("id", "completed_at", "task_title", "task_type", "gained_xp", "period")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=22)
        self.tree.pack(fill="both", expand=True)

        self.tree.heading("id", text="ID")
        self.tree.heading("completed_at", text="Completed At")
        self.tree.heading("task_title", text="Task")
        self.tree.heading("task_type", text="Type")
        self.tree.heading("gained_xp", text="XP")
        self.tree.heading("period", text="Period")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("completed_at", width=190, anchor="w")
        self.tree.column("task_title", width=280, anchor="w")
        self.tree.column("task_type", width=100, anchor="center")
        self.tree.column("gained_xp", width=80, anchor="center")
        self.tree.column("period", width=120, anchor="center")

        self.tree.bind("<Double-1>", lambda _e: self._open_selected_details())

        # Bottom row
        bottom = tk.Frame(self)
        bottom.pack(fill="x", pady=(10, 0))

        self.summary_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.summary_var, foreground="#444").pack(side="left")

        ttk.Button(bottom, text="Details…", command=self._open_selected_details).pack(side="right")

    # ---------------- Filters ----------------
    def _limit_value(self) -> int:
        v = (self.limit_var.get() or "").strip()
        return _safe_int(v, 200)

    def _clear_filters(self) -> None:
        self.type_var.set("All")
        self.minxp_var.set("0")
        self.search_var.set("")
        self.limit_var.set("200")
        self.refresh()
        self.set_status("Filters cleared.")

    def _debounced_refresh(self, _evt=None) -> None:
        if self._debounce_after_id:
            try:
                self.after_cancel(self._debounce_after_id)
            except Exception:
                pass
        self._debounce_after_id = self.after(250, self.refresh)

    # ---------------- Data / Render ----------------
    def refresh(self) -> None:
        task_type = (self.type_var.get() or "All").strip()
        min_xp = _safe_int(self.minxp_var.get(), 0)
        q = (self.search_var.get() or "").strip()
        limit = self._limit_value()

        # DB tek kaynak + filtre SQL'de
        rows = self.service.list_history(
            limit=limit,
            task_type=None if task_type == "All" else task_type,
            min_xp=min_xp if min_xp > 0 else None,
            query=q if q else None,
        ) or []

        # clear
        self._rows_by_iid.clear()
        for item in self.tree.get_children():
            self.tree.delete(item)

        total = len(rows)
        total_xp = sum(_safe_int(r.get("gained_xp", 0)) for r in rows)

        for r in rows:
            iid = self.tree.insert(
                "",
                "end",
                values=(
                    r.get("id"),
                    r.get("completed_at") or "",
                    r.get("task_title") or "-",
                    r.get("task_type") or "-",
                    _safe_int(r.get("gained_xp", 0)),
                    r.get("period") or "",
                ),
            )
            self._rows_by_iid[iid] = r

        self.summary_var.set(f"Rows: {total} | Total XP: {total_xp}")
        self.set_status("History refreshed.")

    # ---------------- Details ----------------
    def _open_selected_details(self) -> None:
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Details", "Select a row first.")
            return

        iid = sel[0]
        data = self._rows_by_iid.get(iid)
        if not data:
            messagebox.showinfo("Details", "Row data not found.")
            return

        LogDetailsDialog(self, title="History Log Details", data=data)
