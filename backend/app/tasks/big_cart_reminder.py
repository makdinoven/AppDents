from datetime import datetime, timedelta

from celery import shared_task
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models_v2 import Cart, User
from app.utils.email_sender.common import send_big_cart_reminder_email


# через сколько часов после изменения корзины можно слать ПЕРВОЕ письмо
BIG_CART_DELAY_HOURS = 24

# пауза между письмами (чтобы не спамить одного юзера каждый запуск)
BIG_CART_INTERVAL_HOURS = 168

# максимальное количество писем по одной корзине
MAX_BIG_CART_REMINDERS = 1

# ограничение пачки за один прогон (защита SMTP)
BIG_CART_BATCH_LIMIT = 100


@shared_task(name="app.tasks.big_cart_reminder.process_big_cart_reminders")
def process_big_cart_reminders() -> int:
    """
    Напоминания о большой корзине:
    1) считаем средний total_amount по корзинам > 0;
    2) выбираем корзины:
       - total_amount > среднего;
       - updated_at < now - BIG_CART_DELAY_HOURS;
       - bigcart_send_count < MAX_BIG_CART_REMINDERS;
       - либо письмо ещё не слалось, либо прошло достаточно времени
         с bigcart_last_sent_at (BIG_CART_INTERVAL_HOURS);
    3) шлём письмо;
    4) увеличиваем bigcart_send_count и обновляем bigcart_last_sent_at
       ТОЛЬКО при успешной отправке.
    """

    db: Session = SessionLocal()
    now = datetime.utcnow()
    cutoff_delay = now - timedelta(hours=BIG_CART_DELAY_HOURS)
    cutoff_interval = now - timedelta(hours=BIG_CART_INTERVAL_HOURS)

    try:
        # 1. Средний чек по корзинам > 0
        avg_amount = (
            db.query(func.avg(Cart.total_amount))
            .filter(Cart.total_amount > 0)
            .scalar()
        ) or 0.0

        if avg_amount <= 0:
            # нет осмысленных корзин
            return 0

        # 2. Кандидаты на напоминание
        carts = (
            db.query(Cart)
            .join(User, User.id == Cart.user_id)
            .filter(
                Cart.total_amount > avg_amount,
                Cart.total_amount > 0,
                Cart.updated_at < cutoff_delay,
                Cart.bigcart_send_count < MAX_BIG_CART_REMINDERS,
                # или ещё не слали, или прошло достаточно времени
                func.coalesce(Cart.bigcart_last_sent_at, datetime(1970, 1, 1)) < cutoff_interval,
            )
            .order_by(Cart.updated_at.asc())
            .limit(BIG_CART_BATCH_LIMIT)
            .all()
        )

        sent_count = 0

        for cart in carts:
            user = cart.user
            if not user or not user.email:
                # не знаем куда слать — просто пропускаем
                continue

            ok = send_big_cart_reminder_email(user.email, cart.total_amount)

            # ❗ В отличие от прошлой таски — счётчик увеличиваем
            # ТОЛЬКО если отправка реально прошла.
            if ok:
                cart.bigcart_send_count += 1
                cart.bigcart_last_sent_at = now
                sent_count += 1

        db.commit()
        return sent_count

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()
