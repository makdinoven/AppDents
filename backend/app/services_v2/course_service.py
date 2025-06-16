import re
from math import ceil
from urllib.parse import urlparse, urlunparse

from sqlalchemy.orm import Session
from sqlalchemy import func
from fastapi import HTTPException
from ..models.models_v2 import Course
from ..schemas_v2.course import CourseUpdate, CourseCreate

_UUID = re.compile(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", re.I)

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
    if update_data.sections:
        # Преобразуем список словарей в один словарь
        new_sections = {}
        for section_item in update_data.sections:
            for key, value in section_item.items():
                new_sections[key] = value.dict()
        course.sections = new_sections
    else:
        course.sections = {}
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


def convert_storage_url(url: str) -> str:
    """Меняет хост *selstorage* или *s3.twcstorage* на cdn.dent-s.com
    и, если надо, выбрасывает первый сегмент-UUID."""
    if not url:
        return url

    p = urlparse(url)
    host, path = p.netloc, p.path.lstrip("/")

    if host.endswith(".selstorage.ru"):
        # Просто меняем хост, путь оставляем полностью
        new_path = path

    elif host == "s3.twcstorage.ru":
        # Если первый сегмент похож на UUID — убираем его
        head, *tail = path.split("/", 1)
        new_path = tail[0] if _UUID.fullmatch(head) and tail else path

    else:                       # остальные домены не трогаем
        return url

    # Собираем новый url
    new_parts = p._replace(netloc="cdn.dent-s.com", path="/" + new_path)
    return urlunparse(new_parts)