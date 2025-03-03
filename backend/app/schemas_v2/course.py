from pydantic import BaseModel
from typing import Optional, Dict, List

# Схема для элемента урока
class Lesson(BaseModel):
    video_link: str
    lesson_name: str

# Схема для секции: объект с названием и списком уроков
class Section(BaseModel):
    section_name: str
    lessons: List[Lesson]

# Схема для детального отображения курса (GET ответ)
class CourseDetailResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = ""
    # Поле lessons теперь соответствует секциям, хранящимся как словарь (ключ – номер секции, значение – Section)
    lessons: Dict[str, Section]

    class Config:
        orm_mode = True

# Схема для обновления курса (PUT запрос)
class CourseUpdate(BaseModel):
    name: str
    description: Optional[str] = ""
    lessons: Dict[str, Section]

    class Config:
        orm_mode = True

# Схема для листинга курсов (только id и name)
class CourseListResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True
