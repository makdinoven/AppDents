from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..dependencies.access_course import get_course_detail_with_access
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Course, User
from ..services_v2.course_service import create_course
from ..services_v2.course_service import list_courses, get_course_detail, update_course
from ..schemas_v2.course import CourseListResponse, CourseDetailResponse, CourseUpdate, CourseCreate

router = APIRouter()

@router.get("/list", response_model=List[CourseListResponse])
def get_course_listing(
    skip: int = Query(0, ge=0),
    limit: int = Query(10, gt=0),
    db: Session = Depends(get_db)
):
    """
    Возвращает листинг курсов: id и name.
    """
    courses = list_courses(db, skip=skip, limit=limit)
    return courses

@router.get("/detail/{course_id}", response_model=CourseDetailResponse)
def get_course_by_id(course_id: int, db: Session = Depends(get_db), course : Course = Depends(get_course_detail_with_access)):
    course = get_course_detail(db, course_id)
    # Если sections хранится как словарь, преобразуем его в список
    sections = course.sections
    if isinstance(sections, dict):
        sections_list = [{k: v} for k, v in sections.items()]
    elif isinstance(sections, list):
        sections_list = sections
    else:
        sections_list = []
    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "sections": sections_list
    }

@router.put("/{course_id}", response_model=CourseDetailResponse)
def update_course_full(
    course_id: int,
    update_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    updated_course = update_course(db, course_id, update_data)
    sections = updated_course.sections
    if isinstance(sections, dict):
        sections_list = [{k: v} for k, v in sections.items()]
    elif isinstance(sections, list):
        sections_list = sections
    else:
        sections_list = []
    return {
        "id": updated_course.id,
        "name": updated_course.name,
        "description": updated_course.description,
        "sections": sections_list
    }


@router.post("/", response_model=CourseListResponse)
def create_new_course(
    course_data: CourseCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Создает новый курс.
    Тело запроса должно соответствовать структуре:
    {
      "name": "Advanced Surgical Guides - All on X",  // опционально
      "description": "Описание курса",                // опционально
      "lessons": {
          "1": {
              "section_name": "Module 1: Introduction",
              "lessons": [
                  { "video_link": "https://...", "lesson_name": "Lesson 1 ..." },
                  ...
              ]
          },
          "2": { ... }
      }
    }
    Если ни одно поле не передано, то по умолчанию:
      name = "Course name"
      description = ""
      lessons = {}
    В ответе возвращается id и name нового курса.
    """
    new_course = create_course(db, course_data)
    return new_course