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
    rate_limit="100/h",          # ограничим SMTP-нагрузку
)
def process_abandoned_checkouts(
    self,
    batch_size: int = 30,
    target_email: str | None = None,
) -> None:
    """
    • Автоматический режим  (target_email=None)  –
      забираем до batch_size лидов, добавленных > 3 часов назад.

    • Ручная проверка (target_email="mail@host") –
      обрабатываем ровно одну запись независимо от времени добавления.

    Каждый лид:
      1. Если учётка уже существует → просто проставляем message_sent=1.
      2. Регистрируем пользователя, выдаём $5, partial-курс.
      3. Шлём маркетинговое письмо с карточкой курса.
      4. Обновляем флаг message_sent.
    """
    db: Session = SessionLocal()
    cutoff = datetime.utcnow() - timedelta(hours=3)

    try:
        # ───────────────────────── формируем запрос ─────────────────────────
        base_query = db.query(AbandonedCheckout).filter(
            AbandonedCheckout.message_sent.is_(False)
        )

        if target_email:
            base_query = base_query.filter(AbandonedCheckout.email == target_email)
        else:
            base_query = base_query.filter(AbandonedCheckout.created_at < cutoff)

        leads = base_query.limit(batch_size).all()
        if not leads:
            logger.info("No abandoned-checkout leads to process.")
            return

        # ─────────────────────── основной цикл обработки ────────────────────
        for lead in leads:
            lead_id       = lead.id
            current_email = lead.email                    # не переходим на target_email
            raw_courses   = (lead.course_ids or "").split(",")
            region        = lead.region or "EN"

            # 1. Учётка уже есть? ------------------------------------------------
            if get_user_by_email(db, current_email):
                db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                    {"message_sent": True}
                )
                logger.info("User %s already exists – flag set, skipping.", current_email)
                continue

            # 2. Регистрация + пароль -------------------------------------------
            password = generate_random_password()
            try:
                user = create_user(db, current_email, password)   # внутри commit()
            except ValueError:
                # параллельная регистрация
                db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                    {"message_sent": True}
                )
                logger.warning("Race condition on %s – marked as sent.", current_email)
                continue

            # 3. Бонус 5 $ -------------------------------------------------------
            credit_balance(
                db,
                user.id,
                MAIL_BONUS,
                WalletTxTypes.ADMIN_ADJUST,
                meta={"reason": "abandoned_checkout"},
            )  # внутри commit()

            # 4. Partial-курс + карточка -----------------------------------------
            course_ids   = [int(c) for c in raw_courses if c.strip()]
            chosen_id    = _choose_course(db, course_ids)
            course_info  = {}

            if chosen_id:
                try:
                    add_partial_course_to_user(
                        db,
                        user.id,
                        chosen_id,
                        source=FreeCourseSource.LANDING,
                    )  # внутри commit()
                    course_info = _build_course_info(db, chosen_id)
                except ValueError as err:
                    logger.warning(
                        "Cannot grant partial %s to %s: %s", chosen_id, current_email, err
                    )

            # 5. Письмо ----------------------------------------------------------
            try:
                send_abandoned_checkout_email(
                    recipient_email=current_email,
                    password=password,
                    course_info=course_info,
                    region=region,
                )
                logger.info("E-mail successfully sent to %s", current_email)
            except Exception as err:
                logger.error("SMTP error for %s: %s", current_email, err)

            # 6. Флаг message_sent ----------------------------------------------
            db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                {"message_sent": True}
            )

        # ───────────────────────── commit одной транзакцией ────────────────────
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
    lessons_raw = str(landing.lessons_count or "").strip()
    lessons_str = lessons_raw if lessons_raw else "lessons"

    return {
        "url":       f"https://dent-s.com/client/course/{landing.page_name}",
        "category":  (landing.tags[0].name.lower() if landing.tags else "course"),
        "price":     price,
        "old_price": old_price,
        "lessons":   lessons_str,
        "title":     landing.landing_name or landing.page_name,
        "img":       landing.preview_photo or "https://dent-s.com/assets/img/placeholder.png",
    }
