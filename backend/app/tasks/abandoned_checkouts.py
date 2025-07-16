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


@celery.task(
    bind=True,
    name="app.tasks.abandoned_checkouts.process_abandoned_checkouts",
    rate_limit="100/h",
)
def process_abandoned_checkouts(self, batch_size: int = 30, target_email: str | None = None,) -> None:
    """
    1) берём лиды старше 3 ч и без письма;
    2) создаём аккаунт, +5$, partial-курс;
    3) шлём маркетинговый e-mail (HTML-шаблон с карточкой курса);
    4) message_sent=True.
    """
    db: Session = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=3)

    try:
        query = (
            db.query(AbandonedCheckout)
            .filter(
                AbandonedCheckout.created_at < cutoff,
                AbandonedCheckout.message_sent.is_(False),
            )
        )
        if target_email:
            query = query.filter(AbandonedCheckout.email == target_email)

        leads = query.limit(batch_size).all()

        for lead in leads:
            # --- 1. уже есть такой пользователь? --------------------------------
            if get_user_by_email(db, lead.email):
                lead.message_sent = True
                continue

            # --- 2. регистрация + случайный пароль -----------------------------
            password = generate_random_password()
            try:
                user = create_user(db, lead.email, password)
            except ValueError:
                lead.message_sent = True
                continue

            # --- 3. подарок 5 $ -------------------------------------------------
            credit_balance(
                db,
                user.id,
                MAIL_BONUS,
                WalletTxTypes.ADMIN_ADJUST,
                meta={"reason": "abandoned_checkout"},
            )

            # --- 4. partial-курс + информация для письма ------------------------
            course_ids = [
                int(c) for c in (lead.course_ids or "").split(",") if c.strip()
            ]
            chosen_course_id = _choose_course(db, course_ids)
            course_info: dict | None = None

            if chosen_course_id:
                # выдаём Partial
                try:
                    add_partial_course_to_user(
                        db,
                        user.id,
                        chosen_course_id,
                        source=FreeCourseSource.LANDING,
                    )
                except ValueError as e:
                    logger.warning(
                        "Cannot grant partial (%s) to %s: %s",
                        chosen_course_id, lead.email, e
                    )

                # собираем данные карточки для письма
                course_info = _build_course_info(db, chosen_course_id)

            # --- 5. письмо ------------------------------------------------------
            try:
                send_abandoned_checkout_email(
                    recipient_email=lead.email,
                    password=password,
                    course_info=course_info or {},
                    region=lead.region or "EN",
                )
            except Exception as e:
                logger.error("E-mail send error to %s: %s", lead.email, e)

            # --- 6. отметка «письмо отправлено» --------------------------------
            lead.message_sent = True

        db.commit()

    except Exception as exc:
        logger.exception("Abandoned-checkout task failed: %s", exc)
        db.rollback()
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
    """
    Собирает данные для карточки курса в письме.
    Берём самый продаваемый лендинг выбранного курса.
    """
    landing: Landing | None = (
        db.query(Landing)
          .join(Landing.courses)
          .filter(Course.id == course_id)
          .order_by(Landing.sales_count.desc())
          .first()
    )
    if not landing:
        return {}

    # нормализуем цены
    price     = landing.new_price or ""
    old_price = landing.old_price or ""
    if price and not price.startswith("$"):
        price = f"${price}"
    if old_price and not old_price.startswith("$"):
        old_price = f"${old_price}"

    return {
        "url":       f"https://dent-s.com/client/course/{landing.page_name}",
        "category":  (landing.tags[0].name.lower() if landing.tags else "course"),
        "price":     price,
        "old_price": old_price,
        "lessons":   int(landing.lessons_count or 0),
        "title":     landing.landing_name or landing.page_name,
        "img":       landing.preview_photo or "https://dent-s.com/assets/img/placeholder.png",
    }
