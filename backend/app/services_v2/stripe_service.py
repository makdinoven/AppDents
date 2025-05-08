import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

import requests
import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request

from ..core.config import settings
from ..models.models_v2 import Course, Landing, Purchase, AdVisit
from ..services_v2.user_service import (
    get_user_by_email,
    create_user,
    add_course_to_user,
    generate_random_password
)
from ..utils.email_sender import (
    send_successful_purchase_email,
    send_already_owned_course_email
)

AD_INACTIVITY_HOURS   = 1   # TTL, который даёт покупка
AD_VISIT_WINDOW_HOURS = 3   #  окно для поиска рекламных визитов
# ────────────────────────────────────────────────────────────────

def _landing_has_recent_ad_visits(db: Session, landing_id: int) -> bool:
    """
    True ‑ если у лендинга были визиты из рекламы
    хотя бы один раз за последние AD_VISIT_WINDOW_HOURS.
    """
    since = datetime.utcnow() - timedelta(hours=AD_VISIT_WINDOW_HOURS)
    return db.query(
        db.query(AdVisit)
              .filter(
                  AdVisit.landing_id == landing_id,
                  AdVisit.visited_at >= since
              )
              .exists()
    ).scalar()


def _hash_email(email: str) -> str:
    """
    Приводим к нижнему регистру, убираем пробелы вокруг
    и хэшируем алгоритмом SHA-256 (hexdigest).
    """
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def _build_fb_event(email: str,
                    amount: float,
                    currency: str,
                    course_ids: list[int],
                    client_ip: str,
                    user_agent: str,
                    fbp: str | None,
                    fbc: str | None,
                    first_name: str | None,
                    last_name: str | None) -> dict:
    """
    Формирует payload **один раз** – его можно многократно посылать
    в разные пиксели.
    """
    if not email:
        raise ValueError("Empty email for Facebook Purchase event")

    hashed_email = _hash_email(email)
    event = {
        "data": [{
            "event_name": "Purchase",
            "event_time": int(datetime.now().timestamp()),
            "user_data": {
                "em": [hashed_email],
                "client_ip_address": client_ip if client_ip != "0.0.0.0" else None,
                "client_user_agent": user_agent or None,
            },
            "custom_data": {
                "currency": currency,
                "value": amount,
                "content_ids": [str(cid) for cid in course_ids],
                "content_type": "course",
            },
        }]
    }

    u = event["data"][0]["user_data"]
    if fbp: u["fbp"] = fbp
    if fbc: u["fbc"] = fbc
    if first_name:
        u["fn"] = [_hash_email(first_name)]
    if last_name and last_name != first_name:
        u["ln"] = [_hash_email(last_name)]

    return event


def _send_facebook_purchase(
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
):
    """
    Отправляет событие **во все пиксели из settings**.
    Любые ошибки логируем, но не прерываем цикл,
    чтобы попытаться отправить в остальные.
    """
    try:
        event_data = _build_fb_event(
            email, amount, currency, course_ids,
            client_ip, user_agent, fbp, fbc, first_name, last_name
        )
        pixels = [
            {"id": settings.FACEBOOK_PIXEL_ID,   "token": settings.FACEBOOK_ACCESS_TOKEN},
            {"id": settings.FACEBOOK_PIXEL_ID_LEARNWORLDS, "token": settings.FACEBOOK_ACCESS_TOKEN_LEARNWORLDS},
        ]

        for p in pixels:
            try:
                resp = requests.post(
                    f"https://graph.facebook.com/v18.0/{p['id']}/events",
                    params={"access_token": p["token"]},
                    json=event_data,
                    timeout=3
                )
                if resp.status_code == 200:
                    logging.info("FB Pixel %s: ok for %s", p["id"], email)
                else:
                    logging.error(
                        "FB Pixel %s error %s – %s",
                        p["id"], resp.status_code, resp.text
                    )
            except Exception as e:
                logging.error("FB Pixel %s failed: %s", p["id"], e, exc_info=True)

    except Exception as e:
        logging.error("Failed to build/send FB events: %s", e, exc_info=True)


def get_stripe_keys_by_region(region: str) -> dict:
    region = region.upper()
    if region == "RU":
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_RU,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_RU,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_RU
        }
    elif region == "EN":
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_EN,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_EN,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_EN
        }
    elif region == "ES":
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_ES,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_ES,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_ES
        }
    else:
        return {
            "secret_key": settings.STRIPE_SECRET_KEY_EN,
            "publishable_key": settings.STRIPE_PUBLISHABLE_KEY_EN,
            "webhook_secret": settings.STRIPE_WEBHOOK_SECRET_EN
        }

