from sqlalchemy.orm import Session
from fastapi import HTTPException
from ..models.models_v2 import Course
from ..schemas_v2.course import CourseUpdate
from typing import List

def list_courses(db: Session, skip: int = 0, limit: int = 10) -> List[Course]:
    return db.query(Course).offset(skip).limit(limit).all()

def get_course_detail(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    return course

def update_course(db: Session, course_id: int, update_data: CourseUpdate) -> Course:
    """
    Обновляет курс: название, описание и lessons (секции).
    Значения из PUT запроса (name, description, lessons) записываются напрямую в поля модели.
    При этом lessons преобразуется из dict[str, Section] в dict[str, dict],
    чтобы объект Section стал нативным dict для JSON.
    """
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")
    course.name = update_data.name
    course.description = update_data.description
    # Преобразуем каждое значение секции через .dict()
    course.lessons = {k: v.dict() for k, v in update_data.lessons.items()} if update_data.lessons else {}
    db.commit()
    db.refresh(course)
    return course
