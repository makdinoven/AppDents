# schemas/course.py
from decimal import Decimal

from pydantic import BaseModel
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

class ModuleFullUpdate(BaseModel):
    id: Optional[int]  # Если передан, обновляем существующий модуль, иначе создаём новый
    title: str
    short_video_link: Optional[str] = None
    full_video_link: Optional[str] = None
    program_text: Optional[str] = None
    duration: Optional[str] = None

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "title": "Introduction to Python",
                "short_video_link": "https://example.com/short.mp4",
                "full_video_link": "https://example.com/full.mp4",
                "program_text": "This module covers the basics of Python.",
                "duration": "1h 30m"
            }
        }

class SectionFullUpdate(BaseModel):
    id: Optional[int]  # Если передан, обновляем существующую секцию, иначе создаём новую
    name: str
    modules: Optional[List[ModuleFullUpdate]] = []

    class Config:
        schema_extra = {
            "example": {
                "id": 1,
                "name": "Getting Started",
                "modules": [
                    {
                        "id": 1,
                        "title": "Introduction to Python",
                        "short_video_link": "https://example.com/short.mp4",
                        "full_video_link": "https://example.com/full.mp4",
                        "program_text": "This module covers the basics of Python.",
                        "duration": "1h 30m"
                    },
                    {
                        "title": "Variables and Data Types",
                        "short_video_link": "https://example.com/short2.mp4",
                        "full_video_link": "https://example.com/full2.mp4",
                        "program_text": "This module introduces variables and data types in Python.",
                        "duration": "1h"
                    }
                ]
            }
        }

class CourseFullUpdate(BaseModel):
    name: str
    description: Optional[str] = None
    sections: Optional[List[SectionFullUpdate]] = []

    class Config:
        schema_extra = {
            "example": {
                "name": "Python Programming 101",
                "description": "An introductory course to Python programming.",
                "sections": [
                    {
                        "id": 1,
                        "name": "Getting Started",
                        "modules": [
                            {
                                "id": 1,
                                "title": "Introduction to Python",
                                "short_video_link": "https://example.com/short.mp4",
                                "full_video_link": "https://example.com/full.mp4",
                                "program_text": "This module covers the basics of Python.",
                                "duration": "1h 30m"
                            },
                            {
                                "title": "Variables and Data Types",
                                "short_video_link": "https://example.com/short2.mp4",
                                "full_video_link": "https://example.com/full2.mp4",
                                "program_text": "This module introduces variables and data types in Python.",
                                "duration": "1h"
                            }
                        ]
                    },
                    {
                        "name": "Advanced Topics",
                        "modules": [
                            {
                                "title": "Object-Oriented Programming",
                                "short_video_link": "https://example.com/oop_short.mp4",
                                "full_video_link": "https://example.com/oop_full.mp4",
                                "program_text": "Deep dive into OOP concepts.",
                                "duration": "2h"
                            }
                        ]
                    }
                ]
            }
        }

class LandingFullData(BaseModel):
    title: str
    old_price: Optional[Decimal] = None
    price: Decimal
    main_image: Optional[str] = None
    main_text: Optional[str] = None
    language: LanguageEnum
    tag_id: Optional[int] = None
    authors: Optional[List[int]] = []  # список id авторов
    sales_count: Optional[int] = 0

    class Config:
        schema_extra = {
            "example": {
                "title": "Python Programming 101",
                "old_price": "100.00",
                "price": "79.99",
                "main_image": "https://example.com/course.jpg",
                "main_text": "Course description and landing page text",
                "language": "en",
                "tag_id": 2,
                "authors": [1, 3],
                "sales_count": 0
            }
        }

class CourseFullData(BaseModel):
    name: str
    description: Optional[str] = None
    landing: LandingFullData
    sections: Optional[List[SectionFullUpdate]] = []

    class Config:
        schema_extra = {
            "example": {
                "name": "Python Programming 101",
                "description": "An introductory course to Python programming.",
                "landing": {
                    "title": "Python Programming 101",
                    "old_price": "100.00",
                    "price": "79.99",
                    "main_image": "https://example.com/course.jpg",
                    "main_text": "Course description and landing page text",
                    "language": "en",
                    "tag_id": 2,
                    "authors": [1, 3],
                    "sales_count": 0
                },
                "sections": [
                    {
                        "id": 1,
                        "name": "Getting Started",
                        "modules": [
                            {
                                "id": 1,
                                "title": "Introduction to Python",
                                "short_video_link": "https://example.com/short.mp4",
                                "full_video_link": "https://example.com/full.mp4",
                                "program_text": "This module covers the basics of Python.",
                                "duration": "1h 30m"
                            },
                            {
                                "title": "Variables and Data Types",
                                "short_video_link": "https://example.com/short2.mp4",
                                "full_video_link": "https://example.com/full2.mp4",
                                "program_text": "This module introduces variables and data types in Python.",
                                "duration": "1h"
                            }
                        ]
                    },
                    {
                        "name": "Advanced Topics",
                        "modules": [
                            {
                                "title": "Object-Oriented Programming",
                                "short_video_link": "https://example.com/oop_short.mp4",
                                "full_video_link": "https://example.com/oop_full.mp4",
                                "program_text": "Deep dive into OOP concepts.",
                                "duration": "2h"
                            }
                        ]
                    }
                ]
            }
        }
