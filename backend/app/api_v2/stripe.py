from fastapi import APIRouter, Request, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..models.models_v2 import Course
from ..services_v2.stripe_service import (
    create_checkout_session,
    handle_webhook_event
)

router = APIRouter()

class CheckoutRequest(BaseModel):
    course_id: int         # ID курса в БД
    price_cents: int       # Цена в центах (например, 1000 = $10.00)
    region: str            # "RU", "EN", "ES"
    user_email: str | None = None  # Если пользователь не авторизован, нужно ввести email
    success_url: str = "https://dent-s.com/"
    cancel_url: str = "https://dent-s.com/"

@router.post("/checkout")
def stripe_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Универсальный эндпоинт для старта Stripe Checkout.
    1. Если пользователь авторизован, используем его email;
       иначе — используем email из тела запроса.
    2. Автоматически находим имя курса по course_id, вместо явной передачи с фронта.
    """

    # Если есть авторизованный пользователь, берём его email
    if current_user:
        email = current_user.email
    else:
        # Если пользователь не авторизован, обязателен email в запросе
        if not data.user_email:
            raise HTTPException(status_code=400, detail="Email is required for unauthenticated checkout")
        email = data.user_email

    # Попытаемся получить курс из БД, чтобы узнать имя и убедиться, что он существует.
    course = db.query(Course).filter(Course.id == data.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # Извлекаем имя курса
    course_name = course.name

    # Создаём session
    checkout_url = create_checkout_session(
        db=db,
        email=email,
        course_id=data.course_id,
        price_cents=data.price_cents,
        course_name=course_name,
        region=data.region,
        success_url=data.success_url,
        cancel_url=data.cancel_url
    )
    return {"checkout_url": checkout_url}

@router.post("/webhook/{region}")
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
