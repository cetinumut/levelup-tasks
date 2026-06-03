#badges.py
from __future__ import annotations
import sqlite3
import datetime
import json
from typing import Any, Callable, Dict, List, Tuple, TypedDict, Literal, cast
from database.badge_repo import BadgeRepository
_badge_repo = BadgeRepository()
# =========================
# Types
# =========================

RuleFn = Callable[[Any, Any, int, Any], bool]
ProgressFn = Callable[[Any, Any, int, Any], Tuple[int, int]]  # (current, target)

Rarity = Literal["common", "rare", "epic", "legendary"]
Category = Literal["progress", "streak", "xp", "misc"]


class Badge(TypedDict, total=False):
    id: str
    name: str
    description: str
    rarity: Rarity
    category: Category
    emoji: str
    progress: ProgressFn
    rule: RuleFn


# =========================
# Helpers
# =========================



def _count_completed_by_type(task_manager, task_type: str) -> int:
    return sum(
        1 for t in getattr(task_manager, "tasks", [])
        if getattr(t, "status", False) is True and getattr(t, "task_type", None) == task_type
    )


def _max_streak_any(task_manager, task_type: str | None = None) -> int:
    mx = 0
    for t in getattr(task_manager, "tasks", []):
        if task_type and getattr(t, "task_type", None) != task_type:
            continue
        mx = max(mx, int(getattr(t, "streak", 0) or 0))
    return mx


# =========================
# Progress builders
# =========================

def _progress_tasks_completed(target: int) -> ProgressFn:
    def progress(player, _task, _gained_xp, _tm) -> Tuple[int, int]:
        cur = int(getattr(player, "completed_tasks", 0) or 0)
        return min(cur, target), target
    return progress


def _progress_complete_type(task_type: str, target: int) -> ProgressFn:
    def progress(_player, _task, _gained_xp, tm) -> Tuple[int, int]:
        cur = _count_completed_by_type(tm, task_type)
        return min(cur, target), target
    return progress


def _progress_single_task_streak(target: int) -> ProgressFn:
    def progress(_player, task, _gained_xp, _tm) -> Tuple[int, int]:
        cur = int(getattr(task, "streak", 0) or 0)
        return min(cur, target), target
    return progress


def _progress_any_task_streak(target: int, task_type: str | None = None) -> ProgressFn:
    def progress(_player, _task, _gained_xp, tm) -> Tuple[int, int]:
        cur = _max_streak_any(tm, task_type=task_type)
        return min(cur, target), target
    return progress


def _progress_xp_single(target: int) -> ProgressFn:
    def progress(_player, _task, gained_xp, _tm) -> Tuple[int, int]:
        cur = int(gained_xp or 0)
        return min(cur, target), target
    return progress


def _rule_from_progress(progress_fn: ProgressFn) -> RuleFn:
    def rule(player, task, gained_xp, tm) -> bool:
        cur, tgt = progress_fn(player, task, gained_xp, tm)
        return cur >= tgt
    return rule


# =========================
# Config loader
# =========================

def load_badges_config(filename: str = "badges_config.json") -> List[Dict[str, Any]]:
    """
    JSON'den badge tanımlarını okur.
    Dosya yoksa/bozuksa boş döner (programı patlatmaz).
    """
    try:
        with open(filename, "r", encoding="utf-8") as f:
            data = json.load(f)
            return data if isinstance(data, list) else []
    except FileNotFoundError:
        print("badges_config.json not found. No badges loaded.")
        return []
    except json.JSONDecodeError:
        print("badges_config.json is corrupted/unreadable. No badges loaded.")
        return []


def _build_progress_from_config(cfg: Dict[str, Any]) -> ProgressFn:
    """
    cfg["type"] değerine göre uygun progress fonksiyonunu üretir.
    """
    btype = str(cfg.get("type", "")).strip()

    target_raw = cfg.get("target", 1)
    try:
        target = int(target_raw)
    except (TypeError, ValueError):
        target = 1

    if btype == "tasks_completed":
        return _progress_tasks_completed(target)

    if btype == "complete_type":
        task_type = str(cfg.get("task_type", "")).strip().lower()
        return _progress_complete_type(task_type, target)

    if btype == "single_task_streak":
        return _progress_single_task_streak(target)

    if btype == "any_task_streak":
        task_type = cfg.get("task_type")
        task_type = str(task_type).strip().lower() if task_type else None
        return _progress_any_task_streak(target, task_type=task_type)

    if btype == "xp_single":
        return _progress_xp_single(target)

    def fallback(_player, _task, _gained_xp, _tm) -> Tuple[int, int]:
        return 0, target
    return fallback


