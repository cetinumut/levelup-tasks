# services/complete_task_service.py
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from database.connection import get_connection
from database.task_repo import TaskRepository
from database.player_repo import PlayerRepository

from history import log_task_completion
from badges import check_and_award_badges


def complete_task_service(
    *,
    task_id: int,
    player: Any,
    tm: Any,
    task_repo: TaskRepository,
    player_repo: PlayerRepository,
    now: Optional[datetime.datetime] = None,
    verbose: bool = True,
) -> Dict[str, Any]:
    """
    Tek transaction (tek commit) içinde:
    - task tamamla + task update
    - player xp/level update + player upsert
    - task_log insert
    - badge_earned insert(ler)

    Dönüş:
      {
        "ok": bool,
        "task": Task|None,
        "gained_xp": int,
        "new_badges": List[dict],
        "message": str
      }
    """
    now = now or datetime.datetime.now()

    conn = get_connection()
    try:
        conn.execute("BEGIN")

        # 1) En güncel task'i DB'den çek
        task = task_repo.get_by_id(task_id, conn=conn)
        if task is None:
            conn.rollback()
            return {
                "ok": False,
                "task": None,
                "gained_xp": 0,
                "new_badges": [],
                "message": "There are no tasks associated with this ID.",
            }

        # 2) Domain kuralı: period aynıysa completion reddedilebilir
        success = task.gorevi_tamamla(now=now, verbose=verbose)
        if not success:
            # gorevi_tamamla zaten mesaj basıyor (verbose=True)
            conn.rollback()
            return {
                "ok": False,
                "task": task,
                "gained_xp": 0,
                "new_badges": [],
                "message": "This task is already completed for the current period.",
            }

        # 3) Task DB update
        task_repo.upsert(task, conn=conn)

        # 4) Player XP/level update + DB upsert
        gained = player.xp_ekleme(task)
        player_repo.upsert(player, conn=conn)

        # 5) task_log insert (aynı conn)
        log_task_completion(player, task, gained, now=now, conn=conn)

        # 6) badge_earned insert(ler) (aynı conn)
        new_badges = check_and_award_badges(
            player,
            task,
            gained,
            tm,
            verbose=verbose,
            conn=conn,
        )

        conn.commit()

    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

    # Transaction bitti → in-memory sync
    try:
        tm.reload_from_repo()
    except Exception:
        # GUI'ye geçince tm farklı olabilir; sorun çıkarma
        pass

    return {
        "ok": True,
        "task": task,
        "gained_xp": int(gained or 0),
        "new_badges": new_badges or [],
        "message": "OK",
    }