def create_checkout_session(
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
    stripe_keys = get_stripe_keys_by_region(region)
    stripe.api_key = stripe_keys["secret_key"]

    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0] or request.client.host or "0.0.0.0"
    user_agent = request.headers.get("User-Agent", "")
    referer = request.headers.get("Referer")
    logging.info("Creating checkout session: email=%s, course_ids=%s, Referer=%s", email, course_ids, referer)

    success_url_with_session = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&region={region}"

    metadata = {
        "course_ids": ",".join(map(str, course_ids)),
        "client_ip": client_ip,
        "user_agent": user_agent,
        "referer": referer or "",
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

logging.basicConfig(level=logging.INFO)


def handle_webhook_event(db: Session, payload: bytes, sig_header: str, region: str):
    logging.info("Начало обработки webhook для региона: %s", region)
    stripe_keys = get_stripe_keys_by_region(region)
    webhook_secret = stripe_keys["webhook_secret"]
    stripe.api_key = stripe_keys["secret_key"]

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logging.info("Webhook событие успешно проверено: %s", event["type"])
    except stripe.error.SignatureVerificationError:
        logging.error("Неверная подпись webhook")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] != "checkout.session.completed":
        return {"status": "ignored"}

    session_obj = event["data"]["object"]
    session_id = session_obj["id"]
    logging.info("Получена сессия: %s", session_id)

    metadata = session_obj.get("metadata", {}) or {}
    logging.info("Получены метаданные: %s", metadata)

    # ─────── Разбор метаданных / параметров ─────────────────────
    full_name  = session_obj.get("customer_details", {}).get("name", "") or ""
    parts      = full_name.strip().split()
    first_name = parts[0] if parts else None
    last_name  = parts[-1] if len(parts) > 1 else None

    course_ids = [int(cid) for cid in (metadata.get("course_ids") or "").split(",") if cid.strip()]
    logging.info("Преобразованные course_ids: %s", course_ids)

    # ─────── Курсы и лендинги, связанные с оплатой ──────────────
    courses_db = db.query(Course).filter(Course.id.in_(course_ids)).all()
    all_landings: List[Landing] = (
        db.query(Landing)
          .join(Landing.courses)
          .filter(Course.id.in_(course_ids))
          .all()
    )

    # лендинги, у которых действительно были рекламные визиты за 3 ч
    landings_recent_ad = {
        ln.id for ln in all_landings if _landing_has_recent_ad_visits(db, ln.id)
    }
    from_ad = bool(landings_recent_ad)
    logging.info("from_ad (по визитам) = %s", from_ad)

    # ─────── Технические данные клиента ─────────────────────────
    email       = session_obj.get("customer_email")
    client_ip   = metadata.get("client_ip", "0.0.0.0")
    user_agent  = metadata.get("user_agent", "")
    fbp_value   = metadata.get("fbp")
    fbc_value   = metadata.get("fbc")

    # ─────── Основная бизнес‑логика не менялась ─────────────────
    if not (email and course_ids):
        logging.warning("Неверные данные для session.completed: email=%s, course_ids=%s", email, course_ids)
        return {"status": "bad_data"}

    logging.info("Обработка успешной оплаты: email=%s, course_ids=%s", email, course_ids)

    # 1. Facebook Pixel
    _send_facebook_purchase(
        email=email,
        amount=session_obj["amount_total"] / 100,
        currency=session_obj["currency"],
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        fbp=fbp_value,
        fbc=fbc_value,
        first_name=first_name,
        last_name=last_name,
    )

    # 2. Пользователь
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

    # 3. Курсы
    already_owned, new_courses = [], []
    for course_obj in courses_db:
        if course_obj in user.courses:
            already_owned.append(course_obj)
            logging.info(
                "Пользователь %s уже имеет курс %s (ID=%s)",
                user.id, course_obj.name, course_obj.id
            )
        else:
            add_course_to_user(db, user.id, course_obj.id)
            new_courses.append(course_obj)
            logging.info(
                "Добавлен новый курс %s (ID=%s) пользователю %s",
                course_obj.name, course_obj.id, user.id
            )

    # Сохраняем связь пользователь–курсы
    db.commit()

    # Создаём одну запись о покупке «сборника»
    if new_courses:
        referer = metadata.get("referer", "")
        landing_for_purchase = None

        if referer:
            try:
                slug = urlparse(referer).path.strip("/").split("/")[-1]
                landing_for_purchase = (
                    db.query(Landing)
                    .filter(Landing.page_name == slug)
                    .first()
                )
                logging.info("Лендинг определён по referer: %s -> ID %s",
                             referer,
                             landing_for_purchase.id if landing_for_purchase else None)
            except Exception as e:
                logging.warning(
                    "Не удалось определить лендинг по referer %s: %s",
                    referer, e
                )

        # Если не удалось по referer, берём первый лендинг первого курса
        if not landing_for_purchase:
            first_course = new_courses[0]
            landing_for_purchase = (
                db.query(Landing)
                .join(Landing.courses)
                .filter(Course.id == first_course.id)
                .first()
            )
            logging.info(
                "Лендинг по умолчанию для курса %s: ID %s",
                first_course.id,
                landing_for_purchase.id if landing_for_purchase else None
            )

        if landing_for_purchase:
            # Увеличиваем счётчик продаж
            landing_for_purchase.sales_count += 1
            logging.info(
                "Увеличен sales_count для лендинга (ID=%s), новый sales_count=%s",
                landing_for_purchase.id,
                landing_for_purchase.sales_count
            )
            # Счетчик
            if landing_for_purchase.id in landings_recent_ad:
                landing_for_purchase.in_advertising = True
                expiry_time = datetime.utcnow() + timedelta(hours=AD_INACTIVITY_HOURS)
                if (not landing_for_purchase.ad_flag_expires_at
                        or landing_for_purchase.ad_flag_expires_at < expiry_time):
                    landing_for_purchase.ad_flag_expires_at = expiry_time

        # Создаём одну запись Purchase с общей суммой
        purchase = Purchase(
            user_id=user.id,
            course_id=None,
            landing_id=landing_for_purchase.id if landing_for_purchase else None,
            from_ad=from_ad,
            amount=session_obj["amount_total"] / 100,
        )
        db.add(purchase)
        db.commit()

    # 4. Письма
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

    return {"status": "ok"}
