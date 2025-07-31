import re
from math import ceil
from urllib.parse import urlparse, urlunparse

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from ..models.models_v2 import Course
from ..schemas_v2.course import CourseUpdate, CourseCreate



def list_courses_paginated(
    db: Session,
    *,
    page: int = 1,
    size: int = 10,
) -> dict:
    # 1) считаем общее число курсов
    total = db.query(func.count(Course.id)).scalar()
    # 2) вычисляем смещение
    offset = (page - 1) * size
    # 3) достаём нужную «страницу»
    courses = (
        db.query(Course)
          .order_by(Course.id.desc())
          .offset(offset)
          .limit(size)
          .all()
    )
    # 4) считаем число страниц
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": courses,
    }

def search_courses_paginated(
    db: Session,
    *,
    q: str,
    page: int = 1,
    size: int = 10,
) -> dict:
    # 1) базовый запрос с поиском по name (case-insensitive)
    base = db.query(Course).filter(Course.name.ilike(f"%{q}%"))
    # 2) общее число по этому фильтру
    total = base.count()
    # 3) пагинация
    offset = (page - 1) * size
    courses = base.offset(offset).limit(size).all()
    # 4) общее число страниц
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": courses,
    }

def get_course_detail(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

def update_course(db: Session, course_id: int, update_data: CourseUpdate) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    course.name = update_data.name
    course.description = update_data.description

    # Перенумеровываем по порядку прихода: 1,2,3,...
    new_sections: dict[str, dict] = {}
    for idx, item in enumerate(update_data.sections, start=1):
        if not isinstance(item, dict) or len(item) != 1:
            raise HTTPException(status_code=422, detail="Each section item must contain exactly one key")
        (_old_key, section_val) = next(iter(item.items()))
        # section_val — Pydantic Section
        new_sections[str(idx)] = section_val.dict()

    course.sections = new_sections

    db.commit()
    db.refresh(course)
    return course

def create_course(db: Session, course_data: CourseCreate) -> Course:
    # Создаем курс с переданными значениями или пустыми значениями, если не переданы
    new_course = Course(
        name = course_data.name if course_data.name else " ",
        description = course_data.description if course_data.description else " ",
        sections = course_data.sections if course_data.sections else {}
    )
    db.add(new_course)
    db.commit()
    db.refresh(new_course)
    # Если имя не было передано, обновляем его по шаблону "Course name {id}"
    if not new_course.name:
        new_course.name = f"Course name"
        db.commit()
        db.refresh(new_course)
    return new_course

def delete_course(db: Session, course_id: int) -> None:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    # Очистка связей с пользователями (ассоциативная таблица users_courses)
    course.users = []
    db.delete(course)
    db.commit()
