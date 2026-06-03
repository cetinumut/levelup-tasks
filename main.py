# main.py
from database.init_db import init_db
from database.player_repo import PlayerRepository
from database.task_repo import TaskRepository
from models import TaskManager
from time_utils import period_reset_if_needed
from menus import main_menu_loop

def bootstrap():
    init_db()  # tablo yoksa oluşturur

    task_repo = TaskRepository()
    player_repo = PlayerRepository()

    tm = TaskManager(repo=task_repo)
    tm.tasks = task_repo.list_all()

    player = player_repo.get()

    for t in tm.tasks:
        period_reset_if_needed(t)

    return player, tm, player_repo

def main():
    player, tm, player_repo = bootstrap()

    main_menu_loop(player, tm,player_repo)

    # çıkışta player'ı DB'ye kaydet
    player_repo.upsert(player)

    print("See you!")

if __name__ == "__main__":
    main()
