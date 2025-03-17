from pydantic import BaseModel
from typing import Optional

class AuthorSimpleResponse(BaseModel):
    id: int
    name: str
    language: str

    class Config:
        orm_mode = True

class AuthorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    photo: Optional[str] = ""
    language: Optional[str] = ""

    class Config:
        orm_mode = True

class AuthorCreate(BaseModel):
    name: str
    description: Optional[str] = ""
    photo: Optional[str] = ""
    language: Optional[str] = "EN"

class AuthorUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    photo: Optional[str] = None
    language: Optional[str] = None