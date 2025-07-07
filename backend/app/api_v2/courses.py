import copy
import inspect
import json
from decimal import Decimal, ROUND_HALF_UP

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import exists, select
from sqlalchemy.orm import Session, selectinload
from typing import List, Dict, Any
from ..db.database import get_db
from ..dependencies.access_course import get_course_detail_with_access
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Course, User, FreeCourseAccess, SpecialOffer, users_courses, LessonPreview
from ..services_v2.course_service import create_course, delete_course, search_courses_paginated, list_courses_paginated
from ..services_v2.course_service import get_course_detail, update_course
from ..schemas_v2.course import CourseListResponse, CourseDetailResponse, CourseUpdate, CourseCreate, \
    CourseListPageResponse, CourseDetailResponsePutRequest, LandingOfferInfo, CourseAccessLevel
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

def _attach_previews_and_trim(
    db: Session,
    sections: List[Dict[str, Any]],
    should_trim: bool,
) -> None:
    """
    • Для каждого урока вызывает get_or_schedule_preview – он сам решит,
      брать сохранённый кадр или запускать генерацию заново.
    • При should_trim=True оставляет video_link только у самого первого урока.
    """

    unlocked_shown = False  # нужно, чтобы показать ссылку ровно один раз
    for sec in sections:
        _, data = next(iter(sec.items()))
        for lesson in data["lessons"]:
            v_link = lesson.get("video_link")
            if not v_link:
                continue

            # всегда проверяем «живость» превью; если его нет – планируем генерацию
            lesson["preview"] = get_or_schedule_preview(db, v_link)

            # «обрезаем» доступ при partial / special-offer
            if should_trim:
                if unlocked_shown:
                    lesson.pop("video_link", None)
                else:
                    unlocked_shown = True

@router.get("/detail/{course_id}", response_model=CourseDetailResponse)
def get_course_by_id(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Обновлённая версия, устраняющая N+1‐проблемы и лишнюю (де)сериализацию.
    Семантика ответа полностью совпадает с прежней.
    """

    # ── 0. Подгружаем связанные коллекции одним запросом ────────────────────
    current_user = (
        db.query(User)
        .options(
            # сразу тащим только нужные поля, чтобы не плодить SELECT'ы
            selectinload(User.free_courses).load_only(
                FreeCourseAccess.course_id, FreeCourseAccess.converted_to_full
            ),
            selectinload(User.special_offers).load_only(
                SpecialOffer.course_id, SpecialOffer.expires_at
            ),
        )
        .get(current_user.id)
    )

    # ── 1. Курс ─────────────────────────────────────────────────────────────
    course: Course = get_course_detail(db, course_id)

    # ── 2. Уровни доступа ──────────────────────────────────────────────────
    is_admin = (current_user.role or "").lower() == "admin"

    has_full = is_admin or db.query(
        exists().where(
            users_courses.c.user_id == current_user.id,
            users_courses.c.course_id == course_id,
        )
    ).scalar()

    has_part = (
        (not is_admin)
        and (course_id in current_user.partial_course_ids)
    )
    has_special = (
        (not has_part)
        and (course_id in current_user.active_special_offer_ids)
    )

    # ── 3. Подготовка секций без json.dumps/loads ───────────────────────────
    sections_raw = course.sections or {}
    sections_data = copy.deepcopy(sections_raw)          # вместо двойной (де)сериализации
    sections: List[Dict[str, Any]] = (
        [{k: v} for k, v in sections_data.items()]
        if isinstance(sections_data, dict)
        else sections_data
    )

    # ── 4. Batch-превью + (опц.) скрытие ссылок ────────────────────────────
    should_trim = (not has_full) and (has_part or has_special)
    _attach_previews_and_trim(db, sections, should_trim)

    # ── 5. Cheapest landing (без изменений) ────────────────────────────────
    cheapest_landing = None
    if not has_full:
        landing = get_cheapest_landing_for_course(db, course_id)
        if landing:
            cheapest_landing = {"id": landing.id}

    landing_info: LandingOfferInfo | None = None
    if cheapest_landing:
        old_price = Decimal(str(landing.old_price))
        original_price = Decimal(str(landing.new_price))
        discounted = (original_price * Decimal("0.85")).quantize(
            Decimal("0.01"), rounding=ROUND_HALF_UP
        )

        landing_info = LandingOfferInfo(
            id=landing.id,
            lessons_count=landing.lessons_count,
            slug=landing.page_name,
            landing_name=landing.landing_name,
            old_price=f"{old_price:.2f}",
            new_price=f"{discounted if has_special else original_price:.2f}",
            duration=landing.duration,
            region=landing.language,
        )

    # ── 6. Финальный уровень доступа ───────────────────────────────────────
    if has_full:
        access_level: CourseAccessLevel = "full"
    elif has_part:
        access_level = "partial"
    elif has_special:
        access_level = "special_offer"
    else:
        access_level = "none"

    # ── 7. Ответ ───────────────────────────────────────────────────────────
    result: dict[str, Any] = {
        "id": course.id,
        "name": course.name,
        "description": course.description,
        "sections": sections,
        "access_level": access_level,
        "cheapest_landing": cheapest_landing,
        "landing": landing_info,
    }

    db.rollback()           # GET не должен мутировать сессию
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
