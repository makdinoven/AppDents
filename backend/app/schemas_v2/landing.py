from enum import Enum

from pydantic import BaseModel, validator
from typing import Optional, List, Dict, Any

from .author import AuthorResponse
from ..utils.relink import convert_storage_url


class LangEnum(str, Enum):
    EN = "EN"
    RU = "RU"
    ES = "ES"
    IT = "IT"
    AR = "AR"
    PT = "PT"


class TagResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class LessonInfoItem(BaseModel):
    link: Optional[str] = ""
    name: Optional[str] = ""
    program: Optional[str] = ""
    duration: Optional[str] = ""
    lecturer: Optional[str] = ""
    preview: Optional[str] = None

class LandingListResponse(BaseModel):
    id: int
    landing_name: str
    page_name: str
    is_hidden: bool = False

    class Config:
        orm_mode = True

class LandingDetailResponse(BaseModel):
    id: int
    language: str
    page_name: Optional[str] = ""
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    # lessons_info теперь возвращается как список объектов, где каждый объект имеет один ключ (например, "lesson1")
    lessons_info: Optional[List[Dict[str, LessonInfoItem]]] = []
    preview_photo: Optional[str] = ""
    sales_count: Optional[int] = 0
    author_ids: Optional[List[int]] = []
    course_ids: Optional[List[int]] = []
    tag_ids: Optional[List[int]] = []
    authors: Optional[List[AuthorResponse]] = []
    tags: Optional[List[TagResponse]] = []
    duration: Optional[str] = ""
    lessons_count: Optional[str] = ""
    is_hidden: bool = False

    class Config:
        orm_mode = True


class LandingCreate(BaseModel):
    page_name: Optional[str] = ""
    language: Optional[str] = "EN"
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    lessons_info: Optional[List[Dict[str, LessonInfoItem]]] = []
    preview_photo: Optional[str] = ""
    sales_count: Optional[int] = 0
    author_ids: Optional[List[int]] = []
    course_ids: Optional[List[int]] = []
    tag_ids: Optional[List[int]] = []
    duration: Optional[str] = ""
    lessons_count: Optional[str] = ""
    is_hidden: Optional[bool] = False

    class Config:
        orm_mode = True

class LandingUpdate(BaseModel):
    page_name: Optional[str] = ""
    language: Optional[str] = "EN"
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    lessons_info: Optional[List[Dict[str, LessonInfoItem]]] = []
    preview_photo: Optional[str] = ""
    sales_count: Optional[int] = ""
    author_ids: Optional[List[int]] = None
    course_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    duration: Optional[str] = ""
    lessons_count: Optional[str] = ""
    is_hidden: Optional[bool] = False

    class Config:
        orm_mode = True

class AuthorCardResponse(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None  # добавили фото

    class Config:
        orm_mode = True

class LandingCardResponse(BaseModel):
    id : int
    first_tag: Optional[str] = None
    landing_name: str
    authors: List[AuthorCardResponse]
    slug: str
    lessons_count: Optional[str] = ""
    main_image: Optional[str] = None
    old_price: Optional[str] = None    # старая цена
    new_price: Optional[str] = None    # новая цена
    course_ids: List[int] = []

    class Config:
        orm_mode = True

class LandingCardsResponse(BaseModel):
    total: int
    cards : List[LandingCardResponse]


class LandingCardsResponsePaginations(BaseModel):
    total: int            # общее число записей
    total_pages: int      # общее число страниц
    page: int             # текущая страница
    size: int             # размер страницы
    cards: List[LandingCardResponse]


class LandingItemResponse(BaseModel):
    id: int
    landing_name: str
    page_name: str
    old_price: str
    new_price: str
    preview_photo: Optional[str] = None  # Если это preview_photo из Landing или main_image из Course
    authors: List[AuthorResponse] = []

class LandingSearchResponse(BaseModel):
    total: int
    items: List[LandingItemResponse]

class LandingListPageResponse(BaseModel):
    total: int            # общее число записей
    total_pages: int      # общее число страниц
    page: int             # текущая страница
    size: int             # размер страницы
    items: List[LandingListResponse]

class FreeAccessRequest(BaseModel):
    email: str
    region: str = "EN"
    ref_code: str | None = None
    event_id: str | None = None  # тот же, что отправили в fbq('track', …, {eventID})
    fbp: str | None = None  # _fbp cookie
    fbc: str | None = None  # _fbc cookie
    event_source_url: str | None = None
    first_name: str | None = None

class TrackAdIn(BaseModel):
    fbp: Optional[str] = None
    fbc: Optional[str] = None