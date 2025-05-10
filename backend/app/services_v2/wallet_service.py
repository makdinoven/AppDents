from typing import List

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import models_v2 as m
from ..services_v2.user_service import generate_unique_referral_code


# -------------------- helpers --------------------

def get_referral_link(db: Session, user: m.User) -> str:
    """Генерирует ссылку https://<APP_URL>/register?ref=<code>."""

    if not user.referral_code:
        user.referral_code = generate_unique_referral_code(db)
        db.commit()
        db.refresh(user)

    return f"{settings.APP_URL}/sign-up?ref={user.referral_code}"


def get_wallet_balance(user: m.User) -> float:
    return user.balance


def get_wallet_transactions(db: Session, user_id: int) -> List[m.WalletTransaction]:
    return (
        db.query(m.WalletTransaction)
        .filter(m.WalletTransaction.user_id == user_id)
        .order_by(m.WalletTransaction.created_at.desc())
        .all()
    )


def get_referral_report(db: Session, inviter_id: int):
    """Возвращает список (User, total_paid, total_cashback)."""

    # Все приглашённые пользователи
    invitees: List[m.User] = db.query(m.User).filter(m.User.invited_by_id == inviter_id).all()

    report = []
    for u in invitees:
        total_paid = (
            db.query(func.coalesce(func.sum(m.Purchase.amount), 0.0))
            .filter(m.Purchase.user_id == u.id)
            .scalar()
            or 0.0
        )

        total_cashback = (
            db.query(func.coalesce(func.sum(m.WalletTransaction.amount), 0.0))
            .filter(
                m.WalletTransaction.user_id == inviter_id,
                m.WalletTransaction.type == m.WalletTxTypes.REFERRAL_CASHBACK,
                m.WalletTransaction.meta['from_user'].astext.cast("int") == u.id,
            )
            .scalar()
            or 0.0
        )

        report.append((u, total_paid, total_cashback))

    return report
