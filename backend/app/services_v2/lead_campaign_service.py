import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ..models.models_v2 import Lead, EmailCampaign, EmailCampaignRecipient, WalletTxTypes
from ..services_v2.user_service import credit_balance

logger = logging.getLogger(__name__)


def normalize_email(email: str) -> str:
    return (email or "").strip().lower()


def delete_lead_by_email(db: Session, email: str) -> int:
    """
    Удаляет lead по email. Возвращает кол-во удалённых строк.
    """
    n_email = normalize_email(email)
    if not n_email:
        return 0
    deleted = (
        db.query(Lead)
        .filter(Lead.email == n_email)
        .delete(synchronize_session=False)
    )
    if deleted:
        db.commit()
    return deleted


def grant_active_campaign_bonuses_for_user(db: Session, *, email: str, user_id: int) -> list[dict]:
    """
    Начисляет бонусы по активным кампаниам, если:
      - (campaign.is_active == True)
      - campaign.bonus_amount > 0
      - recipient.email == email
      - recipient.bonus_granted_at IS NULL

    Идемпотентность: ставим bonus_granted_at только если NULL (UPDATE ... WHERE NULL).
    """
    n_email = normalize_email(email)
    if not n_email:
        return []

    now = datetime.utcnow()
    granted: list[dict] = []

    rows = (
        db.query(EmailCampaignRecipient, EmailCampaign)
        .join(EmailCampaign, EmailCampaign.id == EmailCampaignRecipient.campaign_id)
        .filter(
            EmailCampaignRecipient.email == n_email,
            EmailCampaign.is_active == True,  # noqa: E712
            EmailCampaign.bonus_amount > 0,
            EmailCampaignRecipient.bonus_granted_at.is_(None),
        )
        .all()
    )

    for recipient, campaign in rows:
        # атомарно резервируем (если параллельно сработают два события)
        updated = (
            db.query(EmailCampaignRecipient)
            .filter(
                EmailCampaignRecipient.id == recipient.id,
                EmailCampaignRecipient.bonus_granted_at.is_(None),
            )
            .update({"bonus_granted_at": now}, synchronize_session=False)
        )
        if not updated:
            continue

        try:
            credit_balance(
                db=db,
                user_id=user_id,
                amount=float(campaign.bonus_amount),
                tx_type=WalletTxTypes.ADMIN_ADJUST,
                meta={"reason": "email_campaign_bonus", "campaign_code": campaign.code},
            )
            granted.append({"campaign_code": campaign.code, "amount": float(campaign.bonus_amount)})
            logger.info("Granted campaign bonus: %s → user_id=%s amount=%s", campaign.code, user_id, campaign.bonus_amount)
        except Exception as e:
            # credit_balance делает commit; если упали ДО commit, можно откатить отметку
            db.rollback()
            # best-effort: снимаем отметку, чтобы можно было повторить позже
            try:
                db.query(EmailCampaignRecipient).filter(EmailCampaignRecipient.id == recipient.id).update(
                    {"bonus_granted_at": None}, synchronize_session=False
                )
                db.commit()
            except Exception:
                db.rollback()
            logger.exception("Failed to grant campaign bonus for %s: %s", n_email, e)

    return granted


def consume_lead_and_maybe_grant_bonus(db: Session, *, email: str, user_id: int) -> dict:
    """
    Единая точка:
      - удалить lead по email
      - начислить бонусы по активным кампаниям (если есть recipient)
    """
    n_email = normalize_email(email)
    deleted = delete_lead_by_email(db, n_email)
    bonuses = grant_active_campaign_bonuses_for_user(db, email=n_email, user_id=user_id)
    return {"lead_deleted": bool(deleted), "bonuses": bonuses}


