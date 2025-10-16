from typing import Optional

from pydantic import BaseModel


class AuthorCardResponse(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None  # добавили фото

    class Config:
        orm_mode = True

class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True