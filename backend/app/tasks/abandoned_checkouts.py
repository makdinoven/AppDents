# ────────────────────────── imports ───────────────────────────
import logging
import os
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

logger = get_task_logger(__name__)
MAIL_BONUS = 5.0  # $5 – фиксированный бонус

# Конфигурация из окружения
FRONTEND_URL = os.getenv("FRONTEND_URL", "https://med-g.com")
CDN_PLACEHOLDER_URL = os.getenv(
    "CDN_PLACEHOLDER_URL",
    "https://cdn.med-g.com/assets/img/placeholder.png",
)

REMINDER_INTERVAL = timedelta(days=2)
MAX_SENDS = 5


@celery.task(
    bind=True,
    name="app.tasks.abandoned_checkouts.process_abandoned_checkouts",
    rate_limit="100/h",
)
def process_abandoned_checkouts(
    self,
    batch_size: int = 100,
    target_email: str | None = None,
) -> None:
    """
    Новая логика:
      • первый раз (send_count == 0):
            - если юзера нет → создаём, даём 5$, partial, шлём письмо с паролем
            - если юзер уже есть → шлём только письмо-напоминание без бонусов
      • последующие разы (send_count > 0):
            - только напоминалка без бонуса/partial/создания юзера

    Удаление из таблицы по оплате/регистрации остаётся в других местах.
    """
    db: Session = SessionLocal()
    now = datetime.utcnow()
    first_cutoff = now - timedelta(hours=3)

    try:
        q = db.query(AbandonedCheckout).filter(
            AbandonedCheckout.send_count < MAX_SENDS
        )

        if target_email:
            # ручной режим – по конкретному email, без ограничений по времени
            q = q.filter(AbandonedCheckout.email == target_email)
        else:
            # авто-режим:
            #   • первый раз — запись старше 3 часов
            #   • дальше — прошло 2 суток с последней отправки
            q = q.filter(
                or_(
                    and_(
                        AbandonedCheckout.send_count == 0,
                        AbandonedCheckout.created_at < first_cutoff,
                    ),
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

        for lead in leads:
            try:
                lead_id     = lead.id
                email       = lead.email
                region      = lead.region or "EN"
                raw_courses = (lead.course_ids or "").split(",")
                send_count  = lead.send_count or 0
            except orm_exc.ObjectDeletedError:
                logger.warning("Lead row vanished before processing — skipping.")
                continue

            user = get_user_by_email(db, email)

            # ── ПЕРВЫЙ РАЗ ───────────────────────────────────────────────
            if send_count == 0:
                course_info: dict = {}
                password: str | None = None

                if user is None:
                    # 1) создаём юзера, НО не чистим AbandonedCheckout,
                    #    чтобы можно было слать последующие письма
                    password = generate_random_password()
                    try:
                        user = create_user(
                            db,
                            email=email,
                            password=password,
                            cleanup_abandoned=False,  # <-- важный момент
                        )
                    except ValueError:
                        # race: юзер уже появился
                        user = get_user_by_email(db, email)

                # если юзер есть (создали только что или он уже был)
                if user is not None and send_count == 0:
                    # 2) бонус и partial КУРС — ТОЛЬКО ПРИ ПЕРВОМ ПИСЬМЕ
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

                # 3) письмо – первое: если есть пароль, отправляем с паролем,
                #    иначе просто напоминалку
                try:
                    send_abandoned_checkout_email(
                        recipient_email=email,
                        password=password,
                        course_info=course_info,
                        region=region,
                    )
                    logger.info("First abandoned mail sent to %s", email)
                except Exception as err:
                    logger.error("SMTP error for %s: %s", email, err)

            # ── ПОВТОРНЫЕ ПИСЬМА ─────────────────────────────────────────
            else:
                # только напоминание, без бонусов/partial/создания юзера
                try:
                    course_info = {}
                    # можно взять первый курс из списка и собрать инфу
                    course_ids = [int(c) for c in raw_courses if c.strip().isdigit()]
                    if course_ids:
                        course_info = _build_course_info(db, course_ids[0])

                    send_abandoned_checkout_email(
                        recipient_email=email,
                        password=None,      # пароль только в первом письме
                        course_info=course_info,
                        region=region,
                    )
                    logger.info(
                        "Reminder #%s sent to %s", send_count + 1, email
                    )
                except Exception as err:
                    logger.error("SMTP error (reminder) for %s: %s", email, err)

            # ── обновляем счётчик ────────────────────────────────────────
            db.query(AbandonedCheckout).filter_by(id=lead_id).update(
                {
                    "send_count": send_count + 1,
                    "last_sent_at": now,
                }
            )

        db.commit()

    except Exception as exc:
        db.rollback()
        logger.exception("Abandoned-checkout task failed: %s", exc)
    finally:
        db.close()


# ───────────────────────── helpers ────────────────────────────

def _choose_course(db: Session, course_ids: list[int] | None) -> int | None:
    """Возвращает ID наиболее «популярного» курса из списка (как было раньше)."""
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
    old = landing.old_price or ""
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
