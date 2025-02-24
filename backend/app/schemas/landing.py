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
    tag_id: Optional[int] = None            # Заменили: вместо tag (строка) передаём id тега
    course_id: int                          # Привязка лендинга к курсу
    modules: Optional[List[ModuleCreate]] = []  # Список модулей (уроков)
    authors: Optional[List[int]] = []           # Список id лекторов (авторов)
    sales_count: Optional[int] = 0          # Новое поле для ввода числа продаж (по умолчанию 0)

# Схема для обновления лендинга (все поля опциональные)
class LandingUpdate(BaseModel):
    title: Optional[str] = None
    old_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    main_image: Optional[str] = None
    main_text: Optional[str] = None
    language: Optional[LanguageEnum] = None
    tag_id: Optional[int] = None            # Заменили: вместо tag (строка) передаём id тега
    course_id: Optional[int] = None
    modules: Optional[List[ModuleCreate]] = None
    authors: Optional[List[int]] = None
    sales_count: Optional[int] = None       # Новое поле для обновления числа продаж вручную

# Схема для ответа по автору (лектору)
class AuthorResponse(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

# Схема для карточки лендинга (краткое представление)
class LandingCardResponse(BaseModel):
    id: int
    tag: Optional[str] = None               # Если нужно отдавать только имя тега
    title: str
    main_image: Optional[str] = None
    authors: List[AuthorResponse] = []
    sales_count: int                      # Добавили число продаж в ответ (можно указать как Optional, если требуется)

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
    tag: Optional[str] = None               # Отдавать имя тега, можно сформировать через relationship в модели
    main_image: Optional[str] = None
    duration: Optional[str] = None
    old_price: Optional[Decimal] = None
    price: Optional[Decimal] = None
    main_text: Optional[str] = None
    sales_count: int                      # Новое поле для числа продаж
    course: CourseResponse
    authors: List[AuthorResponse] = []
    modules: List[ModuleResponse] = []

    class Config:
        orm_mode = True

# Схемы для тегов
class TagBase(BaseModel):
    name: str

class TagCreate(TagBase):
    pass

class TagResponse(TagBase):
    id: int

    class Config:
        orm_mode = True

class LandingMinimalResponse(BaseModel):
    id: int
    title: str

    class Config:
        orm_mode = True