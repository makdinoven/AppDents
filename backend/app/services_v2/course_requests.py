from html import escape
from ..utils.email_sender.common import send_html_email  # ✅ используем ваш существующий механизм
from ..utils.hss_cleaner import sanitize_and_linkify
from ..utils.telegram_sender import send_telegram_message
from ..db.database import SessionLocal
from ..models.models_v2 import User
from fastapi import HTTPException, status
import os
import logging

logger = logging.getLogger(__name__)

INFO_EMAIL = os.getenv("INFO_EMAIL", "info.dis.org@gmail.com")


def get_user_email_from_db(user_id: int):
    """Возвращает email пользователя по ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.email if user else None
    finally:
        db.close()


async def send_course_request_email(user_id: int, text: str, domain: str = "unknown"):
    """Формирует и отправляет письмо-заявку и уведомление в Telegram.
    При ошибках отправки логирует их, но не блокирует выполнение запроса.
    """
    safe_html = sanitize_and_linkify(text)
    user_email = get_user_email_from_db(user_id)
    user_email_display = user_email or f"user_id:{user_id}"

    subject = f"Заявка на курс от {user_email_display} [{domain}]"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;">
      <h3>Новая заявка на курс</h3>
      <p><b>Сайт:</b> {escape(domain)}</p>
      <p><b>User:</b> {escape(user_email_display)}</p>
      <p><b>User ID:</b> {user_id}</p>
      <hr>
      <h4>Текст заявки:</h4>
      {safe_html}
      <hr>
      <p>---</p>
      <p>Письмо отправлено автоматически системой.</p>
    </body></html>
    """

    # Пытаемся отправить email, но не блокируем выполнение при ошибке
    email_sent = False
    try:
        ok = send_html_email(INFO_EMAIL, subject, body)
        if ok:
            email_sent = True
            logger.info(f"Email sent successfully to {INFO_EMAIL} for user {user_id}")
        else:
            logger.warning(f"Failed to send email to {INFO_EMAIL} for user {user_id}: почтовый сервер вернул отказ")
    except Exception as e:
        logger.error(f"Failed to send email to {INFO_EMAIL} for user {user_id}: {e}", exc_info=True)

    # Отправляем уведомление в Telegram
    telegram_text = f"""🆕 <b>Новая заявка на курс</b>

🌐 <b>Сайт:</b> {escape(domain)}
👤 <b>Пользователь:</b> {escape(user_email_display)}
🆔 <b>User ID:</b> {user_id}

📝 <b>Текст заявки:</b>
{escape(text[:500])}"""
    
    # Не блокируем выполнение при ошибке Telegram
    telegram_sent = await send_telegram_message(telegram_text)
    
    # Логируем итоговый статус
    if email_sent and telegram_sent:
        logger.info(f"Course request notification sent successfully via email and Telegram for user {user_id}")
    elif email_sent:
        logger.info(f"Course request notification sent via email only for user {user_id}")
    elif telegram_sent:
        logger.info(f"Course request notification sent via Telegram only for user {user_id}")
    else:
        logger.warning(f"Course request notification failed for both email and Telegram for user {user_id}")

    return INFO_EMAIL, user_email
