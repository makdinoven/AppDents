from datetime import datetime, timedelta
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

@router.get("/ads/quarantine")
def ads_quarantine_list(
    language: Optional[str] = Query(None, description="EN/RU/…; пусто = все"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    now = datetime.utcnow()

    rows = _active_ad_periods(db, language)  # [(Landing, started_at)]
    if not rows:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    landing_ids = [l.id for (l, _) in rows]
    cycles      = _cycle_count_map(db, landing_ids)
    first5      = _ad_sales_first5_map(db, [(l.id, st) for (l, st) in rows])

    items = []
    for landing, started_at in rows:
        days = (now - started_at).days
        first5_cnt = first5.get(landing.id, 0)

        # определяем стадийность динамически
        in_first5_window = now < (started_at + timedelta(days=5))
        is_quarantine = in_first5_window or (not in_first5_window and first5_cnt == 0)
        if not is_quarantine:
            continue  # этот лендинг попадёт в /ads/observation

        color = _q_color(days, any_sale=(first5_cnt > 0))

        assign = db.query(LandingAdAssignment).get(landing.id)
        items.append({
            "id": landing.id,
            "landing_name": landing.landing_name,
            "language": landing.language,
            "cycle_no": cycles.get(landing.id, 0),
            "stage_started_at": started_at.isoformat() + "Z",
            "quarantine_ends_at": (started_at + timedelta(days=5)).isoformat() + "Z",
            "days_in_stage": days,
            "ad_purchases_first_5_days": first5_cnt,
            "color": color,
            "assignee": {
                "staff_id": assign.staff_id if assign else None,
                "account_id": assign.account_id if assign else None,
            }
        })

    return {"items": items, "as_of": now.isoformat() + "Z"}

@router.get("/ads/observation")
def ads_observation_list(
    language: Optional[str] = Query(None, description="EN/RU/…; пусто = все"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    now = datetime.utcnow()

    rows = _active_ad_periods(db, language)
    if not rows:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    landing_ids = [l.id for (l, _) in rows]
    cycles      = _cycle_count_map(db, landing_ids)
    first5      = _ad_sales_first5_map(db, [(l.id, st) for (l, st) in rows])

    # сюда берём только тех, кто прошёл 5 дней И имел ≥1 продажу в первые 5 дней
    obs_ids = [l.id for (l, st) in rows if (datetime.utcnow() >= st + timedelta(days=5) and first5.get(l.id, 0) >= 1)]
    if not obs_ids:
        return {"items": [], "as_of": now.isoformat() + "Z"}

    last10 = _ad_sales_last10_map(db, obs_ids)

    items = []
    for (landing, started_at) in rows:
        if landing.id not in obs_ids:
            continue
        sales10 = last10.get(landing.id, 0)
        color = _o_color(sales10)
        assign = db.query(LandingAdAssignment).get(landing.id)

        items.append({
            "id": landing.id,
            "landing_name": landing.landing_name,
            "language": landing.language,
            "cycle_no": cycles.get(landing.id, 0),
            "stage_started_at": started_at.isoformat() + "Z",
            "ad_purchases_last_10_days": sales10,
            "color": color,
            "assignee": {
                "staff_id": assign.staff_id if assign else None,
                "account_id": assign.account_id if assign else None,
            }
        })

    return {"items": items, "as_of": now.isoformat() + "Z"}

# ---- STAFF ----
class StaffIn(BaseModel):
    name: str

@router.get("/ads/staff")
def list_ad_staff(db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    rows = db.query(AdStaff).order_by(AdStaff.name.asc()).all()
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
    rows = db.query(AdAccount).order_by(AdAccount.name.asc()).all()
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
