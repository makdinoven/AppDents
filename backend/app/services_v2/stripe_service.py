import stripe
from sqlalchemy.orm import Session
from fastapi import HTTPException, status


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
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid region '{region}'. Supported: RU, EN, ES."
        )


def create_checkout_session(
    db: Session,
    email: str,
    course_id: int,
    price_cents: int,
    course_name: str,
    region: str,
    success_url: str,
    cancel_url: str
) -> str:
    """
    Создаёт Stripe Checkout Session и возвращает URL, куда нужно перенаправить для оплаты.
    """
    stripe_keys = get_stripe_keys_by_region(region)
    stripe.api_key = stripe_keys["secret_key"]

    # В metadata передадим course_id, email, чтобы на вебхуке определить, кому привязывать
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",   # Или 'rub' для RU
                "product_data": {"name": course_name},
                "unit_amount": price_cents,  # цена в центах
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=success_url,
        cancel_url=cancel_url,
        customer_email=email,
        metadata={
            "course_id": str(course_id),
            "course_name": course_name,
            "user_email": email,
            "price_cents": str(price_cents),
        }
    )

    return session.url


def handle_webhook_event(
    db: Session,
    payload: bytes,
    sig_header: str,
    region: str
):
    """
    Обработка webhook от Stripe. Сценарий:
    - checkout.session.completed => создаём/ищем пользователя, привязываем курс, шлём успешное письмо.
    - checkout.session.async_payment_failed / checkout.session.expired => шлём письмо о неудаче.
    """
    stripe_keys = get_stripe_keys_by_region(region)
    webhook_secret = stripe_keys["webhook_secret"]
    stripe.api_key = stripe_keys["secret_key"]

    try:
        event = stripe.Webhook.construct_event(
            payload=payload,
            sig_header=sig_header,
            secret=webhook_secret
        )
    except stripe.error.SignatureVerificationError:
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    event_type = event["type"]

    if event_type == "checkout.session.completed":
        session = event["data"]["object"]
        metadata = session.get("metadata", {})
        email = metadata.get("user_email")
        course_id = metadata.get("course_id")

        if email and course_id:
            user = get_user_by_email(db, email)
            new_user_created = False

            if not user:
                # Создаём нового пользователя с временным паролем
                random_pass = generate_random_password()
                try:
                    user = create_user(db, email, random_pass)
                    new_user_created = True
                except ValueError:
                    # если вдруг параллельно создан (race-condition),
                    # то повторно достаём
                    user = get_user_by_email(db, email)

            # Привязываем курс к пользователю
            add_course_to_user(db, user.id, int(course_id))

            # Отправляем письмо об успехе
            send_successful_purchase_email(
                recipient_email=email,
                course_id=int(course_id),
                new_account=new_user_created,
                password=random_pass if new_user_created else None
            )

    elif event_type in ("checkout.session.async_payment_failed", "checkout.session.expired"):
        session = event["data"]["object"]
        email = session.get("customer_email")
        metadata = session.get("metadata", {})
        course_id = metadata.get("course_id")

        if email:
            # Отправляем письмо о неудаче
            send_failed_purchase_email(recipient_email=email, course_id=int(course_id) if course_id else None)

    # Можно обрабатывать и другие события
