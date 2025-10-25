# app/api_v2/book_ad_control.py
# Аналитика рекламы для книжных лендингов

from datetime import datetime, timedelta, date
from typing import Optional, List, Literal

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from pymysql import IntegrityError
from sqlalchemy import func, text, and_
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import (
    BookLandingAdAssignment, AdAccount, User, AdStaff, Purchase,
    BookLandingAdPeriod, BookLanding, BookAdVisit
)

router = APIRouter()

DEFAULT_STAFF_NAME = "Не назначен"
DEFAULT_ACCOUNT_NAME = "Не указан"
GRACE_HOURS = 14  # для склейки периодов
WHITE_DAYS_THRESHOLD = 5  # < 5 дней => white

# ============================================================================
# Вспомогательные функции для аналитики
# ============================================================================

def _active_book_ad_periods(db: Session, language: Optional[str] = None):
    """
    Возвращает список (BookLanding, started_at) только для тех, кто сейчас в рекламе,
    по активной записи book_landing_ad_periods (ended_at IS NULL).
    """
    q = (
        db.query(BookLanding, BookLandingAdPeriod.started_at)
          .join(BookLandingAdPeriod, BookLandingAdPeriod.book_landing_id == BookLanding.id)
          .filter(
              BookLanding.in_advertising.is_(True),
              BookLandingAdPeriod.ended_at.is_(None),
          )
    )
    if language:
        q = q.filter(BookLanding.language == language.upper().strip())
    return q.all()


def _merge_periods(periods, now: datetime) -> list[tuple[datetime, datetime|None]]:
    """
    periods: [(started_at, ended_at or None)] отсортированные по started_at.
    Склеиваем соседние, если gap <= GRACE_HOURS.
    """
    if not periods:
        return []
    grace = timedelta(hours=GRACE_HOURS)
    merged = []
    cur_start, cur_end = periods[0][0], periods[0][1] or now

    for st, en in periods[1:]:
        st2, en2 = st, (en or now)
        if st2 - cur_end <= grace:
            cur_end = max(cur_end, en2)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = st2, en2
    merged.append((cur_start, cur_end))
    return merged


def _effective_book_cycle_count_map(db: Session, book_landing_ids: list[int]) -> dict[int, int]:
    """
    Количество СКЛЕЕННЫХ эпизодов рекламы (а не сырых периодов).
    """
    if not book_landing_ids:
        return {}
    rows = (
        db.query(
            BookLandingAdPeriod.book_landing_id,
            BookLandingAdPeriod.started_at,
            BookLandingAdPeriod.ended_at,
        )
        .filter(BookLandingAdPeriod.book_landing_id.in_(book_landing_ids))
        .order_by(BookLandingAdPeriod.book_landing_id.asc(), BookLandingAdPeriod.started_at.asc())
        .all()
    )
    now = datetime.utcnow()
    by_lid: dict[int, list[tuple[datetime, datetime|None]]] = {}
    for lid, st, en in rows:
        by_lid.setdefault(lid, []).append((st, en))

    out: dict[int, int] = {}
    for lid, periods in by_lid.items():
        merged = _merge_periods(periods, now)
        out[lid] = len(merged)
    return out


def _active_book_episode_start_map(db: Session, book_landing_ids: list[int]) -> dict[int, datetime]:
    """
    Для тех, у кого сейчас реклама (есть open-период ended_at IS NULL),
    возвращает НАЧАЛО СКЛЕЕННОГО эпизода (первое started_at с учётом склейки).
    """
    if not book_landing_ids:
        return {}
    now = datetime.utcnow()

    rows = (
        db.query(
            BookLandingAdPeriod.book_landing_id,
            BookLandingAdPeriod.started_at,
            BookLandingAdPeriod.ended_at,
        )
        .filter(BookLandingAdPeriod.book_landing_id.in_(book_landing_ids))
        .order_by(BookLandingAdPeriod.book_landing_id.asc(), BookLandingAdPeriod.started_at.asc())
        .all()
    )

    by_lid: dict[int, list[tuple[datetime, datetime|None]]] = {}
    for lid, st, en in rows:
        by_lid.setdefault(lid, []).append((st, en))

    episode_start: dict[int, datetime] = {}
    for lid, periods in by_lid.items():
        merged = _merge_periods(periods, now)
        if not merged:
            continue
        has_open = any(en is None for _, en in periods)
        if has_open:
            start, _ = merged[-1]
            episode_start[lid] = start
    return episode_start


