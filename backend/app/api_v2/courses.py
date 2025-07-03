import copy
import inspect
import json
from decimal import Decimal, ROUND_HALF_UP

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
    CourseListPageResponse, CourseDetailResponsePutRequest, LandingOfferInfo
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
def get_course_by_id(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):

    course = get_course_detail(db, course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    # — 1. Определяем уровни доступа —
    is_admin    = getattr(current_user, "role", None) == "admin"
    has_full    = is_admin or any(c.id == course_id for c in current_user.courses)
    # partial всегда важнее special_offer
    has_part    = (not is_admin) and course_id in getattr(current_user, "partial_course_ids", [])
    has_special = (not has_part) and course_id in getattr(current_user, "active_special_offer_ids", [])

    # — 2. Готовим секции (очищенная копия) и вставляем preview —
    sections_raw  = course.sections or {}
    sections_data = json.loads(json.dumps(sections_raw))
    sections = (
        [{k: v} for k, v in sections_data.items()]
        if isinstance(sections_data, dict)
        else sections_data
    )

    for sec in sections:
        _, data = next(iter(sec.items()))
        for lesson in data["lessons"]:
            lesson["preview"] = get_or_schedule_preview(db, lesson["video_link"])

    # — 3. Если у пользователя нет полного доступа, но есть partial или special —
    #      показываем только первый урок
    if not has_full and (has_part or has_special):
        unlocked = False
        for sec in sections:
            _, data = next(iter(sec.items()))
            for lesson in data["lessons"]:
                if unlocked:
                    lesson.pop("video_link", None)
                else:
                    unlocked = True

    # — 4. Самый дешевый лендинг для upsell (если нет full) —
    cheapest_landing = None
    if not has_full:
        landing = get_cheapest_landing_for_course(db, course_id)
        if landing:
            cheapest_landing = {"id": landing.id}

    landing_info: LandingOfferInfo | None = None
    if cheapest_landing:
        # берём тот же объект landing, который нашли выше
        old_price = Decimal(str(landing.old_price))
        original = Decimal(str(landing.new_price))
        discounted = (original * Decimal("0.85")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )
        if has_special:
            landing_info = LandingOfferInfo(
                id=landing.id,
                lessons_count=landing.lessons_count,
                slug=landing.page_name,
                landing_name=landing.landing_name,
                old_price=f"{old_price:.2f}",
                new_price=f"{discounted:.2f}",
                duration=landing.duration,
                region=landing.language,
            )
        else:
            landing_info = LandingOfferInfo(
                id=landing.id,
                lessons_count=landing.lessons_count,
                slug=landing.page_name,
                landing_name=landing.landing_name,
                old_price=f"{old_price:.2f}",
                new_price=f"{original:.2f}",
                duration=landing.duration,
                region=landing.language,
            )

    # — 5. Финальный уровень доступа —
    if has_full:
        access_level = "full"
    elif has_part:
        access_level = "partial"
    elif has_special:
        access_level = "special_offer"
    else:
        access_level = "none"

    result = {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "sections": sections,
        "access_level": access_level,
        "cheapest_landing": cheapest_landing,
        "landing": landing_info,
    }

    # GET-запрос — откатываем любые изменения в сессии
    db.rollback()
    return result



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
