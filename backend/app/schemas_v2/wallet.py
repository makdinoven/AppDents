from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime


class ReferralLinkResponse(BaseModel):
    # Ссылка, которую можно скопировать и разослать
    referral_link: str


class ReferralReportItem(BaseModel):
    # Информация по каждому приглашённому
    user_id: int
    email: str
    total_paid: float         # сколько потратил приглашённый
    total_cashback: float     # сколько вы получили кэшбэка от него


class WalletResponse(BaseModel):
    balance: float            # текущий баланс пользователя


class WalletTransactionItem(BaseModel):
    id: int
    amount: float
    type: str
    meta: dict
    created_at: datetime


class ReferralRuleIn(BaseModel):
    min_purchase_no: int
    max_purchase_no: Optional[int]  # null = бесконечность
    percent: float


class ReferralRuleOut(ReferralRuleIn):
    id: int


class ReferralRulesResponse(BaseModel):
    rules: List[ReferralRuleOut]
