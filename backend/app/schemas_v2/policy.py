from typing import Optional
from datetime import datetime
from pydantic import BaseModel


class PolicyResponse(BaseModel):
    """Базовая схема для политик."""
    id: int
    language: str
    title: str
    content: str
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True


class TermsOfUseResponse(PolicyResponse):
    """Схема для условий использования."""
    pass


class PrivacyPolicyResponse(PolicyResponse):
    """Схема для политики конфиденциальности."""
    pass


class CookiePolicyResponse(PolicyResponse):
    """Схема для политики использования файлов cookie."""
    pass


class PolicyCreateRequest(BaseModel):
    """Схема для создания политики."""
    language: str
    title: str
    content: str


class PolicyUpdateRequest(BaseModel):
    """Схема для обновления политики."""
    title: Optional[str] = None
    content: Optional[str] = None
