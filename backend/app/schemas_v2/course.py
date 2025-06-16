from pydantic import BaseModel, Field, validator
from typing import Optional, List, Dict, Literal

from ..services_v2.course_service import convert_storage_url


# Схема для элемента урока
class Lesson(BaseModel):
    video_link: str = ""
    lesson_name: str = ""
    preview: str | None = Field(
        None,
        description="URL JPEG-превью; присутствует всегда, даже при partial-доступе",
    )

    @validator("video_link", pre=True)
    def fix_link(cls, v):
        return convert_storage_url(v)

    class Config:
        orm_mode = True

# Схема для секции: объект с названием и списком уроков
class Section(BaseModel):
    section_name: str = ""
    lessons: Optional[List[Lesson]] = []

class LandingSnippet(BaseModel):
    id: int

# Схема для детального отображения курса (GET ответ)
class CourseDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    # Теперь sections возвращается как список объектов, например: [{ "1": { ... } }, { "2": { ... } }]
    sections: List[Dict[str, Section]]
    access_level: Literal["full", "partial"]
    cheapest_landing: LandingSnippet | None = None

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