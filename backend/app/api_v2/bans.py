import ipaddress
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import BanEmail, BanIP
from ..schemas_v2.ban import (
    BanEmailCreate,
    BanEmailOut,
    BanEmailPatch,
    BanIPCreate,
    BanIPOut,
    BanIPPatch,
    BanLinkIn,
    BanSummaryOut,
)
from ..services_v2.ban_service import sync_nginx_ban_file_and_reload

router = APIRouter()


def _norm_email(email: str) -> str:
    e = (email or "").strip().lower()
    if not e:
        raise HTTPException(status_code=400, detail="email is required")
    return e


def _norm_ip(ip: str) -> str:
    raw = (ip or "").strip()
    if not raw:
        raise HTTPException(status_code=400, detail="ip is required")
    try:
        return str(ipaddress.ip_address(raw))
    except ValueError:
        raise HTTPException(status_code=400, detail="invalid ip")


@router.get("/summary", response_model=BanSummaryOut)
def summary(
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    emails = (
        db.query(BanEmail)
        .options(selectinload(BanEmail.ips))
        .order_by(BanEmail.id.desc())
        .all()
    )
    ips = (
        db.query(BanIP)
        .options(selectinload(BanIP.emails))
        .order_by(BanIP.id.desc())
        .all()
    )
    return {"emails": emails, "ips": ips}


@router.get("/emails", response_model=list[BanEmailOut])
def list_emails(
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return (
        db.query(BanEmail)
        .options(selectinload(BanEmail.ips))
        .order_by(BanEmail.id.desc())
        .all()
    )


@router.post("/emails", response_model=BanEmailOut, status_code=status.HTTP_201_CREATED)
def create_email(
    payload: BanEmailCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("admin")),
):
    email = _norm_email(payload.email)
    obj = db.query(BanEmail).options(selectinload(BanEmail.ips)).filter(BanEmail.email == email).first()
    if obj:
        raise HTTPException(status_code=409, detail="email already banned")

    obj = BanEmail(email=email, note=payload.note, is_manual=True, created_by_admin_id=admin.id)
    db.add(obj)
    db.flush()

    ip_changed = False
    for ip in payload.ips or []:
        if not (ip or "").strip():
            continue
        ip_n = _norm_ip(ip)
        ip_obj = db.query(BanIP).filter(BanIP.ip == ip_n).first()
        if not ip_obj:
            ip_obj = BanIP(ip=ip_n, is_manual=True, created_by_admin_id=admin.id)
            db.add(ip_obj)
            db.flush()
            ip_changed = True
        if ip_obj not in obj.ips:
            obj.ips.append(ip_obj)
            ip_changed = True

    db.commit()
    db.refresh(obj)

    # Пересобираем ban-файл и reload только если реально меняли IP-состав
    if ip_changed:
        sync_nginx_ban_file_and_reload(db)
    return obj


@router.patch("/emails/{email_id}", response_model=BanEmailOut)
def patch_email(
    email_id: int,
    payload: BanEmailPatch,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    obj = db.query(BanEmail).options(selectinload(BanEmail.ips)).filter(BanEmail.id == email_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not found")
    if payload.email is not None:
        obj.email = _norm_email(payload.email)
    if payload.note is not None:
        obj.note = payload.note
    db.commit()
    db.refresh(obj)
    return obj


@router.delete("/emails/{email_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_email(
    email_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    obj = db.query(BanEmail).filter(BanEmail.id == email_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(obj)
    db.commit()
    return None


@router.get("/ips", response_model=list[BanIPOut])
def list_ips(
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return (
        db.query(BanIP)
        .options(selectinload(BanIP.emails))
        .order_by(BanIP.id.desc())
        .all()
    )


@router.post("/ips", response_model=BanIPOut, status_code=status.HTTP_201_CREATED)
def create_ip(
    payload: BanIPCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_roles("admin")),
):
    ip_n = _norm_ip(payload.ip)
    obj = db.query(BanIP).options(selectinload(BanIP.emails)).filter(BanIP.ip == ip_n).first()
    if obj:
        raise HTTPException(status_code=409, detail="ip already banned")

    obj = BanIP(ip=ip_n, note=payload.note, is_manual=True, created_by_admin_id=admin.id)
    db.add(obj)
    db.flush()

    for email in payload.emails or []:
        if not (email or "").strip():
            continue
        e_n = _norm_email(email)
        e_obj = db.query(BanEmail).filter(BanEmail.email == e_n).first()
        if not e_obj:
            e_obj = BanEmail(email=e_n, is_manual=True, created_by_admin_id=admin.id)
            db.add(e_obj)
            db.flush()
        if e_obj not in obj.emails:
            obj.emails.append(e_obj)

    db.commit()
    db.refresh(obj)

    sync_nginx_ban_file_and_reload(db)
    return obj


@router.patch("/ips/{ip_id}", response_model=BanIPOut)
def patch_ip(
    ip_id: int,
    payload: BanIPPatch,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    obj = db.query(BanIP).options(selectinload(BanIP.emails)).filter(BanIP.id == ip_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not found")
    if payload.ip is not None:
        obj.ip = _norm_ip(payload.ip)
    if payload.note is not None:
        obj.note = payload.note
    db.commit()
    db.refresh(obj)

    sync_nginx_ban_file_and_reload(db)
    return obj


@router.delete("/ips/{ip_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_ip(
    ip_id: int,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    obj = db.query(BanIP).filter(BanIP.id == ip_id).first()
    if not obj:
        raise HTTPException(status_code=404, detail="not found")
    db.delete(obj)
    db.commit()

    sync_nginx_ban_file_and_reload(db)
    return None


@router.post("/links", status_code=status.HTTP_201_CREATED)
def create_link(
    payload: BanLinkIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    email = db.query(BanEmail).options(selectinload(BanEmail.ips)).filter(BanEmail.id == payload.email_id).first()
    ip = db.query(BanIP).filter(BanIP.id == payload.ip_id).first()
    if not email or not ip:
        raise HTTPException(status_code=404, detail="not found")
    if ip not in email.ips:
        email.ips.append(ip)
        db.commit()
    return {"ok": True}


@router.delete("/links", status_code=status.HTTP_200_OK)
def delete_link(
    payload: BanLinkIn,
    db: Session = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    email = db.query(BanEmail).options(selectinload(BanEmail.ips)).filter(BanEmail.id == payload.email_id).first()
    ip = db.query(BanIP).filter(BanIP.id == payload.ip_id).first()
    if not email or not ip:
        raise HTTPException(status_code=404, detail="not found")
    if ip in email.ips:
        email.ips.remove(ip)
        db.commit()
    return {"ok": True}


