from pydantic import BaseModel
from typing import Optional, Dict, List, Any

class LessonInfoItem(BaseModel):
    link: Optional[str] = ""
    name: Optional[str] = ""
    program: Optional[str] = ""
    duration: Optional[str] = ""
    lecturer: Optional[str] = ""

class LandingListResponse(BaseModel):
    id: int
    landing_name: str

    class Config:
        orm_mode = True

class LandingDetailResponse(BaseModel):
    id: int
    page_name: Optional[str] = None
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    lessons_info: Optional[Dict[str, LessonInfoItem]] = {}
    preview_photo: Optional[str] = ""
    tag_id: Optional[int] = None
    sales_count: Optional[int] = 0
    author_ids: Optional[List[int]] = []
    course_ids: Optional[List[int]] = []

    class Config:
        orm_mode = True

# Схема для создания лендинга (POST)
class LandingCreate(BaseModel):
    page_name: Optional[str] = ""
    landing_name: Optional[str] = ""
    old_price: Optional[str] = ""
    new_price: Optional[str] = ""
    course_program: Optional[str] = ""
    lessons_info: Optional[Dict[str, LessonInfoItem]] = {}
    preview_photo: Optional[str] = ""
    tag_id: Optional[int] = None
    sales_count: Optional[int] = 0
    author_ids: Optional[List[int]] = []  # для привязки авторов
    course_ids: Optional[List[int]] = []  # для привязки курсов

    class Config:
        orm_mode = True

# Схема для обновления лендинга (PUT)
class LandingUpdate(BaseModel):
    page_name: Optional[str] = None
    landing_name: Optional[str] = None
    old_price: Optional[str] = None
    new_price: Optional[str] = None
    course_program: Optional[str] = None
    lessons_info: Optional[Dict[str, LessonInfoItem]] = None
    preview_photo: Optional[str] = None
    tag_id: Optional[int] = None
    sales_count: Optional[int] = None
    author_ids: Optional[List[int]] = None
    course_ids: Optional[List[int]] = None

    class Config:
        orm_mode = True
