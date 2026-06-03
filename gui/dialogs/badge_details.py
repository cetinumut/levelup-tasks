# gui/dialogs/badge_details.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk


def _clamp(n: int, lo: int, hi: int) -> int:
    return max(lo, min(hi, n))


class BadgeDetailsDialog(tk.Toplevel):
    def __init__(self, master: tk.Widget, *, badge: dict, info: dict):
        super().__init__(master)
        self.badge = badge
        self.info = info

        self.title("Badge Details")
        self.resizable(False, False)

        self._build_ui()
        self._center_over_master(master)

        # modal (isteğe bağlı ama güzel)
        self.transient(master.winfo_toplevel())
        self.grab_set()
        self.focus_set()

    def _build_ui(self) -> None:
        pad = 12
        root = ttk.Frame(self, padding=pad)
        root.grid(row=0, column=0, sticky="nsew")

        # icon + header
        header = ttk.Frame(root)
        header.grid(row=0, column=0, sticky="ew")
        header.columnconfigure(1, weight=1)

        emoji = self.badge.get("emoji", "🏅")
        ttk.Label(header, text=emoji, font=("Segoe UI", 22)).grid(row=0, column=0, rowspan=3, padx=(0, 10))

        bid = self.info.get("id", "")
        name = self.info.get("name", "")
        owned = bool(self.info.get("owned", False))

        ttk.Label(header, text=name, font=("Segoe UI", 13, "bold")).grid(row=0, column=1, sticky="w")
        ttk.Label(header, text=f"ID: {bid}", foreground="#555").grid(row=1, column=1, sticky="w")
        ttk.Label(header, text=f"Owned: {'Yes' if owned else 'No'}", foreground="#555").grid(row=2, column=1, sticky="w")

        ttk.Separator(root, orient="horizontal").grid(row=1, column=0, sticky="ew", pady=(10, 10))

        # description
        desc = self.info.get("description", "") or ""
        ttk.Label(root, text=desc, wraplength=420, justify="left").grid(row=2, column=0, sticky="w")

        # progress (locked ise göster; owned ise %100 göstermek de güzel)
        cur = int(self.info.get("progress_current", 0) or 0)
        tgt = int(self.info.get("progress_target", 1) or 1)
        tgt = max(tgt, 1)
        cur = _clamp(cur, 0, tgt)

        pct = int(round((cur / tgt) * 100))
        if owned:
            pct = 100  # unlock olduysa 100 gösterelim

        ttk.Separator(root, orient="horizontal").grid(row=3, column=0, sticky="ew", pady=(10, 10))

        prog_title = "Progress"
        ttk.Label(root, text=prog_title, font=("Segoe UI", 10, "bold")).grid(row=4, column=0, sticky="w")

        self.pb_var = tk.IntVar(value=_clamp(pct, 0, 100))
        pb = ttk.Progressbar(root, orient="horizontal", mode="determinate", maximum=100, variable=self.pb_var)
        pb.grid(row=5, column=0, sticky="ew", pady=(4, 2))

        meta = "Unlocked ✅" if owned else f"{cur}/{tgt} ({pct}%)"
        ttk.Label(root, text=meta, foreground="#555").grid(row=6, column=0, sticky="w")

        # button row
        btns = ttk.Frame(root)
        btns.grid(row=7, column=0, sticky="e", pady=(12, 0))
        ttk.Button(btns, text="Tamam", command=self.destroy).pack()

    def _center_over_master(self, master: tk.Widget) -> None:
        self.update_idletasks()
        w = self.winfo_width()
        h = self.winfo_height()

        try:
            mx = master.winfo_rootx()
            my = master.winfo_rooty()
            mw = master.winfo_width()
            mh = master.winfo_height()
            x = mx + (mw // 2) - (w // 2)
            y = my + (mh // 2) - (h // 2)
        except Exception:
            x = 200
            y = 200

        self.geometry(f"{w}x{h}+{x}+{y}")
