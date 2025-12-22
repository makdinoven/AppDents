from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class BanIPShort(BaseModel):
    id: int
    ip: str

    class Config:
        orm_mode = True


class BanEmailShort(BaseModel):
    id: int
    email: str

    class Config:
        orm_mode = True


class BanEmailOut(BaseModel):
    id: int
    email: str
    note: Optional[str] = None
    is_manual: bool
    created_by_admin_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    ips: List[BanIPShort] = []

    class Config:
        orm_mode = True


class BanIPOut(BaseModel):
    id: int
    ip: str
    note: Optional[str] = None
    is_manual: bool
    created_by_admin_id: Optional[int] = None
    created_at: datetime
    updated_at: datetime
    emails: List[BanEmailShort] = []

    class Config:
        orm_mode = True


class BanEmailCreate(BaseModel):
    email: str
    note: Optional[str] = None
    ips: List[str] = Field(default_factory=list, description="Optional: list of IPs to create/link")


class BanIPCreate(BaseModel):
    ip: str
    note: Optional[str] = None
    emails: List[str] = Field(default_factory=list, description="Optional: list of emails to create/link")


class BanEmailPatch(BaseModel):
    email: Optional[str] = None
    note: Optional[str] = None


class BanIPPatch(BaseModel):
    ip: Optional[str] = None
    note: Optional[str] = None


class BanLinkIn(BaseModel):
    email_id: int
    ip_id: int


class BanSummaryOut(BaseModel):
    emails: List[BanEmailOut]
    ips: List[BanIPOut]


