# api/stripe_api.py
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.services.auth import get_current_user_optional
from app.services.stripe_service import create_checkout_session, handle_webhook_event
from app.models.models_v2 import Course

stripe_router = APIRouter()

class CheckoutRequest(BaseModel):
    course_ids: list[int]         # Список ID курсов для покупки
    price_cents: int              # Итоговая цена в центах (одна сумма для всех курсов)
    region: str                   # "RU", "EN", "ES"
    user_email: str | None = None  # Если пользователь не авторизован, email обязателен
    success_url: str = "https://example.com/payment-success"
    cancel_url: str = "https://example.com/payment-cancel"

@stripe_router.post("/checkout")
def stripe_checkout(
    data: CheckoutRequest,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user_optional)
):
    """
    Эндпоинт для старта Stripe Checkout.
    1. Если пользователь авторизован, используем его email, иначе — берём из запроса.
    2. Извлекаем из БД все курсы по переданным course_ids.
    3. Формируем название продукта как объединение имён курсов.
    4. Создаём Stripe Checkout-сессию с одним line_item (общая цена).
    """

    # Определяем email
    if current_user:
        email = current_user.email
    else:
        if not data.user_email:
            raise HTTPException(status_code=400, detail="Email is required for unauthenticated checkout")
        email = data.user_email

    # Извлекаем курсы из БД
    courses = db.query(Course).filter(Course.id.in_(data.course_ids)).all()
    if not courses or len(courses) != len(data.course_ids):
        raise HTTPException(status_code=404, detail="One or more courses not found")

    # Формируем название продукта как объединение имён курсов
    course_names = [course.name for course in courses]
    product_name = "Purchase: " + ", ".join(course_names)

    # Создаём Stripe Checkout-сессию с одним line_item
    checkout_url = create_checkout_session(
        db=db,
        email=email,
        course_ids=data.course_ids,
        product_name=product_name,
        price_cents=data.price_cents,
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
