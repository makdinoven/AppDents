from html import escape
from ..utils.email_sender.common import send_html_email  # ✅ используем ваш существующий механизм
from ..utils.hss_cleaner import sanitize_and_linkify
from ..db.database import SessionLocal
from ..models.models_v2 import User
from fastapi import HTTPException, status

INFO_EMAIL = os.getenv("INFO_EMAIL", "info.dis.org@gmail.com")


def get_user_email_from_db(user_id: int):
    """Возвращает email пользователя по ID"""
    db = SessionLocal()
    try:
        user = db.query(User).filter(User.id == user_id).first()
        return user.email if user else None
    finally:
        db.close()


def send_course_request_email(user_id: int, text: str):
    """Формирует и отправляет письмо-заявку.
    При ошибке отправки бросает HTTPException(502) для корректного ответа API.
    """
    safe_html = sanitize_and_linkify(text)
    user_email = get_user_email_from_db(user_id)
    user_email_display = user_email or f"user_id:{user_id}"

    subject = f"Заявка на курс от {user_email_display}"
    body = f"""
    <html><body style="font-family:Arial,sans-serif;">
      <h3>Новая заявка на курс</h3>
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

    try:
        ok = send_html_email(INFO_EMAIL, subject, body)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось отправить email (внутренняя ошибка почтового сервера).",
        ) from e

    if not ok:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Не удалось отправить email (почтовый сервер вернул отказ).",
        )

    return INFO_EMAIL, user_email
