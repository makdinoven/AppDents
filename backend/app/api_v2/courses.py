import copy

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..db.database import get_db
from ..dependencies.access_course import get_course_detail_with_access
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Course, User
from ..services_v2.course_service import create_course, delete_course, search_courses_paginated, list_courses_paginated
from ..services_v2.course_service import get_course_detail, update_course
from ..schemas_v2.course import CourseListResponse, CourseDetailResponse, CourseUpdate, CourseCreate, \
    CourseListPageResponse, CourseDetailResponsePutRequest
from ..services_v2.landing_service import get_cheapest_landing_for_course
from ..services_v2.preview_service import get_or_schedule_preview

router = APIRouter()

@router.get(
    "/list",
    response_model=CourseListPageResponse,
    summary="Список курсов (пагинация по стра ницам)"
)
def get_course_listing(
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    db: Session = Depends(get_db),
) -> dict:
    """
    Возвращает страницу курсов:
    {
      total: <общее количество курсов>,
      total_pages: <число страниц>,
      page: <текущая страница>,
      size: <размер страницы>,
      items: [ …CourseListResponse… ]
    }
    """
    return list_courses_paginated(db, page=page, size=size)

@router.get(
    "/list/search",
    response_model=CourseListPageResponse,
    summary="Поиск курсов с пагинацией"
)
def search_course_listing(
    q: str = Query(..., min_length=1, description="Строка для поиска в имени курса"),
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    db: Session = Depends(get_db),
) -> dict:
    """
    То же, что /list, но фильтрует по подстроке в имени курса.
    """
    return search_courses_paginated(db, q=q, page=page, size=size)

@router.get("/detail/{course_id}", response_model=CourseDetailResponse)
def get_course_by_id(                     # noqa: C901 – cyclomatic OK
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Подробности курса с учётом уровня доступа.

    Уровни:
        • full           – купил курс / админ
        • special_offer  – спец-предложение (24 ч, первый урок открыт)
        • partial        – бесплатный первый урок
        • none           – доступа нет
    """
    import copy
    import logging
    logger = logging.getLogger(__name__)

    course = get_course_detail(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    is_admin = getattr(current_user, "role", None) == "admin"

    # --------- определяем права ----------
    has_full = is_admin or any(c.id == course_id for c in current_user.courses)
    has_special = course_id in getattr(current_user, "active_special_offer_ids", [])
    has_part = (
        (not is_admin)
        and course_id in getattr(current_user, "partial_course_ids", [])
    )

    # --------- sections → list ----------
    raw_sections = course.sections or {}
    sections = (
        [{k: v} for k, v in raw_sections.items()]
        if isinstance(raw_sections, dict)
        else list(raw_sections)
    )

    # --------- вставляем превью ----------
    for sec in sections:
        key, data = next(iter(sec.items()))
        new_lessons = []
        for lesson in data["lessons"]:
            lesson_copy = copy.deepcopy(lesson)
            lesson_copy["preview"] = get_or_schedule_preview(  # миниатюра
                db, lesson_copy["video_link"]
            )
            new_lessons.append(lesson_copy)
        data["lessons"] = new_lessons
        sec[key] = data

    # --------- скрываем видео после первого ----------
    if has_part or has_special:
        unlocked = False
        for sec in sections:
            key, data = next(iter(sec.items()))
            for lesson in data["lessons"]:
                if unlocked:
                    lesson.pop("video_link", None)
                else:
                    unlocked = True

    # --------- лендинг с минимальной ценой ----------
    cheapest_landing = None
    if not has_full:
        landing = get_cheapest_landing_for_course(db, course_id)
        if landing:
            cheapest_landing = {"id": landing.id}

    # --------- итоговый уровень ----------
    if has_full:
        access_level = "full"
    elif has_special:
        access_level = "special_offer"
    elif has_part:
        access_level = "partial"
    else:
        access_level = "none"

    logger.debug(
        "User %s → course %s → %s access",
        current_user.id, course_id, access_level,
    )

    return {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "sections": sections,
        "access_level": access_level,
        "cheapest_landing": cheapest_landing,
    }



@router.put("/{course_id}", response_model=CourseDetailResponsePutRequest)
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

@router.delete("/{course_id}", response_model=dict)
def delete_course_route(course_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
    delete_course(db, course_id)
    return {"detail": "Course deleted successfully"}
