

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
from ..models.models_v2 import Course, Landing, Purchase, WalletTxTypes, User, ProcessedStripeEvent, PurchaseSource, \
    AbandonedCheckout, FreeCourseAccess, FreeCourseSource
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
from ..utils.facebook import send_facebook_events

logging.basicConfig(level=logging.INFO)

# ───────────────────────────────────────────────────────────────
# Lead helper
# ───────────────────────────────────────────────────────────────
def _save_lead(db: Session, session_obj: dict, email: str | None, region: str):
    """
    Пишем запись в AbandonedCheckout или подробно логируем,
    почему запись не была создана.
    """
    session_id = session_obj["id"]

    # 0.  нет email → бессмысленно
    if not email:
        logging.info("Skip lead: no email in session %s", session_id)
        return False

    # 1.  e-mail уже зарегистрирован
    if get_user_by_email(db, email):
        logging.info("Skip lead: email %s already registered (session %s)",
                     email, session_id)
        return False

    # 2.  пытаемся вставить
    try:
        db.add(AbandonedCheckout(
            session_id = session_id,
            email      = email,
            course_ids = (session_obj.get("metadata") or {}).get("course_ids", ""),
            region     = (session_obj.get("metadata") or {})
                         .get("purchase_lang", region).upper(),
        ))
        db.commit()
        logging.info("Lead saved to AbandonedCheckout: %s (session %s)",
                     email, session_id)
        return True

    except IntegrityError:
        db.rollback()
        logging.info("Skip lead: duplicate for session %s (email %s)",
                     session_id, email)
        return False

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

