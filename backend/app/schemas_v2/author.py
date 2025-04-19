from pydantic import BaseModel
from typing import Optional, List


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

class AuthorResponsePage(BaseModel):
    id: int
    name: str
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

class LandingForAuthor(BaseModel):
    id: int
    landing_name: str
    page_name: str
    old_price: str
    new_price: str
    main_image: Optional[str]
    first_tag: Optional[str]
    course_ids: List[int]

# Новая схема полного ответа
class AuthorFullDetailResponse(AuthorResponse):
    landings: List[LandingForAuthor]
    course_ids: List[int]
    total_new_price: float
    landing_count: int