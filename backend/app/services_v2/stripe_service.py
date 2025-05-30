

import hashlib
import json
import logging
import uuid
from datetime import datetime
from typing import List
from urllib.parse import urlparse

import requests
import stripe
from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from ..services_v2.wallet_service import debit_balance, get_cashback_percent
from ..core.config import settings
from ..models.models_v2 import Course, Landing, Purchase, WalletTxTypes, User, ProcessedStripeEvent
from ..services_v2.user_service import (
    add_course_to_user,
    create_user,
    generate_random_password,
    get_user_by_email, credit_balance,
)
from ..utils.email_sender import (
    send_already_owned_course_email,
    send_successful_purchase_email,
)


logging.basicConfig(level=logging.INFO)

# ────────────────────────────────────────────────────────────────
# Вспомогательные функции
# ────────────────────────────────────────────────────────────────


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
    event_id: str,
    event_name: str = "Purchase",
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> dict:
    """
    Формирует payload для Facebook Conversions API.
    ``event_name`` — "Purchase" или "Donate".
    """

    if not email:
        raise ValueError("Empty email for Facebook event")

    # ---------- 1. user_data ----------
    user_data: dict = {
        "em": [_hash_email(email)],
        "client_ip_address": None if client_ip == "0.0.0.0" else client_ip,
        "client_user_agent": user_agent or None,
    }

    # дополнительные Facebook-идентификаторы
    if external_id:
        user_data["external_id"] = [external_id]
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc

    # персональные поля
    if first_name:
        user_data["fn"] = [_hash_plain(first_name)]
    if last_name and last_name != first_name:
        user_data["ln"] = [_hash_plain(last_name)]

    # ---------- 2. финальный event ----------
    event = {
        "data": [
            {
                "event_name": event_name,          # <-- главное отличие
                "event_time": event_time,
                "event_id": event_id,
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
        "FB event built → %s | %s | amount=%s %s | courses=%s",
        email, event_name, amount, currency.upper(), course_ids,
    )
    return event
def _send_facebook_events(
    *,
    event_id: str,
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

    if not event_id:
        raise ValueError("event_id is required for FB deduplication")

    """Шлёт Purchase в два пикселя и Donate в третий."""

    # ——— 1. Собираем payload-ы
    purchase_payload = _build_fb_event(
        event_name="Purchase",
        email=email,
        amount=amount,
        currency=currency,
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        event_time=event_time,
        event_id=event_id,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
        last_name=last_name,
    )
    donate_payload = _build_fb_event(            # отличается только именем
        event_name="Donate",
        email=email,
        amount=amount,
        currency=currency,
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        event_time=event_time,
        event_id=event_id,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
        last_name=last_name,
    )

    # ——— 2. Список пикселей
    pixels_purchase = [
        {"id": settings.FACEBOOK_PIXEL_ID, "token": settings.FACEBOOK_ACCESS_TOKEN},
        {"id": settings.FACEBOOK_PIXEL_ID_LEARNWORLDS,
         "token": settings.FACEBOOK_ACCESS_TOKEN_LEARNWORLDS},
    ]
    pixel_donation = {
        "id": settings.FACEBOOK_PIXEL_ID_DONATION,
        "token": settings.FACEBOOK_ACCESS_TOKEN_DONATION,
    }

    # ——— 3. Отправляем
    def _post(pixel: dict, payload: dict, tag: str):
        try:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{pixel['id']}/events",
                params={"access_token": pixel["token"]},
                json=payload,
                timeout=3,
            )
            if resp.status_code == 200:
                logging.info("FB %s Pixel %s — OK (email=%s)",
                             tag, pixel['id'], email)
            else:
                logging.error("FB %s Pixel %s — %s %s",
                              tag, pixel['id'], resp.status_code, resp.text)
        except Exception as e:
            logging.error("FB %s Pixel %s failed: %s",
                          tag, pixel['id'], e, exc_info=True)

    for p in pixels_purchase:
        _post(p, purchase_payload, "Purchase")
    _post(pixel_donation, donate_payload, "Donate")

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
    landing_ids: list[int] | None = None,
    from_ad : bool | None = None,
    extra_metadata: dict | None = None,
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
    if landing_ids:
        # сериализуем список в JSON-строку, чтобы в webhook легко распарсить
        metadata["landing_ids"] = json.dumps(landing_ids)

    if from_ad is not None:
        # сохраняем точно то, что придёт с фронта: "true" или "false"
        metadata["from_ad"] = str(from_ad).lower()

    if extra_metadata:
        metadata.update(extra_metadata)


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

    stripe_event_id: str = event["id"]
    try:
        db.add(ProcessedStripeEvent(id=stripe_event_id))
        db.flush()  # пытаемся вставить сразу
    except IntegrityError:
        db.rollback()  # было уже в таблице → дубликат
        logging.info("Duplicate webhook %s — skip", stripe_event_id)
        return {"status": "duplicate"}


    metadata = session_obj.get("metadata", {}) or {}
    balance_used_cents = int(metadata.get("balance_used", "0") or 0)
    balance_used = balance_used_cents / 100
    logging.info("balance_used (из metadata) = %.2f USD", balance_used)

    logging.info("Получены метаданные: %s", metadata)

    # 4. Основные данные заказа
    email = session_obj.get("customer_email")
    course_ids = [
        int(cid) for cid in (metadata.get("course_ids") or "").split(",") if cid.strip()
    ]
    logging.info("Преобразованные course_ids: %s", course_ids)

    # разбираем landing_ids из metadata
    # разбираем landing_ids из metadata
    raw = metadata.get("landing_ids", "")
    try:
        landing_ids_list = json.loads(raw) or []
    except ValueError:
        landing_ids_list = [int(x) for x in raw.split(",") if x.strip()]

    # fallback: если landing_ids не пришёл или пустой — определяем лендинг по referer или первому курсу
    if not landing_ids_list:
        referer = metadata.get("referer", "")
        landing_for_purchase = None

        # пробуем по slug из referer
        if referer:
            slug = urlparse(referer).path.strip("/").split("/")[-1]
            landing_for_purchase = db.query(Landing).filter_by(page_name=slug).first()

        # если по referer не нашли — первый лендинг первого курса
        if not landing_for_purchase and course_ids:
            landing_for_purchase = (
                db.query(Landing)
                .join(Landing.courses)
                .filter(Course.id == course_ids[0])
                .first()
            )

        # сохраняем в список
        if landing_for_purchase:
            landing_ids_list = [landing_for_purchase.id]
    logging.info("Landings: %s", landing_ids_list)
    # 5. Точное время события
    event_time = session_obj.get("created", int(datetime.utcnow().timestamp()))

    raw_from_ad = metadata.get("from_ad", "false").lower()
    from_ad = (raw_from_ad == "true")
    logging.info("from_ad (из metadata) = %s", from_ad)

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

    #. Пользователь (user уже получен) создаем корзину для него.
    if metadata.get("transfer_cart") == "true":
        cart_ids_raw = metadata.get("cart_landing_ids", "[]")
        try:
            cart_ids = json.loads(cart_ids_raw)
        except Exception:
            cart_ids = []
        from ..services_v2 import cart_service as cs
        for lid in cart_ids:
            try:
                cs.add_landing(db, user, int(lid))
            except Exception as e:
                logging.warning("Не удалось добавить лендинг %s в корзину пользователя %s: %s",
                                lid, user.id, e)

    # ───── Привязка реферального кода гостя ─────
    ref_code = metadata.get("ref_code")
    if ref_code and user.invited_by_id is None:
        inviter = db.query(User).filter(User.referral_code == ref_code).first()
        if inviter and inviter.id != user.id:
            user.invited_by_id = inviter.id
            db.commit()
            logging.info("Ref-code %s применён: user %s → inviter %s",
                         ref_code, user.id, inviter.id)
        else:
            logging.info("Ref-code %s невалиден или self-referral (user %s)",
                         ref_code, user.id)
    # ─────────────────────────────────────────────

    # 11. Курсы → пользователю
    courses_db = db.query(Course).filter(Course.id.in_(course_ids)).all()
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

    # Запись Purchase с правильным landing_id
    for lid in landing_ids_list:
        ln = db.query(Landing).filter_by(id=lid).one_or_none()
        if ln:
            ln.sales_count = (ln.sales_count or 0) + 1
            logging.info("sales_count++ для лендинга ID=%s → %s", ln.id, ln.sales_count)
    purchase = None
    if new_courses:
        # создаём Purchase: первую запись – с полной суммой, остальные – с amount=0
        amount_total = session_obj["amount_total"] / 100.0
        for idx, lid in enumerate(landing_ids_list):
            p = Purchase(
                user_id=user.id,
                course_id=None,
                landing_id=lid,
                from_ad=from_ad,
                amount=amount_total if idx == 0 else 0.0,
            )
            db.add(p)
            if idx == 0:
                purchase = p
    db.commit()

    if balance_used > 0:
        try:
            debit_balance(
                db,
                user_id=user.id,
                amount=balance_used,
                meta={
                    "reason": "partial_purchase",
                    "purchase_id": purchase.id if purchase else None,
                },
            )
            logging.info("С баланса пользователя %s списано %.2f USD (partial)",
                         user.id, balance_used)
        except ValueError:
            # на случай, если баланс внезапно меньше, просто логируем
            logging.error("Не удалось снять %.2f USD с баланса user=%s",
                          balance_used, user.id)

    # 9. Отправляем событие Purchase в FB
    _send_facebook_events(
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
        event_id=session_obj["id"]
    )

    if purchase and user.invited_by_id:
        percent = get_cashback_percent(db, user.id)
        if percent > 0:
            reward = purchase.amount * (percent / 100)
            credit_balance(
                db,
                user_id=user.invited_by_id,
                amount=reward,
                tx_type=WalletTxTypes.REFERRAL_CASHBACK,
                meta={
                    "from_user": user.id,
                    "purchase_id": purchase.id,
                    "percent": percent,
                }
            )
            logging.info(
                "Начислен кэшбэк %.2f USD (%s%%) пригласителю %s "
                "за purchase_id=%s",
                reward, percent, user.invited_by_id, purchase.id
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
