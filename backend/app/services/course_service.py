# services/courses.py
from sqlalchemy.orm import Session
from ..models.models import Course
from ..schemas.course import CourseCreate, CourseUpdate
from typing import List

def create_course(db: Session, course_data: CourseCreate) -> Course:
    course = Course(name=course_data.name, description=course_data.description)
    db.add(course)
    db.commit()
    db.refresh(course)
    return course

def update_course(db: Session, course_id: int, course_data: CourseUpdate) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    if course_data.name is not None:
        course.name = course_data.name
    if course_data.description is not None:
        course.description = course_data.description
    db.commit()
    db.refresh(course)
    return course

def delete_course(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    db.delete(course)
    db.commit()
    return course

def get_course(db: Session, course_id: int) -> Course:
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise ValueError("Курс не найден")
    return course

def list_courses(db: Session) -> List[Course]:
    courses = db.query(Course).all()
    return courses

def search_courses(db: Session, query: str) -> List[Course]:
    """
    Ищет курсы по части названия (регистронезависимый поиск).
    """
    courses = db.query(Course).filter(Course.name.ilike(f"%{query}%")).all()
    return courses