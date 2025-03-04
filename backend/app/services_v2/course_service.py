from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.models_v2 import Course
from ..schemas_v2.course import CourseUpdate, CourseCreate
from typing import List

def list_courses(db: Session, skip: int = 0, limit: int = 10) -> List[Course]:
    return db.query(Course).offset(skip).limit(limit).all()

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