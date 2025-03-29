import logging
from datetime import datetime
from typing import List

import requests
import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from fastapi import Request



from ..core.config import settings
from ..services_v2.user_service import (
    get_user_by_email,
    create_user,
    add_course_to_user,
    generate_random_password
)

from ..utils.email_sender import (
    send_successful_purchase_email,
    send_failed_purchase_email
)


def _send_facebook_purchase(
        email: str,
        amount: float,
        currency: str,
        course_ids: list[int],
        client_ip: str,
        user_agent: str,
        fbp: str | None = None,
        fbc: str | None = None
):
    try:
        if not email:  # Добавляем валидацию
            logging.warning("Empty email for Facebook Purchase event")
            return

        event_data = {
            "data": [{
                "event_name": "Purchase",
                "event_time": int(datetime.now().timestamp()),
                "user_data": {
                    "em": [email.lower()],
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

        # Добавляем fbp / fbc в user_data, если есть
        user_data = event_data["data"][0]["user_data"]
        if fbp:
            user_data["fbp"] = fbp
        if fbc:
            user_data["fbc"] = fbc

        response = requests.post(
            f"https://graph.facebook.com/v18.0/{settings.FACEBOOK_PIXEL_ID}/events",
            params={"access_token": settings.FACEBOOK_ACCESS_TOKEN},
            json=event_data,
            timeout=3  # Добавляем таймаут
        )

        if response.status_code != 200:
            logging.error(f"Facebook Pixel error: {response.status_code} - {response.text}")

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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid region '{region}'")

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
    fbc: str | None = None
) -> str:
    stripe_keys = get_stripe_keys_by_region(region)
    stripe.api_key = stripe_keys["secret_key"]

    client_ip = request.headers.get("X-Forwarded-For", "").split(",")[0] or request.client.host or "0.0.0.0"
    user_agent = request.headers.get("User-Agent", "")

    success_url_with_session = f"{success_url}?session_id={{CHECKOUT_SESSION_ID}}&region={region}"

    metadata = {
        "course_ids": ",".join(map(str, course_ids)),
        "client_ip": client_ip,
        "user_agent": user_agent
    }
    if fbp:
        metadata["fbp"] = fbp
    if fbc:
        metadata["fbc"] = fbc

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
        metadata=metadata
    )
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
        session = event["data"]["object"]
        session_id = session["id"]
        logging.info("Получена сессия : %s", session_id)
        metadata = session.get("metadata", {})
        logging.info("Получены метаданные: %s", metadata)
        course_ids_str = metadata.get("course_ids", "")
        # Преобразуем строку "101,102,103" в список [101, 102, 103]
        if isinstance(course_ids_str, str):
            # Если данные пришли в виде строки, например "306" или "306,143"
            course_ids = [int(cid) for cid in course_ids_str.split(",") if cid.strip()]
        elif isinstance(course_ids_str, list):
            # Если данные пришли в виде списка, например [306] или [306,143]
            course_ids = [int(cid) for cid in course_ids_str]
        else:
            course_ids = []
        logging.info("Преобразованные course_ids: %s", course_ids)
        email = session.get("customer_email")
        client_ip = metadata.get("client_ip", "0.0.0.0")  # IP из метаданных
        user_agent = metadata.get("user_agent", "")  # User-Agent из метаданных
        fbp_value = metadata.get("fbp")
        fbc_value = metadata.get("fbc")
        if email and course_ids:
            _send_facebook_purchase(
                email=email,
                amount=session["amount_total"] / 100,
                currency=session["currency"],
                course_ids=course_ids,
                client_ip=client_ip,
                user_agent=user_agent,
                fbp=fbp_value,
                fbc=fbc_value
            )
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
            for cid in course_ids:
                logging.info("Добавляю курс %s пользователю %s", cid, user.id)
                add_course_to_user(db, user.id, cid)
                logging.info("Курсы успешно добавлены пользователю %s", user.id)
            # Отправка письма об успешной покупке
            send_successful_purchase_email(
                recipient_email=email,
                course_id=0,  # Если требуется, можно передавать как-то список или отдельное значение
                new_account=new_user_created,
                password=random_pass if new_user_created else None
            )
    elif event["type"] in ("checkout.session.async_payment_failed", "checkout.session.expired"):
        session = event["data"]["object"]
        email = session.get("customer_email")
        if email:
            send_failed_purchase_email(recipient_email=email, course_id=0)