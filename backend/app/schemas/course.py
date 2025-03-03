# schemas/course.py
from pydantic import BaseModel
from typing import List, Optional
from ..schemas.landing import ModuleResponse  # Переиспользуем схему ответа для модуля из landing.py

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

