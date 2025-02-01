# schemas/landings.py
from pydantic import BaseModel
from typing import List, Optional
from decimal import Decimal
from enum import Enum
class LanguageEnum(str, Enum):
    EN = "en"
    ES = "es"
    RU = "ru"

# Схема для создания модуля (урока)
class ModuleCreate(BaseModel):
    title: str
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

# Схема для создания лендинга (используется в POST-запросе)
class LandingCreate(BaseModel):
    title: str
    old_price: Optional[Decimal] = None
    price: Decimal
    main_image: Optional[str] = None
    main_text: Optional[str] = None         # Программа курса
    language: LanguageEnum
    tag: Optional[str] = None
    course_id: int                          # Привязка лендинга к курсу
    modules: Optional[List[ModuleCreate]] = []  # Список модулей (уроков)
    authors: Optional[List[int]] = []           # Список id лекторов (авторов)

# Схема для обновления лендинга (все поля опциональные)
class LandingUpdate(BaseModel):
    title: Optional[str] = None
    old_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    main_image: Optional[str] = None
    main_text: Optional[str] = None
    language: Optional[LanguageEnum] = None
    tag: Optional[str] = None
    course_id: Optional[int] = None
    modules: Optional[List[ModuleCreate]] = None
    authors: Optional[List[int]] = None

# Схема для ответа по автору (лектору)
class AuthorResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# Схема для карточки лендинга (краткое представление)
class LandingCardResponse(BaseModel):
    id: int
    tag: Optional[str] = None
    title: str
    main_image: Optional[str] = None
    authors: List[AuthorResponse] = []

    class Config:
        orm_mode = True

# Схема для ответа по модулю (уроку)
class ModuleResponse(BaseModel):
    id: int
    title: str
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

    class Config:
        orm_mode = True

# Схема для ответа по курсу (минимальное представление)
class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None

    class Config:
        orm_mode = True

# Схема для полной информации о лендинге (используется в GET /landings/{landing_id})
class LandingDetailResponse(BaseModel):
    id: int
    language: LanguageEnum
    title: str
    tag: Optional[str] = None
    main_image: Optional[str] = None
    duration: Optional[str] = None
    old_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    main_text: Optional[str] = None
    course: CourseResponse
    authors: List[AuthorResponse] = []
    modules: List[ModuleResponse] = []

    class Config:
        orm_mode = True