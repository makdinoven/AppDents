from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict
from enum import Enum as PyEnum

from ..utils.relink import convert_storage_url

class LandingOfferInfo(BaseModel):
    slug:         str
    landing_name: str
    old_price:    str
    new_price:    str   # ← цена со скидкой 15 %
    duration:     str | None
# Схема для элемента урока
class Lesson(BaseModel):
    video_link: str = ""
    lesson_name: str = ""
    preview: str | None = Field(
        None,
        description="URL JPEG-превью; присутствует всегда, даже при partial-доступе",
    )

    class Config:
        orm_mode = True

# Схема для секции: объект с названием и списком уроков
class Section(BaseModel):
    section_name: str = ""
    lessons: Optional[List[Lesson]] = []

class LandingSnippet(BaseModel):
    id: int

class CourseAccessLevel(str, PyEnum):
    FULL          = "full"           # куплен курс / админ
    SPECIAL_OFFER = "special_offer"  # спец-предложение (24 ч, первый урок открыт)
    PARTIAL       = "partial"        # бесплатный первый урок
    NONE          = "none"           # доступа нет
# Схема для детального отображения курса (GET ответ)
class CourseDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    # Теперь sections возвращается как список объектов, например: [{ "1": { ... } }, { "2": { ... } }]
    sections: List[Dict[str, Section]]
    access_level: CourseAccessLevel
    cheapest_landing: LandingSnippet | None = None
    landing: LandingOfferInfo | None

    class Config:
        orm_mode = True

class CourseDetailResponsePutRequest(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    sections: List[Dict[str, Section]]


    class Config:
        orm_mode = True

# Схема для обновления курса (PUT запрос)
class CourseUpdate(BaseModel):
    name: str
    description: Optional[str] = ""
    sections: List[Dict[str, Section]]

    class Config:
        orm_mode = True

# Схема для листинга курсов (только id и name)
class CourseListResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class CourseListResponseShort(BaseModel):
    id: int

    class Config:
        orm_mode = True

# Схема для создания курса (POST запрос)
class CourseCreate(BaseModel):
    name: Optional[str] = ""
    description: Optional[str] = ""
    sections: Optional[List[Dict[str, Section]]] = []

    class Config:
        orm_mode = True

class CourseListPageResponse(BaseModel):
    total: int                      # общее число курсов
    total_pages: int                # общее число страниц
    page: int                       # текущая страница
    size: int                       # размер страницы
    items: List[CourseListResponse]  # сами курсы на этой странице
