from pydantic import BaseModel
from typing import Optional, List, Dict

# Схема для элемента урока
class Lesson(BaseModel):
    video_link: str = ""
    lesson_name: str = ""

# Схема для секции: объект с названием и списком уроков
class Section(BaseModel):
    section_name: str = ""
    lessons: Optional[List[Lesson]] = []

# Схема для детального отображения курса (GET ответ)
class CourseDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    # Теперь sections возвращается как список объектов, например: [{ "1": { ... } }, { "2": { ... } }]
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
