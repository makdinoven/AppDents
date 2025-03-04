from pydantic import BaseModel
from typing import Optional

class AuthorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    photo: Optional[str] = None

    class Config:
        orm_mode = True

class AuthorSimpleResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
