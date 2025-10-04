from datetime import datetime, timedelta, date
from typing import Optional

from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel
from sqlalchemy import func, text, and_
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import LandingAdAssignment, AdAccount, User, AdStaff, Purchase, \
    LandingAdPeriod, Landing

router = APIRouter()

DEFAULT_STAFF_NAME = "Не назначен"
DEFAULT_ACCOUNT_NAME = "Не указан"

def _active_ad_periods(db: Session, language: Optional[str] = None):
    """
    Возвращает список (Landing, started_at) только для тех, кто сейчас в рекламе,
    по активной записи landing_ad_periods (ended_at IS NULL).
    """
    q = (
        db.query(Landing, LandingAdPeriod.started_at)
          .join(LandingAdPeriod, LandingAdPeriod.landing_id == Landing.id)
          .filter(
              Landing.in_advertising.is_(True),
              LandingAdPeriod.ended_at.is_(None),
          )
    )
    if language:
        q = q.filter(Landing.language == language.upper().strip())
    return q.all()

def _cycle_count_map(db: Session, landing_ids: list[int]) -> dict[int, int]:
    rows = (
        db.query(LandingAdPeriod.landing_id, func.count().label("cnt"))
          .filter(LandingAdPeriod.landing_id.in_(landing_ids))
          .group_by(LandingAdPeriod.landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}

def _ad_sales_first5_map(db: Session, pairs: list[tuple[int, datetime]]) -> dict[int, int]:
    """
    pairs: [(landing_id, started_at)]
    """
    if not pairs:
        return {}
    # подготавливаем временную таблицу в памяти: landing_id -> started_at
    # сделаем через VALUES-подобный UNION ALL
    from sqlalchemy import literal, union_all, select
    parts = []
    for lid, st in pairs:
        parts.append(select(literal(lid).label("lid"), literal(st).label("st")))
    ap = union_all(*parts).alias("ap")

    # COUNT(*) where p.from_ad=1 and p.created_at in [st, least(st+5d, now))
    now = datetime.utcnow()
    five = func.date_add(ap.c.st, text("INTERVAL 5 DAY"))
    win_end = func.least(five, func.utc_timestamp())
    rows = (
        db.query(ap.c.lid, func.count(Purchase.id))
          .join(Purchase, and_(
              Purchase.landing_id == ap.c.lid,
              Purchase.from_ad.is_(True),
              Purchase.created_at >= ap.c.st,
              Purchase.created_at <  win_end,
          ))
          .group_by(ap.c.lid)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}

def _ad_sales_last10_map(db: Session, landing_ids: list[int]) -> dict[int, int]:
    if not landing_ids:
        return {}
    now = datetime.utcnow()
    win_start = now - timedelta(days=10)
    rows = (
        db.query(Purchase.landing_id, func.count(Purchase.id))
          .filter(
              Purchase.landing_id.in_(landing_ids),
              Purchase.from_ad.is_(True),
              Purchase.created_at >= win_start,
              Purchase.created_at <  now,
          )
          .group_by(Purchase.landing_id)
          .all()
    )
    return {lid: int(cnt) for lid, cnt in rows}

def _q_color(days:int, any_sale:bool) -> str:
    if any_sale:
        return "green"
    if days <= 2:
        return "white"
    if days == 3:
        return "orange"
    return "red"  # 5-й день попадёт сюда до переразметки

def _o_color(sales10:int) -> str:
    if sales10 <= 1:
        return "red"
    if sales10 <= 3:
        return "orange"
    return "green"

GRACE_HOURS = 14

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
        # если перерыв между cur_end и st2 небольшой — склеиваем
        if st2 - cur_end <= grace:
            # расширяем конец
            cur_end = max(cur_end, en2)
        else:
            merged.append((cur_start, cur_end))
            cur_start, cur_end = st2, en2
    merged.append((cur_start, cur_end))
    return merged

def _effective_cycle_count_map(db: Session, landing_ids: list[int]) -> dict[int, int]:
    """
    Количество СКЛЕЕННЫХ эпизодов рекламы (а не сырых периодов).
    """
    if not landing_ids:
        return {}
    rows = (
        db.query(
            LandingAdPeriod.landing_id,
            LandingAdPeriod.started_at,
            LandingAdPeriod.ended_at,
        )
        .filter(LandingAdPeriod.landing_id.in_(landing_ids))
        .order_by(LandingAdPeriod.landing_id.asc(), LandingAdPeriod.started_at.asc())
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

def _active_episode_start_map(db: Session, landing_ids: list[int]) -> dict[int, datetime]:
    """
    Для тех, у кого сейчас реклама (есть open-период ended_at IS NULL),
    возвращает НАЧАЛО СКЛЕЕННОГО эпизода (первое started_at с учётом склейки).
    """
    if not landing_ids:
        return {}
    now = datetime.utcnow()

    # грузим все периоды по нужным лендингам
    rows = (
        db.query(
            LandingAdPeriod.landing_id,
            LandingAdPeriod.started_at,
            LandingAdPeriod.ended_at,
        )
        .filter(LandingAdPeriod.landing_id.in_(landing_ids))
        .order_by(LandingAdPeriod.landing_id.asc(), LandingAdPeriod.started_at.asc())
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
        # активный эпизод = последний в склеенном списке, если сейчас есть open-период
        # проверим: есть ли open-период вообще (с ended_at IS NULL)
        has_open = any(en is None for _, en in periods)
        if has_open:
            start, _ = merged[-1]
            episode_start[lid] = start
    return episode_start

from typing import Optional, List, Literal
from fastapi import Query, Depends, HTTPException
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..dependencies.role_checker import require_roles
from ..db.database import get_db
from ..models.models_v2 import User, Landing, LandingAdAssignment

ColorLiteral = Literal["white", "orange", "red", "green"]

def _color_rank_quarantine(c: str) -> int:
    # важность: red > orange > white > green
    order = {"red": 3, "orange": 2, "white": 1, "green": 0}
    return order.get(c, -1)

def _color_rank_observation(c: str) -> int:
    # для наблюдения тоже используем red > orange > white > green
    return _color_rank_quarantine(c)


@router.get("/ads/quarantine")
def ads_quarantine_list(
    language: Optional[str] = Query(None, description="EN/RU/…; пусто = все"),
    # ── фильтры
    q: Optional[str] = Query(None, description="Поиск по landing_name (ILIKE)"),
    staff_id: Optional[int] = Query(None, description="Фильтр по ответственному"),
    account_id: Optional[int] = Query(None, description="Фильтр по рекламному кабинету"),
    colors: Optional[List[ColorLiteral]] = Query(None, description="white|orange|red|green"),
    cycle_min: Optional[int] = Query(None),
    cycle_max: Optional[int] = Query(None),
    days_min: Optional[int] = Query(None, description="Мин. дней в стадии"),
    days_max: Optional[int] = Query(None, description="Макс. дней в стадии"),
    first5_min: Optional[int] = Query(None, description="Мин. ad-продаж за первые 5 дней"),
    first5_max: Optional[int] = Query(None, description="Макс. ad-продаж за первые 5 дней"),
    stage_start_from: Optional[date] = Query(None, description="Не раньше этой даты (склеённый старт)"),
    stage_start_to: Optional[date] = Query(None, description="Не позже этой даты (склеённый старт)"),
    # ── сортировка
    sort_by: Literal["deadline", "days", "first5", "cycle", "name", "language", "stage_start", "color"] = Query("deadline"),
    sort_dir: Literal["asc", "desc"] = Query("asc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    now = datetime.utcnow()

    rows = _active_ad_periods(db, language)  # [(Landing, started_at_of_open_period)]
    if not rows:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    landing_ids = [l.id for (l, _) in rows]

    # 1) начало СКЛЕЕННОГО эпизода
    episode_start_map = _active_episode_start_map(db, landing_ids)

    # 2) корректный счётчик кругов
    cycles_map = _effective_cycle_count_map(db, landing_ids)

    # 3) продажи в первые 5 дней от СКЛЕЕННОГО начала
    pairs = [(l.id, episode_start_map.get(l.id)) for (l, _) in rows if episode_start_map.get(l.id)]
    first5_map = _ad_sales_first5_map(db, pairs)

    # 4) назначения + словари имён (одним батчем)
    assign_rows = db.query(LandingAdAssignment).filter(LandingAdAssignment.landing_id.in_(landing_ids)).all()
    assign_map = {a.landing_id: a for a in assign_rows}
    staff_ids = [a.staff_id for a in assign_rows if a.staff_id is not None]
    acc_ids = [a.account_id for a in assign_rows if a.account_id is not None]
    staff_name_map = {s.id: s.name for s in db.query(AdStaff).filter(AdStaff.id.in_(staff_ids)).all()} if staff_ids else {}
    acc_name_map = {a.id: a.name for a in db.query(AdAccount).filter(AdAccount.id.in_(acc_ids)).all()} if acc_ids else {}

    # 5) собираем сырой список
    raw = []
    for landing, _open_started_at in rows:
        st = episode_start_map.get(landing.id)
        if not st:
            continue

        days = (now - st).days  # целые дни
        first5_cnt = int(first5_map.get(landing.id, 0))
        in_first5_window = now < (st + timedelta(days=5))
        is_quarantine = in_first5_window or (not in_first5_window and first5_cnt == 0)
        if not is_quarantine:
            continue

        color = _q_color(days, any_sale=(first5_cnt > 0))
        assign = assign_map.get(landing.id)
        q_end = st + timedelta(days=5)

        cycle_no = int(cycles_map.get(landing.id, 0))  # гарантируем int

        raw.append({
            "id": landing.id,
            "landing_name": landing.landing_name,
            "language": landing.language,
            "cycle_no": cycle_no,
            "stage_started_dt": st,
            "quarantine_ends_dt": q_end,
            "days_in_stage": int(days),
            "ad_purchases_first_5_days": first5_cnt,
            "color": color,
            "staff_id": getattr(assign, "staff_id", None),
            "account_id": getattr(assign, "account_id", None),
        })

    # 6) фильтры (инклюзивные границы)
    def _like(s: str, sub: str) -> bool:
        return sub.lower() in (s or "").lower()

    filtered = []
    for r in raw:
        if q and not _like(r["landing_name"], q):
            continue
        if staff_id is not None and r["staff_id"] != staff_id:
            continue
        if account_id is not None and r["account_id"] != account_id:
            continue
        if colors and r["color"] not in colors:
            continue
        if cycle_min is not None and r["cycle_no"] < int(cycle_min):
            continue
        if cycle_max is not None and r["cycle_no"] > int(cycle_max):
            continue
        if days_min is not None and r["days_in_stage"] < int(days_min):
            continue
        if days_max is not None and r["days_in_stage"] > int(days_max):
            continue
        if first5_min is not None and r["ad_purchases_first_5_days"] < int(first5_min):
            continue
        if first5_max is not None and r["ad_purchases_first_5_days"] > int(first5_max):
            continue
        if stage_start_from is not None and r["stage_started_dt"].date() < stage_start_from:
            continue
        if stage_start_to is not None and r["stage_started_dt"].date() > stage_start_to:
            continue
        filtered.append(r)

    # 7) сортировка
    reverse = (sort_dir == "desc")
    if sort_by == "deadline":
        keyfn = lambda x: x["quarantine_ends_dt"]
    elif sort_by == "days":
        keyfn = lambda x: x["days_in_stage"]
    elif sort_by == "first5":
        keyfn = lambda x: x["ad_purchases_first_5_days"]
    elif sort_by == "cycle":
        keyfn = lambda x: x["cycle_no"]
    elif sort_by == "name":
        keyfn = lambda x: (x["landing_name"] or "").lower()
    elif sort_by == "language":
        keyfn = lambda x: (x["language"] or "")
    elif sort_by == "stage_start":
        keyfn = lambda x: x["stage_started_dt"]
    elif sort_by == "color":
        keyfn = lambda x: _color_rank_quarantine(x["color"])
    else:
        keyfn = lambda x: x["quarantine_ends_dt"]

    sorted_rows = sorted(filtered, key=keyfn, reverse=reverse)

    # 8) финальный ответ (добавили имена, не ломая структуру)
    items = []
    for r in sorted_rows:
        sid = r["staff_id"]
        aid = r["account_id"]
        items.append({
            "id": r["id"],
            "landing_name": r["landing_name"],
            "language": r["language"],
            "cycle_no": r["cycle_no"],
            "stage_started_at": r["stage_started_dt"].isoformat() + "Z",
            "quarantine_ends_at": r["quarantine_ends_dt"].isoformat() + "Z",
            "days_in_stage": r["days_in_stage"],
            "ad_purchases_first_5_days": r["ad_purchases_first_5_days"],
            "color": r["color"],
            "assignee": {
                "staff_id": sid,
                "staff_name": staff_name_map.get(sid, DEFAULT_STAFF_NAME) if sid is not None else DEFAULT_STAFF_NAME,
                "account_id": aid,
                "account_name": acc_name_map.get(aid, DEFAULT_ACCOUNT_NAME) if aid is not None else DEFAULT_ACCOUNT_NAME,
            }
        })

    return {"items": items, "as_of": now.isoformat() + "Z"}


@router.get("/ads/observation")
def ads_observation_list(
    language: Optional[str] = Query(None, description="EN/RU/…; пусто = все"),
    # ── фильтры
    q: Optional[str] = Query(None, description="Поиск по landing_name (ILIKE)"),
    staff_id: Optional[int] = Query(None),
    account_id: Optional[int] = Query(None),
    colors: Optional[List[ColorLiteral]] = Query(None, description="white|orange|red|green"),
    cycle_min: Optional[int] = Query(None),
    cycle_max: Optional[int] = Query(None),
    days_min: Optional[int] = Query(None),
    days_max: Optional[int] = Query(None),
    sales10_min: Optional[int] = Query(None, description="Мин. ad-продаж за последние 10 дней"),
    sales10_max: Optional[int] = Query(None, description="Макс. ad-продаж за последние 10 дней"),
    stage_start_from: Optional[date] = Query(None, description="Не раньше этой даты (склеённый старт)"),
    stage_start_to: Optional[date] = Query(None, description="Не позже этой даты (склеённый старт)"),
    # ── сортировка
    sort_by: Literal["sales10", "days", "cycle", "name", "language", "stage_start", "color"] = Query("sales10"),
    sort_dir: Literal["asc", "desc"] = Query("desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    now = datetime.utcnow()

    rows = _active_ad_periods(db, language)
    if not rows:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    landing_ids = [l.id for (l, _) in rows]
    episode_start_map = _active_episode_start_map(db, landing_ids)
    cycles_map = _effective_cycle_count_map(db, landing_ids)

    pairs = [(l.id, episode_start_map.get(l.id)) for (l, _) in rows if episode_start_map.get(l.id)]
    first5_map = _ad_sales_first5_map(db, pairs)

    # кандидаты в наблюдение
    obs_ids = [
        l.id for (l, _st) in rows
        if (episode_start_map.get(l.id) is not None
            and now >= episode_start_map[l.id] + timedelta(days=5)
            and int(first5_map.get(l.id, 0)) >= 1)
    ]
    if not obs_ids:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    last10_map = _ad_sales_last10_map(db, obs_ids)

    # назначения + имена
    assign_rows = db.query(LandingAdAssignment).filter(LandingAdAssignment.landing_id.in_(obs_ids)).all()
    assign_map = {a.landing_id: a for a in assign_rows}
    staff_ids = [a.staff_id for a in assign_rows if a.staff_id is not None]
    acc_ids = [a.account_id for a in assign_rows if a.account_id is not None]
    staff_name_map = {s.id: s.name for s in db.query(AdStaff).filter(AdStaff.id.in_(staff_ids)).all()} if staff_ids else {}
    acc_name_map = {a.id: a.name for a in db.query(AdAccount).filter(AdAccount.id.in_(acc_ids)).all()} if acc_ids else {}

    # сырые строки
    raw = []
    for (landing, _st_open) in rows:
        if landing.id not in obs_ids:
            continue
        st = episode_start_map[landing.id]
        days = (now - st).days
        sales10 = int(last10_map.get(landing.id, 0))
        color = _o_color(sales10)
        assign = assign_map.get(landing.id)
        cycle_no = int(cycles_map.get(landing.id, 0))

        raw.append({
            "id": landing.id,
            "landing_name": landing.landing_name,
            "language": landing.language,
            "cycle_no": cycle_no,
            "stage_started_dt": st,
            "days_in_stage": int(days),
            "ad_purchases_last_10_days": sales10,
            "color": color,
            "staff_id": getattr(assign, "staff_id", None),
            "account_id": getattr(assign, "account_id", None),
        })

    # фильтры (инклюзивные)
    def _like(s: str, sub: str) -> bool:
        return sub.lower() in (s or "").lower()

    filtered = []
    for r in raw:
        if q and not _like(r["landing_name"], q):
            continue
        if staff_id is not None and r["staff_id"] != staff_id:
            continue
        if account_id is not None and r["account_id"] != account_id:
            continue
        if colors and r["color"] not in colors:
            continue
        if cycle_min is not None and r["cycle_no"] < int(cycle_min):
            continue
        if cycle_max is not None and r["cycle_no"] > int(cycle_max):
            continue
        if days_min is not None and r["days_in_stage"] < int(days_min):
            continue
        if days_max is not None and r["days_in_stage"] > int(days_max):
            continue
        if sales10_min is not None and r["ad_purchases_last_10_days"] < int(sales10_min):
            continue
        if sales10_max is not None and r["ad_purchases_last_10_days"] > int(sales10_max):
            continue
        if stage_start_from is not None and r["stage_started_dt"].date() < stage_start_from:
            continue
        if stage_start_to is not None and r["stage_started_dt"].date() > stage_start_to:
            continue
        filtered.append(r)

    # сортировка
    reverse = (sort_dir == "desc")
    if sort_by == "sales10":
        keyfn = lambda x: x["ad_purchases_last_10_days"]
    elif sort_by == "days":
        keyfn = lambda x: x["days_in_stage"]
    elif sort_by == "cycle":
        keyfn = lambda x: x["cycle_no"]
    elif sort_by == "name":
        keyfn = lambda x: (x["landing_name"] or "").lower()
    elif sort_by == "language":
        keyfn = lambda x: (x["language"] or "")
    elif sort_by == "stage_start":
        keyfn = lambda x: x["stage_started_dt"]
    elif sort_by == "color":
        keyfn = lambda x: _color_rank_observation(x["color"])
    else:
        keyfn = lambda x: x["ad_purchases_last_10_days"]

    sorted_rows = sorted(filtered, key=keyfn, reverse=reverse)

    items = []
    for r in sorted_rows:
        sid = r["staff_id"]
        aid = r["account_id"]
        items.append({
            "id": r["id"],
            "landing_name": r["landing_name"],
            "language": r["language"],
            "cycle_no": r["cycle_no"],
            "stage_started_at": r["stage_started_dt"].isoformat() + "Z",
            "days_in_stage": r["days_in_stage"],
            "ad_purchases_last_10_days": r["ad_purchases_last_10_days"],
            "color": r["color"],
            "assignee": {
                "staff_id": sid,
                "staff_name": staff_name_map.get(sid, DEFAULT_STAFF_NAME) if sid is not None else DEFAULT_STAFF_NAME,
                "account_id": aid,
                "account_name": acc_name_map.get(aid, DEFAULT_ACCOUNT_NAME) if aid is not None else DEFAULT_ACCOUNT_NAME,
            }
        })

    return {"items": items, "as_of": now.isoformat() + "Z"}

# ---- STAFF ----
class StaffIn(BaseModel):
    name: str

@router.get("/ads/staff")
def list_ad_staff(db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    rows = db.query(AdStaff).order_by(AdStaff.id.asc()).all()
    return [{"id": r.id, "name": r.name} for r in rows]

@router.post("/ads/staff", status_code=201)
def create_ad_staff(payload: StaffIn, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = AdStaff(name=payload.name); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id}

@router.put("/ads/staff/{staff_id}")
def update_ad_staff(staff_id: int, payload: StaffIn, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = db.query(AdStaff).get(staff_id)
    if not row: raise HTTPException(404, "Staff not found")
    row.name = payload.name; db.commit(); return {"ok": True}

@router.delete("/ads/staff/{staff_id}", status_code=204)
def delete_ad_staff(staff_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = db.query(AdStaff).get(staff_id)
    if not row: raise HTTPException(404, "Staff not found")
    db.delete(row); db.commit(); return

# ---- ACCOUNTS ----
class AccountIn(BaseModel):
    name: str

@router.get("/ads/accounts")
def list_ad_accounts(db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    rows = db.query(AdAccount).order_by(AdAccount.id.asc()).all()
    return [{"id": r.id, "name": r.name} for r in rows]

@router.post("/ads/accounts", status_code=201)
def create_ad_account(payload: AccountIn, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = AdAccount(name=payload.name); db.add(row); db.commit(); db.refresh(row)
    return {"id": row.id}

@router.put("/ads/accounts/{account_id}")
def update_ad_account(account_id: int, payload: AccountIn, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = db.query(AdAccount).get(account_id)
    if not row: raise HTTPException(404, "Account not found")
    row.name = payload.name; db.commit(); return {"ok": True}

@router.delete("/ads/accounts/{account_id}", status_code=204)
def delete_ad_account(account_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    row = db.query(AdAccount).get(account_id)
    if not row: raise HTTPException(404, "Account not found")
    db.delete(row); db.commit(); return

# ---- ASSIGNMENT ----
class AssignmentIn(BaseModel):
    staff_id: Optional[int] = None
    account_id: Optional[int] = None

@router.get("/ads/landing/{landing_id}/assignment")
def get_assignment(landing_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    a = db.query(LandingAdAssignment).get(landing_id)
    return {"landing_id": landing_id, "staff_id": a.staff_id if a else None, "account_id": a.account_id if a else None}

@router.put("/ads/landing/{landing_id}/assignment")
def set_assignment(landing_id: int, payload: AssignmentIn, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    if payload.staff_id:
        if not db.query(AdStaff.id).filter(AdStaff.id == payload.staff_id).first():
            raise HTTPException(400, "Invalid staff_id")
    if payload.account_id:
        if not db.query(AdAccount.id).filter(AdAccount.id == payload.account_id).first():
            raise HTTPException(400, "Invalid account_id")

    a = db.query(LandingAdAssignment).get(landing_id)
    if not a:
        a = LandingAdAssignment(landing_id=landing_id, staff_id=payload.staff_id, account_id=payload.account_id)
        db.add(a)
    else:
        a.staff_id = payload.staff_id
        a.account_id = payload.account_id
    db.commit()
    return {"ok": True}
