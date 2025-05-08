from pydantic import BaseModel
from typing import Optional, List


class AuthorSimpleResponse(BaseModel):
    id: int
    name: str
    language: str

    class Config:
        orm_mode = True

class AuthorSimpleResponseWithPhoto(BaseModel):
    id: int
    name: str
    photo: str = ""

    class Config:
        orm_mode = True

class AuthorResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    photo: Optional[str] = ""
    language: Optional[str] = ""
    courses_count: int = 0

    class Config:
        orm_mode = True

class AuthorResponseForFullDetails(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    photo: Optional[str] = ""

    class Config:
        orm_mode = True

class AuthorResponsePage(BaseModel):
    id: int
    name: str
    photo: Optional[str] = ""
    description: Optional[str] = ""
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
    slug: str
    old_price: str
    new_price: str
    lessons_count: Optional[str]
    main_image: Optional[str]
    first_tag: Optional[str]
    course_ids: List[int]
    authors: List[AuthorSimpleResponseWithPhoto]

# Новая схема полного ответа
class AuthorFullDetailResponse(AuthorResponseForFullDetails):
    landings: List[LandingForAuthor]
    course_ids: List[int]
    total_new_price: float
    total_old_price: float
    landing_count: int
    lessons_count : Optional[str] = ""

class AuthorsPage(BaseModel):
    total: int           # общее число записей
    total_pages: int     # общее число страниц
    page: int            # текущая страница
    size: int            # размер страницы (число элементов на странице)
    items: List[AuthorResponse]