from pydantic import BaseModel
from typing import Optional, List

from AppDents.backend.app.schemas_v2.book import BookLandingCardResponse


class AuthorSimpleResponse(BaseModel):
    id: int
    name: str
    language: str

    class Config:
        orm_mode = True

class BookSimpleResponse(BaseModel):
    id: int
    title: str
    slug: str
    cover_url: str | None = ""

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
    books_count: int | None = None
    tags: List[str] = []

    class Config:
        orm_mode = True
        exclude_none = True

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

class AuthorFullDetailResponse(AuthorResponseForFullDetails):
    landings: List[LandingForAuthor]
    books: List[BookSimpleResponse] | None = None
    landing_ids: List[int] | None = None
    book_landing_ids: List[int] | None = None
    book_landings: List[BookLandingCardResponse] | None = None
    course_ids: List[int]
    books_count: int | None = None                    # ← НОВОЕ
    total_new_price: float            # только курсы (как было)
    total_books_price: float | None = None            # ← НОВОЕ
    total_courses_books_price: float | None = None    # ← НОВОЕ
    total_old_price: float
    total_books_old_price: float | None = None
    total_courses_old_price: float | None = None
    landing_count: int
    lessons_count: Optional[str] = ""
    tags: List[str]

    class Config:
        orm_mode = True
        exclude_none = True


class AuthorsPage(BaseModel):
    total: int           # общее число записей
    total_pages: int     # общее число страниц
    page: int            # текущая страница
    size: int            # размер страницы (число элементов на странице)
    items: List[AuthorResponse]