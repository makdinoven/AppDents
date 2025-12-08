

import hashlib
import json
import logging
import uuid
from datetime import datetime, timedelta
from typing import List
from urllib.parse import urlparse

import requests
import stripe
from fastapi import HTTPException, Request
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .book_service import books_in_landing
from ..services_v2.wallet_service import debit_balance, get_cashback_percent
from ..core.config import settings
from ..models.models_v2 import Course, Landing, Purchase, WalletTxTypes, User, ProcessedStripeEvent, PurchaseSource, \
    AbandonedCheckout, FreeCourseAccess, FreeCourseSource, BookLanding, Book, AdVisit, BookAdVisit
from ..services_v2.user_service import (
    add_course_to_user,
    create_user,
    generate_random_password,
    get_user_by_email, credit_balance, add_book_to_user,
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

# ───────────────────────────────────────────────────────────────
# IP-based Ad Attribution helper
# ───────────────────────────────────────────────────────────────
def check_ad_visit_by_ip(db: Session, ip_address: str) -> bool:
    """Проверяет, был ли рекламный визит с данного IP за последние 24 часа."""
    if not ip_address or ip_address == "0.0.0.0":
        return False
    
    cutoff = datetime.utcnow() - timedelta(hours=24)
    
    # Проверяем ad_visits (курсовые лендинги)
    course_visit = db.query(AdVisit).filter(
        AdVisit.ip_address == ip_address,
        AdVisit.visited_at >= cutoff
    ).first()
    if course_visit:
        return True
    
    # Проверяем book_ad_visits (книжные лендинги)
    book_visit = db.query(BookAdVisit).filter(
        BookAdVisit.ip_address == ip_address,
        BookAdVisit.visited_at >= cutoff
    ).first()
    return book_visit is not None


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
    course_ids: List[int] | None = None,
    book_ids: List[int] | None = None,
    product_name: str | None = None,
    price_cents: int,
    region: str,
    success_url: str,
    cancel_url: str,
    request: Request,
    fbp: str | None = None,
    fbc: str | None = None,
    landing_ids: list[int] | None = None,
    book_landing_ids: List[int] | None = None,
    from_ad : bool | None = None,
    extra_metadata: dict | None = None,
) -> str:
    """Создаёт Stripe Checkout Session и возвращает URL оплаты."""
    course_ids = course_ids or []
    book_ids = book_ids or []
    book_landing_ids = book_landing_ids or []

    course_names: list[str] = []
    if course_ids:
        course_names = [
            c.name for c in db.query(Course).filter(Course.id.in_(course_ids)).all()
        ]

    book_titles: list[str] = []
    if book_landing_ids:
        bl_list = db.query(BookLanding).filter(BookLanding.id.in_(book_landing_ids)).all()
        for bl in bl_list:
            for b in books_in_landing(db, bl):
                book_titles.append(b.title)

    # уберём дубликаты, сохраняя порядок
    seen = set()
    book_titles = [t for t in book_titles if not (t in seen or seen.add(t))]

    # Если product_name не передали – формируем:
    if not product_name:
        parts = []
        if course_names:
            parts.append(", ".join(course_names))
        if book_titles:
            parts.append(", ".join(book_titles))
        if not parts:
            # ни курсов, ни книг — нечего чек-аутить
            raise HTTPException(status_code=400, detail="Nothing to checkout")

        product_name = "Purchase: " + " | ".join(parts)




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
    
    # Извлекаем slug из referer заранее для надежного определения лендинга
    referer_slug = None
    if referer:
        try:
            parsed_path = urlparse(referer).path.strip("/")
            if parsed_path:
                referer_slug = parsed_path.split("/")[-1]
        except Exception as e:
            logging.warning("Failed to parse referer slug: %s", e)
    
    metadata: dict = {
        "course_ids": ",".join(map(str, course_ids)),
        "client_ip": client_ip,
        "user_agent": user_agent,
        "referer": referer,
        "external_id": external_id,
        "purchase_lang": purchase_lang,
    }
    
    # Сохраняем slug отдельно для надежного определения лендинга
    if referer_slug:
        metadata["referer_slug"] = referer_slug
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

        # На всякий случай докинем книги в metadata, если роут не положил
    if book_landing_ids and "book_landing_ids" not in metadata:
        metadata["book_landing_ids"] = json.dumps(book_landing_ids)

    # Обрезаем все значения метаданных до 500 символов (лимит Stripe)
    for key, value in metadata.items():
        if value and isinstance(value, str) and len(value) > 500:
            metadata[key] = value[:500]
            logging.warning("Metadata key '%s' truncated from %d to 500 chars", key, len(value))

    logging.info("Checkout product_name → %s", product_name)
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
        landing_for_purchase = None
        
        # Приоритет 1: используем предварительно извлеченный slug
        referer_slug = metadata.get("referer_slug", "")
        if referer_slug:
            landing_for_purchase = db.query(Landing).filter_by(page_name=referer_slug).first()
            if landing_for_purchase:
                logging.info("Landing определен по referer_slug: %s → %s", referer_slug, landing_for_purchase.id)
        
        # Приоритет 2: пробуем парсить полный referer (может быть обрезан)
        if not landing_for_purchase:
            referer = metadata.get("referer", "")
            if referer:
                try:
                    slug = urlparse(referer).path.strip("/").split("/")[-1]
                    if slug:
                        landing_for_purchase = db.query(Landing).filter_by(page_name=slug).first()
                        if landing_for_purchase:
                            logging.info("Landing определен по полному referer: %s → %s", slug, landing_for_purchase.id)
                except Exception as e:
                    logging.warning("Failed to parse referer in webhook: %s", e)

        # Приоритет 3: первый лендинг первого курса
        if not landing_for_purchase and course_ids:
            landing_for_purchase = (
                db.query(Landing)
                .join(Landing.courses)
                .filter(Course.id == course_ids[0])
                .first()
            )
            if landing_for_purchase:
                logging.info("Landing определен по первому курсу: %s → %s", course_ids[0], landing_for_purchase.id)

        if landing_for_purchase:
            landing_ids_list = [landing_for_purchase.id]

    # [CHANGE] окончательный фолбэк: даже если ничего не нашли — создадим Purchase с NULL-landing
    if not landing_ids_list:
        # если нет курсовых лендингов, но есть книжные — финансовый факт пойдёт в книжные
        if metadata.get("book_landing_ids"):
            landing_ids_list = []
        else:
            logging.warning("landing_ids_list is empty → will create Purchase with landing_id=NULL")
            landing_ids_list = [None]

    logging.info("Landings: %s", landing_ids_list)

    # 9) Время события и атрибуция рекламы
    event_time = session.get("created", int(datetime.utcnow().timestamp()))

    # 10) Персональные/тех данные (нужны для атрибуции по IP)
    full_name = (session.get("customer_details", {}) or {}).get("name", "") or ""
    parts = full_name.strip().split()
    first_name = parts[0] if parts else None
    last_name = parts[-1] if len(parts) > 1 else None

    client_ip = metadata.get("client_ip", "0.0.0.0")
    user_agent = metadata.get("user_agent", "")
    external_id = metadata.get("external_id")
    fbp_value = metadata.get("fbp")
    fbc_value = metadata.get("fbc")

    raw_from_ad = (metadata.get("from_ad", "false") or "false").lower()
    from_ad = (raw_from_ad == "true")
    logging.info("from_ad (из metadata) = %s", from_ad)

    # Дополнительная атрибуция по IP (24-часовое окно)
    if not from_ad:
        if check_ad_visit_by_ip(db, client_ip):
            from_ad = True
            logging.info("from_ad overridden to True by IP attribution (ip=%s)", client_ip)

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

    md = session.get("metadata") or {}
    book_landing_ids_list = []
    book_ids_list = []

    try:
        if md.get("book_landing_ids"):
            book_landing_ids_list = list({int(x) for x in json.loads(md["book_landing_ids"])})
    except Exception:
        logging.warning("Bad metadata.book_landing_ids: %s", md.get("book_landing_ids"))

    try:
        if md.get("book_ids"):
            book_ids_list = list({int(x) for x in json.loads(md["book_ids"])})
    except Exception:
        logging.warning("Bad metadata.book_ids: %s", md.get("book_ids"))

    # 12.1) Выдаём книги, купленные напрямую
    new_books = []
    already_owned_books = []

    # 12.2) Обрабатываем книжные ЛЕНДИНГИ: выдаём книги из лендинга, инкрементим sales_count
    purchased_book_ids = set(book_ids_list)
    book_landing_purchase_records: list[Purchase] = []
    book_purchase_records: list[Purchase] = []

    for blid in book_landing_ids_list:
        bl = db.query(BookLanding).filter(
            BookLanding.id == blid
        ).one_or_none()
        if not bl:
            logging.warning("Book landing %s not found", blid)
            continue

        if bl.is_hidden:
            logging.info("Book landing %s скрыт, но покупка подтверждена — выдаём доступ", blid)

        books_from_bl = books_in_landing(db, bl)
        for b in books_from_bl:
            if b in user.books:
                already_owned_books.append(b)
            else:
                add_book_to_user(db, user.id, b.id)
                new_books.append(b)

        # аккумулируем для FB
        purchased_book_ids.update(b.id for b in books_from_bl)

        # sales_count++ у книжного лендинга
        bl.sales_count = (bl.sales_count or 0) + 1

        book_landing_purchase = Purchase(
            user_id=user.id,
            book_landing_id=blid,
            book_id=None,
            from_ad=from_ad,
            amount=0.0,
            source=purchase_source,
        )
        db.add(book_landing_purchase)
        book_landing_purchase_records.append(book_landing_purchase)

    # 12.3) Чистим корзину от купленных книжных лендингов (если были)
    try:
        cart_bl_ids = []
        if md.get("cart_book_landing_ids"):
            cart_bl_ids = list({int(x) for x in json.loads(md["cart_book_landing_ids"])})
        for blid in set(book_landing_ids_list) | set(cart_bl_ids):
            cs.remove_book_silent(db, user, blid)
    except Exception as e:
        logging.warning("Failed to cleanup cart book landings: %s", e)

    # 12.4) Фиксируем покупки отдельных книг (если переданы напрямую)
    for bid in book_ids_list:
        book_purchase = Purchase(
            user_id=user.id,
            book_landing_id=None,
            book_id=bid,
            from_ad=from_ad,
            amount=0.0,
            source=purchase_source,
        )
        db.add(book_purchase)
        book_purchase_records.append(book_purchase)

    # 15) [CHANGE] Создаём Purchase ВСЕГДА (финансовый факт), даже если нет новых курсов / landing_id = NULL
    amount_total = (session.get("amount_total") or 0) / 100.0
    purchase = None
    if landing_ids_list:
        for idx, lid in enumerate(landing_ids_list):
            p = Purchase(
                user_id=user.id,
                landing_id=lid,
                from_ad=from_ad,
                amount=amount_total if idx == 0 else 0.0,
                source=purchase_source,
            )
            db.add(p)
            if idx == 0:
                purchase = p

    elif book_landing_ids_list:
        if book_landing_purchase_records:
            first_purchase = book_landing_purchase_records[0]
            first_purchase.amount = amount_total
            purchase = first_purchase
        else:
            for idx, blid in enumerate(book_landing_ids_list):
                p = Purchase(
                    user_id=user.id,
                    book_landing_id=blid,
                    from_ad=from_ad,
                    amount=amount_total if idx == 0 else 0.0,
                    source=purchase_source,
                )
                db.add(p)
                if idx == 0:
                    purchase = p

    elif book_ids_list:
        if book_purchase_records:
            first_purchase = book_purchase_records[0]
            first_purchase.amount = amount_total
            purchase = first_purchase
        else:
            for idx, bid in enumerate(book_ids_list):
                p = Purchase(
                    user_id=user.id,
                    book_id=bid,
                    from_ad=from_ad,
                    amount=amount_total if idx == 0 else 0.0,
                    source=purchase_source,
                )
                db.add(p)
                if idx == 0:
                    purchase = p

    else:
        # крайний фолбэк
        p = Purchase(
            user_id=user.id,
            landing_id=None,
            from_ad=from_ad,
            amount=amount_total,
            source=purchase_source,
        )
        db.add(p)
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
            # Извлекаем URL источника для лучшего attribution
            event_source_url = (
                metadata.get("referer") or 
                metadata.get("success_url") or 
                session.get("success_url")
            )
            
            # Собираем теги для логики MEDG (plastic_surgery и др.)
            tag_names_set: set[str] = set()
            # Теги из лендингов
            if landing_ids_list:
                for lid in landing_ids_list:
                    if lid:
                        landing_obj = db.query(Landing).filter_by(id=lid).first()
                        if landing_obj and hasattr(landing_obj, 'tags') and landing_obj.tags:
                            tag_names_set.update(t.name for t in landing_obj.tags if t.name)
            # Теги из книжных лендингов
            if book_landing_ids_list:
                for blid in book_landing_ids_list:
                    bl_obj = db.query(BookLanding).filter_by(id=blid).first()
                    if bl_obj and hasattr(bl_obj, 'tags') and bl_obj.tags:
                        tag_names_set.update(t.name for t in bl_obj.tags if t.name)
            # Теги из книг
            if purchased_book_ids:
                books_with_tags = db.query(Book).filter(Book.id.in_(list(purchased_book_ids))).all()
                for book_obj in books_with_tags:
                    if hasattr(book_obj, 'tags') and book_obj.tags:
                        tag_names_set.update(t.name for t in book_obj.tags if t.name)
            
            logging.info("FB event tags collected: %s", list(tag_names_set))
            
            send_facebook_events(
                region=purchase_lang,
                email=email,
                amount=amount_total,
                currency=session.get("currency"),
                course_ids=course_ids,
                book_ids=sorted(purchased_book_ids),
                client_ip=client_ip,
                user_agent=user_agent,
                external_id=external_id,
                fbp=fbp_value,
                fbc=fbc_value,
                first_name=first_name,
                last_name=last_name,
                event_time=event_time,
                event_id=session_id,  # используем ID сессии для дедупликации на стороне FB
                event_source_url=event_source_url,
                tag_names=list(tag_names_set),  # теги для MEDG логики
            )
            logging.info("FB Purchase sent (from_ad=True, url=%s)", event_source_url or "N/A")
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
        # Собираем названия книг для письма: из новых книжных выдач + прямых покупок
        book_titles: list[str] = [b.title for b in new_books]
        try:
            if purchased_book_ids:
                extra_books = db.query(Book).filter(Book.id.in_(list(purchased_book_ids))).all()
                for b in extra_books:
                    if b.title not in book_titles:
                        book_titles.append(b.title)
        except Exception:
            logging.exception("Failed to collect book titles for email")

        send_successful_purchase_email(
            recipient_email=email,
            course_names=[c.name for c in (new_full + new_partial)],
            new_account=new_user_created,
            password=random_pass if new_user_created else None,
            region=region,
            book_titles=book_titles or None,
        )

    logging.info("Обработка завершена успешно (session=%s)", session_id)
    return {"status": "ok"}

