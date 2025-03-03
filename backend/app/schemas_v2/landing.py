from pydantic import BaseModel
from typing import Optional, Dict, Any

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
    # lessons_info теперь имеет строго заданную структуру – словарь, где ключ – строка (например, "lesson1"), а значение – LessonInfoItem
    lessons_info: Optional[Dict[str, LessonInfoItem]]
    linked_courses: Optional[Dict[str, Any]]
    preview_photo: Optional[str] = ""
    tag_id: Optional[int] = None
    sales_count: Optional[int] = 0

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
    linked_courses: Optional[Dict[str, Any]] = {}
    preview_photo: Optional[str] = ""
    tag_id: Optional[int] = None
    sales_count: Optional[int] = 0

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
    linked_courses: Optional[Dict[str, Any]] = None
    preview_photo: Optional[str] = None
    tag_id: Optional[int] = None
    sales_count: Optional[int] = None

    class Config:
        orm_mode = True
