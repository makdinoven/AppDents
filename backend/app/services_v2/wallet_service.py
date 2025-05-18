from typing import List

from sqlalchemy import func, or_, Integer, cast
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models import models_v2 as m
from ..models.models_v2 import Purchase, ReferralRule
from ..schemas_v2.wallet import ReferralReportItem
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


def get_referral_report(db, inviter_id: int) -> List[ReferralReportItem]:
    """
    Возвращает список приглашённых + суммы.
    Работает и в MySQL, и в PostgreSQL.
    """
    invited = db.query(m.User).filter(m.User.invited_by_id == inviter_id).all()
    report = []

    for u in invited:
        # 1) сколько потратил приглашённый
        total_paid = (
            db.query(func.coalesce(func.sum(m.Purchase.amount), 0.0))
              .filter(m.Purchase.user_id == u.id)
              .scalar() or 0.0
        )

        # 2) сколько кэшбэка получили с этого приглашённого
        # --- MySQL-совместимый фильтр JSON ---
        from_user_filter = cast(
            func.JSON_UNQUOTE(
                func.JSON_EXTRACT(m.WalletTransaction.meta, '$.from_user')
            ),
            Integer
        ) == u.id

        total_cashback = (
            db.query(func.coalesce(func.sum(m.WalletTransaction.amount), 0.0))
              .filter(
                  m.WalletTransaction.user_id == inviter_id,
                  m.WalletTransaction.type == m.WalletTxTypes.REFERRAL_CASHBACK,
                  from_user_filter
              )
              .scalar() or 0.0
        )

        report.append(
            ReferralReportItem(
                user_id=u.id,
                email=u.email,
                total_paid=total_paid,
                total_cashback=total_cashback
            )
        )

    return report

def get_cashback_percent(db: Session, invitee_id: int) -> float:
    """
    Находит порядковый номер покупки invitee_id (1,2,…),
    ищет в referral_rules подходящий диапазон и возвращает percent.
    """
    purchase_count = (
        db.query(func.count(Purchase.id))
          .filter(Purchase.user_id == invitee_id)
          .scalar()
        or 0
    )
    rule = (
        db.query(ReferralRule)
          .filter(
              ReferralRule.min_purchase_no <= purchase_count,
              or_(
                  ReferralRule.max_purchase_no == None,
                  ReferralRule.max_purchase_no >= purchase_count
              )
          )
          .order_by(ReferralRule.min_purchase_no.desc())
          .first()
    )
    return rule.percent if rule else 0.0