def load_badges(filename: str = "badges_config.json") -> List[Badge]:
    """
    JSON badge'lerini yükler, her birine progress + rule ekler.
    """
    configs = load_badges_config(filename)
    badges: List[Badge] = []

    seen_ids = set()
    for cfg in configs:
        if not isinstance(cfg, dict):
            continue

        bid = str(cfg.get("id", "")).strip()
        if not bid or bid in seen_ids:
            continue
        seen_ids.add(bid)

        name = str(cfg.get("name", bid)).strip()
        desc = str(cfg.get("description", "")).strip()

        progress_fn = _build_progress_from_config(cfg)

        # --- rarity/category: whitelist + cast (Literal hatalarını çözer) ---
        raw_rarity = str(cfg.get("rarity", "common")).strip().lower()
        raw_category = str(cfg.get("category", "misc")).strip().lower()
        if raw_rarity not in ("common", "rare", "epic", "legendary"):
            raw_rarity = "common"
        if raw_category not in ("progress", "streak", "xp", "misc"):
            raw_category = "misc"

        rarity = cast(Rarity, raw_rarity)
        category = cast(Category, raw_category)

        emoji = str(cfg.get("emoji", "🏅"))

        badge: Badge = {
            "id": bid,
            "name": name,
            "description": desc,
            "rarity": rarity,
            "category": category,
            "emoji": emoji,
            "progress": progress_fn,
            "rule": _rule_from_progress(progress_fn),
        }

        badges.append(badge)

    return badges


# BADGES artık JSON’dan geliyor:
BADGES: List[Badge] = load_badges("badges_config.json")


# =========================
# Public API
# =========================

def check_and_award_badges(player, task, gained_xp: int, task_manager, verbose: bool = True,  conn: sqlite3.Connection | None = None):
    owned_ids = set(_badge_repo.list_earned_ids(conn=conn))
    newly_awarded: List[Dict[str, str]] = []

    for badge in BADGES:
        badge_id = badge.get("id", "")
        if not badge_id or badge_id in owned_ids:
            continue

        try:
            ok = badge["rule"](player, task, gained_xp, task_manager)
        except Exception:
            ok = False

        if not ok:
            continue

        owned_ids.add(badge_id)
        awarded_at = datetime.datetime.now().isoformat()

        context = {
            "task_id": getattr(task, "id", None),
            "task_title": getattr(task, "title", None),
            "task_type": getattr(task, "task_type", None),
            "gained_xp": int(gained_xp or 0),
        }

        # DB insert (transaction dışarıdan yönetilebilsin)
        _badge_repo.insert_earned(
            badge_id=badge_id,
            badge_name=badge.get("name", badge_id),
            awarded_at=awarded_at,
            context=context,
            conn=conn,
        )

        newly_awarded.append({
            "id": badge_id,
            "name": badge.get("name", badge_id),
            "description": badge.get("description", ""),
        })

    if verbose and newly_awarded:
        print("\n🏅 NEW BADGES UNLOCKED!")
        for b in newly_awarded:
            print(f"- {b['name']}: {b['description']}")
        print()

    return newly_awarded




def list_badges(player, task=None, gained_xp: int = 0, task_manager=None, verbose: bool = True):
    """
    Owned + Locked badge’leri progress ile listeler.
    Owned bilgisi artık DB'den (badge_earned) gelir.
    """
    owned_ids = set(_badge_repo.list_earned_ids())

    owned: List[Badge] = []
    locked: List[Tuple[Badge, int, int]] = []

    for badge in BADGES:
        bid = badge.get("id", "")
        if not bid:
            continue

        if bid in owned_ids:
            owned.append(badge)
        else:
            cur, target = (0, 1)
            if task_manager is not None:
                try:
                    cur, target = badge["progress"](player, task, gained_xp, task_manager)
                except Exception:
                    cur, target = (0, 1)
            locked.append((badge, cur, target))

    if verbose:
        print("\n--- YOUR BADGES ---")
        if not owned:
            print("Owned: (none)")
        else:
            print("Owned:")
            for b in owned:
                print(
                    f"  ✅ {b.get('emoji','🏅')} {b.get('name','-')} "
                    f"[{b.get('rarity','common')}/{b.get('category','misc')}] — {b.get('description','')}"
                )

        print("\nLocked:")
        if not locked:
            print("  (none)")
        else:
            for b, cur, target in locked:
                if task_manager is None:
                    print(
                        f"  🔒 {b.get('emoji','🏅')} {b.get('name','-')} "
                        f"[{b.get('rarity','common')}/{b.get('category','misc')}] — {b.get('description','')}"
                    )
                else:
                    print(
                        f"  🔒 {b.get('emoji','🏅')} {b.get('name','-')} "
                        f"[{b.get('rarity','common')}/{b.get('category','misc')}] — {b.get('description','')} "
                        f"({cur}/{target})"
                    )
        print()

    return owned, locked

