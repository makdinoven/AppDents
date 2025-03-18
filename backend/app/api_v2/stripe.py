from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..services_v2.stripe_service import (
    create_checkout_session,
    handle_webhook_event
)

stripe_router = APIRouter()

class CheckoutRequest(BaseModel):
    course_id: int         # ID курса в БД
    course_name: str       # Название курса (можно брать из БД, но для примера передаём)
    price_cents: int       # Цена в центах (например, 1000 = $10.00)
    region: str            # "RU", "EN", "ES"
    user_email: str | None = None  # Если пользователь не авторизован, нужно ввести email
    success_url: str = "https://dent-s.com/"
    cancel_url: str = "https://dent-s.com/"

@stripe_router.post("/checkout")
def stripe_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user_optional)
):
    """
    Универсальный эндпоинт для старта Stripe Checkout.
    Если пользователь авторизован, используем его email;
    если нет — используем email из тела запроса.
    """
    # Если есть авторизованный пользователь, берём его email
    if current_user:
        email = current_user.email
    else:
        # Если пользователь не авторизован, обязателен email в запросе
        if not data.user_email:
            raise HTTPException(status_code=400, detail="Email is required for unauthenticated checkout")
        email = data.user_email

    # Создаём session
    checkout_url = create_checkout_session(
        db=db,
        email=email,
        course_id=data.course_id,
        price_cents=data.price_cents,
        course_name=data.course_name,
        region=data.region,
        success_url=data.success_url,
        cancel_url=data.cancel_url
    )
    return {"checkout_url": checkout_url}

@stripe_router.post("/webhook/{region}")
async def stripe_webhook(
    region: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Stripe Webhook для обработки события успешной / неуспешной оплаты.
    """
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
