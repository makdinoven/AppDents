"""
Полный модуль обработчика Stripe-платежей с отправкой события Purchase
в Facebook Conversions API. Включает:

• external_id (user/uuid) → user_data.external_id
• правильный event_time — timestamp создания Stripe-сессии
• хэширование first_name / last_name (SHA-256, lower-case)
• проверку payment_status == “paid”
• подробное логирование всех этапов
"""

import hashlib
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

import requests
import stripe
from fastapi import HTTPException, Request
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.models_v2 import Course, Landing, Purchase, AdVisit
from ..services_v2.user_service import (
    add_course_to_user,
    create_user,
    generate_random_password,
    get_user_by_email,
)
from ..utils.email_sender import (
    send_already_owned_course_email,
    send_successful_purchase_email,
)

# ────────────────────────────────────────────────────────────────
# Константы и базовая настройка логов
# ────────────────────────────────────────────────────────────────
AD_INACTIVITY_HOURS = 1     # TTL флага in_advertising после продажи (часы)
AD_VISIT_WINDOW_HOURS = 3   # окно, в котором считаем посещения рекламой (часы)

logging.basicConfig(level=logging.INFO)

# ────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ────────────────────────────────────────────────────────────────
def _landing_has_recent_ad_visits(db: Session, landing_id: int) -> bool:
    """True, если у лендинга были визиты из рекламы за последние N часов."""
    since = datetime.utcnow() - timedelta(hours=AD_VISIT_WINDOW_HOURS)
    return db.query(
        db.query(AdVisit)
        .filter(AdVisit.landing_id == landing_id, AdVisit.visited_at >= since)
        .exists()
    ).scalar()


