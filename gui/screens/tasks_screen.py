# gui/screens/tasks_screen.py
from __future__ import annotations

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Any, Callable, List, Optional

from gui.dialogs.task_form import TaskFormDialog


class TasksScreen(tk.Frame):
    def __init__(self, master, *, service: Any, set_status: Callable[[str], None]):
        super().__init__(master)
        self.service = service
        self.set_status = set_status

        self._debounce_after_id: str | None = None

        self._build_ui()
        self.refresh()

    # ---------------- UI ----------------
    def _build_ui(self) -> None:
        # Top row: title + action buttons
        top = tk.Frame(self)
        top.pack(fill="x")

        ttk.Label(top, text="Tasks", font=("Segoe UI", 16, "bold")).pack(side="left")

        ttk.Button(top, text="Add", command=self._add).pack(side="right", padx=(6, 0))
        ttk.Button(top, text="Edit", command=self._edit).pack(side="right", padx=(6, 0))
        ttk.Button(top, text="Delete", command=self._delete).pack(side="right", padx=(6, 0))
        ttk.Button(top, text="Complete", command=self._complete).pack(side="right", padx=(6, 0))
        ttk.Button(top, text="Refresh", command=self.refresh).pack(side="right", padx=(6, 0))

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 8))

        # Filters row
        filters = tk.Frame(self)
        filters.pack(fill="x")

        ttk.Label(filters, text="Search:").pack(side="left", padx=(0, 6))
        self.search_var = tk.StringVar(value="")
        self.search_entry = ttk.Entry(filters, textvariable=self.search_var, width=28)
        self.search_entry.pack(side="left", padx=(0, 14))
        self.search_entry.bind("<KeyRelease>", self._debounced_refresh)

        ttk.Label(filters, text="Status:").pack(side="left", padx=(0, 6))
        self.status_var = tk.StringVar(value="All")
        self.status_cb = ttk.Combobox(
            filters,
            textvariable=self.status_var,
            values=["All", "Pending", "Done"],
            state="readonly",
            width=10,
        )
        self.status_cb.pack(side="left", padx=(0, 14))
        self.status_cb.bind("<<ComboboxSelected>>", lambda _e: self.refresh())

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

        ttk.Button(filters, text="Clear", command=self._clear_filters).pack(side="left")

        ttk.Separator(self, orient="horizontal").pack(fill="x", pady=(10, 10))

        # Table
        columns = ("id", "title", "type", "priority", "difficulty", "status", "streak", "best_streak")
        self.tree = ttk.Treeview(self, columns=columns, show="headings", height=20)
        self.tree.pack(fill="both", expand=True)

        headings = {
            "id": "ID",
            "title": "Title",
            "type": "Type",
            "priority": "Priority",
            "difficulty": "Diff",
            "status": "Status",
            "streak": "Streak",
            "best_streak": "Best",
        }
        for col in columns:
            self.tree.heading(col, text=headings[col])
            self.tree.column(col, width=120, anchor="w")

        self.tree.column("id", width=60, anchor="center")
        self.tree.column("difficulty", width=60, anchor="center")
        self.tree.column("status", width=90, anchor="center")
        self.tree.column("streak", width=70, anchor="center")
        self.tree.column("best_streak", width=70, anchor="center")

        # double click edit
        self.tree.bind("<Double-1>", lambda _e: self._edit())

        # Bottom summary
        bottom = tk.Frame(self)
        bottom.pack(fill="x", pady=(10, 0))

        self.summary_var = tk.StringVar(value="")
        ttk.Label(bottom, textvariable=self.summary_var, foreground="#444").pack(side="left")

    # ---------------- Helpers ----------------
    def _debounced_refresh(self, _evt=None) -> None:
        # Search yazarken her tuşta DB çağırmayalım, 250ms bekletelim.
        if self._debounce_after_id:
            try:
                self.after_cancel(self._debounce_after_id)
            except Exception:
                pass
        self._debounce_after_id = self.after(250, self.refresh)

    def _clear_filters(self) -> None:
        self.search_var.set("")
        self.status_var.set("All")
        self.type_var.set("All")
        self.refresh()
        self.set_status("Filters cleared.")

    def _selected_task_id(self) -> int | None:
        sel = self.tree.selection()
        if not sel:
            return None
        vals = self.tree.item(sel[0], "values")
        if not vals:
            return None
        try:
            return int(vals[0])
        except Exception:
            return None

    # ---------------- Data / Render ----------------
    def refresh(self) -> None:
        tasks = self.service.list_tasks()

        # Apply filters
        q = (self.search_var.get() or "").strip().lower()
        status_f = self.status_var.get()
        type_f = self.type_var.get()

        filtered = []
        for t in tasks:
            title = (getattr(t, "title", "") or "").lower()
            desc = (getattr(t, "description", "") or "").lower()
            cat = (getattr(t, "category", "") or "").lower()

            if q and (q not in title and q not in desc and q not in cat):
                continue

            is_done = bool(getattr(t, "status", False))
            if status_f == "Done" and not is_done:
                continue
            if status_f == "Pending" and is_done:
                continue

            ttype = getattr(t, "task_type", "") or ""
            if type_f != "All" and ttype != type_f:
                continue

            filtered.append(t)

        # Clear tree
        for item in self.tree.get_children():
            self.tree.delete(item)

        # Fill
        total_all = len(tasks)
        total = len(filtered)
        done = 0
        for t in filtered:
            is_done = bool(getattr(t, "status", False))
            if is_done:
                done += 1

            status_txt = "Done" if is_done else "Pending"

            self.tree.insert(
                "",
                "end",
                values=(
                    getattr(t, "id", 0),
                    getattr(t, "title", ""),
                    getattr(t, "task_type", ""),
                    getattr(t, "priority", ""),
                    getattr(t, "difficulty", 2),
                    status_txt,
                    getattr(t, "streak", 0),
                    getattr(t, "best_streak", 0),
                ),
            )

        pending = total - done
        if total != total_all:
            self.summary_var.set(f"Showing: {total}/{total_all} | Done: {done} | Pending: {pending}")
        else:
            self.summary_var.set(f"Total: {total} | Done: {done} | Pending: {pending}")

        self.set_status("Tasks refreshed.")

    # ---------------- Actions ----------------
    def _add(self) -> None:
        dlg = TaskFormDialog(self, title="Add Task")
        self.wait_window(dlg)
        if not dlg.result:
            return

        self.service.add_task(dlg.result)
        self.refresh()
        self.set_status("Task added.")

    def _edit(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            messagebox.showinfo("Edit", "Select a task first.")
            return

        t = self.service.get_task(task_id)
        if not t:
            messagebox.showerror("Edit", "Task not found.")
            return

        initial = {
            "title": getattr(t, "title", ""),
            "description": getattr(t, "description", ""),
            "category": getattr(t, "category", ""),
            "priority": getattr(t, "priority", "medium"),
            "difficulty": getattr(t, "difficulty", 2),
            "task_type": getattr(t, "task_type", "daily"),
        }

        dlg = TaskFormDialog(self, title=f"Edit Task #{task_id}", initial=initial)
        self.wait_window(dlg)
        if not dlg.result:
            return

        ok = self.service.edit_task(task_id, dlg.result)
        if not ok:
            messagebox.showerror("Edit", "Update failed.")
            return

        self.refresh()
        self.set_status("Task updated.")

    def _delete(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            messagebox.showinfo("Delete", "Select a task first.")
            return

        if not messagebox.askyesno("Delete", f"Delete task #{task_id}?"):
            return

        ok = self.service.delete_task(task_id)
        if not ok:
            messagebox.showerror("Delete", "Delete failed.")
            return

        self.refresh()
        self.set_status("Task deleted.")

    def _complete(self) -> None:
        task_id = self._selected_task_id()
        if task_id is None:
            messagebox.showinfo("Complete", "Select a task first.")
            return

        res = self.service.complete_task(task_id)
        if not res.ok:
            messagebox.showwarning("Complete", res.message)
            self.set_status(res.message)
            return

        if res.newly_awarded:
            lines = "\n".join([f"- {b['name']}" for b in res.newly_awarded])
            messagebox.showinfo("New Badges!", f"🏅 New badges unlocked:\n{lines}")

        self.refresh()
        self.set_status(res.message)
