#models.py
from __future__ import annotations
import datetime
from time_utils import parse_iso_datetime, period_key, is_next_period
from typing import Optional, List
import sqlite3



class Task:
    def __init__(
        self,
        id: int | None = None,
        title: str = "title",
        description: str = "",
        category: str = "category",
        priority: str = "medium",
        difficulty: int = 2,
        task_type: str = "daily",
        status: bool = False,
        created_at: str | None = None,
        due_date: str | None = None,
        streak: int = 0,
        completed_at: str | None = None,
        best_streak: int = 0,
    ):
        self.id = int(id) if id is not None else None
        self.title = title
        self.description = description
        self.category = category
        self.priority = priority
        self.difficulty = int(difficulty) if difficulty is not None else 2
        self.task_type = task_type
        self.status = bool(status)
        self.created_at = created_at
        self.due_date = due_date
        self.streak = int(streak or 0)
        self.completed_at = completed_at
        self.best_streak = int(best_streak or 0)


    #görevi kontrol etmek için kullanılır. statusü True yapar.

    def gorevi_tamamla(self, now=None, verbose=True):
        now = now or datetime.datetime.now()
        now_iso = now.isoformat()

        if self.task_type == "epic":
            self.status = True
            self.completed_at = now_iso
            return True

        last_dt = parse_iso_datetime(self.completed_at)
        current_period = period_key(self.task_type, now)
        last_period = period_key(self.task_type, last_dt) if last_dt else None

        if last_period is not None and current_period == last_period:
            self.status = True
            if verbose:
                print("This task is already completed for the current period.")
            return False  # <<< önemli

        if last_dt and is_next_period(self.task_type, last_dt, now):
            self.streak += 1
        else:
            self.streak = 1

        if self.streak > self.best_streak:
            self.best_streak = self.streak

        self.status = True
        self.completed_at = now_iso
        return True

    def __str__(self):
        status_text = "Done" if self.status else "Pending"

        # daily/weekly/monthly için streak göster
        if self.task_type in ["daily", "weekly", "monthly"]:
            return f"[{self.id}] {self.title} | {self.task_type} | {self.priority} | Status: {status_text} | Streak: {self.streak} (Best: {self.best_streak})"

        # epic için streak yok
        return f"[{self.id}] {self.title} | {self.task_type} | {self.priority} | Status: {status_text}"

    #görevin xp değerini hesaplayan metot

    def xp_hesapla_gorev(self):
        if self.task_type == "daily" :
            tur_xp = 10
        elif self.task_type == "weekly":
            tur_xp = 50
        elif self.task_type == "monthly":
            tur_xp = 200
        elif self.task_type == "epic":
            tur_xp = 1000
        else:
            tur_xp = 10
        if self.difficulty == 1 :
            zorluk_xp = 0.8
        elif self.difficulty == 2 :
            zorluk_xp = 1
        elif self.difficulty ==3:
            zorluk_xp = 1.2
        else:
            zorluk_xp = 1
        if self.priority == "low":
            oncelik_xp = 0.9
        elif self.priority == "medium":
            oncelik_xp = 1
        elif self.priority == "high":
            oncelik_xp = 1.1
        else:
            oncelik_xp = 1

        xp_gorev = tur_xp * zorluk_xp * oncelik_xp
        return int(xp_gorev)

    # Task'ın bütün alanlarını dict. olarak döndürür.
    def to_dict(self):
        data = {"id": self.id,
                "title": self.title,
                "description": self.description,
                "category": self.category,
                "priority": self.priority,
                "difficulty": self.difficulty,
                "task_type": self.task_type,
                "status": self.status,
                "created_at": self.created_at,
                "due_date": self.due_date,
                "streak": self.streak,
                "completed_at": self.completed_at,
                "best_streak": self.best_streak
        }
        return data

    #Data isimli bir dict'den Task objesi üretip döndürür.
    @classmethod
    def from_dict(cls, data):
        return cls(
            id=data.get("id"),
            title=data.get("title"),
            description=data.get("description"),
            category=data.get("category"),
            priority=data.get("priority"),
            difficulty=data.get("difficulty"),
            task_type=data.get("task_type"),
            status=data.get("status"),
            created_at=data.get("created_at"),
            due_date=data.get("due_date"),
            streak=data.get("streak",0),
            completed_at=data.get("completed_at"),
            best_streak=data.get("best_streak",0)
        )

    def detay_yazdir(self):
        print("\n--- TASK DETAILS ---")
        print(f"ID: {self.id}")
        print(f"Title: {self.title}")
        print(f"Description: {self.description}")
        print(f"Category: {self.category}")
        print(f"Priority: {self.priority}")
        print(f"Difficulty: {self.difficulty}")
        print(f"Type: {self.task_type}")
        print(f"Status: {'Done' if self.status else 'Pending'}")
        print(f"Completed At: {self.completed_at}")
        if self.task_type in ["daily", "weekly", "monthly"]:
            print(f"Streak: {self.streak}")
            print(f"Best Streak: {self.best_streak}")


