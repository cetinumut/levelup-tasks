#time_utils
import datetime

#ZAMAN FONKSİYONLARI
def parse_iso_datetime(dt_str):
    if not dt_str:
        return None
    try:
        return datetime.datetime.fromisoformat(dt_str)
    except ValueError:
        return None

def period_key(task_type, dt):
    """dt: datetime -> task_type'a gore period anahtari"""
    if task_type == "daily":
        return dt.date().isoformat()  # "2026-01-20"
    if task_type == "weekly":
        iso_year, iso_week, _ = dt.isocalendar()
        return f"{iso_year}-W{iso_week:02d}"  # "2026-W04"
    if task_type == "monthly":
        return f"{dt.year}-{dt.month:02d}"  # "2026-01"
    if task_type == "epic":
        return None
    return dt.date().isoformat()

def is_next_period(task_type, last_dt, now_dt):
    """last_dt -> now_dt tam olarak bir sonraki period mu?"""
    if task_type == "daily":
        return (now_dt.date() - last_dt.date()).days == 1

    if task_type == "weekly":
        ly, lw, _ = last_dt.isocalendar()
        ny, nw, _ = now_dt.isocalendar()
        # geçen hafta -> bu hafta kontrolü (yıl geçişini de kapsar)
        last_monday = last_dt - datetime.timedelta(days=last_dt.weekday())
        next_monday = last_monday + datetime.timedelta(days=7)
        now_monday = now_dt - datetime.timedelta(days=now_dt.weekday())
        return now_monday.date() == next_monday.date()

    if task_type == "monthly":
        last_total = last_dt.year * 12 + last_dt.month
        now_total = now_dt.year * 12 + now_dt.month
        return (now_total - last_total) == 1

    return False


def period_reset_if_needed(task):
    if task.task_type not in ["daily", "weekly", "monthly"]:
        return

    last_dt = parse_iso_datetime(task.completed_at)
    if not last_dt:
        task.status = False
        return

    now = datetime.datetime.now()
    if period_key(task.task_type, now) != period_key(task.task_type, last_dt):
        task.status = False