def _hash_email(email: str) -> str:
    """Нормализуем e-mail и хэшируем его (SHA-256 → hexdigest)."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _hash_plain(value: str) -> str:
    """Trim → lower → SHA-256. Для first_name / last_name и др. персональных полей."""
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()


# ────────────────────────────────────────────────────────────────
# Facebook Conversions API
# ────────────────────────────────────────────────────────────────
def _build_fb_event(
    *,
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    event_time: int,
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> dict:
    """Формирует один payload Purchase для Conversions API."""

    if not email:
        raise ValueError("Empty email for Facebook Purchase event")

    user_data: dict = {
        "em": [_hash_email(email)],
        "client_ip_address": None if client_ip == "0.0.0.0" else client_ip,
        "client_user_agent": user_agent or None,
    }

    # дополнительные идентификаторы
    if external_id:
        user_data["external_id"] = [external_id]  # UUID / user_id можно не хэшировать
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc

    # персональные поля
    if first_name:
        user_data["fn"] = [_hash_plain(first_name)]
    if last_name and last_name != first_name:
        user_data["ln"] = [_hash_plain(last_name)]

    event = {
        "data": [
            {
                "event_name": "Purchase",
                "event_time": event_time,
                "user_data": user_data,
                "custom_data": {
                    "currency": currency,
                    "value": amount,
                    "content_ids": [str(cid) for cid in course_ids],
                    "content_type": "course",
                },
            }
        ]
    }
    logging.info(
        "FB event built → %s | amount=%s %s | courses=%s",
        email,
        amount,
        currency.upper(),
        course_ids,
    )
    return event


def _send_facebook_purchase(
    *,
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    event_time: int,
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    """Отправляет Purchase во все пиксели из settings, логируя каждый шаг."""

    event_payload = _build_fb_event(
        email=email,
        amount=amount,
        currency=currency,
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        event_time=event_time,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
        last_name=last_name,
    )

    pixels = [
        {"id": settings.FACEBOOK_PIXEL_ID, "token": settings.FACEBOOK_ACCESS_TOKEN},
        {"id": settings.FACEBOOK_PIXEL_ID_LEARNWORLDS,
         "token": settings.FACEBOOK_ACCESS_TOKEN_LEARNWORLDS},
    ]

    for p in pixels:
        try:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{p['id']}/events",
                params={"access_token": p["token"]},
                json=event_payload,
                timeout=3,
            )
            if resp.status_code == 200:
                logging.info("FB Pixel %s — OK (email=%s)", p["id"], email)
            else:
                logging.error("FB Pixel %s — %s %s",
                              p["id"], resp.status_code, resp.text)
        except Exception as e:
            logging.error("FB Pixel %s failed: %s", p["id"], e, exc_info=True)


# ────────────────────────────────────────────────────────────────
# Stripe helpers
# ────────────────────────────────────────────────────────────────
def get_stripe_keys_by_region(region: str) -> dict:
    region = region.upper()
    if region == "RU":
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_RU,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_RU,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_RU,
        }
    if region == "ES":
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_ES,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_ES,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_ES,
        }
    # fallback → EN
    return {
        "secret_key": settings.STRIPE_SECRET_KEY_EN,
        "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_EN,
        "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_EN,
    }


# ────────────────────────────────────────────────────────────────
# Создание Checkout Session
# ────────────────────────────────────────────────────────────────
def create_checkout_session(
    *,
    db: Session,
    email: str,
    course_ids: List[int],
    product_name: str,
    price_cents: int,
    region: str,
    success_url: str,
    cancel_url: str,
    request: Request,
    fbp: str | None = None,
    fbc: str | None = None,
) -> str:
    """Создаёт Stripe Checkout Session и возвращает URL оплаты."""

    stripe_keys = get_stripe_keys_by_region(region)
    stripe.api_key = stripe_keys["secret_key"]

    client_ip = (
        request.headers.get("X-Forwarded-For", "").split(",")[0]
        or request.client.host
        or "0.0.0.0"
    )
    user_agent = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer", "")

    logging.info("Creating Checkout Session: email=%s, courses=%s, referer=%s",
                 email, course_ids, referer)

    # внешний ID генерируем сразу (UUID, пока user.id не знаем)
    user = get_user_by_email(db, email)
    if user:  # «старый» пользователь
        external_id = str(user.id)
    else:  # первый заказ — генерим UUID
        external_id = str(uuid.uuid4())

    success_url_with_session = (
        f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&region={region}"
    )

    metadata: dict = {
        "course_ids": ",".join(map(str, course_ids)),
        "client_ip": client_ip,
        "user_agent": user_agent,
        "referer": referer,
        "external_id": external_id,
    }
    if fbp:
        metadata["fbp"] = fbp
    if fbc:
        metadata["fbc"] = fbc

    logging.info("Metadata for Stripe session: %s", metadata)

    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": product_name},
                "unit_amount": price_cents,
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url_with_session,
        cancel_url=cancel_url,
        customer_email=email,
        metadata=metadata,
    )

    logging.info("Stripe session created: id=%s", session["id"])
    return session.url


# ────────────────────────────────────────────────────────────────
# Webhook обработчик
# ────────────────────────────────────────────────────────────────
def handle_webhook_event(db: Session, payload: bytes, sig_header: str, region: str):
    logging.info("Начало обработки webhook для региона: %s", region)

    stripe_keys = get_stripe_keys_by_region(region)
    stripe.api_key = stripe_keys["secret_key"]
    webhook_secret = stripe_keys["webhook_secret"]

    # 1. Проверяем подпись
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logging.info("Webhook verified: %s", event["type"])
    except stripe.error.SignatureVerificationError:
        logging.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    exists = db.query(Purchase.id).filter_by(stripe_event_id=event["id"]).first()
    if exists:
        logging.info("Stripe event %s уже обработан → %s", event["id"], exists[0])
        return {"status": "duplicate"}

    # 2. Интересует только completed
    if event["type"] != "checkout.session.completed":
        return {"status": "ignored"}

    session_obj = event["data"]["object"]
    session_id = session_obj["id"]
    logging.info("Получена сессия: %s", session_id)

    # 3. Проверяем, что деньги действительно списаны
    if session_obj.get("payment_status") != "paid":
        logging.info("Session %s не оплачена (payment_status=%s) — пропускаем",
                     session_id, session_obj.get("payment_status"))
        return {"status": "unpaid"}

    metadata = session_obj.get("metadata", {}) or {}
    logging.info("Получены метаданные: %s", metadata)

    # 4. Основные данные заказа
    email = session_obj.get("customer_email")
    course_ids = [
        int(cid) for cid in (metadata.get("course_ids") or "").split(",") if cid.strip()
    ]
    logging.info("Преобразованные course_ids: %s", course_ids)

    # 5. Точное время события
    event_time = session_obj.get("created", int(datetime.utcnow().timestamp()))

    # 6. Персональные данные
    full_name = session_obj.get("customer_details", {}).get("name", "") or ""
    parts = full_name.strip().split()
    first_name = parts[0] if parts else None
    last_name = parts[-1] if len(parts) > 1 else None

    # 7. Технические данные клиента
    client_ip = metadata.get("client_ip", "0.0.0.0")
    user_agent = metadata.get("user_agent", "")
    external_id = metadata.get("external_id")
    fbp_value = metadata.get("fbp")
    fbc_value = metadata.get("fbc")

    # 8. Лэндинги + рекламный трафик
    courses_db = db.query(Course).filter(Course.id.in_(course_ids)).all()
    all_landings: List[Landing] = (
        db.query(Landing)
        .join(Landing.courses)
        .filter(Course.id.in_(course_ids))
        .all()
    )
    landings_recent_ad = {
        ln.id for ln in all_landings if _landing_has_recent_ad_visits(db, ln.id)
    }
    from_ad = bool(landings_recent_ad)
    logging.info("from_ad (по визитам) = %s", from_ad)

    # 10. Пользователь
    user = get_user_by_email(db, email)
    new_user_created, random_pass = False, None
    if not user:
        random_pass = generate_random_password()
        try:
            user = create_user(db, email, random_pass)
            new_user_created = True
            logging.info("Создан новый пользователь с email: %s", email)
        except ValueError:
            user = get_user_by_email(db, email)
    else:
        logging.info("Найден существующий пользователь: %s", user.id)

    # 11. Курсы → пользователю
    already_owned, new_courses = [], []
    for course_obj in courses_db:
        if course_obj in user.courses:
            already_owned.append(course_obj)
            logging.info("Пользователь %s уже имеет курс %s (ID=%s)",
                         user.id, course_obj.name, course_obj.id)
        else:
            add_course_to_user(db, user.id, course_obj.id)
            new_courses.append(course_obj)
            logging.info("Добавлен новый курс %s (ID=%s) пользователю %s",
                         course_obj.name, course_obj.id, user.id)

    # 12. Работа с лендингом + запись Purchase
    if new_courses:
        referer = metadata.get("referer", "")
        landing_for_purchase = None

        # 12.1 Пытаемся определить лендинг по referer
        if referer:
            try:
                slug = urlparse(referer).path.strip("/").split("/")[-1]
                landing_for_purchase = (
                    db.query(Landing)
                    .filter(Landing.page_name == slug)
                    .first()
                )
                logging.info("Лендинг определён по referer: %s → ID %s",
                             referer,
                             landing_for_purchase.id if landing_for_purchase else None)
            except Exception as e:
                logging.warning("Не удалось определить лендинг по referer %s: %s",
                                referer, e)

        # 12.2 fallback: первый лендинг первого курса
        if not landing_for_purchase:
            first_course = new_courses[0]
            landing_for_purchase = (
                db.query(Landing)
                .join(Landing.courses)
                .filter(Course.id == first_course.id)
                .first()
            )
            logging.info("Лендинг по умолчанию для курса %s: ID %s",
                         first_course.id,
                         landing_for_purchase.id if landing_for_purchase else None)

        # 12.3 Обновляем счётчик и ad-флаг
        if landing_for_purchase:
            landing_for_purchase.sales_count += 1
            logging.info("sales_count++ для лендинга ID=%s → %s",
                         landing_for_purchase.id,
                         landing_for_purchase.sales_count)
            if landing_for_purchase.id in landings_recent_ad:
                landing_for_purchase.in_advertising = True
                expiry = datetime.utcnow() + timedelta(hours=AD_INACTIVITY_HOURS)
                if (not landing_for_purchase.ad_flag_expires_at or
                        landing_for_purchase.ad_flag_expires_at < expiry):
                    landing_for_purchase.ad_flag_expires_at = expiry

        # 12.4 Записываем покупку
        purchase = Purchase(
            user_id=user.id,
            course_id=None,  # это «сборная» покупка сразу нескольких курсов
            landing_id=landing_for_purchase.id if landing_for_purchase else None,
            from_ad=from_ad,
            amount=session_obj["amount_total"] / 100,
            stripe_event_id=event["id"],  # для идемпотентности (совет из первого ответа)
        )
        db.add(purchase)
    db.commit()

    # 9. Отправляем событие Purchase в FB
    _send_facebook_purchase(
        email=email,
        amount=session_obj["amount_total"] / 100,
        currency=session_obj["currency"],
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        external_id=external_id,
        fbp=fbp_value,
        fbc=fbc_value,
        first_name=first_name,
        last_name=last_name,
        event_time=event_time,
    )
    # 13. Письма
    if already_owned:
        send_already_owned_course_email(
            recipient_email=email,
            course_names=[c.name for c in already_owned],
            region=region,
        )

    if new_courses:
        send_successful_purchase_email(
            recipient_email=email,
            course_names=[c.name for c in new_courses],
            new_account=new_user_created,
            password=random_pass if new_user_created else None,
            region=region,
        )

    logging.info("Обработка завершена успешно (session=%s)", session_id)
    return {"status": "ok"}
