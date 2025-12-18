# backend/app/tasks/abandoned_checkouts.py

# ────────────────────────── imports ───────────────────────────
import logging
import os
import time
from datetime import datetime, timedelta

from celery.utils.log import get_task_logger
from sqlalchemy import func, or_, and_
from sqlalchemy.orm import Session
from sqlalchemy.orm import exc as orm_exc

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
from ..utils.email_sender import send_abandoned_checkout_email

# ───────────────────────────────────────────────────────────────

logger = get_task_logger(__name__)
MAIL_BONUS = 5.0  # $5 – фиксированный бонус

FRONTEND_URL = os.getenv("FRONTEND_URL", "https://med-g.com")
CDN_PLACEHOLDER_URL = os.getenv(
    "CDN_PLACEHOLDER_URL",
    "https://cdn.med-g.com/assets/img/placeholder.png",
)

REMINDER_INTERVAL = timedelta(days=5)   # пауза между письмами
MAX_SENDS = 7                           # максимум писем на одного лида

# задержка между отправками писем (секунды) — защита от Gmail rate limit
EMAIL_SEND_DELAY_SECONDS = 3


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
    Логика:
      • максимум 7 писем
      • между письмами — минимум 2 суток
      • ПЕРВОЕ письмо (send_count == 0):
            - если пользователя нет:
                    → создаём нового (cleanup_abandoned=False)
                    → даём бонус 5$
                    → даём partial курс
                    → отправляем письмо с паролем
            - если пользователь уже есть:
                    → НЕ даём бонус
                    → НЕ даём partial
                    → письмо без пароля (просто напоминание)
      • ПОСЛЕДУЮЩИЕ письма:
            - только напоминания, без бонусов и partial
      • send_count увеличивается ТОЛЬКО при успешной отправке (SMTP ОК)
      • если письмо НЕ ушло → send_count НЕ увеличивается (повторяем)
      • Удаление лидов при регистрации/оплате происходит в других местах.
    """

    db: Session = SessionLocal()
    now = datetime.utcnow()
    first_cutoff = now - timedelta(hours=3)

    try:
        # Формируем выборку
        q = db.query(AbandonedCheckout).filter(
            AbandonedCheckout.send_count < MAX_SENDS
        )

        if target_email:
            # ручной режим без ограничений по времени
            q = q.filter(AbandonedCheckout.email == target_email)
        else:
            # авто режим — строго по интервалам
            q = q.filter(
                or_(
                    # Первое письмо → запись старше 3h
                    and_(
                        AbandonedCheckout.send_count == 0,
                        AbandonedCheckout.created_at < first_cutoff,
                    ),
                    # Повторные письма → интервал 2 суток
                    and_(
                        AbandonedCheckout.send_count > 0,
                        AbandonedCheckout.last_sent_at <= now - REMINDER_INTERVAL,
                    ),
                )
            )

        leads = (
            q.order_by(AbandonedCheckout.id)
             .limit(batch_size)
             .with_for_update(skip_locked=True)
             .all()
        )

        if not leads:
            logger.info("No abandoned-checkout leads to process.")
            db.commit()
            return

        # Обрабатываем лиды
        for lead in leads:
            try:
                lead_id     = lead.id
                email       = lead.email
                region      = lead.region or "EN"
                raw_courses = (lead.course_ids or "").split(",")
                send_count  = lead.send_count or 0
            except orm_exc.ObjectDeletedError:
                logger.warning("Lead row vanished — skipping.")
                continue

            # Проверяем существование пользователя
            user = get_user_by_email(db, email)
            email_sent = False  # важно!

            # ────────────────────────── ПЕРВОЕ ПИСЬМО ───────────────────────────
            if send_count == 0:
                course_info: dict = {}
                password: str | None = None

                if user is None:
                    # создаём юзера → только тогда бонус и partial
                    password = generate_random_password()
                    try:
                        user = create_user(
                            db,
                            email=email,
                            password=password,
                            cleanup_abandoned=False,
                        )
                    except ValueError:
                        # race: юзер появился между проверкой и create_user
                        user = get_user_by_email(db, email)

                # Если password != None → новый юзер создан в этой таске → бонус и partial
                if password is not None and user is not None:
                    try:
                        credit_balance(
                            db,
                            user.id,
                            MAIL_BONUS,
                            WalletTxTypes.ADMIN_ADJUST,
                            meta={"reason": "abandoned_checkout"},
                        )
                    except Exception as e:
                        logger.warning("Cannot credit bonus to %s: %s", email, e)

                    # выдаём partial курс
                    course_ids = [
                        int(c) for c in raw_courses if c.strip().isdigit()
                    ]
                    chosen_id = _choose_course(db, course_ids)
                    if chosen_id:
                        try:
                            add_partial_course_to_user(
                                db,
                                user.id,
                                chosen_id,
                                source=FreeCourseSource.LANDING,
                            )
                        except ValueError as err:
                            logger.warning(
                                "Partial %s → %s: %s", chosen_id, email, err
                            )
                        course_info = _build_course_info(db, chosen_id)

                # Отправляем первое письмо (с паролем только для новых пользователей)
                try:
                    send_abandoned_checkout_email(
                        recipient_email=email,
                        password=password,
                        course_info=course_info,
                        region=region,
                    )
                    logger.info("First abandoned mail sent to %s", email)
                    email_sent = True
                    # задержка между отправками для избежания Gmail rate limit
                    time.sleep(EMAIL_SEND_DELAY_SECONDS)
                except Exception as err:
                    logger.error("SMTP error for %s: %s", email, err)

            # ────────────────────────── ПОВТОРНЫЕ ПИСЬМА ─────────────────────────
            else:
                course_info: dict = {}
                course_ids = [
                    int(c) for c in raw_courses if c.strip().isdigit()
                ]

                if course_ids:
                    chosen_id = _choose_course(db, course_ids)
                    course_info = _build_course_info(
                        db,
                        chosen_id or course_ids[0],
                    )

                try:
                    send_abandoned_checkout_email(
                        recipient_email=email,
                        password=None,  # пароль только в первом письме
                        course_info=course_info,
                        region=region,
                    )
                    logger.info(
                        "Reminder #%s sent to %s", send_count + 1, email
                    )
                    email_sent = True
                    # задержка между отправками для избежания Gmail rate limit
                    time.sleep(EMAIL_SEND_DELAY_SECONDS)
                except Exception as err:
                    logger.error(
                        "SMTP error (reminder) for %s: %s", email, err
                    )

            # ─────────────────────── обновляем send_count (ТОЛЬКО УСПЕХ) ─────────
            if email_sent:
                db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                    {
                        "send_count": send_count + 1,
                        "last_sent_at": now,
                    }
                )
            else:
                logger.warning(
                    "Email to %s NOT SENT, send_count stays at %s (retry next run)",
                    email,
                    send_count,
                )

        db.commit()

    except Exception as exc:
        db.rollback()
        logger.exception("Abandoned-checkout task failed: %s", exc)
    finally:
        db.close()


# ─────────────────────────── helpers ───────────────────────────

def _choose_course(db: Session, course_ids: list[int] | None) -> int | None:
    """Возвращает ID наиболее «популярного» курса из списка."""
    if not course_ids:
        return None
    if len(course_ids) == 1:
        return course_ids[0]

    pop_rows = (
        db.query(
            Course.id,
            func.coalesce(func.sum(Landing.sales_count), 0).label("sales"),
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

    price = landing.new_price or ""
    old   = landing.old_price or ""
    if price and not str(price).startswith("$"):
        price = f"${price}"
    if old and not str(old).startswith("$"):
        old = f"${old}"

    lessons_str = landing.lessons_count or ""

    img_url = (
        getattr(landing, "preview_photo", None)
        or getattr(landing, "preview_img", None)
        or getattr(landing, "preview_image", None)
        or CDN_PLACEHOLDER_URL
    )

    return {
        "url": f"{FRONTEND_URL}/client/course/{landing.page_name}",
        "price": price,
        "old_price": old,
        "lessons": lessons_str,
        "title": landing.landing_name or landing.page_name,
        "img": img_url,
    }
