# app/api/payments.py
import stripe
import secrets
import string
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks, status
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.core.config import settings
from app.models.models import Landing, User
from app.services.user_service import get_user_by_email, add_course_to_user, create_user
from app.utils.email_sender import send_successful_purchase_email

router = APIRouter()
stripe.api_key = settings.STRIPE_SECRET_KEY


def generate_random_password(length: int = 12) -> str:
    alphabet = string.ascii_letters + string.digits
    return ''.join(secrets.choice(alphabet) for _ in range(length))


@router.post("/create-checkout-session", summary="Создать Stripe Checkout-сессию для покупки курса")
def create_checkout_session(course_id: int, email: str, db: Session = Depends(get_db)):
    """
    Создает сессию оплаты в Stripe для указанного курса.
    Использует данные из таблицы Landing для определения цены и описания курса.
    """
    # Получаем лендинг по course_id (предполагается, что каждый курс имеет один лендинг)
    landing = db.query(Landing).filter(Landing.course_id == course_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found for the course")
    # Цена из БД (например, Decimal), переводим в центы
    price_cents = int(landing.price * 100)

    # Задайте success_url и cancel_url (замените yourdomain.com на ваш домен)
    success_url = "https://yourdomain.com/payment-success?session_id={CHECKOUT_SESSION_ID}"
    cancel_url = "https://yourdomain.com/payment-cancelled"

    try:
        session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{
                "price_data": {
                    "currency": "usd",  # измените валюту при необходимости
                    "product_data": {
                        "name": landing.title,
                        "description": landing.main_text,
                    },
                    "unit_amount": price_cents,
                },
                "quantity": 1,
            }],
            mode="payment",
            customer_email=email,
            metadata={
                "course_id": course_id,
                "email": email,
            },
            success_url=success_url,
            cancel_url=cancel_url,
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

    return {"sessionId": session.id}


@router.post("/webhook", status_code=200)
async def stripe_webhook(request: Request, db: Session = Depends(get_db), background_tasks: BackgroundTasks = None):
    """
    Обрабатывает webhook-события от Stripe.
    При событии checkout.session.completed:
      - Извлекает email и course_id из metadata,
      - Если пользователя с таким email нет, создаёт новый аккаунт с случайным паролем,
      - Привязывает купленный курс к пользователю,
      - Отправляет письмо с подтверждением покупки.
    """
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = settings.STRIPE_WEBHOOK_SECRET
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Webhook Error: {str(e)}")

    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        course_id = session["metadata"].get("course_id")
        email = session["metadata"].get("email")
        amount_total = session.get("amount_total")  # в центах

        # Проверяем, существует ли пользователь с данным email
        user = get_user_by_email(db, email)
        if not user:
            # Создаем нового пользователя с случайным паролем
            new_password = generate_random_password()
            user = create_user(db, email=email, password=new_password, name="")
            # Отправляем письмо с информацией для нового аккаунта
            if background_tasks:
                background_tasks.add_task(send_successful_purchase_email, email, course_id, new_account=True,
                                          password=new_password)
            else:
                send_successful_purchase_email(email, course_id, new_account=True, password=new_password)
        else:
            # Отправляем письмо о подтверждении покупки для существующего пользователя
            if background_tasks:
                background_tasks.add_task(send_successful_purchase_email, email, course_id, new_account=False)
            else:
                send_successful_purchase_email(email, course_id, new_account=False)
        # Привязываем курс к пользователю
        try:
            add_course_to_user(db, user.id, int(course_id), float(amount_total) / 100)
        except Exception as e:
            print("Error adding course to user:", e)

    return {"status": "success"}
