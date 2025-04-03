from pydantic import BaseModel
from typing import Optional, List, Dict, Any

from .author import AuthorResponse

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

class LandingListResponse(BaseModel):
    id: int
    landing_name: str
    page_name: str

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

    class Config:
        orm_mode = True

class LandingCreate(BaseModel):
    page_name: Optional[str] = ""
    language: Optional[str] = "EN"
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    # Входной формат для lessons_info – список объектов
    lessons_info: Optional[List[Dict[str, LessonInfoItem]]] = []
    preview_photo: Optional[str] = ""
    sales_count: Optional[int] = 0
    author_ids: Optional[List[int]] = []
    course_ids: Optional[List[int]] = []
    tag_ids: Optional[List[int]] = []
    duration: Optional[str] = ""
    lessons_count: Optional[str] = ""

    class Config:
        orm_mode = True

class LandingUpdate(BaseModel):
    page_name: Optional[str] = ""
    language: Optional[str] = "EN"
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    lessons_info: Optional[List[Dict[str, LessonInfoItem]]] = ""
    preview_photo: Optional[str] = ""
    sales_count: Optional[int] = ""
    author_ids: Optional[List[int]] = None
    course_ids: Optional[List[int]] = None
    tag_ids: Optional[List[int]] = None
    duration: Optional[str] = ""
    lessons_count: Optional[str] = ""

    class Config:
        orm_mode = True

class AuthorCardResponse(BaseModel):
    id: int
    name: str
    photo: Optional[str] = None  # добавили фото

    class Config:
        orm_mode = True

class LandingCardResponse(BaseModel):
    first_tag: Optional[str] = None
    landing_name: str
    authors: List[AuthorCardResponse]
    slug: str
    main_image: Optional[str] = None
    old_price: Optional[str] = None    # старая цена
    new_price: Optional[str] = None    # новая цена

    class Config:
        orm_mode = True