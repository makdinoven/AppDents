
from pydantic import BaseModel
from typing import Optional

class AuthorCreate(BaseModel):
    name: str
    description: Optional[str] = None
    photo: Optional[str] = None

class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    photo: Optional[str] = None

class AuthorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    photo: Optional[str] = None

    class Config:
        orm_mode = True
