# gui/screens/stats_screen.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk
from typing import Any, Callable, Dict, List, Optional

from gui.dialogs.log_details import LogDetailsDialog


def _safe_int(x, default: int = 0) -> int:
    try:
        return int(x)
    except (TypeError, ValueError):
        return default


class StatsScreen(tk.Frame):
    def __init__(self, master, *, service: Any, set_status: Callable[[str], None]):
        super().__init__(master)
        self.service = service
        self.set_status = set_status

        # ✅ Top XP satırlarının full dict cache'i (double click için)
        self._topxp_rows: List[Dict[str, Any]] = []

        self._build_ui()
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        # Top bar
        top = tk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="Stats", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        # KPI cards row
        kpi = tk.Frame(self)
        kpi.pack(fill="x")

        for i in range(4):
            kpi.columnconfigure(i, weight=1)

        self.kpi_total_logs = self._make_card(kpi, "Total Completions", "0")
        self.kpi_total_xp = self._make_card(kpi, "Total XP (logs)", "0")
        self.kpi_last_days_tasks = self._make_card(kpi, "Last X Days Completed", "0")
        self.kpi_last_days_xp = self._make_card(kpi, "Last X Days XP", "0")

        self.kpi_total_logs.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.kpi_total_xp.grid(row=0, column=1, sticky="nsew", padx=(0, 10))
        self.kpi_last_days_tasks.grid(row=0, column=2, sticky="nsew", padx=(0, 10))
        self.kpi_last_days_xp.grid(row=0, column=3, sticky="nsew")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=12)

        # Controls row
        controls = tk.Frame(self)
        controls.pack(fill="x")

        ttk.Label(controls, text="Days:").pack(side="left", padx=(0, 6))
        self.days_var = tk.StringVar(value="30")
        self.days_cb = ttk.Combobox(
            controls,
            textvariable=self.days_var,
            values=["7", "14", "30", "60", "90", "180", "365"],
            width=8,
            state="readonly",
        )
        self.days_cb.pack(side="left", padx=(0, 14))
        self.days_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        ttk.Label(controls, text="Top XP:").pack(side="left", padx=(0, 6))
        self.topn_var = tk.StringVar(value="5")
        self.topn_cb = ttk.Combobox(
            controls,
            textvariable=self.topn_var,
            values=["3", "5", "10", "20"],
            width=8,
            state="readonly",
        )
        self.topn_cb.pack(side="left", padx=(0, 14))
        self.topn_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

        # Body split
        body = tk.Frame(self)
        body.pack(fill="both", expand=True)

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        # LEFT PANEL
        left = tk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        left.rowconfigure(1, weight=1)
        left.columnconfigure(0, weight=1)

        ttk.Label(left, text="Last X Days Breakdown", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        self.last_days_meta = tk.StringVar(value="")
        ttk.Label(left, textvariable=self.last_days_meta, foreground="#555").grid(
            row=0, column=0, sticky="e"
        )

        cols1 = ("type", "count")
        self.by_type_tree = ttk.Treeview(left, columns=cols1, show="headings", height=12)
        self.by_type_tree.grid(row=1, column=0, sticky="nsew")

        self.by_type_tree.heading("type", text="Type")
        self.by_type_tree.heading("count", text="Count")
        self.by_type_tree.column("type", width=140, anchor="w")
        self.by_type_tree.column("count", width=90, anchor="center")

        # RIGHT PANEL
        right = tk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        right.rowconfigure(1, weight=1)
        right.columnconfigure(0, weight=1)

        ttk.Label(right, text="Top XP Completions", font=("Segoe UI", 12, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 6)
        )

        cols2 = ("title", "xp", "date")
        self.topxp_tree = ttk.Treeview(right, columns=cols2, show="headings", height=12)
        self.topxp_tree.grid(row=1, column=0, sticky="nsew")

        self.topxp_tree.heading("title", text="Title")
        self.topxp_tree.heading("xp", text="XP")
        self.topxp_tree.heading("date", text="Completed At")
        self.topxp_tree.column("title", width=210, anchor="w")
        self.topxp_tree.column("xp", width=70, anchor="center")
        self.topxp_tree.column("date", width=170, anchor="w")

        # ✅ Double click => details
        self.topxp_tree.bind("<Double-1>", lambda _e: self._open_topxp_details())

        # Most completed card
        self.most_card = tk.Frame(right, padx=10, pady=10, relief="groove", borderwidth=1)
        self.most_card.grid(row=2, column=0, sticky="ew", pady=(10, 0))

        self.most_title_var = tk.StringVar(value="Most Completed: -")
        self.most_meta_var = tk.StringVar(value="")

        ttk.Label(self.most_card, textvariable=self.most_title_var, font=("Segoe UI", 11, "bold")).pack(anchor="w")
        ttk.Label(self.most_card, textvariable=self.most_meta_var, foreground="#555").pack(anchor="w", pady=(2, 0))

        bottom = tk.Frame(self)
        bottom.pack(fill="x", pady=(10, 0))
        self.hint_var = tk.StringVar(value="Tip: Change Days / Top XP to update the panels.")
        ttk.Label(bottom, textvariable=self.hint_var, foreground="#555").pack(side="left")

    def _make_card(self, master: tk.Widget, title: str, value: str) -> tk.Frame:
        card = tk.Frame(master, padx=10, pady=10, relief="groove", borderwidth=1)
        card.columnconfigure(0, weight=1)

        tvar = tk.StringVar(value=title)
        vvar = tk.StringVar(value=value)

        card._title_var = tvar  # type: ignore[attr-defined]
        card._value_var = vvar  # type: ignore[attr-defined]

        ttk.Label(card, textvariable=tvar, foreground="#555").grid(row=0, column=0, sticky="w")
        ttk.Label(card, textvariable=vvar, font=("Segoe UI", 18, "bold")).grid(row=1, column=0, sticky="w", pady=(4, 0))
        return card

    # ---------------- Data ----------------
    def refresh(self) -> None:
        days = _safe_int(self.days_var.get(), 30)
        topn = _safe_int(self.topn_var.get(), 5)

        overview = self.service.stats_overview() or {}
        last_days = self.service.stats_last_days(days=days) or {}
        topxp = self.service.stats_top_xp(n=topn) or []
        most = self.service.stats_most_completed()

        total_logs = _safe_int(overview.get("total_logs", 0))
        total_xp = _safe_int(overview.get("total_xp", 0))
        ld_tasks = _safe_int(last_days.get("total_tasks", 0))
        ld_xp = _safe_int(last_days.get("total_xp", 0))

        self._set_card_value(self.kpi_total_logs, str(total_logs))
        self._set_card_value(self.kpi_total_xp, str(total_xp))
        self._set_card_value(self.kpi_last_days_tasks, str(ld_tasks))
        self._set_card_value(self.kpi_last_days_xp, str(ld_xp))

        by_type = last_days.get("by_type") or {}
        self._render_by_type(by_type, days=days, total_tasks=ld_tasks, total_xp=ld_xp)

        self._render_top_xp(topxp, n=topn)
        self._render_most_completed(most)

        self.set_status("Stats refreshed.")

    def _set_card_value(self, card: tk.Frame, value: str) -> None:
        vvar = getattr(card, "_value_var", None)
        if vvar is not None:
            vvar.set(value)

    def _render_by_type(self, by_type: Dict[str, int], *, days: int, total_tasks: int, total_xp: int) -> None:
        for item in self.by_type_tree.get_children():
            self.by_type_tree.delete(item)

        for ttype, cnt in sorted(by_type.items(), key=lambda x: x[0]):
            self.by_type_tree.insert("", "end", values=(ttype, int(cnt)))

        self.last_days_meta.set(f"{days}d | tasks={total_tasks} | xp={total_xp}")

    def _render_top_xp(self, topxp: List[Dict[str, Any]], *, n: int) -> None:
        # ✅ cache doldur (double click buradan okuyacak)
        self._topxp_rows = topxp[: max(n, 0)]

        for item in self.topxp_tree.get_children():
            self.topxp_tree.delete(item)

        for h in self._topxp_rows:
            self.topxp_tree.insert(
                "",
                "end",
                values=(
                    h.get("task_title") or "-",
                    _safe_int(h.get("gained_xp", 0)),
                    h.get("completed_at") or "",
                ),
            )

    def _render_most_completed(self, most: Optional[Dict[str, Any]]) -> None:
        if not most:
            self.most_title_var.set("Most Completed: -")
            self.most_meta_var.set("")
            return

        title = most.get("task_title") or "-"
        cnt = _safe_int(most.get("count", 0))
        self.most_title_var.set(f"Most Completed: {title}")
        self.most_meta_var.set(f"{cnt} times")

    def _open_topxp_details(self) -> None:
        sel = self.topxp_tree.selection()
        if not sel:
            return
        iid = sel[0]
        idx = self.topxp_tree.index(iid)
        if idx < 0 or idx >= len(self._topxp_rows):
            return
        data = self._topxp_rows[idx]
        LogDetailsDialog(self, title="Top XP Log Details", data=data)
