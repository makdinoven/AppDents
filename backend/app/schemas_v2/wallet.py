from typing import Optional, List, Any
from pydantic import BaseModel, Field
from datetime import datetime


class ReferralLinkResponse(BaseModel):
    # Ссылка, которую можно скопировать и разослать
    referral_link: str


class ReferralReportItem(BaseModel):
    # Информация по каждому приглашённому
    email: str
    total_cashback: float     # сколько вы получили кэшбэка от него


class WalletResponse(BaseModel):
    balance: float            # текущий баланс пользователя

class AdminAdjustRequest(BaseModel):
    user_id: int
    amount: float
    meta: Optional[dict] = None

class WalletBookItem(BaseModel):
    id: int
    title: str
    slug: Optional[str] = None
    cover_url: Optional[str] = None


class WalletTransactionItem(BaseModel):
    id: int
    amount: float
    type: str
    meta: dict[str, Any] | None = Field(default_factory=dict)
    created_at: datetime
    slug: Optional[str] = None
    landing_name: Optional[str] = None
    email: Optional[str] = None
    book_landing_id: Optional[int] = None
    book_landing_slug: Optional[str] = None
    book_landing_name: Optional[str] = None
    books: List[WalletBookItem] = Field(default_factory=list)

class ReferralRuleIn(BaseModel):
    min_purchase_no: int
    max_purchase_no: Optional[int]  # null = бесконечность
    percent: float


class ReferralRuleOut(ReferralRuleIn):
    id: int


class ReferralRulesResponse(BaseModel):
    rules: List[ReferralRuleOut]
