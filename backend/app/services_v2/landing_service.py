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
        tag_id = landing_data.tag_id,
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
    if update_data.page_name is not None:
        landing.page_name = update_data.page_name
    if update_data.landing_name is not None:
        landing.landing_name = update_data.landing_name
    if update_data.old_price is not None:
        landing.old_price = update_data.old_price
    if update_data.new_price is not None:
        landing.new_price = update_data.new_price
    if update_data.course_program is not None:
        landing.course_program = update_data.course_program
    if update_data.lessons_info is not None:
        landing.lessons_info = [
            {k: v.dict() if hasattr(v, "dict") else v for k, v in lesson_item.items()}
            for lesson_item in update_data.lessons_info
        ]
    if update_data.preview_photo is not None:
        landing.preview_photo = update_data.preview_photo
    if update_data.tag_id is not None:
        tag = db.query(Tag).filter(Tag.id == update_data.tag_id).first()
        if not tag:
            raise HTTPException(status_code=400, detail="Tag not found")
        landing.tag_id = update_data.tag_id
    if update_data.sales_count is not None:
        landing.sales_count = update_data.sales_count
    if update_data.language is not None:
        landing.language = update_data.language
    if update_data.author_ids is not None:
        authors = db.query(Author).filter(Author.id.in_(update_data.author_ids)).all()
        landing.authors = authors
    if update_data.course_ids is not None:
        courses = db.query(Course).filter(Course.id.in_(update_data.course_ids)).all()
        landing.courses = courses
    if update_data.tag_ids is not None:
        tags = db.query(Tag).filter(Tag.id.in_(update_data.tag_ids)).all()
        landing.tags = tags
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