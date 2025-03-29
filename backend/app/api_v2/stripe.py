# api/stripe_api.py
import time

import stripe
from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..services_v2.stripe_service import create_checkout_session, handle_webhook_event, get_stripe_keys_by_region
from ..models.models_v2 import Course
from ..services_v2.user_service import get_user_by_email, create_user, create_access_token

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
    # 1. Проверяем и определяем email
    if current_user:
        email = current_user.email
    else:
        if not data.user_email:
            raise HTTPException(status_code=400, detail="Email is required for unauthenticated checkout")
        email = data.user_email

    # 2. Проверяем курсы в БД
    courses = db.query(Course).filter(Course.id.in_(data.course_ids)).all()
    if not courses or len(courses) != len(data.course_ids):
        raise HTTPException(status_code=404, detail="One or more courses not found")

    # 3. Формируем название продукта
    course_names = [course.name for course in courses]
    product_name = "Purchase: " + ", ".join(course_names)

    # 4. Вызываем функцию для создания сессии Stripe
    checkout_url = create_checkout_session(
        db=db,
        email=email,
        course_ids=data.course_ids,
        product_name=product_name,
        price_cents=data.price_cents,
        region=data.region,
        success_url=data.success_url,
        cancel_url=data.cancel_url,
        request=request,
        fbp=data.fbp,
        fbc=data.fbc
    )
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
        # Если через 5 секунд пользователь так и не появился,
        # значит что-то пошло не так (вебхук не сработал, сбой и т.д.).
        raise HTTPException(
            status_code=404,
            detail="User not found. Possibly webhook is delayed or user creation failed."
        )

    # 5. Генерируем Bearer-токен
    token = create_access_token({"user_id": user.id})

    return {"access_token": token, "token_type": "bearer"}