def _book_ad_sales_last10_map(db: Session, book_landing_ids: list[int]) -> dict[int, int]:
    """Рекламные продажи книжных лендингов за последние 10 дней."""
    if not book_landing_ids:
        return {}
    now = datetime.utcnow()
    win_start = now - timedelta(days=10)
    rows = (
        db.query(Purchase.book_landing_id, func.count(Purchase.id))
          .filter(
              Purchase.book_landing_id.in_(book_landing_ids),
              Purchase.from_ad.is_(True),
              Purchase.created_at >= win_start,
              Purchase.created_at <  now,
          )
          .group_by(Purchase.book_landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}


def _book_ad_visits_last10_map(db: Session, book_landing_ids: list[int]) -> dict[int, int]:
    """Посещения с рекламы для книжных лендингов за последние 10 дней (AV10d)."""
    if not book_landing_ids:
        return {}
    now = datetime.utcnow()
    win_start = now - timedelta(days=10)
    rows = (
        db.query(BookAdVisit.book_landing_id, func.count(BookAdVisit.id))
          .filter(
              BookAdVisit.book_landing_id.in_(book_landing_ids),
              BookAdVisit.visited_at >= win_start,
              BookAdVisit.visited_at <  now,
          )
          .group_by(BookAdVisit.book_landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}


def _book_total_purchases_last10_map(db: Session, book_landing_ids: list[int]) -> dict[int, int]:
    """Все покупки (рекламные и нерекламные) книжных лендингов за последние 10 дней (TP10d)."""
    if not book_landing_ids:
        return {}
    now = datetime.utcnow()
    win_start = now - timedelta(days=10)
    rows = (
        db.query(Purchase.book_landing_id, func.count(Purchase.id))
          .filter(
              Purchase.book_landing_id.in_(book_landing_ids),
              Purchase.created_at >= win_start,
              Purchase.created_at <  now,
          )
          .group_by(Purchase.book_landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}


def _book_ad_sales_lifetime_map(db: Session, book_landing_ids: list[int]) -> dict[int, int]:
    """Рекламные продажи книжных лендингов за всё время."""
    if not book_landing_ids:
        return {}
    rows = (
        db.query(Purchase.book_landing_id, func.count(Purchase.id))
          .filter(
              Purchase.book_landing_id.in_(book_landing_ids),
              Purchase.from_ad.is_(True),
          )
          .group_by(Purchase.book_landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}


def _book_overview_color(now: datetime, stage_start: datetime, sales10: int, lifetime_sales: int) -> str:
    """
    Определяет цвет для overview книжного лендинга:
    - white: < 5 дней от старта
    - green: sales10 > 3
    - orange: 1 <= sales10 <= 3
    - black: sales10 == 0 && lifetime_sales > 3
    - red: sales10 == 0 && lifetime_sales <= 3
    """
    if (now - stage_start).days < WHITE_DAYS_THRESHOLD:
        return "white"
    if sales10 > 3:
        return "green"
    if 1 <= sales10 <= 3:
        return "orange"
    # sales10 == 0
    if lifetime_sales > 3:
        return "black"
    return "red"


# ============================================================================
# API Endpoints
# ============================================================================

OverviewColor = Literal["white", "orange", "red", "green", "black"]


@router.get("/ads/books/overview")
def book_ads_overview_list(
    language: Optional[str] = Query(None, description="EN/RU/…; пусто = все"),
    # ── фильтры
    q: Optional[str] = Query(None, description="Поиск по landing_name (ILIKE)"),
    staff_id: Optional[int] = Query(None),
    colors: Optional[List[OverviewColor]] = Query(None, description="white|orange|red|green|black"),
    days_min: Optional[int] = Query(None),
    days_max: Optional[int] = Query(None),
    av10d_min: Optional[int] = Query(None, description="Мин. ad-посещений за последние 10 дней"),
    av10d_max: Optional[int] = Query(None, description="Макс. ad-посещений за последние 10 дней"),
    sales10_min: Optional[int] = Query(None, description="Мин. ad-продаж за последние 10 дней"),
    sales10_max: Optional[int] = Query(None, description="Макс. ad-продаж за последние 10 дней"),
    tp10d_min: Optional[int] = Query(None, description="Мин. всех продаж за последние 10 дней"),
    tp10d_max: Optional[int] = Query(None, description="Макс. всех продаж за последние 10 дней"),
    apall_min: Optional[int] = Query(None, description="Мин. ad-продаж за всё время"),
    apall_max: Optional[int] = Query(None, description="Макс. ad-продаж за всё время"),
    stage_start_from: Optional[date] = Query(None, description="Не раньше этой даты (склеённый старт)"),
    stage_start_to: Optional[date] = Query(None, description="Не позже этой даты (склеённый старт)"),
    # ── сортировка
    sort_by: Literal["sales10", "days", "name", "language", "stage_start", "color", "av10d", "tp10d", "apall"] = Query("color"),
    sort_dir: Literal["asc", "desc"] = Query("desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Общая аналитика по книжным лендингам в рекламе.
    Показывает метрики: посещения, продажи, время в рекламе, цветовую индикацию.
    """
    now = datetime.utcnow()

    # только те, кто сейчас помечен "в рекламе"
    base = (
        db.query(BookLanding, BookLandingAdPeriod.started_at)
          .join(BookLandingAdPeriod, BookLandingAdPeriod.book_landing_id == BookLanding.id)
          .filter(
              BookLanding.in_advertising.is_(True),
              BookLandingAdPeriod.ended_at.is_(None),
          )
    )
    if language:
        base = base.filter(BookLanding.language == language.upper().strip())

    rows = base.all()  # [(BookLanding, started_at_of_open_period)]
    if not rows:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    book_landing_ids = [bl.id for (bl, _) in rows]

    # 1) склеённое начало активного эпизода
    episode_start_map = _active_book_episode_start_map(db, book_landing_ids)

    # 2) продажи: рекламные за 10 дней + за всё время
    sales10_map = _book_ad_sales_last10_map(db, book_landing_ids)
    lifetime_map = _book_ad_sales_lifetime_map(db, book_landing_ids)

    # 3) посещения с рекламы за последние 10 дней
    visits10_map = _book_ad_visits_last10_map(db, book_landing_ids)

    # 4) все покупки за последние 10 дней
    total_purchases10_map = _book_total_purchases_last10_map(db, book_landing_ids)

    # 5) назначения + имена
    assign_rows = db.query(BookLandingAdAssignment).filter(BookLandingAdAssignment.book_landing_id.in_(book_landing_ids)).all()
    assign_map = {a.book_landing_id: a for a in assign_rows}
    staff_ids = [a.staff_id for a in assign_rows if a.staff_id is not None]
    acc_ids = [a.account_id for a in assign_rows if a.account_id is not None]
    staff_name_map = {s.id: s.name for s in db.query(AdStaff).filter(AdStaff.id.in_(staff_ids)).all()} if staff_ids else {}
    acc_name_map = {a.id: a.name for a in db.query(AdAccount).filter(AdAccount.id.in_(acc_ids)).all()} if acc_ids else {}

    # 6) собираем сырые строки
    raw = []
    for book_landing, _st_open in rows:
        st = episode_start_map.get(book_landing.id)
        if not st:
            continue

        days = (now - st).days
        s10 = int(sales10_map.get(book_landing.id, 0))
        life = int(lifetime_map.get(book_landing.id, 0))
        color = _book_overview_color(now, st, s10, life)

        assign = assign_map.get(book_landing.id)
        av10d = int(visits10_map.get(book_landing.id, 0))
        tp10d = int(total_purchases10_map.get(book_landing.id, 0))

        raw.append({
            "id": book_landing.id,
            "landing_name": book_landing.landing_name,
            "language": book_landing.language,
            "stage_started_dt": st,
            "days_in_stage": int(days),
            # Visits
            "ad_visits_last_10_days": av10d,
            # Purchases
            "ad_purchases_last_10_days": s10,
            "total_purchases_last_10_days": tp10d,
            "ad_purchases_lifetime": life,
            "total_purchases_lifetime": book_landing.sales_count or 0,
            "color": color,
            "staff_id": getattr(assign, "staff_id", None),
            "account_id": getattr(assign, "account_id", None),
        })

    # 7) фильтры
    def _like(s: str, sub: str) -> bool:
        return sub.lower() in (s or "").lower()

    filtered = []
    for r in raw:
        if q and not _like(r["landing_name"], q):
            continue
        if staff_id is not None and r["staff_id"] != staff_id:
            continue
        if colors and r["color"] not in colors:
            continue
        if days_min is not None and r["days_in_stage"] < int(days_min):
            continue
        if days_max is not None and r["days_in_stage"] > int(days_max):
            continue
        if av10d_min is not None and r["ad_visits_last_10_days"] < int(av10d_min):
            continue
        if av10d_max is not None and r["ad_visits_last_10_days"] > int(av10d_max):
            continue
        if sales10_min is not None and r["ad_purchases_last_10_days"] < int(sales10_min):
            continue
        if sales10_max is not None and r["ad_purchases_last_10_days"] > int(sales10_max):
            continue
        if tp10d_min is not None and r["total_purchases_last_10_days"] < int(tp10d_min):
            continue
        if tp10d_max is not None and r["total_purchases_last_10_days"] > int(tp10d_max):
            continue
        if apall_min is not None and r["ad_purchases_lifetime"] < int(apall_min):
            continue
        if apall_max is not None and r["ad_purchases_lifetime"] > int(apall_max):
            continue
        if stage_start_from is not None and r["stage_started_dt"].date() < stage_start_from:
            continue
        if stage_start_to is not None and r["stage_started_dt"].date() > stage_start_to:
            continue
        filtered.append(r)

    # 8) сортировка
    def _color_rank(c: str) -> int:
        # black > red > white > orange > green
        order = {"black": 4, "red": 3, "white": 2, "orange": 1, "green": 0}
        return order.get(c, -1)

    reverse = (sort_dir == "desc")
    if sort_by == "sales10":
        keyfn = lambda x: x["ad_purchases_last_10_days"]
    elif sort_by == "days":
        keyfn = lambda x: x["days_in_stage"]
    elif sort_by == "name":
        keyfn = lambda x: (x["landing_name"] or "").lower()
    elif sort_by == "language":
        keyfn = lambda x: (x["language"] or "")
    elif sort_by == "stage_start":
        keyfn = lambda x: x["stage_started_dt"]
    elif sort_by == "color":
        keyfn = lambda x: _color_rank(x["color"])
    elif sort_by == "av10d":
        keyfn = lambda x: x["ad_visits_last_10_days"]
    elif sort_by == "tp10d":
        keyfn = lambda x: x["total_purchases_last_10_days"]
    elif sort_by == "apall":
        keyfn = lambda x: x["ad_purchases_lifetime"]
    else:
        keyfn = lambda x: _color_rank(x["color"])

    sorted_rows = sorted(filtered, key=keyfn, reverse=reverse)

    # 9) финальный ответ
    items = []
    for r in sorted_rows:
        sid = r["staff_id"]; aid = r["account_id"]
        items.append({
            "id": r["id"],
            "landing_name": r["landing_name"],
            "language": r["language"],
            # Visits (Посещения)
            "ad_visits_last_10_days": r["ad_visits_last_10_days"],
            # Purchases (Покупки)
            "ad_purchases_last_10_days": r["ad_purchases_last_10_days"],
            "total_purchases_last_10_days": r["total_purchases_last_10_days"],
            "ad_purchases_lifetime": r["ad_purchases_lifetime"],
            "total_purchases_lifetime": r["total_purchases_lifetime"],
            # Time (Время)
            "stage_started_at": r["stage_started_dt"].isoformat() + "Z",
            "days_in_stage": r["days_in_stage"],
            # Color
            "color": r["color"],
            # Assignee
            "assignee": {
                "staff_id": sid,
                "staff_name": staff_name_map.get(sid, DEFAULT_STAFF_NAME) if sid is not None else DEFAULT_STAFF_NAME,
                "account_id": aid,
                "account_name": acc_name_map.get(aid, DEFAULT_ACCOUNT_NAME) if aid is not None else DEFAULT_ACCOUNT_NAME,
            }
        })

    return {"items": items, "as_of": now.isoformat() + "Z"}


# ============================================================================
# Assignment Endpoints
# ============================================================================

class AssignmentIn(BaseModel):
    staff_id: Optional[int] = None
    account_id: Optional[int] = None


@router.get("/ads/books/landing/{book_landing_id}/assignment")
def get_book_assignment(
    book_landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """Получить назначение ответственного и кабинета для книжного лендинга."""
    a = db.query(BookLandingAdAssignment).get(book_landing_id)
    return {
        "book_landing_id": book_landing_id,
        "staff_id": a.staff_id if a else None,
        "account_id": a.account_id if a else None
    }


@router.put("/ads/books/landing/{book_landing_id}/assignment")
def set_book_assignment(
    book_landing_id: int,
    payload: AssignmentIn,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """Установить назначение ответственного и кабинета для книжного лендинга."""
    if payload.staff_id:
        if not db.query(AdStaff.id).filter(AdStaff.id == payload.staff_id).first():
            raise HTTPException(400, "Invalid staff_id")
    if payload.account_id:
        if not db.query(AdAccount.id).filter(AdAccount.id == payload.account_id).first():
            raise HTTPException(400, "Invalid account_id")

    a = db.query(BookLandingAdAssignment).get(book_landing_id)
    if not a:
        a = BookLandingAdAssignment(
            book_landing_id=book_landing_id,
            staff_id=payload.staff_id,
            account_id=payload.account_id
        )
        db.add(a)
    else:
        a.staff_id = payload.staff_id
        a.account_id = payload.account_id
    db.commit()
    return {"ok": True}

