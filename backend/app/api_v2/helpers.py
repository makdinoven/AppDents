# app/api/admin_import.py
from __future__ import annotations

import csv
import io
import uuid
from typing import Annotated, Iterable

import pandas as pd
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from starlette.responses import StreamingResponse

from ..db.database import get_db
from ..models.models_v2 import User, AbandonedCheckout, Landing

router = APIRouter(prefix="/admin", tags=["admin"])


# ────────────────────────────────────────────────────────────────
# helpers
# ────────────────────────────────────────────────────────────────
def _iter_failed_emails(rows: Iterable[dict]) -> set[str]:
    """
    Возвращает множество e-mail'ов из CSV-отчёта Stripe,
    где оплата не была успешной.
    Приоритет колонок:
      1) Customer Email
      2) email (metadata)
    """
    failed = set()

    for row in rows:
        # Признак «не успешной» оплаты – на ваш выбор:
        status_not_ok = row.get("Status", "").strip().lower() != "paid"
        captured      = row.get("Captured", "").strip().lower()   # '' / 'True' / 'False'
        captured_not_ok = captured == "false"

        if not (status_not_ok or captured_not_ok):
            continue

        email = (row.get("Customer Email") or row.get("email (metadata)"))
        if email:
            failed.add(email.strip().lower())

    return failed


def _insert_leads(db: Session, emails: set[str]) -> tuple[int, int]:
    """
    Пишет e-mails в AbandonedCheckout.  Возвращает:
        added  – сколько строк вставили
        skipped – сколько пропустили (аккаунт существует или дубль)
    """
    added, skipped = 0, 0

    # уже зарегистрированные пользователи
    existing = {
        e.lower() for (e,) in
        db.query(User.email).filter(User.email.in_(emails)).all()
    }

    for email in emails - existing:
        try:
            db.add(
                AbandonedCheckout(
                    session_id=f"import_{uuid.uuid4()}",
                    email=email,
                    course_ids="",
                    region="EN",
                )
            )
            db.flush()      # ловим дубль session_id/email до commit
            added += 1
        except Exception:
            db.rollback()
            skipped += 1

    db.commit()
    return added, skipped


# ────────────────────────────────────────────────────────────────
# API-роут
# ────────────────────────────────────────────────────────────────
@router.post(
    "/import_failed_payments",
    summary="Импорт неуспешных оплат (CSV из Stripe)",
    status_code=status.HTTP_201_CREATED,
)
async def import_failed_payments(
    file: Annotated[UploadFile, File(description="CSV файл из Stripe")],
    db: Session = Depends(get_db),
):
    """
    Принимает CSV-файл выгрузки платежей Stripe и
    добавляет e-mail’ы «неоплаченных» сессий в таблицу
    abandoned_checkouts, если у этих адресов ещё нет аккаунта.
    """
    if file.content_type not in ("text/csv", "application/vnd.ms-excel"):
        raise HTTPException(
            status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            detail="Файл должен быть в формате CSV",
        )

    content = await file.read()
    try:
        # csv модуль работает со str, поэтому декодируем bytes → str
        text_io = io.StringIO(content.decode("utf-8-sig"))
        reader = csv.DictReader(text_io)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Не удалось прочитать CSV: {e}")

    emails = _iter_failed_emails(reader)
    if not emails:
        return {"imported": 0, "skipped": 0, "detail": "В файле нет неуспешных оплат"}

    added, skipped = _insert_leads(db, emails)
    return {
        "imported": added,
        "skipped": skipped,
        "total_in_file": len(emails),
    }
@router.get("/export-landings")
def export_landings(db: Session = Depends(get_db)):
    # Получаем все лендинги
    landings = db.query(Landing).all()

    # Собираем данные
    rows = []
    for l in landings:
        tags = ", ".join([t.name for t in l.tags])
        rows.append({
            "landing_name":    l.landing_name,
            "course_program":  l.course_program,
            "language":        l.language,
            "duration":        l.duration,
            "lessons_count":   l.lessons_count,
            "tags":            tags,
            "sales_count":     l.sales_count,
        })

    # Создаем Excel в памяти с openpyxl
    df = pd.DataFrame(rows)
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Landings")
    output.seek(0)

    # Отдаем файл для скачивания
    headers = {
        "Content-Disposition": "attachment; filename=landings_export.xlsx"
    }
    return StreamingResponse(
        output,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers=headers
    )