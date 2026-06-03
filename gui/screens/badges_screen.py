# gui/screens/badges_screen.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Callable, Optional

from badges import list_badges, show_badge_details
from gui.dialogs.badge_details import BadgeDetailsDialog


def _badge_label(b: dict) -> str:
    emoji = b.get("emoji", "🏅")
    name = b.get("name", "-")
    rarity = b.get("rarity", "common")
    category = b.get("category", "misc")
    return f"{emoji} {name} [{rarity}/{category}]"


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


class BadgesScreen(tk.Frame):
    def __init__(self, master: tk.Widget, *, service, set_status: Callable[[str], None]):
        super().__init__(master)
        self.service = service
        self.set_status = set_status

        self._owned_items: list[dict] = []
        self._locked_items: list[tuple[dict, int, int]] = []  # (badge, cur, tgt)

        self._build_ui()
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        top = tk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="Badges", font=("Segoe UI", 16, "bold")).pack(side="left")
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        filters = tk.Frame(self)
        filters.pack(fill="x")

        ttk.Label(filters, text="Rarity:").pack(side="left", padx=(0, 6))
        self.rarity_var = tk.StringVar(value="")
        self.rarity_cb = ttk.Combobox(
            filters,
            textvariable=self.rarity_var,
            values=["", "common", "rare", "epic", "legendary"],
            state="readonly",
            width=12,
        )
        self.rarity_cb.pack(side="left", padx=(0, 16))

        ttk.Label(filters, text="Category:").pack(side="left", padx=(0, 6))
        self.category_var = tk.StringVar(value="")
        self.category_cb = ttk.Combobox(
            filters,
            textvariable=self.category_var,
            values=["", "progress", "streak", "xp", "misc"],
            state="readonly",
            width=12,
        )
        self.category_cb.pack(side="left", padx=(0, 16))

        ttk.Button(filters, text="Apply", command=self.apply_filters).pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=10)

        body = tk.Frame(self)
        body.pack(fill="both", expand=True)

        body.columnconfigure(0, weight=1)
        body.columnconfigure(1, weight=1)
        body.rowconfigure(0, weight=1)

        left = tk.Frame(body)
        left.grid(row=0, column=0, sticky="nsew", padx=(0, 8))
        ttk.Label(left, text="Owned", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        self.owned_list = tk.Listbox(left, height=18)
        self.owned_list.pack(fill="both", expand=True)
        self.owned_list.bind("<<ListboxSelect>>", self._on_select_owned)

        right = tk.Frame(body)
        right.grid(row=0, column=1, sticky="nsew", padx=(8, 0))
        ttk.Label(right, text="Locked", font=("Segoe UI", 12, "bold")).pack(anchor="w", pady=(0, 6))

        self.locked_list = tk.Listbox(right, height=18)
        self.locked_list.pack(fill="both", expand=True)
        self.locked_list.bind("<<ListboxSelect>>", self._on_select_locked)

        bottom = tk.Frame(self)
        bottom.pack(fill="x", pady=(10, 0))

        prog_box = tk.Frame(bottom)
        prog_box.pack(side="left", fill="x", expand=True)

        self.progress_title_var = tk.StringVar(value="Select a badge to see progress.")
        ttk.Label(prog_box, textvariable=self.progress_title_var).pack(anchor="w")

        self.progress_var = tk.IntVar(value=0)
        self.progressbar = ttk.Progressbar(
            prog_box,
            orient="horizontal",
            mode="determinate",
            maximum=100,
            variable=self.progress_var,
        )
        self.progressbar.pack(fill="x", pady=(4, 0))

        self.progress_meta_var = tk.StringVar(value="")
        ttk.Label(prog_box, textvariable=self.progress_meta_var, foreground="#555").pack(anchor="w", pady=(2, 0))

        self.counts_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.counts_var, foreground="#444").pack(side="left", padx=(12, 0))

        ttk.Button(bottom, text="Details…", command=self.show_details_for_selected).pack(side="right")

    # ---------------- Data ----------------
    def refresh(self) -> None:
        # DB tek kaynak: tasks DB'den reload
        self.service.tm.reload_from_repo()

        owned, locked = list_badges(self.service.player, task_manager=self.service.tm, verbose=False)
        self._owned_items = owned
        self._locked_items = locked

        self._render_lists()
        self._render_counts()
        self._clear_progress()

        self.set_status("Badges refreshed.")

    def apply_filters(self) -> None:
        rarity = self.rarity_var.get().strip() or None
        category = self.category_var.get().strip() or None

        owned, locked = list_badges(self.service.player, task_manager=self.service.tm, verbose=False)

        def match(b: dict) -> bool:
            if rarity and b.get("rarity") != rarity:
                return False
            if category and b.get("category") != category:
                return False
            return True

        self._owned_items = [b for b in owned if match(b)]
        self._locked_items = [(b, cur, tgt) for (b, cur, tgt) in locked if match(b)]

        self._render_lists()
        self._render_counts()
        self._clear_progress()

        self.set_status("Filter applied.")

    def _render_lists(self) -> None:
        self.owned_list.delete(0, "end")
        self.locked_list.delete(0, "end")

        for b in self._owned_items:
            self.owned_list.insert("end", _badge_label(b))

        for b, cur, tgt in self._locked_items:
            self.locked_list.insert("end", f"{_badge_label(b)} ({cur}/{tgt})")

    def _render_counts(self) -> None:
        self.counts_var.set(f"Owned: {len(self._owned_items)} | Locked: {len(self._locked_items)}")

    # ---------------- Selection / Progress ----------------
    def _clear_progress(self) -> None:
        self.progress_var.set(0)
        self.progress_title_var.set("Select a badge to see progress.")
        self.progress_meta_var.set("")
        self.owned_list.selection_clear(0, "end")
        self.locked_list.selection_clear(0, "end")

    def _on_select_owned(self, _evt=None) -> None:
        self.locked_list.selection_clear(0, "end")
        idxs = self.owned_list.curselection()
        if not idxs:
            return
        b = self._owned_items[int(idxs[0])]
        self._set_progress_for_badge(badge=b, owned=True, cur=1, tgt=1)

    def _on_select_locked(self, _evt=None) -> None:
        self.owned_list.selection_clear(0, "end")
        idxs = self.locked_list.curselection()
        if not idxs:
            return
        b, cur, tgt = self._locked_items[int(idxs[0])]
        self._set_progress_for_badge(badge=b, owned=False, cur=cur, tgt=tgt)

    def _set_progress_for_badge(self, *, badge: dict, owned: bool, cur: int, tgt: int) -> None:
        name = badge.get("name", "-")
        rarity = badge.get("rarity", "common")
        category = badge.get("category", "misc")

        if owned:
            pct = 100
            self.progress_title_var.set(f"✅ {name} [{rarity}/{category}]")
            self.progress_meta_var.set("Unlocked ✅")
        else:
            tgt = max(int(tgt or 1), 1)
            cur = _clamp(int(cur or 0), 0, tgt)
            pct = int(round((cur / tgt) * 100))
            self.progress_title_var.set(f"🔒 {name} [{rarity}/{category}]")
            self.progress_meta_var.set(f"Progress: {cur}/{tgt} ({pct}%)")

        self.progress_var.set(_clamp(pct, 0, 100))

    # ---------------- Details ----------------
    def show_details_for_selected(self) -> None:
        b = self._get_selected_badge()
        if not b:
            messagebox.showinfo("Badge Details", "Select a badge first.")
            return

        info = show_badge_details(self.service.player, b.get("id", ""), task_manager=self.service.tm, verbose=False)
        if not info:
            messagebox.showinfo("Badge Details", "Badge not found.")
            return

        BadgeDetailsDialog(self, badge=b, info=info)

    def _get_selected_badge(self) -> Optional[dict]:
        idxs_o = self.owned_list.curselection()
        if idxs_o:
            return self._owned_items[int(idxs_o[0])]

        idxs_l = self.locked_list.curselection()
        if idxs_l:
            b, _cur, _tgt = self._locked_items[int(idxs_l[0])]
            return b

        return None