def get_stripe_pmc_by_region(region: str) -> str | None:
    """Возвращает ID Payment-Method-Configuration для региона
       или None, если хотим использовать payment_method_types."""
    region = region.upper()
    if region == "RU":
        return settings.STRIPE_PMC_RU
    if region == "ES":
        return settings.STRIPE_PMC_ES
    # fallback → EN
    return settings.STRIPE_PMC_EN

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
    purchase_lang = region.upper()
    metadata: dict = {
        "course_ids": ",".join(map(str, course_ids)),
        "client_ip": client_ip,
        "user_agent": user_agent,
        "referer": referer,
        "external_id": external_id,
        "purchase_lang": purchase_lang,
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

    pmc_id = get_stripe_pmc_by_region(region)

    session_params = {
        "line_items": [{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": product_name},
                "unit_amount": price_cents,
            },
            "quantity": 1,
        }],
        "mode": "payment",
        "success_url": success_url_with_session,
        "cancel_url": cancel_url,
        "customer_email": email,
        "metadata": metadata,
    }

    # либо PMC, либо список методов (одновременно нельзя!)
    if pmc_id:
        session_params["payment_method_configuration"] = pmc_id
    else:
        session_params["payment_method_types"] = ["card"]

    # ── СОЗДАЁМ СЕССИЮ ────────────────────────────────────────────
    session = stripe.checkout.Session.create(**session_params)
    if not user:
        _save_lead(db, session, email, region)

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

    # 1) Верификация подписи Stripe
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
        logging.info("Webhook verified: %s", event["type"])
    except stripe.error.SignatureVerificationError:
        logging.error("Invalid webhook signature")
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    session_obj = event["data"]["object"]
    session_id = session_obj["id"]
    email = session_obj.get("customer_email")
    event_type = event["type"]
    logging.info("Получена сессия: %s, event_type=%s", session_id, event_type)

    # 2) Подтягиваем актуальное состояние сессии (иногда полезно при async-оплатах)
    try:
        session = stripe.checkout.Session.retrieve(
            session_id,
            expand=["payment_intent", "customer_details"]
        )
    except Exception as e:
        logging.warning("Не удалось получить расширенную сессию %s: %s. Работаем с event.data.object", session_id, e)
        session = session_obj

    payment_status = session.get("payment_status")
    livemode = session.get("livemode")
    logging.info("Stripe session: status=%s, livemode=%s, amount_total=%s %s",
                 payment_status, livemode, session.get("amount_total"), session.get("currency"))

    # 3) Интересуют оплаченные события. Учитываем и async-success.
    allowed_types = {
        "checkout.session.completed",
        "checkout.session.async_payment_succeeded",
    }

    if event_type not in allowed_types:
        # unpaid / no_payment_required / и т.д. → если не оплачено, пишем лид
        if payment_status != "paid":
            _save_lead(db, session, email, region)
        return {"status": "ignored_event"}

    # 4) Деньги действительно списаны?
    if payment_status != "paid":
        _save_lead(db, session, email, region)
        return {"status": "completed_unpaid"}

    # 5) Удаляем лиды по этому email (если были)
    deleted = (
        db.query(AbandonedCheckout)
        .filter(AbandonedCheckout.email == email)
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
        logging.info("Removed %s abandoned leads for email %s", deleted, email)

    # 6) Дедупликация по event.id
    stripe_event_id: str = event["id"]
    try:
        db.add(ProcessedStripeEvent(id=stripe_event_id))
        db.flush()
    except IntegrityError:
        db.rollback()
        logging.info("Duplicate webhook %s — skip", stripe_event_id)
        return {"status": "duplicate"}

    # 7) Метаданные
    metadata = session.get("metadata", {}) or {}
    logging.info("Получены метаданные: %s", metadata)

    balance_used_cents = int(metadata.get("balance_used", "0") or 0)
    balance_used = balance_used_cents / 100
    logging.info("balance_used (из metadata) = %.2f USD", balance_used)

    # 8) Основные данные заказа
    try:
        course_ids = [int(cid) for cid in (metadata.get("course_ids") or "").split(",") if cid.strip()]
    except Exception:
        course_ids = []
    logging.info("Преобразованные course_ids: %s", course_ids)

    # Разбираем landing_ids из metadata
    raw = metadata.get("landing_ids", "")
    try:
        landing_ids_list = json.loads(raw) or []
    except ValueError:
        try:
            landing_ids_list = [int(x) for x in raw.split(",") if x.strip()]
        except Exception:
            landing_ids_list = []

    # fallback: если landing_ids пуст — пытаемся определить по referer или по первому курсу
    if not landing_ids_list:
        referer = metadata.get("referer", "")
        landing_for_purchase = None

        # пробуем по slug из referer
        if referer:
            slug = urlparse(referer).path.strip("/").split("/")[-1]
            if slug:
                landing_for_purchase = db.query(Landing).filter_by(page_name=slug).first()

        # если по referer не нашли — первый лендинг первого курса
        if not landing_for_purchase and course_ids:
            landing_for_purchase = (
                db.query(Landing)
                .join(Landing.courses)
                .filter(Course.id == course_ids[0])
                .first()
            )

        if landing_for_purchase:
            landing_ids_list = [landing_for_purchase.id]

    # [CHANGE] окончательный фолбэк: даже если ничего не нашли — создадим Purchase с NULL-landing
    if not landing_ids_list:
        logging.warning("landing_ids_list is empty → will create Purchase with landing_id=NULL")
        landing_ids_list = [None]

    logging.info("Landings: %s", landing_ids_list)

    # 9) Время события и атрибуция рекламы
    event_time = session.get("created", int(datetime.utcnow().timestamp()))

    raw_from_ad = (metadata.get("from_ad", "false") or "false").lower()
    from_ad = (raw_from_ad == "true")
    logging.info("from_ad (из metadata) = %s", from_ad)

    # 10) Персональные/тех данные
    full_name = (session.get("customer_details", {}) or {}).get("name", "") or ""
    parts = full_name.strip().split()
    first_name = parts[0] if parts else None
    last_name = parts[-1] if len(parts) > 1 else None

    client_ip = metadata.get("client_ip", "0.0.0.0")
    user_agent = metadata.get("user_agent", "")
    external_id = metadata.get("external_id")
    fbp_value = metadata.get("fbp")
    fbc_value = metadata.get("fbc")

    # 11) Пользователь
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

    # (опционально) перенос корзины
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

    # 12) Реферальный код
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

    # 13) Выдача курсов пользователю (как у тебя было)
    courses_db = db.query(Course).filter(Course.id.in_(course_ids)).all() if course_ids else []
    already_owned, new_full, new_partial = [], [], []

    raw_source = metadata.get("source", PurchaseSource.OTHER.value)
    try:
        purchase_source = PurchaseSource(raw_source)
    except ValueError:
        purchase_source = PurchaseSource.OTHER

    for course_obj in courses_db:
        if course_obj in user.courses:
            already_owned.append(course_obj)
        else:
            if purchase_source == PurchaseSource.LANDING_WEBINAR:
                # выдаём частичный доступ
                db.add(FreeCourseAccess(
                    user_id=user.id,
                    course_id=course_obj.id,
                    source=FreeCourseSource.LANDING
                ))
                new_partial.append(course_obj)
            else:
                # полная выдача
                add_course_to_user(db, user.id, course_obj.id)
                from ..services_v2.user_service import promote_course_to_full
                promote_course_to_full(db, user.id, course_obj.id)
                new_full.append(course_obj)
            logging.info("Добавлен новый курс %s (ID=%s) пользователю %s",
                         course_obj.name, course_obj.id, user.id)

    # Если в корзине были эти лендинги — почистим
    if user.cart and landing_ids_list:
        from ..services_v2 import cart_service as cs
        for lid in landing_ids_list:
            if lid is not None:
                cs.remove_silent(db, user, lid)
        if not user.cart.items:
            cs.clear_cart(db, user)

    # 14) Инкрементируем sales_count только у валидных лендингов
    for lid in landing_ids_list:
        if lid is not None:
            ln = db.query(Landing).filter_by(id=lid).one_or_none()
            if ln:
                ln.sales_count = (ln.sales_count or 0) + 1
                logging.info("sales_count++ для лендинга ID=%s → %s", ln.id, ln.sales_count)

    # 15) [CHANGE] Создаём Purchase ВСЕГДА (финансовый факт), даже если нет новых курсов / landing_id = NULL
    amount_total = (session.get("amount_total") or 0) / 100.0
    purchase = None
    for idx, lid in enumerate(landing_ids_list):
        p = Purchase(
            user_id=user.id,
            course_id=None,  # при желании можно связать с первым course_id
            landing_id=lid,  # может быть None — у тебя nullable=True
            from_ad=from_ad,
            amount=amount_total if idx == 0 else 0.0,
            source=purchase_source,
        )
        db.add(p)
        if idx == 0:
            purchase = p

    db.commit()
    logging.info("Purchase(s) committed. first_purchase_id=%s, amount_total=%.2f", getattr(purchase, "id", None), amount_total)

    # 16) Списываем баланс, если использовался
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
            logging.info("С баланса пользователя %s списано %.2f USD (partial)", user.id, balance_used)
        except ValueError:
            logging.error("Не удалось снять %.2f USD с баланса user=%s", balance_used, user.id)

    # 17) [CHANGE] Отправляем событие в FB ТОЛЬКО для рекламы (from_ad=True) и только после коммита
    purchase_lang = (metadata.get("purchase_lang") or region).upper()
    if from_ad:
        try:
            send_facebook_events(
                region=purchase_lang,
                email=email,
                amount=amount_total,
                currency=session.get("currency"),
                course_ids=course_ids,
                client_ip=client_ip,
                user_agent=user_agent,
                external_id=external_id,
                fbp=fbp_value,
                fbc=fbc_value,
                first_name=first_name,
                last_name=last_name,
                event_time=event_time,
                event_id=session_id,  # используем ID сессии для дедупликации на стороне FB
            )
            logging.info("FB Purchase sent (from_ad=True)")
        except Exception:
            logging.exception("FB sending failed (from_ad=True)")
    else:
        logging.info("Skip FB sending (from_ad=False)")

    # 18) Реферальный кэшбэк — как было
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
                "Начислен кэшбэк %.2f USD (%s%%) пригласителю %s за purchase_id=%s",
                reward, percent, user.invited_by_id, purchase.id
            )

    # 19) Письма
    if already_owned:
        send_already_owned_course_email(
            recipient_email=email,
            course_names=[c.name for c in already_owned],
            region=region,
        )

    if (new_full + new_partial):
        send_successful_purchase_email(
            recipient_email=email,
            course_names=[c.name for c in (new_full + new_partial)],
            new_account=new_user_created,
            password=random_pass if new_user_created else None,
            region=region,
        )

    logging.info("Обработка завершена успешно (session=%s)", session_id)
    return {"status": "ok"}

