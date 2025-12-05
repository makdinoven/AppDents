# app/tasks/referral_campaign.py

from datetime import date

from celery import shared_task
from sqlalchemy import text

from app.db.session import SessionLocal
from app.core.config import settings
from app.services import email_sender

# Лимит отправок в день (в диапазоне 200–300 как ты просил)
MAX_DAILY_REFERRAL_EMAILS = 250


def _get_today_sent_count(db) -> int:
    """
    Сколько писем по реферальной кампании уже отправлено сегодня.
    Считаем только status='sent'.
    """
    today = date.today()
    q = text("""
        SELECT COUNT(*) AS cnt
        FROM referral_campaign_emails
        WHERE sent_at IS NOT NULL
          AND status = 'sent'
          AND DATE(sent_at) = :today
    """)
    return db.execute(q, {"today": today}).scalar_one() or 0


def _eligible_users_query(limit: int):
    """
    Юзеры, которым можно отправить письмо про реферальную программу.

    Условия:
    - есть email;
    - мы ЕЩЁ НЕ слали им это письмо (нет записи в referral_campaign_emails);
    - юзер ЕЩЁ НИКОГО не приглашал:
        а) ни одного зарегистрированного реферала (нет users.invited_by_id = u.id);
        б) ни одного отправленного инвайта по email (нет записи в invitations.sender_id = u.id).
    """
    return text("""
        SELECT
            u.id,
            u.email,
            u.referral_code
        FROM users AS u
        WHERE
            u.email IS NOT NULL
            AND u.email != ''

            -- 1) Письмо по этой кампании ещё не отправляли
            AND NOT EXISTS (
                SELECT 1
                FROM referral_campaign_emails rce
                WHERE rce.user_id = u.id
            )

            -- 2а) У юзера НЕТ зарегистрированных рефералов
            AND NOT EXISTS (
                SELECT 1
                FROM users AS u2
                WHERE u2.invited_by_id = u.id
            )

            -- 2б) И он ещё никому не отправлял инвайт на почту
            AND NOT EXISTS (
                SELECT 1
                FROM invitations AS i
                WHERE i.sender_id = u.id
            )

        ORDER BY u.id
        LIMIT :limit
    """)


def _mark_email(
    db,
    *,
    user_id: int,
    email: str,
    status: str,
    error_message: str = None,
) -> None:
    """
    Логируем результат отправки в referral_campaign_emails.

    ON DUPLICATE KEY UPDATE нужен на случай, если по юзеру уже есть запись,
    но мы хотим обновить статус/ошибку.
    """
    db.execute(
        text("""
            INSERT INTO referral_campaign_emails (user_id, email, status, error_message, sent_at, created_at)
            VALUES (
                :user_id,
                :email,
                :status,
                :error_message,
                CASE WHEN :status = 'sent' THEN NOW() ELSE NULL END,
                NOW()
            )
            ON DUPLICATE KEY UPDATE
                status        = VALUES(status),
                error_message = VALUES(error_message),
                sent_at       = VALUES(sent_at)
        """),
        {
            "user_id": user_id,
            "email": email,
            "status": status,
            "error_message": error_message,
        },
    )


@shared_task
def send_referral_campaign_batch():
    """
    Ежедневный батч рассылки по реферальной программе.

    Логика:
    1) Считаем, сколько уже отправлено сегодня (sent_today).
    2) Если лимит выбран — выходим.
    3) Берём из users пачку тех, кто:
       - ещё не получал это письмо;
       - ещё никого не приглашал (ни зарегистрированных рефералов, ни инвайтов).
    4) Шлём каждому письмо, логируем результат в referral_campaign_emails.
    """
    db = SessionLocal()
    try:
        sent_today = _get_today_sent_count(db)
        remaining = MAX_DAILY_REFERRAL_EMAILS - sent_today
        if remaining <= 0:
            return f"Daily limit reached: {sent_today}"

        rows = db.execute(
            _eligible_users_query(remaining),
            {"limit": remaining},
        ).mappings().all()

        if not rows:
            return "No eligible users for referral campaign"

        for row in rows:
            user_id = row["id"]
            email = row["email"]
            referral_code = row["referral_code"] or str(user_id)

            # динамическая реферальная ссылка;
            # домен берём из settings.APP_URL
            referral_link = f"{settings.APP_URL}/ref/{referral_code}"

            try:
                ok = email_sender.send_referral_program_email(
                    recipient_email=email,
                    referral_link=referral_link,
                    region="EN",      # при желании потом можно подтащить язык юзера
                    bonus_percent=50,
                )
                if ok:
                    _mark_email(
                        db,
                        user_id=user_id,
                        email=email,
                        status="sent",
                    )
                else:
                    _mark_email(
                        db,
                        user_id=user_id,
                        email=email,
                        status="error",
                        error_message="send_html_email returned False",
                    )
            except Exception as exc:
                _mark_email(
                    db,
                    user_id=user_id,
                    email=email,
                    status="error",
                    error_message=str(exc),
                )

        db.commit()
        return f"Sent referral campaign emails: {len(rows)}"

    finally:
        db.close()
