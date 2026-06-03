# services/app_service.py
from __future__ import annotations

import datetime
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from database.connection import get_connection
from database.task_repo import TaskRepository
from database.player_repo import PlayerRepository
from database.tasklog_repo import TaskLogRepository

from stats import stats_overview, last_n_days_summary, top_xp_tasks, most_completed_task

from history import log_task_completion
from badges import check_and_award_badges
from badges import (
    list_badges,
    search_badges,
    show_badge_details,
    list_badges_filtered,
)


@dataclass
class CompleteResult:
    ok: bool
    message: str
    gained_xp: int = 0
    level: int = 0
    xp: int = 0
    newly_awarded: List[Dict[str, str]] | None = None


class AppService:
    """
    GUI/CLI fark etmez: uygulamanın use-case'leri burada.
    GUI sadece burayı çağırır. Repo/SQL bilmez.
    """

    def __init__(self, *, tm: Any, player: Any, task_repo: TaskRepository, player_repo: PlayerRepository):
        self.tm = tm
        self.player = player
        self.task_repo = task_repo
        self.player_repo = player_repo
        self.tasklog_repo = TaskLogRepository()

    # ---------- Tasks ----------
    def list_tasks(self) -> List[Any]:
        self.tm.reload_from_repo()
        return list(self.tm.tasks)

    def get_task(self, task_id: int) -> Any | None:
        return self.task_repo.get_by_id(task_id)

    def add_task(self, data: Dict[str, Any]) -> Any:
        # TaskManager içinden ekleyelim (id üretimi + repo upsert akışı sende düzgün)
        t = self.tm.gorev_ekle(
            data["title"],
            data.get("description", ""),
            data.get("category", ""),
            data.get("priority", "medium"),
            data.get("difficulty", 2),
            data.get("task_type", "daily"),
        )
        return t

    def edit_task(self, task_id: int, data: Dict[str, Any]) -> bool:
        t = self.task_repo.get_by_id(task_id)
        if not t:
            return False

        # alan güncelle
        t.title = data["title"]
        t.description = data.get("description", "")
        t.category = data.get("category", "")
        t.priority = data.get("priority", "medium")
        t.difficulty = int(data.get("difficulty", 2))
        t.task_type = data.get("task_type", "daily")

        self.task_repo.upsert(t)  # kendi conn açar, tek işlem
        self.tm.reload_from_repo()
        return True

    def delete_task(self, task_id: int) -> bool:
        ok = self.task_repo.delete(task_id)
        self.tm.reload_from_repo()
        return ok

    def complete_task(self, task_id: int) -> CompleteResult:
        """
        Tek transaction içinde:
        - task update
        - task_log insert
        - badge_earned insert
        - player upsert
        """
        now = datetime.datetime.now()

        with get_connection() as conn:
            task = self.task_repo.get_by_id(task_id, conn=conn)
            if not task:
                return CompleteResult(ok=False, message="Task not found.")

            success = task.gorevi_tamamla(now=now, verbose=False)
            if not success:
                return CompleteResult(ok=False, message="This task is already completed for the current period.")

            # XP + level
            gained = self.player.xp_ekleme(task)

            # DB writes (aynı conn)
            self.task_repo.upsert(task, conn=conn)
            log_task_completion(self.player, task, gained, now=now, conn=conn)
            newly = check_and_award_badges(self.player, task, gained, self.tm, verbose=False, conn=conn)
            self.player_repo.upsert(self.player, conn=conn)
            # commit: context manager çıkışında 1 kez commit olur

        # memory sync
        self.tm.reload_from_repo()

        return CompleteResult(
            ok=True,
            message=f"Completed: +{gained} XP | Level: {self.player.level} | XP: {self.player.xp}",
            gained_xp=gained,
            level=self.player.level,
            xp=self.player.xp,
            newly_awarded=newly or [],
        )

    def list_badges(self, *, rarity: str | None = None, category: str | None = None):
        """
        UI için tek entrypoint:
        - rarity/category verilirse filtreli döner
        - yoksa owned + locked döner
        """
        if rarity or category:
            return list_badges_filtered(self.player, self.tm, rarity=rarity, category=category, verbose=False)
        return list_badges(self.player, task_manager=self.tm, verbose=False)

    def search_badges(self, query: str):
        return search_badges(query)

    def badge_details(self, badge_id: str):
        return show_badge_details(self.player, badge_id, task_manager=self.tm, verbose=False)

    def list_history(
            self,
            *,
            limit: int = 200,
            task_type: str | None = None,
            min_xp: int | None = None,
            query: str | None = None,
    ):
        """
        task_log tablosundan history döner (DB tek kaynak).
        Filtreler DB tarafında uygulanır.
        """
        if not hasattr(self, "tasklog_repo") or self.tasklog_repo is None:
            self.tasklog_repo = TaskLogRepository()

        return self.tasklog_repo.list_timeline(
            limit=limit,
            task_type=task_type,
            min_xp=min_xp,
            query=query,
        )
    def stats_overview(self):
        return stats_overview(verbose=False)

    def stats_last_days(self, days: int = 30):
        return last_n_days_summary(days=days, verbose=False)

    def stats_top_xp(self, n: int = 5):
        return top_xp_tasks(n=n, verbose=False)

    def stats_most_completed(self):
        return most_completed_task(verbose=False)