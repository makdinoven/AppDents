# app/tasks/referral_campaign.py

from datetime import datetime

from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy import exists

from ..db.database import SessionLocal
from ..core.config import settings
from ..utils import email_sender
from ..models.models_v2 import User, Invitation, ReferralCampaignEmail
from ..utils.user_language import get_user_preferred_language

# лимит за один прогон (~26 писем/час для 80 писем/час суммарно)
MAX_HOURLY_REFERRAL_EMAILS = 26


def _get_session() -> Session:
    return SessionLocal()


@shared_task(name="app.tasks.referral_campaign.send_referral_campaign_batch")
def send_referral_campaign_batch(max_per_run: int | None = None) -> str:
    """
    Рассылка писем про реферальную программу.

    Логика:
    - берём максимум `max_per_run` (или MAX_HOURLY_REFERRAL_EMAILS) пользователей;
    - у пользователя:
        * есть email,
        * ещё НЕ отправляли это письмо (нет ReferralCampaignEmail),
        * нет зарегистрированных рефералов (invited_users пустой),
        * нет отправленных инвайтов (Invitation.sender_id = user.id);
    - шлём письмо, пишем запись в ReferralCampaignEmail.
    """
    limit = max_per_run or MAX_HOURLY_REFERRAL_EMAILS
    db = _get_session()

    try:
        # выбираем всех, кому можно слать
        # нормальный вариант через ORM: invited_users.any() и подзапросы exists
        users_q = (
            db.query(User)
            .filter(
                User.email.isnot(None),
                User.email != "",
                # ещё не слали эту кампанию
                ~db.query(ReferralCampaignEmail.id)
                  .filter(ReferralCampaignEmail.user_id == User.id)
                  .exists(),
                # нет зарегистрированных рефералов
                ~User.invited_users.any(),
                # не отправлял инвайты по email
                ~db.query(Invitation.id)
                  .filter(Invitation.sender_id == User.id)
                  .exists(),
            )
            .order_by(User.id)
            .limit(limit)
        )

        users = users_q.all()
        if not users:
            return "No eligible users for referral campaign"

        sent_count = 0

        for user in users:
            referral_code = user.referral_code or str(user.id)
            referral_link = f"{settings.APP_URL}/ref/{referral_code}"

            status = "error"
            error_message: str | None = None
            sent_at = None

            try:
                # Определяем предпочитаемый язык пользователя
                user_language = get_user_preferred_language(user, db)
                ok = email_sender.send_referral_program_email(
                    recipient_email=user.email,
                    referral_link=referral_link,
                    region=user_language,
                    bonus_percent=50,
                )
                if ok:
                    status = "sent"
                    sent_at = datetime.utcnow()
                    sent_count += 1
                else:
                    status = "error"
                    error_message = "send_html_email returned False"
            except Exception as exc:
                status = "error"
                error_message = str(exc)

            db.add(
                ReferralCampaignEmail(
                    user_id=user.id,
                    email=user.email,
                    status=status,
                    error_message=error_message,
                    sent_at=sent_at,
                )
            )

        db.commit()
        return f"Sent referral campaign emails: {sent_count}"

    finally:
        db.close()
