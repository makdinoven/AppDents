# schemas/course.py
from decimal import Decimal

from pydantic import BaseModel, Field, validator
from typing import List, Optional
from ..schemas.landing import ModuleResponse, LanguageEnum  # Переиспользуем схему ответа для модуля из landing.py

# --- Модули ---
class ModuleCreate(BaseModel):
    title: str
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

class ModuleUpdate(BaseModel):
    title: Optional[str] = None
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

# --- Секции ---
class SectionCreate(BaseModel):
    name: str

class SectionUpdate(BaseModel):
    name: Optional[str] = None

class SectionResponse(BaseModel):
    id: int
    name: str
    modules: List[ModuleResponse] = []

    class Config:
        orm_mode = True

# --- Курсы ---
class CourseCreate(BaseModel):
    name: str
    description: Optional[str] = None

class CourseUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class CourseResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    sections: List[SectionResponse] = []

    class Config:
        orm_mode = True

class ModuleFullData(BaseModel):
    title: str
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

class SectionFullData(BaseModel):
    name: str
    modules: Optional[List[ModuleFullData]] = None

    @validator("modules", pre=True, always=True)
    def set_modules(cls, v):
        return v or []

class LandingFullData(BaseModel):
    title: str
    old_price: Optional[Decimal] = None
    price: Decimal
    main_image: Optional[str] = None
    main_text: Optional[str] = None
    language: LanguageEnum
    tag_id: Optional[int] = None
    authors: Optional[List[int]] = None  # список id авторов
    sales_count: Optional[int] = 0

    @validator("authors", pre=True, always=True)
    def set_authors(cls, v):
        return v or []

class CourseFullData(BaseModel):
    name: str
    description: Optional[str] = None
    landing: LandingFullData
    sections: Optional[List[SectionFullData]] = None

    @validator("sections", pre=True, always=True)
    def set_sections(cls, v):
        return v or []

# ========= Выходные схемы =========

class ModuleFullResponse(BaseModel):
    id: int
    title: str
    hort_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    uration: Optional[str] = None

    class Config:
        orm_mode = True

class SectionFullResponse(BaseModel):
    section_id: int
    section_title: str
    modules: List[ModuleFullResponse] = None

    @validator("modules", pre=True, always=True)
    def set_modules(cls, v):
        return v or []

    class Config:
        orm_mode = True

class LandingFullResponse(BaseModel):
    title: str
    old_price: Optional[Decimal] = None
    rice: Decimal
    main_image: Optional[str] = None
    main_text: Optional[str] = None
    language: LanguageEnum
    tag_id: Optional[int] = None
    authors: List[int] = None
    sales_count: int = 0

    @validator("landing_authors", pre=True, always=True)
    def set_authors(cls, v):
        return v or []

    class Config:
        orm_mode = True

class CourseFullResponse(BaseModel):
    name: str
    description: Optional[str] = None
    landing: LandingFullResponse
    sections: List[SectionFullResponse] = None

    @validator("sections", pre=True, always=True)
    def set_sections(cls, v):
        return v or []

    class Config:
        orm_mode = True