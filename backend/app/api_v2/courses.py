from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..dependencies.access_course import get_course_detail_with_access
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Course, User
from ..services_v2.course_service import list_courses, get_course_detail, update_course
from ..schemas_v2.course import CourseListResponse, CourseDetailResponse, CourseUpdate

router = APIRouter(prefix="/courses", tags=["courses"])

@router.get("/", response_model=List[CourseListResponse])
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

@router.get("/{course_id}", response_model=CourseDetailResponse)
def get_course_by_id(course_id: int, db: Session = Depends(get_db), Course : Course = Depends(get_course_detail_with_access)):
    """
    Возвращает детальную информацию о курсе.
    Формат ответа:
    {
      "id": 30,
      "name": "Advanced Surgical Guides - All on X",
      "description": "Add Description",
      "lessons": {
         "1": {
           "section_name": "Module 1: Introduction",
           "lessons": [
              { "video_link": "https://play.boomstream.com/iKaAnlOc", "lesson_name": "Lesson 1: Implant Ninja introduces Digital Guru" },
              { "video_link": "https://play.boomstream.com/wi7ofFLA", "lesson_name": "Lesson 2: Welcome to the Course! Implant Ninja" },
              { "video_link": "new link", "lesson_name": "new lesson" },
              { "video_link": "https://play.boomstream.com/bKHzDTwg", "lesson_name": "Lesson 3: Superfast overview..." }
           ]
         },
         "2": { ... },
         ...
      }
    }
    """
    course = get_course_detail(db, course_id)
    return course

@router.put("/{course_id}", response_model=CourseDetailResponse)
def update_course_full(
    course_id: int,
    update_data: CourseUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """
    Обновляет курс полностью.
    PUT запрос должен содержать:
    {
      "name": "Advanced Surgical Guides - All on X",
      "description": "",
      "lessons": {
         "1": {
             "section_name": "Module 1: Introduction",
             "lessons": [
                { "video_link": "https://play.boomstream.com/iKaAnlOc", "lesson_name": "Lesson 1: Implant Ninja introduces Digital Guru" },
                { "video_link": "https://play.boomstream.com/wi7ofFLA", "lesson_name": "Lesson 2: Welcome to the Course! Implant Ninja" },
                { "video_link": "https://play.boomstream.com/bKHzDTwg", "lesson_name": "Lesson 3: Superfast overview..." }
             ]
         },
         "2": { ... },
         ...
      }
    }
    Все значения из PUT запроса записываются напрямую в поля модели:
      - name → name,
      - description → description,
      - lessons → lessons.
    """
    updated_course = update_course(db, course_id, update_data)
    return updated_course