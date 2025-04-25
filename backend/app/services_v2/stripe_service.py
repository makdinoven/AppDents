import hashlib
import logging
import re
from datetime import datetime, timedelta
from typing import List

import requests
import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException, status, Request

from ..core.config import settings
from ..models.models_v2 import Course, Landing, Purchase
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

def _hash_email(email: str) -> str:
    """
    Приводим к нижнему регистру, убираем пробелы вокруг
    и хэшируем алгоритмом SHA-256 (hexdigest).
    """
    normalized = email.strip().lower()
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()

def _send_facebook_purchase(
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    fbp: str | None = None,
    fbc: str | None = None,
    phone: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
):
    try:
        if not email:
            logging.warning("Empty email for Facebook Purchase event")
            return

        hashed_email = _hash_email(email)
        event_data = {
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

        user_data = event_data["data"][0]["user_data"]
        if fbp:
            user_data["fbp"] = fbp
        if fbc:
            user_data["fbc"] = fbc
        if phone:
            # Оставляем только цифры и хешируем
            digits = re.sub(r"\D", "", phone)
            hashed_phone = hashlib.sha256(digits.encode("utf-8")).hexdigest()
            user_data["ph"] = [hashed_phone]
        if first_name:
            fn_norm = first_name.strip().lower()
            user_data["fn"] = [hashlib.sha256(fn_norm.encode("utf-8")).hexdigest()]

        if last_name:
            ln_norm = last_name.strip().lower()
            user_data["ln"] = [hashlib.sha256(ln_norm.encode("utf-8")).hexdigest()]

        response = requests.post(
            f"https://graph.facebook.com/v18.0/{settings.FACEBOOK_PIXEL_ID}/events",
            params={"access_token": settings.FACEBOOK_ACCESS_TOKEN},
            json=event_data,
            timeout=3
        )

        if response.status_code != 200:
            logging.error(f"Facebook Pixel error: {response.status_code} - {response.text}")
        else:
            logging.info("Facebook event sent successfully for email: %s", email)

    except Exception as e:
        logging.error(f"Failed to send Facebook event: {str(e)}", exc_info=True)

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
    ad: bool = False
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
        "ad": "true" if ad else "false"
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
        phone_number_collection={"enabled": True}
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
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )
        logging.info("Webhook событие успешно проверено: %s", event["type"])
    except stripe.error.SignatureVerificationError:
        logging.error("Неверная подпись webhook")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    if event["type"] == "checkout.session.completed":
        session_obj = event["data"]["object"]
        session_id = session_obj["id"]
        logging.info("Получена сессия: %s", session_id)

        metadata = session_obj.get("metadata", {})
        logging.info("Получены метаданные: %s", metadata)
        from_ad = (metadata.get("ad") == "true")
        phone = session_obj.get("customer_details", {}).get("phone")
        full_name = session_obj.get("customer_details", {}).get("name", "") or ""
        parts = full_name.strip().split()
        first_name = parts[0] if parts else None
        last_name = parts[-1] if len(parts) > 1 else None

        course_ids_str = metadata.get("course_ids", "")
        if isinstance(course_ids_str, str):
            course_ids = [int(cid) for cid in course_ids_str.split(",") if cid.strip()]
        else:
            course_ids = []
        logging.info("Преобразованные course_ids: %s", course_ids)

        # Получаем курсы из БД и их названия
        courses_db = db.query(Course).filter(Course.id.in_(course_ids)).all()
        course_names_all = [c.name for c in courses_db]
        logging.info("Названия курсов из БД: %s", course_names_all)

        email = session_obj.get("customer_email")
        client_ip = metadata.get("client_ip", "0.0.0.0")
        user_agent = metadata.get("user_agent", "")
        fbp_value = metadata.get("fbp")
        fbc_value = metadata.get("fbc")

        if email and course_ids:
            logging.info("Обработка успешной оплаты: email=%s, course_ids=%s", email, course_ids)

            # 1. Отправляем событие в Facebook
            _send_facebook_purchase(
                email=email,
                amount=session_obj["amount_total"] / 100,
                currency=session_obj["currency"],
                course_ids=course_ids,
                client_ip=client_ip,
                user_agent=user_agent,
                fbp=fbp_value,
                fbc=fbc_value,
                phone=phone,
                first_name=first_name,
                last_name=last_name
            )

            # 2. Проверяем, существует ли пользователь; если нет, создаём его
            user = get_user_by_email(db, email)
            new_user_created = False
            random_pass = None
            if not user:
                random_pass = generate_random_password()
                try:
                    user = create_user(db, email, random_pass)
                    new_user_created = True
                    logging.info("Создан новый пользователь с email: %s", email)
                except ValueError:
                    user = get_user_by_email(db, email)
                    logging.warning("Ошибка создания пользователя, использую существующего: %s", email)
            else:
                logging.info("Найден существующий пользователь: %s", user.id)

            # 3. Разделяем курсы на уже имеющиеся и новые
            # 3. Разделяем курсы на уже имеющиеся и новые
            already_owned = []
            new_courses = []
            for course_obj in courses_db:
                if course_obj in user.courses:
                    already_owned.append(course_obj)
                    logging.info("Пользователь %s уже имеет курс %s (ID=%s)", user.id, course_obj.name, course_obj.id)
                else:
                    add_course_to_user(db, user.id, course_obj.id)
                    new_courses.append(course_obj)
                    logging.info("Добавлен новый курс %s (ID=%s) пользователю %s", course_obj.name, course_obj.id,
                                 user.id)

                    # Увеличиваем sales_count у лендингов, связанных с курсом
                    landings = db.query(Landing).join(Landing.courses).filter(Course.id == course_obj.id).all()
                    for landing in landings:
                        landing.sales_count += 1
                        if from_ad:
                            landing.in_advertising = True
                            expiry_time = datetime.utcnow() + timedelta(hours=6)
                            # Если уже был выставлен срок, продлеваем только если он меньше новой даты
                            if not landing.ad_flag_expires_at or landing.ad_flag_expires_at < expiry_time:
                                landing.ad_flag_expires_at = expiry_time
                        logging.info("Увеличен sales_count для лендинга (ID=%s), новый sales_count=%s", landing.id,
                                     landing.sales_count)
                    purchase = Purchase(
                        user_id=user.id,
                        course_id=course_obj.id,
                        # если у вас 1:1 "курс <-> лендинг" — можно взять landings[0].id
                        # но если много лендингов, придётся решить, какой именно ID хранить.
                        landing_id=landings[0].id if landings else None,
                        from_ad=from_ad,
                        amount = session_obj["amount_total"] / 100
                    )
                    db.add(purchase)
            db.commit()

            # 4. Если оплачены курсы, которые уже есть – отправляем специальное письмо
            if already_owned:
                owned_names = [c.name for c in already_owned]
                logging.info("Пользователь оплатил курсы, которые уже имеет: %s", owned_names)
                send_already_owned_course_email(
                    recipient_email=email,
                    course_names=owned_names,
                    region=region,
                )

            # 5. Если есть новые курсы – отправляем письмо об успешной покупке
            if new_courses:
                new_names = [c.name for c in new_courses]
                logging.info("Новые курсы, добавленные пользователю: %s", new_names)
                send_successful_purchase_email(
                    recipient_email=email,
                    course_names=new_names,
                    new_account=new_user_created,
                    password=random_pass if new_user_created else None,
                    region=region
                )
        else:
            logging.warning("Неверные данные для session.completed: email=%s, course_ids=%s", email, course_ids)