# api/stripe_api.py
import json
import logging
import time

import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..services_v2.cart_service import clear_cart
from ..services_v2.stripe_service import create_checkout_session, handle_webhook_event, get_stripe_keys_by_region
from ..models.models_v2 import Course, PurchaseSource
from ..services_v2.user_service import get_user_by_email, create_access_token, add_course_to_user
from ..services_v2.wallet_service import debit_balance
from ..utils.email_sender import send_successful_purchase_email

router = APIRouter()

class CheckoutRequest(BaseModel):
    course_ids: list[int]         # Список ID курсов для покупки
    price_cents: int              # Итоговая цена в центах (одна сумма для всех курсов)
    region: str                   # "RU", "EN", "ES"
    user_email: str | None = None  # Если пользователь не авторизован, email обязателен
    success_url: str = "https://example.com/payment-success"
    cancel_url: str = "https://example.com/payment-cancel"
    fbp: str | None = None  # Из cookie _fbp
    fbc: str | None = None  # Из cookie _fbc
    use_balance: bool = False
    transfer_cart: bool = False  # ←
    cart_landing_ids: list[int] | None = None
    ref_code: str | None = None
    source: PurchaseSource | None = None
    from_ad: bool | None = None

@router.post("/checkout")
def stripe_checkout(
    data: CheckoutRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Создаём Stripe Checkout session.
    Если пользователь не авторизован, требует user_email.
    Принимаем fbp/fbc (из cookies на фронте) и записываем их в metadata.
    """

    logging.info("Начало обработки запроса на создание Stripe сессии: %s", data.json())
    # 1. Проверяем и определяем email
    if current_user:
        email = current_user.email
        logging.info("Аутентифицированный пользователь, email: %s", email)
    else:
        if not data.user_email:
            logging.error("Email не передан для неавторизованного пользователя.")
            raise HTTPException(status_code=400, detail="Email is required for unauthenticated checkout")
        email = data.user_email
        logging.info("Неавторизованный пользователь, email: %s", email)

    if data.use_balance and current_user is None:
        raise HTTPException(400, "use_balance=true доступно только авторизованным")

    if data.transfer_cart and not data.cart_landing_ids:
        raise HTTPException(400, "cart_landing_ids required when transfer_cart=true")

    unique_course_ids = list(dict.fromkeys(data.course_ids))
    logging.info("Уникальные course_ids → %s", unique_course_ids)

    # 2. Проверяем курсы в БД
    courses = db.query(Course).filter(Course.id.in_(unique_course_ids)).all()
    found_ids = [c.id for c in courses]
    logging.info("Найдено в БД: %s", found_ids)

    if not courses or set(found_ids) != set(unique_course_ids):
        logging.error(
            "Не найдены все курсы. Передано: %s, найдено: %s",
            unique_course_ids, found_ids
        )
        raise HTTPException(status_code=404, detail="One or more courses not found")

    logging.info("Найдены курсы: %s", found_ids)

    # 3. Формируем название продукта
    course_names = [course.name for course in courses]
    product_name = "Purchase: " + ", ".join(course_names)
    logging.info("Сформировано название продукта: %s", product_name)
    logging.info("Регион: %s", data.region)

    total_price_usd = data.price_cents / 100
    balance_used = 0.0  # ← объявляем заранее

    if data.use_balance and current_user:
        balance_avail = float(current_user.balance or 0)

        if balance_avail >= total_price_usd - 1e-6:
            # ---- 1. списываем деньги и открываем курсы --------------------
            debit_balance(
                db,
                user_id=current_user.id,
                amount=total_price_usd,
                meta={"reason": "full_purchase", "courses": unique_course_ids},
            )
            for c in courses:
                add_course_to_user(db, current_user.id, c.id)

            # ---- 2. синхронизируем корзину --------------------------------
            from ..services_v2 import cart_service as cs

            # набор купленных course_id
            purchased = set(unique_course_ids)

            # для каждого CartItem проверяем: ВСЕ ли его курсы куплены
            for item in list(current_user.cart.items or []):
                landing_course_ids = {cr.id for cr in item.landing.courses}
                if landing_course_ids and landing_course_ids.issubset(purchased):
                    cs.remove_silent(db, current_user, item.landing_id)

            if not current_user.cart.items:  # корзина опустела
                cs.clear_cart(db, current_user)

            # если после удаления корзина пуста – полностью обнуляем
            if current_user.cart and not current_user.cart.items:
                cs.clear_cart(db, current_user)

            db.refresh(current_user)

            # ---- 3. письмо и ответ фронту ---------------------------------
            send_successful_purchase_email(
                recipient_email=current_user.email,
                course_names=[c.name for c in courses],
                new_account=False,
                region=data.region,
            )
            return {
                "checkout_url": None,
                "paid_with_balance": True,
                "balance_left": round(float(current_user.balance or 0), 2)
            }

        # --- Частичная ---
        balance_used = balance_avail

    stripe_amount_cents = data.price_cents - int(round(balance_used * 100))
    if stripe_amount_cents <= 0:
        # сюда не попадём: полная оплата балансом уже обработана выше
        stripe_amount_cents = 0

    purchase_source = data.source or PurchaseSource.OTHER

    extra = {}
    if data.transfer_cart:
        extra["transfer_cart"] = "true"
        extra["cart_landing_ids"] = json.dumps(data.cart_landing_ids)
    if balance_used:
        extra["balance_used"] = str(int(round(balance_used * 100)))
    if data.ref_code:
        extra["ref_code"] = data.ref_code
    extra["source"] = purchase_source.value

    # 4. Вызываем функцию для создания сессии Stripe
    checkout_url = create_checkout_session(
        db=db,
        email=email,
        course_ids=unique_course_ids,
        product_name=product_name,
        price_cents=stripe_amount_cents,
        region=data.region,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
        request=request,
        fbp=data.fbp,
        fbc=data.fbc,
        extra_metadata=extra,
        from_ad=data.from_ad
    )
    logging.info("Stripe сессия успешно создана, URL: %s", checkout_url)

    return {"checkout_url": checkout_url}

@router.post("/webhook/{region}")
async def stripe_webhook(
    region: str,
    request: Request,
    db: Session = Depends(get_db)
):
    payload = await request.body()
    sig_header = request.headers.get("Stripe-Signature")
    if not sig_header:
        raise HTTPException(status_code=400, detail="Missing Stripe-Signature header")

    handle_webhook_event(
        db=db,
        payload=payload,
        sig_header=sig_header,
        region=region
    )
    return {"status": "ok"}


class CompletePurchaseRequest(BaseModel):
    session_id: str
    region: str

@router.post("/complete-purchase")
def complete_purchase(
        data: CompletePurchaseRequest,
        db: Session = Depends(get_db),
):
    """
    После успешной оплаты Stripe редиректит пользователя на success_url?session_id=...
    Фронтенд "достает" session_id из query-параметров и вызывает этот эндпоинт.

    Здесь мы:
    1. Проверяем оплату через Stripe (session_id).
    2. Проверяем, что вебхук успел создать пользователя по email.
       - Если не успел, пробуем ретраи в течение N секунд.
    3. Генерируем JWT-токен и возвращаем его для авторизации.

    Обратите внимание: мы НЕ создаём пользователя здесь, так как логика создания
    находится в webhook-е (handle_webhook_event).
    """

    if data.region:
        stripe_keys = get_stripe_keys_by_region(data.region)
        stripe.api_key = stripe_keys["secret_key"]
    else:
        raise HTTPException(status_code=400, detail="Missing Stripe region")
    # 1. Получаем Session от Stripe
    try:
        checkout_session = stripe.checkout.Session.retrieve(data.session_id)
    except stripe.error.InvalidRequestError:
        raise HTTPException(
            status_code=400,
            detail="Invalid or expired session_id"
        )

    # 2. Проверяем статус платежа
    if checkout_session.payment_status != "paid":
        raise HTTPException(
            status_code=400,
            detail="Payment not completed (payment_status != paid)"
        )

    # 3. Достаём email
    email = checkout_session.get("customer_email")
    if not email:
        raise HTTPException(
            status_code=400,
            detail="No customer_email in checkout session"
        )
    user = None
    max_retries = 10
    retry_delay = 0.5

    for _ in range(max_retries):
        user = get_user_by_email(db, email)
        if user:
            break
        time.sleep(retry_delay)

    if not user:
        raise HTTPException(
            status_code=404,
            detail="User not found. Possibly webhook is delayed or user creation failed."
        )

    # 5. Генерируем Bearer-токен
    token = create_access_token({"user_id": user.id})

    return {"access_token": token, "token_type": "bearer"}