class Player():
    def __init__(self,username,level=1,xp=0,xp_for_next_level=100,completed_tasks=0,badges=None,badge_history=None, task_history=None):
        self.username = username
        self.level = level
        self.xp = xp
        self.xp_for_next_level = xp_for_next_level
        self.completed_tasks = completed_tasks
        self.badges = badges or []
        self.badge_history = badge_history or []
        self.task_history = task_history or []


        #görevden gelen xpyi mevcut xpye ekler.gerekirse level atlatır. completed_task sayacını arttırır.
    def xp_ekleme(self,task):
        gained_xp = task.xp_hesapla_gorev()
        self.xp += gained_xp
        self.completed_tasks += 1
        self.level_kontrol()
        return gained_xp
    #leveli kontrol edip. arttırır.
    def level_kontrol(self):
        while self.xp >= self.xp_for_next_level:
            self.level += 1
            self.xp = self.xp - self.xp_for_next_level
            self.xp_for_next_level = 50 * self.level * self.level

    def istatistik_yazdir(self):
        print(f"Player's name: {self.username}")
        print(f"Level: {self.level}")
        print(f"XP: {self.xp}")
        print(f"XP need for next level : {self.xp_for_next_level}")
        print(f"List completed tasks : {self.completed_tasks}")

    #Player alanlarını dict olarak döndürür.
    def to_dict(self):
        data = {"username": self.username,
                "level": self.level,
                "xp": self.xp,
                "xp_for_next_level": self.xp_for_next_level,
                "completed_tasks": self.completed_tasks,
                "badges": self.badges,
                "badge_history": self.badge_history,
                "task_history": self.task_history
                }
        return data

    #Dictden player yaratıp döndürür.
    @classmethod
    def from_dict(cls, data):
        return cls(
            username=data.get("username"),
            level=data.get("level", 1),
            xp=data.get("xp", 0),
            xp_for_next_level=data.get("xp_for_next_level", 100),
            completed_tasks=data.get("completed_tasks", 0),
            badges=data.get("badges", []),
            badge_history=data.get("badge_history", []),
            task_history=data.get("task_history", []),

        )



class TaskManager:
    def __init__(self, repo=None):
        self.tasks: List[Task] = []
        self.repo = repo  # TaskRepository

    # ---------- LOAD / SYNC ----------
    def reload_from_repo(self, conn: sqlite3.Connection | None = None) -> None:
        if self.repo is None:
            return
        self.tasks.clear()
        self.tasks.extend(self.repo.list_all(conn=conn))

    def _sync_after_write(self, conn: sqlite3.Connection | None = None) -> None:
        """DB tek kaynak: her write sonrası belleği DB’den güncelle."""
        if self.repo is None:
            return
        self.tasks = self.repo.list_all(conn=conn)

    # ---------- CRUD ----------
    def gorev_ekle(
        self,
        title: str,
        description: str = "",
        category: str = "common",
        priority: str = "medium",
        difficulty: int = 2,
        task_type: str = "daily",
        conn: sqlite3.Connection | None = None,
    ) -> Task:
        yeni = Task(
            id=None,  # repo insert edince id set edecek
            title=title,
            description=description,
            category=category,
            priority=priority,
            difficulty=difficulty,
            task_type=task_type,
            status=False,
        )

        if self.repo:
            yeni = self.repo.upsert(yeni, conn=conn)  # id set olur
            self._sync_after_write(conn=conn)
        else:
            # JSON/legacy fallback
            yeni.id = (max((t.id for t in self.tasks), default=0) + 1)
            self.tasks.append(yeni)

        return yeni

    def tum_gorevleri_listele(self) -> None:
        if not self.tasks:
            print("There are no tasks.")
            return
        for task in self.tasks:
            print(task)

    def bekleyen_gorevleri_listele(self) -> None:
        pending = [t for t in self.tasks if not getattr(t, "status", False)]
        if not pending:
            print("(no pending tasks)")
            return
        for t in pending:
            print(t)

    def tamamlanan_gorevleri_listele(self) -> None:
        done = [t for t in self.tasks if getattr(t, "status", False)]
        if not done:
            print("(no completed tasks)")
            return
        for t in done:
            print(t)

    def gorevleri_oncelige_gore_listele(self) -> None:
        order = {"high": 0, "medium": 1, "low": 2}
        for t in sorted(self.tasks, key=lambda x: order.get(getattr(x, "priority", "medium"), 1)):
            print(t)

    def gorevleri_ture_gore_listele(self, task_type: str) -> None:
        task_type = (task_type or "").strip().lower()
        filtered = [t for t in self.tasks if getattr(t, "task_type", "").lower() == task_type]
        if not filtered:
            print("(none)")
            return
        for t in filtered:
            print(t)

    def id_ile_gorev_bul(self, gorev_id: int) -> Optional[Task]:
        for task in self.tasks:
            if task.id == gorev_id:
                return task
        return None

    def gorev_tamamla(self, gorev_id, now=None):
        task = self.id_ile_gorev_bul(gorev_id)
        if task is None:
            print("There are no tasks associated with this ID.")
            return None

        success = task.gorevi_tamamla(now=now, verbose=True)
        if not success:
            return None

        return task

    def gorev_sil(self, gorev_id: int, conn: sqlite3.Connection | None = None) -> bool:
        task = self.id_ile_gorev_bul(gorev_id)
        if task is None:
            return False

        if self.repo:
            ok = self.repo.delete(gorev_id, conn=conn)
            self._sync_after_write(conn=conn)
            return ok

        self.tasks.remove(task)
        return True

    def gorev_guncelle(self, task: Task, conn: sqlite3.Connection | None = None) -> None:
        if task is None:
            return

        if self.repo:
            self.repo.upsert(task, conn=conn)
            self._sync_after_write(conn=conn)
            return

        # JSON/legacy fallback: zaten aynı objeyi tutuyorsun → ekstra işlem gerekmez
        return
