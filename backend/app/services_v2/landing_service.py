from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List
from ..models.models_v2 import Landing, Author, Course, Tag
from ..schemas_v2.landing import LandingCreate, LandingUpdate

def list_landings(db: Session, skip: int = 0, limit: int = 10) -> List[Landing]:
    return db.query(Landing).offset(skip).limit(limit).all()

def get_landing_detail(db: Session, landing_id: int) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    return landing

def create_landing(db: Session, landing_data: LandingCreate) -> Landing:
    new_landing = Landing(
        page_name = landing_data.page_name,
        language = landing_data.language,
        landing_name = landing_data.landing_name,
        old_price = landing_data.old_price,
        new_price = landing_data.new_price,
        course_program = landing_data.course_program,
        lessons_info = landing_data.lessons_info,
        preview_photo = landing_data.preview_photo,
        sales_count = landing_data.sales_count
    )
    db.add(new_landing)
    db.commit()
    db.refresh(new_landing)
    # Привязка авторов через ассоциативную таблицу landing_authors
    if landing_data.author_ids:
        authors = db.query(Author).filter(Author.id.in_(landing_data.author_ids)).all()
        new_landing.authors = authors
    # Привязка курсов через ассоциативную таблицу landing_course
    if landing_data.course_ids:
        courses = db.query(Course).filter(Course.id.in_(landing_data.course_ids)).all()
        new_landing.courses = courses
    db.commit()
    db.refresh(new_landing)
    if landing_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(landing_data.tag_ids)).all()
        new_landing.tags = tags
    # Если landing_name не задано, обновляем его автоматически
    if not new_landing.landing_name:
        new_landing.landing_name = f"Landing name {new_landing.id}"
        db.commit()
        db.refresh(new_landing)
    return new_landing


def update_landing(db: Session, landing_id: int, update_data: LandingUpdate) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # Обновление простых (скалярных) полей
    for field in ["page_name", "landing_name", "old_price", "new_price",
                  "course_program", "preview_photo", "sales_count", "language"]:
        value = getattr(update_data, field)
        if value is not None:
            setattr(landing, field, value)

    # Обновление lessons_info (преобразуем объекты LessonInfoItem в словари)
    if update_data.lessons_info is not None:
        landing.lessons_info = [
            {k: v.dict() if hasattr(v, "dict") else v for k, v in lesson_item.items()}
            for lesson_item in update_data.lessons_info
        ]

    # Обновление ассоциаций через ассоциативные таблицы
    if update_data.author_ids is not None:
        landing.authors = db.query(Author).filter(Author.id.in_(update_data.author_ids)).all()
    if update_data.course_ids is not None:
        landing.courses = db.query(Course).filter(Course.id.in_(update_data.course_ids)).all()
    if update_data.tag_ids is not None:
        landing.tags = db.query(Tag).filter(Tag.id.in_(update_data.tag_ids)).all()

    db.commit()
    db.refresh(landing)
    return landing


def delete_landing(db: Session, landing_id: int) -> None:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    # Очистка связей с курсами (через landing_course) и с авторами (через landing_authors)
    landing.courses = []
    landing.authors = []
    landing.tags = []
    db.delete(landing)
    db.commit()