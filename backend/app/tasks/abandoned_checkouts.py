# ────────────────────────── imports ───────────────────────────
import logging
from datetime import datetime, timedelta

from celery.utils.log import get_task_logger
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..celery_app import celery
from ..db.database import SessionLocal
from ..models.models_v2 import (
    AbandonedCheckout,
    Landing,
    Course,
    WalletTxTypes,
    FreeCourseSource,
)
from ..services_v2.user_service import (
    get_user_by_email,
    create_user,
    generate_random_password,
    credit_balance,
    add_partial_course_to_user,
)
# ↓ новый импорт
from ..utils.email_sender import send_abandoned_checkout_email  # <= NEW
# ───────────────────────────────────────────────────────────────

logger = get_task_logger(__name__)
MAIL_BONUS = 5.0        # $5 – фиксированный бонус


from sqlalchemy.orm import exc as orm_exc

@celery.task(
    bind=True,
    name="app.tasks.abandoned_checkouts.process_abandoned_checkouts",
    rate_limit="100/h",
)
def process_abandoned_checkouts(
    self,
    batch_size: int = 30,
    target_email: str | None = None,
) -> None:
    """
    • auto-режим → берём batch_size лидов старше 3 ч;
    • ручной режим → обрабатываем ровно один e-mail независимо от времени.

    Каждая строка обрабатывается только одним воркером,
    благодаря FOR UPDATE ... SKIP LOCKED.
    """
    db: Session = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=3)

    try:
        # ─── формируем и блокируем выборку ───────────────────────────────
        q = db.query(AbandonedCheckout).filter(
            AbandonedCheckout.message_sent.is_(False)
        )

        if target_email:
            q = q.filter(AbandonedCheckout.email == target_email)
        else:
            q = q.filter(AbandonedCheckout.created_at < cutoff)

        leads = (
            q.order_by(AbandonedCheckout.id)
             .limit(batch_size)
             .with_for_update(skip_locked=True)     # ← блокировка
             .all()
        )

        if not leads:
            logger.info("No abandoned-checkout leads to process.")
            db.commit()
            return

        # ─── обработка ----------------------------------------------------
        for lead in leads:
            try:
                # сохраняем поля пока объект «жив»
                lead_id     = lead.id
                email       = lead.email
                region      = lead.region or "EN"
                raw_courses = (lead.course_ids or "").split(",")

            except orm_exc.ObjectDeletedError:
                logger.warning("Lead row vanished before processing — skipping.")
                continue

            # 1. пользователь уже существует
            if get_user_by_email(db, email):
                db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                    {"message_sent": True}
                )
                logger.info("User %s exists — flag set, skipped.", email)
                continue

            # 2. регистрация
            password = generate_random_password()
            try:
                user = create_user(db, email, password)        # делает commit()
            except ValueError:
                db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                    {"message_sent": True}
                )
                logger.warning("Race condition on %s — marked as sent.", email)
                continue

            # 3. бонус 5 $
            credit_balance(
                db, user.id, MAIL_BONUS, WalletTxTypes.ADMIN_ADJUST,
                meta={"reason": "abandoned_checkout"},
            )  # commit() внутри

            # 4. partial-курс
            course_ids  = [int(c) for c in raw_courses if c.strip().isdigit()]
            chosen_id   = _choose_course(db, course_ids)
            course_info = {}

            if chosen_id:
                try:
                    add_partial_course_to_user(
                        db, user.id, chosen_id, source=FreeCourseSource.LANDING
                    )  # commit() внутри
                    course_info = _build_course_info(db, chosen_id)
                except ValueError as err:
                    logger.warning("Partial %s → %s: %s", chosen_id, email, err)

            # 5. письмо
            try:
                send_abandoned_checkout_email(
                    recipient_email=email,
                    password=password,
                    course_info=course_info,
                    region=region,
                )
                logger.info("Mail sent to %s", email)
            except Exception as err:
                logger.error("SMTP error for %s: %s", email, err)

            # 6. отметка message_sent
            db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                {"message_sent": True}
            )

        db.commit()

    except Exception as exc:
        db.rollback()
        logger.exception("Abandoned-checkout task failed: %s", exc)
    finally:
        db.close()




# ───────────────────────── helpers ────────────────────────────
def _choose_course(db: Session, course_ids: list[int] | None) -> int | None:
    """Возвращает ID наиболее «популярного» курса из списка."""
    if not course_ids:
        return None
    if len(course_ids) == 1:
        return course_ids[0]

    pop_rows = (
        db.query(
            Course.id,
            func.coalesce(func.sum(Landing.sales_count), 0).label("sales")
        )
        .join(Landing.courses)
        .filter(Course.id.in_(course_ids))
        .group_by(Course.id)
        .all()
    )
    if not pop_rows:
        return course_ids[0]

    return max(pop_rows, key=lambda r: r.sales).id


def _build_course_info(db: Session, course_id: int) -> dict[str, str]:
    landing: Landing | None = (
        db.query(Landing)
          .join(Landing.courses)
          .filter(Course.id == course_id)
          .order_by(Landing.sales_count.desc())
          .first()
    )
    if not landing:
        return {}

    # цены
    price = landing.new_price or ""
    old   = landing.old_price or ""
    if price and not price.startswith("$"):
        price = f"${price}"
    if old and not old.startswith("$"):
        old = f"${old}"

    # уроки как готовая строка
    lessons_str = landing.lessons_count or ""

    # картинка — пытаемся несколько полей подряд
    img_url = (
        getattr(landing, "preview_photo", None)
        or getattr(landing, "preview_img", None)
        or getattr(landing, "preview_image", None)
        or "https://dent-s.com/assets/img/placeholder.png"
    )

    return {
        "url":       f"https://dent-s.com/client/course/{landing.page_name}",
        "price":     price,
        "old_price": old,
        "lessons":   lessons_str,
        "title":     landing.landing_name or landing.page_name,
        "img":       img_url,
    }