def _badge_by_id(badge_id: str) -> Badge | None:
    badge_id = (badge_id or "").strip()
    for b in BADGES:
        if b.get("id") == badge_id:
            return b
    return None


def search_badges(query: str) -> List[Badge]:
    q = (query or "").strip().lower()
    if not q:
        return []
    results: List[Badge] = []
    for b in BADGES:
        name = str(b.get("name", "")).lower()
        desc = str(b.get("description", "")).lower()
        bid = str(b.get("id", "")).lower()
        if q in name or q in desc or q in bid:
            results.append(b)
    return results


def show_badge_details(player, badge_id: str, task=None, gained_xp: int = 0, task_manager=None, verbose: bool = True):
    b = _badge_by_id(badge_id)
    if b is None:
        if verbose:
            print("Badge not found.")
        return None

    owned_ids = set(_badge_repo.list_earned_ids())
    owned = (b.get("id", "") in owned_ids)

    cur, target = (0, 1)
    if task_manager is not None:
        try:
            cur, target = b["progress"](player, task, gained_xp, task_manager)
        except Exception:
            cur, target = (0, 1)

    info = {
        "id": b.get("id", ""),
        "name": b.get("name", ""),
        "description": b.get("description", ""),
        "owned": owned,
        "progress_current": cur,
        "progress_target": target,
    }

    if verbose:
        print("\n--- BADGE DETAILS ---")
        print(f"ID: {info['id']}")
        print(f"Name: {info['name']}")
        print(f"Description: {info['description']}")
        print(f"Owned: {'Yes' if owned else 'No'}")
        if task_manager is not None and not owned:
            print(f"Progress: {cur}/{target}")
        print()

    return info


def list_badges_filtered(player, task_manager, rarity: str | None = None, category: str | None = None, verbose: bool = True):
    rarity_n = rarity.strip().lower() if rarity else None
    category_n = category.strip().lower() if category else None

    owned, locked = list_badges(player, task_manager=task_manager, verbose=False)

    def match(b: Badge) -> bool:
        if rarity_n and b.get("rarity") != rarity_n:
            return False
        if category_n and b.get("category") != category_n:
            return False
        return True

    owned_f = [b for b in owned if match(b)]
    locked_f = [(b, cur, target) for (b, cur, target) in locked if match(b)]

    if verbose:
        print("\n--- FILTERED BADGES ---")
        print(f"Filter -> rarity={rarity_n or 'ANY'}, category={category_n or 'ANY'}")

        print("\nOwned:")
        if not owned_f:
            print("  (none)")
        else:
            for b in owned_f:
                print(f"  ✅ {b.get('emoji','🏅')} {b.get('name','-')} [{b.get('rarity','common')}/{b.get('category','misc')}] — {b.get('description','')}")

        print("\nLocked:")
        if not locked_f:
            print("  (none)")
        else:
            for b, cur, target in locked_f:
                print(f"  🔒 {b.get('emoji','🏅')} {b.get('name','-')} [{b.get('rarity','common')}/{b.get('category','misc')}] — {b.get('description','')} ({cur}/{target})")
        print()

    return owned_f, locked_f

def show_badge_timeline(player=None, limit=None, verbose=True):
    items = _badge_repo.list_timeline(limit=limit)
    if verbose:
        print("\n--- BADGE TIMELINE ---")
        if not items:
            print("No badge history yet.\n")
            return items
        for h in items:
            extra = []
            if h.get("task_title"):
                extra.append(f"task='{h.get('task_title')}'")
            if h.get("task_type"):
                extra.append(f"type={h.get('task_type')}")
            if h.get("gained_xp") is not None:
                extra.append(f"xp={h.get('gained_xp')}")
            extra_txt = (" | " + ", ".join(extra)) if extra else ""
            print(f"- {h.get('awarded_at')} | {h.get('badge_id')} | {h.get('badge_name')}{extra_txt}")
        print()
    return items
