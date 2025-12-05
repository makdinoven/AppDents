from pydantic import BaseModel, Field
from typing import Optional, List

from ..schemas_v2.book import BookLandingCardResponse
from ..schemas_v2.common import CatalogFiltersMetadata


class AuthorSimpleResponse(BaseModel):
    id: int
    name: str
    language: str

    class Config:
        orm_mode = True

class BookSimpleResponse(BaseModel):
    id: int
    title: str
    slug: str | None = None
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
    course_ids: List[int] | None = None
    book_ids: List[int] | None = None
    books_count: int | None = None                    # ← НОВОЕ
    total_new_price: float            # только курсы (как было)
    total_books_price: float | None = None            # ← НОВОЕ
    total_courses_books_price: float | None = None    # ← НОВОЕ
    total_old_price: float
    total_books_old_price: float | None = None
    total_courses_books_old_price: float | None = None
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


# ═══════════════════ V2: Карточки авторов с фильтрами ═══════════════════

class AuthorCardV2Response(BaseModel):
    """
    Карточка автора для каталога с расширенными данными.
    """
    id: int
    name: str
    description: Optional[str] = ""
    photo: Optional[str] = ""
    language: Optional[str] = ""
    courses_count: int = Field(0, description="Количество уникальных курсов")
    books_count: int = Field(0, description="Количество книг с видимыми лендингами")
    tags: List[str] = Field(default_factory=list, description="Теги из курсов и книг автора")
    total_min_price: Optional[float] = Field(
        None, 
        description="Минимальная суммарная цена (мин. цена каждого курса + мин. цена каждой книги)"
    )
    popularity: int = Field(0, description="Популярность (сумма sales_count из Landing + BookLanding)")

    class Config:
        orm_mode = True


class AuthorsCardsV2Response(BaseModel):
    """
    Ответ с карточками авторов, пагинацией и метаданными фильтров.
    
    Аналогично BookLandingCardsV2Response для книг.
    """
    total: int = Field(..., description="Общее количество авторов после фильтрации")
    total_pages: int = Field(..., description="Общее количество страниц")
    page: int = Field(..., description="Текущая страница")
    size: int = Field(..., description="Размер страницы")
    cards: List[AuthorCardV2Response] = Field(default_factory=list, description="Карточки авторов")
    filters: Optional[CatalogFiltersMetadata] = Field(
        None, 
        description="Метаданные фильтров (если include_filters=true)"
    )

    class Config:
        schema_extra = {
            "example": {
                "total": 150,
                "total_pages": 8,
                "page": 1,
                "size": 20,
                "cards": [
                    {
                        "id": 1,
                        "name": "John Smith",
                        "description": "Expert in dental surgery",
                        "photo": "https://example.com/photo.jpg",
                        "language": "EN",
                        "courses_count": 5,
                        "books_count": 3,
                        "tags": ["Surgery", "Implantology"],
                        "total_min_price": 450.0,
                        "popularity": 1250
                    }
                ],
                "filters": None
            }
        }