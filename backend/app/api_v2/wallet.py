from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..dependencies.auth import get_current_user
from ..db.database import get_db
from ..models import models_v2 as m
from ..schemas_v2.wallet import (
    ReferralLinkResponse,
    WalletResponse,
    WalletTransactionItem,
    ReferralReportItem, AdminAdjustRequest,
)
from ..services_v2 import wallet_service as ws

router = APIRouter(tags=["wallet"])


@router.get("/referral-link", response_model=ReferralLinkResponse)
def my_referral_link(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    link = ws.get_referral_link(db, current_user)
    return ReferralLinkResponse(referral_link=link)


@router.get("/referrals", response_model=List[ReferralReportItem])
def my_referrals(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    # get_referral_report уже возвращает List[ReferralReportItem]
    return ws.get_referral_report(db, current_user.id)


@router.get("/wallet", response_model=WalletResponse)
def wallet_balance(current_user: m.User = Depends(get_current_user)):
    return WalletResponse(balance=ws.get_wallet_balance(current_user))


@router.get("/transactions", response_model=List[WalletTransactionItem])
def wallet_transactions(
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    txs = ws.get_wallet_transactions(db, current_user.id)
    return [
        WalletTransactionItem(
            id=tx.id,
            amount=tx.amount,
            type=tx.type.value,
            meta=tx.meta,
            created_at=tx.created_at,
        )
        for tx in txs
    ]

@router.post(
    "/admin/adjust",
    response_model=WalletResponse,
    summary="Админская корректировка баланса"
)
def admin_adjust_balance(
    req: AdminAdjustRequest,
    db: Session = Depends(get_db),
    current_user: m.User = Depends(get_current_user),
):
    # простая проверка на роль; подставьте ту логику, что есть у вас
    if current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Нет прав")

    try:
        ws.admin_adjust_balance(db, req.user_id, req.amount, req.meta)
    except ValueError as e:
        # не хватает средств или пользователь не найден
        raise HTTPException(status_code=400, detail=str(e))

    # возвращаем актуальный баланс пользователя
    user = db.query(m.User).get(req.user_id)
    return WalletResponse(balance=user.balance)
