import copy
import hashlib
import json
import os
import uuid
import logging
from datetime import datetime, timedelta, time, date
from decimal import Decimal, ROUND_HALF_UP

import redis
from fastapi import APIRouter, Depends, Query, status, HTTPException, Request
from sqlalchemy import or_
from fastapi import APIRouter, Depends, Query, status, HTTPException, Request, Body
from pydantic import BaseModel
from sqlalchemy import or_, func, cast
from sqlalchemy.types import Numeric as SqlNumeric
from sqlalchemy.orm import Session, selectinload, joinedload
from typing import List, Optional, Dict, Literal, Union
from math import ceil
from ..db.database import get_db

# Redis для кэширования
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
_rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)
LANDING_CACHE_TTL = 180  # 2 минуты кэша
from ..dependencies.auth import get_current_user, get_current_user_optional
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Tag, Landing, Author, LandingVisit, Purchase, LandingAdPeriod, \
    BookLanding, BookLandingVisit, BookLandingAdPeriod
from ..schemas_v2.author import AuthorResponse

from ..services_v2.landing_service import get_landing_detail, create_landing, update_landing, \
    delete_landing, get_landing_cards, get_top_landings_by_sales, \
    get_purchases_by_language, get_landing_cards_pagination, list_landings_paginated, search_landings_paginated, \
    track_ad_visit, get_recommended_landing_cards, get_personalized_landing_cards, get_purchases_by_language_per_day, \
    open_ad_period_if_needed, AD_TTL, get_sales_totals
from ..services_v2.book_service import (
    get_top_book_landings_by_sales,
    get_book_sales_totals,
)
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate, TrackAdIn
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate, TagResponse, \
    LandingSearchResponse, LandingCardsResponse, LandingItemResponse, LandingCardsResponsePaginations, \
    LandingListPageResponse, LangEnum, FreeAccessRequest, LandingCardsV2Response, LandingCardResponse
from pydantic import BaseModel
from ..schemas_v2.common import TagResponse, CatalogFiltersMetadata
from ..services_v2.filter_aggregation_service import (
    build_landing_base_query,
    aggregate_landing_filters,
    parse_duration_to_minutes,
    calculate_landing_lessons_count,
)
from ..services_v2.preview_service import get_or_schedule_preview, get_previews_batch
from ..services_v2.user_service import add_partial_course_to_user, create_access_token, create_user, \
    generate_random_password, get_user_by_email
from ..utils.email_sender import send_password_to_user
from ..utils.facebook import send_registration_event

router = APIRouter()

@router.get(
    "/list",
    response_model=LandingListPageResponse,
    summary="Список лендингов (пагинация по страницам)"
)
def get_landing_listing(
    page: int = Query(1, ge=1, description="Номер страницы (≥1)"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    language: Optional[LangEnum] = Query(
        None,
        description="Фильтр по языку: EN, RU, ES, IT, AR, PT"
    ),
    db: Session = Depends(get_db),
):
    return list_landings_paginated(db, language=language, page=page, size=size)


@router.get(
    "/list/search",
    response_model=LandingListPageResponse,
    summary="Поиск лендингов по имени или slug с пагинацией"
)
def search_landing_listing(
    q: str = Query(..., min_length=1, description="Подстрока для поиска"),
    page: int = Query(1, ge=1),
    size: int = Query(10, gt=0),
    language: Optional[LangEnum] = Query(
        None,
        description="Фильтр по языку: EN, RU, ES, IT, AR, PT"
    ),
    db: Session = Depends(get_db),
):
    return search_landings_paginated(db, q=q, language=language, page=page, size=size)


@router.get("/detail/{landing_id}", response_model=LandingDetailResponse)
def get_landing_by_id(
    landing_id: int,
    db: Session = Depends(get_db)
):
    # 1) Забираем лендинг по id + нужные связи
    landing = (
        db.query(Landing)
          .options(
              selectinload(Landing.authors)
                .selectinload(Author.landings)
                  .selectinload(Landing.courses),
              selectinload(Landing.authors)
                .selectinload(Author.landings)
                  .selectinload(Landing.tags),
          )
          .filter(Landing.id == landing_id)    # <-- здесь id вместо page_name
          .first()
    )
    if not landing:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": {
                    "code": "LANDING_NOT_FOUND",
                    "message": "Landing not found",
                    "translation_key": "error.landing_not_found",
                    "params": {}
                }
            },
        )

    # 2) Приводим lessons_info к списку
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []

    # 3) Безопасное приведение цены
    def _safe_price(v) -> float:
        try:
            return float(v)
        except:
            return float("inf")

    # 4) Строим authors_list точно так же, как в get_landing_by_page
    authors_list = []
    for a in landing.authors:
        # 4.1) минимальная цена по каждому курсу
        min_price: Dict[int, float] = {}
        for l in a.landings:
            p = _safe_price(l.new_price)
            for c in l.courses:
                if p < min_price.get(c.id, float("inf")):
                    min_price[c.id] = p

        # 4.2) оставляем только «дешёвые» лендинги
        kept = [
            l for l in a.landings
            if not any(
                _safe_price(l.new_price) > min_price.get(c.id, _safe_price(l.new_price))
                for c in l.courses
            )
        ]

        # 4.3) собираем уникальные курсы и теги
        unique_courses = {c.id for l in kept for c in l.courses}
        unique_tags    = sorted({t.name for l in kept for t in l.tags})

        authors_list.append({
            "id": a.id,
            "name": a.name,
            "description": a.description or "",
            "photo": a.photo or "",
            "language": a.language,
            "courses_count": len(unique_courses),
            "tags": unique_tags,
        })

    # 5) Детали самого лендинга
    tags_list  = [{"id": t.id, "name": t.name} for t in landing.tags]
    course_ids = [c.id for c in landing.courses]
    author_ids = [a.id for a in landing.authors]
    tag_ids    = [t.id for t in landing.tags]

    return {
        "id": landing.id,
        "page_name": landing.page_name,
        "language": landing.language,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": lessons_list,
        "preview_photo": landing.preview_photo,
        "sales_count": landing.sales_count,
        "author_ids": author_ids,
        "course_ids": course_ids,
        "tag_ids": tag_ids,
        "authors": authors_list,   # <- теперь идентичен by-page
        "tags": tags_list,
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
        "is_hidden": landing.is_hidden,
    }

def _build_landing_response(
    db: Session,
    landing: Landing,
    lessons_out: List[dict],
    authors_list: List[dict],
) -> dict:
    """Формирует финальный ответ (вынесено для переиспользования)."""
    return {
        "id": landing.id,
        "page_name": landing.page_name,
        "language": landing.language,
        "landing_name": landing.landing_name,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_program": landing.course_program,
        "lessons_info": lessons_out,
        "preview_photo": landing.preview_photo,
        "sales_count": landing.sales_count,
        "author_ids": [a.id for a in landing.authors],
        "course_ids": [c.id for c in landing.courses],
        "tag_ids": [t.id for t in landing.tags],
        "authors": authors_list,
        "tags": [{"id": t.id, "name": t.name} for t in landing.tags],
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
        "is_hidden": landing.is_hidden,
    }


def _get_landing_cache_key(page_name: str) -> str:
    """Ключ кэша для лендинга."""
    return f"landing:detail:{hashlib.md5(page_name.encode()).hexdigest()}"


def _get_cached_landing(page_name: str) -> Optional[dict]:
    """Попробовать получить лендинг из кэша."""
    try:
        key = _get_landing_cache_key(page_name)
        data = _rds.get(key)
        if data:
            return json.loads(data)
    except Exception:
        pass
    return None


def _set_cached_landing(page_name: str, response: dict) -> None:
    """Сохранить лендинг в кэш."""
    try:
        key = _get_landing_cache_key(page_name)
        _rds.setex(key, LANDING_CACHE_TTL, json.dumps(response, default=str))
    except Exception:
        pass


@router.get(
    "/detail/by-page/{page_name}",
    response_model=LandingDetailResponse,
    summary="Детали лендинга по slug с превью уроков",
)
def get_landing_by_page(
    page_name: str,
    db: Session = Depends(get_db),
):
    """
    • Возвращает подробную информацию о лендинге **page_name**.
    • Для каждого урока в `lessons_info` добавляется поле **preview** –
      CDN-ссылка на кадр (или плейсхолдер, пока кадр не готов).
    • Если видео ещё не обрабатывалось – Celery-таска `generate_preview`
      ставится в очередь асинхронно; фронт сразу получает плейсхолдер.
    """
    log = logging.getLogger("landing-detail")
    
    # 0. Проверяем кэш
    cached = _get_cached_landing(page_name)
    if cached:
        return cached
    
    # 1. Берём лендинг с оптимизированными связями
    #    Загружаем только прямые связи лендинга (без вложенных лендингов авторов)
    landing: Landing | None = (
        db.query(Landing)
          .options(
              selectinload(Landing.authors),
              selectinload(Landing.courses),
              selectinload(Landing.tags),
          )
          .filter(Landing.page_name == page_name)
          .first()
    )
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # 2. Приводим lessons_info → list[dict]
    raw_lessons = landing.lessons_info or []
    lessons_list: List[dict] = (
        [{k: v} for k, v in raw_lessons.items()]
        if isinstance(raw_lessons, dict) else
        list(raw_lessons)
    )

    # 3. Собираем все video_link'и для батчевого запроса превью
    video_links: List[str] = []
    for item in lessons_list:
        if not item:
            continue
        key, lesson = next(iter(item.items()), (None, None))
        if lesson and isinstance(lesson, dict):
            video_link = lesson.get("link") or lesson.get("video_link")
            if video_link:
                video_links.append(video_link)
    
    # 4. Получаем все превью одним батч-запросом (без HTTP проверок)
    previews_map: Dict[str, str] = {}
    if video_links:
        try:
            previews_map = get_previews_batch(db, video_links)
        except Exception:
            log.exception("Failed batch preview fetch")

    # 5. Добавляем превью к каждому уроку
    lessons_out: List[dict] = []
    for item in lessons_list:
        if not item:
            continue
        key, lesson = next(iter(item.items()), (None, None))
        if lesson is None:
            continue
        lesson_copy = copy.deepcopy(lesson)

        video_link = lesson_copy.get("link") or lesson_copy.get("video_link")
        if video_link and video_link in previews_map:
            lesson_copy["preview"] = previews_map[video_link]

        lessons_out.append({key: lesson_copy})

    # 6. Собираем authors_list
    #    Оптимизация: для каждого автора делаем один агрегированный запрос
    #    вместо загрузки всех его лендингов
    authors_list: List[dict] = []
    
    if landing.authors:
        author_ids = [a.id for a in landing.authors]
        
        # Получаем агрегированные данные по авторам одним запросом
        author_stats = _get_author_stats_batch(db, author_ids)
        
        for a in landing.authors:
            stats = author_stats.get(a.id, {"courses_count": 0, "tags": []})
            authors_list.append({
                "id": a.id,
                "name": a.name,
                "description": a.description or "",
                "photo": a.photo or "",
                "language": a.language,
                "courses_count": stats["courses_count"],
                "tags": stats["tags"],
            })

    # 7. Формируем ответ
    response = _build_landing_response(db, landing, lessons_out, authors_list)
    
    # 8. Кэшируем результат
    _set_cached_landing(page_name, response)
    
    return response


def _get_author_stats_batch(db: Session, author_ids: List[int]) -> Dict[int, dict]:
    """
    Получить статистику по авторам (количество курсов и теги) оптимизированным запросом.
    
    Возвращает: {author_id: {"courses_count": N, "tags": [...]}}
    """
    if not author_ids:
        return {}
    
    from ..models.models_v2 import landing_authors, landing_course, landing_tags
    
    result: Dict[int, dict] = {aid: {"courses_count": 0, "tags": []} for aid in author_ids}
    
    # Запрос для подсчёта уникальных курсов на автора
    courses_query = (
        db.query(
            landing_authors.c.author_id,
            func.count(func.distinct(landing_course.c.course_id)).label("cnt")
        )
        .join(Landing, Landing.id == landing_authors.c.landing_id)
        .join(landing_course, landing_course.c.landing_id == Landing.id)
        .filter(
            landing_authors.c.author_id.in_(author_ids),
            Landing.is_hidden == False
        )
        .group_by(landing_authors.c.author_id)
    )
    
    for author_id, cnt in courses_query:
        result[author_id]["courses_count"] = cnt
    
    # Запрос для получения уникальных тегов на автора
    from ..models.models_v2 import Tag as TagModel
    tags_query = (
        db.query(
            landing_authors.c.author_id,
            TagModel.name
        )
        .join(Landing, Landing.id == landing_authors.c.landing_id)
        .join(landing_tags, landing_tags.c.landing_id == Landing.id)
        .join(TagModel, TagModel.id == landing_tags.c.tag_id)
        .filter(
            landing_authors.c.author_id.in_(author_ids),
            Landing.is_hidden == False
        )
        .distinct()
    )
    
    author_tags: Dict[int, set] = {aid: set() for aid in author_ids}
    for author_id, tag_name in tags_query:
        author_tags[author_id].add(tag_name)
    
    for author_id, tags in author_tags.items():
        result[author_id]["tags"] = sorted(tags)
    
    return result

@router.post("/", response_model=LandingListResponse)
def create_new_landing(
    landing_data: LandingCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    new_landing = create_landing(db, landing_data)
    return {
        "id": new_landing.id,
        "landing_name": new_landing.landing_name,
        "page_name": new_landing.page_name,
        "language": new_landing.language,
        "is_hidden": new_landing.is_hidden,
    }

@router.put("/{landing_id}", response_model=LandingDetailResponse)
def update_landing_full(
    landing_id: int,
    update_data: LandingUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    updated_landing = update_landing(db, landing_id, update_data)
    lessons = updated_landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    return {
        "id": updated_landing.id,
        "page_name": updated_landing.page_name,
        "language": updated_landing.language,
        "landing_name": updated_landing.landing_name,
        "old_price": updated_landing.old_price,
        "new_price": updated_landing.new_price,
        "course_program": updated_landing.course_program,
        "lessons_info": lessons_list,
        "preview_photo": updated_landing.preview_photo,
        "sales_count": updated_landing.sales_count,
        "author_ids": [author.id for author in updated_landing.authors] if updated_landing.authors else [],
        "course_ids": [course.id for course in updated_landing.courses] if updated_landing.courses else [],
        "tag_ids": [tag.id for tag in updated_landing.tags] if updated_landing.tags else [],
        "duration": updated_landing.duration,
        "lessons_count": updated_landing.lessons_count,
        "is_hidden": updated_landing.is_hidden,
    }

@router.get("/tags", response_model=List[TagResponse])
def get_all_tags(db: Session = Depends(get_db)):
    tags = db.query(Tag).all()
    return tags

@router.delete("/{landing_id}", response_model=dict)
def delete_landing_route(landing_id: int, db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    delete_landing(db, landing_id)
    return {"detail": "Landing deleted successfully"}

@router.get("/cards", response_model=LandingCardsResponse)
def get_cards(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, gt=0),
    tags: Optional[List[str]] = Query(None, description="Список тегов для фильтрации"),
    sort: Optional[str] = Query(None, description="Фильтр: popular, discount, new"),
    language: Optional[str] = Query(None, description="Язык лендинга: ES, EN, RU"),
    db: Session = Depends(get_db)
):
    """
    Получение карточек лендингов с пагинацией, фильтрацией по тегам и сортировкой.
    В ответе возвращаются общее количество лендингов по фильтрам и список карточек.
    """
    result = get_landing_cards(
        db=db,
        skip=skip,
        limit=limit,
        tags=tags,
        sort=sort,
        language=language,
    )
    return result

@router.get(
    "/v1/cards",
    response_model=LandingCardsResponsePaginations,
    summary="Карточки лендингов с пагинацией, сортировкой и поиском"
)
def get_cards(
    tags: Optional[List[str]] = Query(None, description="Фильтрация по тегам"),
    sort: Optional[str] = Query(None, description="Сортировка: popular, discount, new"),
    language: Optional[str] = Query(None, description="Язык лендинга: ES, EN, RU"),
    q: Optional[str] = Query(
        None,
        min_length=1,
        description="Строка поиска (landing_name, page_name)"
    ),
    single_course: Optional[bool] = Query(
        False,
        description="Если true — только лендинги, у которых ровно один курс"
    ),
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, gt=0, description="Размер страницы"),
    db: Session = Depends(get_db),
):
    return get_landing_cards_pagination(
        db,
        page=page,
        size=size,
        tags=tags,
        sort=sort,
        language=language,
        q=q,
        single_course=single_course,
    )


# ═══════════════════ V2: Карточки с расширенными фильтрами ═══════════════════

def _serialize_landing_card(landing: Landing) -> dict:
    """
    Сериализация лендинга в стандартную карточку (как LandingCardResponse).
    """
    return {
        "id": landing.id,
        "first_tag": landing.tags[0].name if landing.tags else None,
        "landing_name": landing.landing_name or "",
        "authors": [
            {"id": a.id, "name": a.name, "photo": a.photo}
            for a in (landing.authors or [])
        ],
        "slug": landing.page_name,
        "lessons_count": landing.lessons_count,
        "main_image": landing.preview_photo,
        "old_price": landing.old_price,
        "new_price": landing.new_price,
        "course_ids": [c.id for c in (landing.courses or [])],
    }


def _get_landing_sort_key(landing: Landing, db: Session, sort: str):
    """
    Возвращает ключ сортировки для лендинга (для сортировок в памяти).
    """
    if sort in ("duration_asc", "duration_desc"):
        duration_minutes = parse_duration_to_minutes(landing.duration)
        return duration_minutes or 0
    elif sort in ("lessons_asc", "lessons_desc"):
        lessons_count_num = calculate_landing_lessons_count(db, landing.id)
        return lessons_count_num or 0
    return 0


@router.get(
    "/v2/cards",
    response_model=LandingCardsV2Response,
    summary="V2: Карточки курсовых лендингов с расширенными фильтрами и метаданными",
    description="""
    Версия 2 эндпоинта для получения карточек курсовых лендингов.
    
    ## Основные возможности:
    
    ### Фильтрация:
    - **language** - фильтр по языку (EN, RU, ES, IT, AR, PT)
    - **tags** - фильтр по тегам (ID тегов, можно несколько)
    - **author_ids** - фильтр по ID авторов (можно несколько)
    - **price_from, price_to** - диапазон цены (new_price)
    - **q** - поисковый запрос по названию
    
    ### Сортировка:
    - **popular_asc** / **popular_desc** - по популярности (sales_count)
    - **price_asc** / **price_desc** - по цене
    - **duration_asc** / **duration_desc** - по длительности курса
    - **new_asc** / **new_desc** - по новизне (created_at)
    - **lessons_asc** / **lessons_desc** - по количеству уроков
    - **recommend** - персональные рекомендации (только для авторизованных!)
    
    ### Метаданные фильтров:
    При **include_filters=true** в ответе будет дополнительное поле `filters` с метаданными:
    - Список всех доступных авторов с количеством курсов
    - Список всех доступных тегов с количеством курсов
    - Диапазон цен
    - Список доступных опций сортировки (включая "Рекомендации" для авторизованных)
    
    ### Примеры использования:
    
    1. Получить первую страницу с метаданными фильтров:
       ```
       GET /v2/cards?page=1&size=20&include_filters=true
       ```
    
    2. Фильтрация по автору и тегам:
       ```
       GET /v2/cards?author_ids=1&tags=5&tags=10
       ```
    
    3. Поиск с сортировкой по цене:
       ```
       GET /v2/cards?q=implant&sort=price_asc
       ```
    
    4. Персональные рекомендации (требуется авторизация):
       ```
       GET /v2/cards?sort=recommend
       ```
    """,
    tags=["public"]
)
def landing_cards_v2(
    # Фильтры
    language: Optional[str] = Query(
        None,
        description="Язык лендинга (EN, RU, ES, IT, AR, PT)",
        regex="^(EN|RU|ES|IT|AR|PT)$"
    ),
    tags: Optional[List[int]] = Query(
        None,
        description="Фильтр по тегам (ID тегов, можно несколько)"
    ),
    author_ids: Optional[List[int]] = Query(
        None,
        description="Фильтр по ID авторов (можно несколько)"
    ),
    price_from: Optional[float] = Query(
        None,
        ge=0,
        description="Цена от (new_price)"
    ),
    price_to: Optional[float] = Query(
        None,
        ge=0,
        description="Цена до (new_price)"
    ),
    lessons_from: Optional[int] = Query(
        None,
        ge=0,
        description="Количество уроков от (сумма уроков всех курсов лендинга)"
    ),
    lessons_to: Optional[int] = Query(
        None,
        ge=0,
        description="Количество уроков до (сумма уроков всех курсов лендинга)"
    ),
    q: Optional[str] = Query(
        None,
        min_length=1,
        description="Поиск по landing_name или page_name"
    ),
    # Сортировка
    sort: Optional[str] = Query(
        None,
        description="Сортировка: popular_asc/desc, price_asc/desc, duration_asc/desc, new_asc/desc, lessons_asc/desc, recommend (только для авторизованных)",
        regex="^(popular_asc|popular_desc|price_asc|price_desc|duration_asc|duration_desc|new_asc|new_desc|lessons_asc|lessons_desc|recommend)$"
    ),
    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, gt=0, le=100, description="Размер страницы"),
    # Метаданные фильтров
    include_filters: bool = Query(
        False,
        description="Включить метаданные фильтров в ответ (authors, tags, price ranges, sorts)"
    ),
    db: Session = Depends(get_db),
    current_user: Optional[User] = Depends(get_current_user_optional),
):
    """
    V2 эндпоинт для получения карточек курсовых лендингов с расширенными фильтрами.
    
    Поддерживает:
    - Множественные фильтры (авторы, теги)
    - Фильтры по диапазону цены
    - Расширенные сортировки (в обе стороны)
    - Персональные рекомендации для авторизованных пользователей
    - Опциональные метаданные фильтров с актуальными counts
    """
    is_authenticated = current_user is not None
    
    # Если запрошена сортировка "recommend", но пользователь не авторизован - ошибка
    if sort == "recommend" and not is_authenticated:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "error": {
                    "code": "AUTH_REQUIRED_FOR_RECOMMEND",
                    "message": "Authorization required for recommendations sort",
                    "translation_key": "error.auth_required_for_recommend",
                    "params": {}
                }
            }
        )
    
    # Сортировка "recommend" использует существующую логику персонализированных рекомендаций
    if sort == "recommend" and is_authenticated:
        # Используем существующую функцию для рекомендаций
        result = get_recommended_landing_cards(
            db,
            user_id=current_user.id,
            skip=(page - 1) * size,
            limit=size,
            language=language,
        )
        
        # Переформатируем результат под V2 формат
        cards = []
        for card in result.get("cards", []):
            # Получаем полный объект лендинга для сериализации
            landing = db.query(Landing).options(
                selectinload(Landing.authors),
                selectinload(Landing.tags),
                selectinload(Landing.courses),
            ).filter(Landing.id == card["id"]).first()
            if landing:
                cards.append(_serialize_landing_card(landing))
        
        total = result.get("total", 0)
        
        # Получаем метаданные фильтров, если запрошено
        filters_metadata = None
        if include_filters:
            current_filters = {
                'language': language,
                'tags': tags,
                'author_ids': author_ids,
                'price_from': price_from,
                'price_to': price_to,
                'lessons_from': lessons_from,
                'lessons_to': lessons_to,
                'q': q,
            }
            base = build_landing_base_query(
                db=db,
                language=language,
                tags=tags,
                author_ids=author_ids,
                price_from=price_from,
                price_to=price_to,
                lessons_from=lessons_from,
                lessons_to=lessons_to,
                q=q,
            )
            filters_metadata = aggregate_landing_filters(
                db=db,
                base_query=base.order_by(None),
                current_filters=current_filters,
                include_recommend=is_authenticated
            )
        
        return LandingCardsV2Response(
            total=total,
            total_pages=ceil(total / size) if total > 0 else 0,
            page=page,
            size=size,
            cards=cards,
            filters=filters_metadata
        )
    
    # Собираем все фильтры в словарь
    current_filters = {
        'language': language,
        'tags': tags,
        'author_ids': author_ids,
        'price_from': price_from,
        'price_to': price_to,
        'lessons_from': lessons_from,
        'lessons_to': lessons_to,
        'q': q,
    }
    
    # Строим базовый запрос с применением всех фильтров
    base = build_landing_base_query(
        db=db,
        language=language,
        tags=tags,
        author_ids=author_ids,
        price_from=price_from,
        price_to=price_to,
        lessons_from=lessons_from,
        lessons_to=lessons_to,
        q=q,
    )
    
    # Применяем сортировку
    if sort == "price_asc":
        base = base.order_by(
            cast(Landing.new_price, SqlNumeric(10, 2)).asc(),
            Landing.id.asc()
        )
    elif sort == "price_desc":
        base = base.order_by(
            cast(Landing.new_price, SqlNumeric(10, 2)).desc(),
            Landing.id.desc()
        )
    elif sort == "popular_asc":
        base = base.order_by(
            Landing.sales_count.is_(None),
            Landing.sales_count.asc(),
            Landing.id.asc()
        )
    elif sort == "popular_desc":
        base = base.order_by(
            Landing.sales_count.is_(None),
            Landing.sales_count.desc(),
            Landing.id.desc()
        )
    elif sort == "new_asc":
        base = base.order_by(
            Landing.created_at.is_(None),
            Landing.created_at.asc(),
            Landing.id.asc()
        )
    elif sort == "new_desc":
        base = base.order_by(
            Landing.created_at.is_(None),
            Landing.created_at.desc(),
            Landing.id.desc()
        )
    elif sort == "duration_asc" or sort == "duration_desc":
        # Для сортировки по длительности нужно парсить строку duration
        # Это сложно сделать на уровне SQL, поэтому сортируем в памяти после получения
        pass  # Обработаем после получения данных
    elif sort == "lessons_asc" or sort == "lessons_desc":
        # Для сортировки по урокам нужен подзапрос
        # Создаём подзапрос для подсчёта уроков
        # Это сложнее, так как уроки хранятся в JSON - сортируем в памяти
        pass  # Обработаем после получения данных
    else:
        # Дефолтная сортировка - по новизне
        base = base.order_by(
            Landing.created_at.is_(None),
            Landing.created_at.desc(),
            Landing.id.desc()
        )
    
    # Подсчитываем total
    total = base.order_by(None).with_entities(func.count()).scalar() or 0
    
    # Получаем метаданные фильтров, если запрошено
    filters_metadata = None
    if include_filters:
        filters_metadata = aggregate_landing_filters(
            db=db,
            base_query=base.order_by(None),
            current_filters=current_filters,
            include_recommend=is_authenticated
        )
    
    # Для сортировки по duration и lessons нужна специальная обработка
    if sort in ("duration_asc", "duration_desc", "lessons_asc", "lessons_desc"):
        # Получаем все лендинги и сортируем в памяти
        all_landings = base.all()
        
        # Собираем данные с метриками для сортировки
        landings_with_metrics = []
        for landing in all_landings:
            sort_key = _get_landing_sort_key(landing, db, sort)
            landings_with_metrics.append((landing, sort_key))
        
        # Сортируем
        if sort in ("duration_asc", "lessons_asc"):
            landings_with_metrics.sort(key=lambda x: (x[1], x[0].id))
        else:  # duration_desc, lessons_desc
            landings_with_metrics.sort(key=lambda x: (-x[1], -x[0].id))
        
        # Применяем пагинацию в памяти
        start_idx = (page - 1) * size
        end_idx = start_idx + size
        paginated = landings_with_metrics[start_idx:end_idx]
        cards = [_serialize_landing_card(landing) for landing, _ in paginated]
    else:
        # Стандартная пагинация через SQL
        rows = base.offset((page - 1) * size).limit(size).all()
        cards = [_serialize_landing_card(r) for r in rows]
    
    return LandingCardsV2Response(
        total=total,
        total_pages=ceil(total / size) if total > 0 else 0,
        page=page,
        size=size,
        cards=cards,
        filters=filters_metadata
    )


@router.get("/search", response_model=LandingSearchResponse)
def search_landings(
        q: str = Query(..., min_length=0, description="Поиск по названию лендинга или имени лектора"),
        language: Optional[str] = Query(None, description="Язык лендинга (EN, RU, ES, PT, AR, IT)"),
        db: Session = Depends(get_db)
):
    """
    Поиск лендингов:
      - по названию (landing_name) или
      - по имени лектора (author.name).
    Дополнительно можно передать language, чтобы отфильтровать результаты по языку.
    В ответе:
      - общее число результатов (total),
      - список лендингов (items),
      - у каждого лендинга: id, landing_name, page_name, old_price, new_price,
        preview_photo, список авторов (id, name, photo).
    """

    query = (
        db.query(Landing)
        .outerjoin(Landing.authors)
        .filter(Landing.is_hidden == False)
        .filter(
            or_(
                Landing.landing_name.ilike(f"%{q}%"),
                Author.name.ilike(f"%{q}%")
            )
        )
    )

    if language:
        query = query.filter(Landing.language == language)

    landings = query.distinct().all()
    if not landings:
        landings = []

    # Формируем список объектов под нужную схему
    items_response = []
    for landing in landings:
        authors_list = [
            AuthorResponse(
                id=author.id,
                name=author.name,
                photo=author.photo
            )
            for author in landing.authors
        ]

        items_response.append(
            LandingItemResponse(
                id=landing.id,
                landing_name=landing.landing_name,
                page_name=landing.page_name,
                old_price=landing.old_price,
                new_price=landing.new_price,
                preview_photo=landing.preview_photo,
                authors=authors_list
            )
        )

    return LandingSearchResponse(
        total=len(items_response),
        items=items_response
    )

@router.patch("/set-hidden/{landing_id}", response_model=LandingDetailResponse)
def set_landing_is_hidden(
    landing_id: int,
    is_hidden: bool = Query(..., description="True, чтобы скрыть лендинг, False, чтобы показать"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    """Обновляет флаг is_hidden для лендинга по его ID."""
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    landing.is_hidden = is_hidden
    db.commit()
    db.refresh(landing)
    return landing


@router.get("/analytics/language-stats")
def language_stats(
        start_date: Optional[date] = Query(
            None,
            description="Дата начала (YYYY-MM-DD)."
        ),
        end_date: Optional[date] = Query(
            None,
            description="Дата конца (YYYY-MM-DD, включительно)."
        ),
        db: Session = Depends(get_db),
        detailed:   bool  = Query(True, description="Нужна ли разбивка по дням"),
        current_admin: User = Depends(require_roles("admin"))
):
    """
    Возвращает статистику покупок по языкам за указанный период.

    Логика выбора периода:
    - Нет ни start_date, ни end_date → за сегодняшний UTC‑день [00:00 – теперь).
    - Есть только start_date от начала start_date до текущего времени.
    - Есть и start_date, и end_date → от начала start_date до конца end_date (00:00 следующего дня).
    - Есть только end_date ошибка.
    """
    now = datetime.utcnow()

    if start_date is None and end_date is None:
        # за сегодняшний день
        start_dt = datetime(now.year, now.month, now.day)
        end_dt = now

    elif start_date is not None and end_date is None:
        # от начала указанных суток до текущего момента
        start_dt = datetime.combine(start_date, time.min)
        end_dt = now

    elif start_date is not None and end_date is not None:
        # от начала start_date до начала дня после end_date
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min)

    else:
        # end_date без start_date — некорректно
        raise HTTPException(
            status_code=400,
            detail="Если указываете end_date,  нужно обязательно передать start_date."
        )

    total = get_purchases_by_language(db, start_dt, end_dt)

    daily = []
    if detailed:
        daily = get_purchases_by_language_per_day(db, start_dt, end_dt)


    return {"total": total, "daily": daily}

SortBy = Literal["sales", "created_at"]
SortDir = Literal["asc", "desc"]

@router.get("/most-popular")
def most_popular_landings(
    language: Optional[str] = Query(None),
    limit: int = Query(10, gt=0, le=500),
    start_date: Optional[date] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Конец периода (YYYY-MM-DD, включительно)"),
    sort_by: str = Query("sales", description="Поле сортировки: sales | created_at"),
    sort_dir: str = Query("desc", description="Направление: asc | desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    # нормализуем даты как раньше
    if not start_date and not end_date:
        sd, ed = None, None
    elif start_date and not end_date:
        sd, ed = start_date, None
    elif start_date and end_date:
        sd, ed = start_date, end_date
    else:
        raise HTTPException(
            status_code=400,
            detail="Если указываете end_date, нужно обязательно передать start_date."
        )

    # список
    rows = get_top_landings_by_sales(
        db=db,
        language=language,
        limit=limit,
        start_date=sd,
        end_date=ed,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    items = [
        {
            "id": l.id,
            "landing_name": l.landing_name,
            "slug": l.page_name,
            "sales_count": int(sales or 0),
            "ad_sales_count": int(ad_sales_count or 0),
            "language": l.language,
            "in_advertising": l.in_advertising,
            "created_at": l.created_at.isoformat() if getattr(l, "created_at", None) else None,
        }
        for (l, sales, ad_sales_count) in rows
    ]

    # totals по тем же фильтрам (датам/языку)
    totals = get_sales_totals(
        db=db,
        language=language,
        start_date=sd,
        end_date=ed,
    )

    return {
        "totals": totals,   # {"sales_total": N, "ad_sales_total": M}
        "items": items
    }


@router.get("/most-popular/books")
def most_popular_book_landings(
    language: Optional[str] = Query(None),
    limit: int = Query(10, gt=0, le=500),
    start_date: Optional[date] = Query(None, description="Начало периода (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Конец периода (YYYY-MM-DD, включительно)"),
    sort_by: str = Query("sales", description="Поле сортировки: sales | created_at"),
    sort_dir: str = Query("desc", description="Направление: asc | desc"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    if not start_date and not end_date:
        sd, ed = None, None
    elif start_date and not end_date:
        sd, ed = start_date, None
    elif start_date and end_date:
        sd, ed = start_date, end_date
    else:
        raise HTTPException(
            status_code=400,
            detail="Если указываете end_date, нужно обязательно передать start_date."
        )

    rows = get_top_book_landings_by_sales(
        db=db,
        language=language,
        limit=limit,
        start_date=sd,
        end_date=ed,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )

    items = [
        {
            "id": bl.id,
            "landing_name": bl.landing_name,
            "slug": bl.page_name,
            "sales_count": int(sales or 0),
            "ad_sales_count": int(ad_sales_count or 0),
            "language": bl.language,
            "in_advertising": bl.in_advertising,
            "created_at": bl.created_at.isoformat() if getattr(bl, "created_at", None) else None,
        }
        for (bl, sales, ad_sales_count) in rows
    ]

    totals = get_book_sales_totals(
        db=db,
        language=language,
        start_date=sd,
        end_date=ed,
    )

    return {
        "totals": totals,
        "items": items,
    }

def _client_ip(request: Request) -> str:
    xfwd = request.headers.get("x-forwarded-for", "")
    return (xfwd.split(",")[0].strip() if xfwd else request.client.host)

@router.post("/track-ad/{slug}")
def track_ad(slug: str,
             request: Request,
            payload: Optional[TrackAdIn] = Body(None),
             db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.page_name == slug).first()
    if not landing:
        raise HTTPException(404)
    payload = payload or TrackAdIn()
    # 1) собрать fbp/fbc максимально надёжно
    fbp = payload.fbp or request.cookies.get("_fbp")
    fbc = payload.fbc or request.cookies.get("_fbc")
    ip = _client_ip(request)
    track_ad_visit(db=db, landing_id=landing.id, fbp=fbp, fbc=fbc, ip=ip)
    return {"ok": True}

@router.post("/free-access/{landing_id}")
def grant_free_access(
    landing_id: int,
    data: FreeAccessRequest,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """
    • Авторизованным — просто выдаём partial.
    • Неавторизованным — создаём аккаунт (если нужно), даём partial,
      шлём пароль, логиним (JWT в ответе).
    • Один бесплатный курс на аккаунт.
    """
    landing = (
        db.query(Landing)
          .options(selectinload(Landing.courses))
          .filter(Landing.id == landing_id)
          .first()
    )
    if not landing:
        raise HTTPException(404, "Landing not found")
    inviter = None
    if data.ref_code:
        inviter = (
            db.query(User)
            .filter(User.referral_code == data.ref_code)
            .first()
        )
        if not inviter:
            print("Ref-code %s не найден", data.ref_code)

    # ----- определяем / создаём пользователя -----
    random_pass = None
    new_user_created = False
    if current_user:
        user = current_user
    else:
        if not data.email:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={
                    "error": {
                        "code": "EMAIL_REQUIRED",
                        "message": "E-mail required",
                        "translation_key": "error.email_required",
                        "params": {}
                    }
                },
            )
        user = get_user_by_email(db, data.email)
        if not user:
            random_pass = generate_random_password()
            user = create_user(db, data.email, random_pass, invited_by=inviter)
            new_user_created = True  # ④
            send_password_to_user(user.email, random_pass, data.region)
        
        # Проверяем, не является ли пользователь администратором
        from ..utils.role_utils import is_admin
        if is_admin(user):
            logging.warning("Попытка автологина администратора через grant_free_access: %s", data.email)
            raise HTTPException(
                status_code=403,
                detail="Admin users cannot use auto-login for free access for security reasons"
            )
        
        # автологин
        token = create_access_token({"user_id": user.id})

    # ----- пытаемся выдать partial -----
    for course in landing.courses:
        try:
            add_partial_course_to_user(db, user.id, course.id)
        except ValueError as exc:
            if str(exc) == "free_course_already_taken":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "FREE_COURSE_ALREADY_TAKEN",
                            "message": "Free course already used",
                            "translation_key": "error.free_course_already_taken",
                            "params": {}
                        }
                    },
                )
            elif str(exc) == "course_already_purchased":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "COURSE_ALREADY_PURCHASED",
                            "message": "Course already purchased",
                            "translation_key": "error.course_already_purchased",
                            "params": {}
                        }
                    },
                )
            elif str(exc) == "partial_already_granted":
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={
                        "error": {
                            "code": "PARTIAL_ALREADY_GRANTED",
                            "message": "Partial access already granted",
                            "translation_key": "error.partial_already_granted",
                            "params": {}
                        }
                    },
                )
    db.commit()
    if new_user_created:  # посылаем только при реальной регистрации
        client_ip = (
                request.headers.get("X-Forwarded-For", "").split(",")[0]
                or request.client.host
                or "0.0.0.0"
        )
        user_agent = request.headers.get("User-Agent", "")
        send_registration_event(
            email=user.email,
            region=data.region,
            client_ip=client_ip,
            user_agent=user_agent,
            event_id=data.event_id or str(uuid.uuid4()),
            event_source_url=data.event_source_url,
            external_id=str(user.id),
            fbp=data.fbp,
            fbc=data.fbc,

        )

    resp = {
        "detail": "Partial access granted",
        "course_ids": [c.id for c in landing.courses],
    }
    if not current_user:
        resp["access_token"] = token
        if random_pass:
            resp["password"] = random_pass   # фронт покажет и сразу затрёт

    return resp

@router.get(
    "/recommend/cards",
    response_model=LandingCardsResponse,
    summary="Персональные карточки лендингов"
)
def personalized_cards(
    limit: int = Query(20, gt=0, le=100),
    skip: int = Query(0, ge=0),
    tags: Optional[List[str]] = Query(None, description="Фильтр по тегам"),
    sort: str = Query(
        "recommend",
        regex="^(popular|discount|new|recommend)$",
        description="popular | discount | new | recommend"
    ),
    language: Optional[str] = Query(None, description="Язык лендинга: ES, EN, RU"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    """
    • **popular / discount / new** — старая логика, но без уже купленных курсов.
    • **reccomend** — collaborative filtering (co-purchases).
    """
    return get_personalized_landing_cards(
        db,
        user_id=current.id,
        skip=skip,
        limit=limit,
        tags=tags,
        sort=sort,
        language=language,
    )
class VisitIn(BaseModel):
    from_ad: bool = False


@router.post("/{landing_id}/visit", status_code=201)
def track_landing_visit(
    landing_id: int,
    payload: VisitIn | None = None,
    db: Session = Depends(get_db),
):
    exists = db.query(Landing.id).filter(Landing.id == landing_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Landing not found")

    payload = payload or VisitIn()
    from_ad = bool(payload.from_ad)

    # 1) фиксируем визит (только в landing_visits)
    db.add(LandingVisit(
        landing_id=landing_id,
        from_ad=from_ad,
    ))

    # 2) если визит рекламный — продлеваем TTL ТОЛЬКО если реклама уже включена
    if from_ad:
        now = datetime.utcnow()
        landing = (
            db.query(Landing)
              .filter(Landing.id == landing_id)
              .with_for_update()
              .first()
        )
        if landing and landing.in_advertising:
            # гарантируем открытый период, если вдруг его нет
            open_ad_period_if_needed(db, landing_id, started_by=None)

            # продлеваем TTL
            new_ttl = now + AD_TTL
            if not landing.ad_flag_expires_at or landing.ad_flag_expires_at < new_ttl:
                landing.ad_flag_expires_at = new_ttl

        # ВАЖНО: если in_advertising == False, НИЧЕГО не включаем и не трогаем период/TTL

    db.commit()
    return {"ok": True}


Granularity = Literal["hour", "day"]

def _resolve_period(
    start_date: Optional[date],
    end_date: Optional[date],
) -> tuple[datetime, datetime]:
    now = datetime.utcnow()
    if start_date is None and end_date is None:
        return datetime(now.year, now.month, now.day), now
    if start_date is not None and end_date is None:
        return datetime.combine(start_date, time.min), now
    if start_date is not None and end_date is not None:
        return datetime.combine(start_date, time.min), datetime.combine(end_date + timedelta(days=1), time.min)
    raise HTTPException(status_code=400, detail="Если указываете end_date, нужно обязательно передать start_date.")

def _auto_granularity(start_dt: datetime, end_dt: datetime) -> Granularity:
    return "hour" if (end_dt - start_dt) <= timedelta(hours=48) else "day"

def _bucket_expr_mysql(ts_col, granularity: Granularity):
    if granularity == "day":
        return func.date(ts_col)  # 'YYYY-MM-DD'
    return func.date_format(ts_col, '%Y-%m-%d %H:00:00')  # 'YYYY-MM-DD HH:00:00'

def _coerce_bucket_to_dt(v, granularity: Granularity) -> datetime:
    if isinstance(v, datetime):
        return v.replace(minute=0, second=0, microsecond=0) if granularity == "hour" else v.replace(hour=0, minute=0, second=0, microsecond=0)
    if isinstance(v, date):
        return datetime(v.year, v.month, v.day)
    # MySQL DATE_FORMAT -> str
    from datetime import datetime as _dt
    if len(v) == 19:
        return _dt.strptime(v, "%Y-%m-%d %H:%M:%S")
    return _dt.strptime(v, "%Y-%m-%d")

def _iter_grid(start_dt: datetime, end_dt: datetime, granularity: Granularity):
    step = timedelta(hours=1) if granularity == "hour" else timedelta(days=1)
    cur = start_dt.replace(minute=0, second=0, microsecond=0) if granularity == "hour" \
        else start_dt.replace(hour=0, minute=0, second=0, microsecond=0)
    while cur < end_dt:
        yield cur
        cur += step

def _fill_series(start_dt: datetime, end_dt: datetime, granularity: Granularity, m: Dict[datetime, int]):
    return [{"ts": ts.isoformat() + "Z", "count": int(m.get(ts, 0))} for ts in _iter_grid(start_dt, end_dt, granularity)]

def _fetch_counts(
    db: Session,
    ts_col,
    filters,
    start_dt: datetime,
    end_dt: datetime,
    granularity: Granularity,
) -> tuple[Dict[datetime, int], int]:
    bucket = _bucket_expr_mysql(ts_col, granularity).label("b")
    rows = (db.query(bucket, func.count("*"))
              .filter(ts_col >= start_dt, ts_col < end_dt, *filters)
              .group_by(bucket)
              .order_by(bucket)
              .all())
    m: Dict[datetime, int] = {}
    total = 0
    for b, cnt in rows:
        dt = _coerce_bucket_to_dt(b, granularity)
        m[dt] = int(cnt)
        total += int(cnt)
    return m, total

def _pct(numer: int, denom: int) -> float:
    if denom <= 0:
        return 0.0
    # округление до двух знаков как в витринах
    return float(Decimal(numer) / Decimal(denom).quantize(Decimal("1.00"), rounding=ROUND_HALF_UP)*100)

def _sum_maps(*maps: Dict[datetime, int]) -> Dict[datetime, int]:
    out: Dict[datetime, int] = {}
    for m in maps:
        for k, v in m.items():
            out[k] = out.get(k, 0) + int(v)
    return out

@router.get("/analytics/landing-traffic")
def landing_traffic(
    landing_id: int,
    start_date: Optional[date] = Query(None, description="Начало (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Конец (YYYY-MM-DD, включительно)"),
    bucket:     Optional[Granularity] = Query(None, description="hour|day; по умолчанию авто"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    # 1) лендинг + имя
    landing_row = (
        db.query(Landing.id, Landing.landing_name, Landing.created_at)
          .filter(Landing.id == landing_id)
          .first()
    )
    if not landing_row:
        raise HTTPException(status_code=404, detail="Landing not found")
    landing_name = landing_row.landing_name
    landing_created_at = landing_row.created_at

    # 2) период и гранулярность
    start_dt, end_dt = _resolve_period(start_date, end_date)
    gran = bucket or _auto_granularity(start_dt, end_dt)

    # 3) визиты/покупки за диапазон (у тебя это уже было)
    visit_map, visits_range_total = _fetch_counts(
        db=db,
        ts_col=LandingVisit.visited_at,
        filters=[LandingVisit.landing_id == landing_id],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    purchase_map, purchases_range_total = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[Purchase.landing_id == landing_id],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    # 4) суммы «за всё время» (без ограничений по дате)
    visits_all_time = (
        db.query(func.count(LandingVisit.id))
          .filter(LandingVisit.landing_id == landing_id)
          .scalar()
        or 0
    )
    purchases_all_time = (
        db.query(func.count(Purchase.id))
          .filter(Purchase.landing_id == landing_id)
          .scalar()
        or 0
    )
    ad_visit_map, ad_visits_range_total = _fetch_counts(
        db=db,
        ts_col=LandingVisit.visited_at,
        filters=[LandingVisit.landing_id == landing_id,
                 LandingVisit.from_ad.is_(True)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )
    # Пересечение периодов рекламы с выбранным окном [start_dt, end_dt)
    period_rows = (
        db.query(LandingAdPeriod.started_at, LandingAdPeriod.ended_at)
        .filter(
            LandingAdPeriod.landing_id == landing_id,
            LandingAdPeriod.started_at < end_dt,
            func.coalesce(LandingAdPeriod.ended_at, datetime.utcnow()) > start_dt
        )
        .order_by(LandingAdPeriod.started_at.asc())
        .all()
    )

    ad_periods = []
    now = datetime.utcnow()
    for s, e in period_rows:
        clip_start = max(s, start_dt)
        clip_end = min(e or now, end_dt)
        if clip_start < clip_end:
            ad_periods.append({
                "start": clip_start.isoformat() + "Z",
                "end": clip_end.isoformat() + "Z"
            })

    ad_visits_all_time = (
                             db.query(func.count(LandingVisit.id))
                             .filter(LandingVisit.landing_id == landing_id,
                                     LandingVisit.from_ad.is_(True))
                             .scalar()
                         ) or 0

    first_visit_at = (
        db.query(func.min(LandingVisit.visited_at))
        .filter(LandingVisit.landing_id == landing_id)
        .scalar()
    )

    if first_visit_at is not None:
        purchases_since_first_visit = (
                                          db.query(func.count(Purchase.id))
                                          .filter(
                                              Purchase.landing_id == landing_id,
                                              Purchase.created_at >= first_visit_at
                                          )
                                          .scalar()
                                      ) or 0
    else:
        purchases_since_first_visit = 0

    conversion_all_time_percent = _pct(purchases_since_first_visit, visits_all_time)

    return {
        "landing": {
            "id": landing_id,
            "name": landing_name,
            "created_at": landing_created_at,
            "in_advertising": bool(db.query(Landing.in_advertising).filter(Landing.id == landing_id).scalar()),
        },
        "range": {
            "start": start_dt.isoformat() + "Z",
            "end":   end_dt.isoformat() + "Z",
        },
        "granularity": gran,

        # Итоги
        "totals_all_time": {
            "visits": visits_all_time,
            "ad_visits": ad_visits_all_time,
            "purchases": purchases_all_time,
            "conversion_percent": conversion_all_time_percent,
            "purchases_first_visit":purchases_since_first_visit,
        },
        "totals_range": {
            "visits": visits_range_total,
            "ad_visits": ad_visits_range_total,
            "purchases": purchases_range_total
        },
        # Серии для графика
        "series": {
            "visits": _fill_series(start_dt, end_dt, gran, visit_map),
            "ad_visits": _fill_series(start_dt, end_dt, gran, ad_visit_map),
            "purchases": _fill_series(start_dt, end_dt, gran, purchase_map),
        },
        "ad_periods": ad_periods
    }

@router.get("/analytics/book-landing-traffic")
def book_landing_traffic(
    book_landing_id: int,
    start_date: Optional[date] = Query(None, description="Начало (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Конец (YYYY-MM-DD, включительно)"),
    bucket:     Optional[Granularity] = Query(None, description="hour|day; по умолчанию авто"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    # 1) лендинг + имя
    landing_row = (
        db.query(BookLanding.id, BookLanding.landing_name, BookLanding.created_at)
          .filter(BookLanding.id == book_landing_id)
          .first()
    )
    if not landing_row:
        raise HTTPException(status_code=404, detail="Book landing not found")
    landing_name = landing_row.landing_name
    landing_created_at = landing_row.created_at

    # 2) период и гранулярность
    start_dt, end_dt = _resolve_period(start_date, end_date)
    gran = bucket or _auto_granularity(start_dt, end_dt)

    # 3) визиты/покупки за диапазон
    visit_map, visits_range_total = _fetch_counts(
        db=db,
        ts_col=BookLandingVisit.visited_at,
        filters=[BookLandingVisit.book_landing_id == book_landing_id],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    purchase_map, purchases_range_total = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[Purchase.book_landing_id == book_landing_id],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    # 4) суммы «за всё время»
    visits_all_time = (
        db.query(func.count(BookLandingVisit.id))
          .filter(BookLandingVisit.book_landing_id == book_landing_id)
          .scalar()
        or 0
    )
    purchases_all_time = (
        db.query(func.count(Purchase.id))
          .filter(Purchase.book_landing_id == book_landing_id)
          .scalar()
        or 0
    )

    ad_visit_map, ad_visits_range_total = _fetch_counts(
        db=db,
        ts_col=BookLandingVisit.visited_at,
        filters=[BookLandingVisit.book_landing_id == book_landing_id,
                 BookLandingVisit.from_ad.is_(True)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    # Пересечение периодов рекламы с выбранным окном [start_dt, end_dt)
    period_rows = (
        db.query(BookLandingAdPeriod.started_at, BookLandingAdPeriod.ended_at)
        .filter(
            BookLandingAdPeriod.book_landing_id == book_landing_id,
            BookLandingAdPeriod.started_at < end_dt,
            func.coalesce(BookLandingAdPeriod.ended_at, datetime.utcnow()) > start_dt
        )
        .order_by(BookLandingAdPeriod.started_at.asc())
        .all()
    )

    ad_periods = []
    now = datetime.utcnow()
    for s, e in period_rows:
        clip_start = max(s, start_dt)
        clip_end = min(e or now, end_dt)
        if clip_start < clip_end:
            ad_periods.append({
                "start": clip_start.isoformat() + "Z",
                "end": clip_end.isoformat() + "Z"
            })

    ad_visits_all_time = (
        db.query(func.count(BookLandingVisit.id))
          .filter(
              BookLandingVisit.book_landing_id == book_landing_id,
              BookLandingVisit.from_ad.is_(True)
          )
          .scalar()
    ) or 0

    first_visit_at = (
        db.query(func.min(BookLandingVisit.visited_at))
        .filter(BookLandingVisit.book_landing_id == book_landing_id)
        .scalar()
    )

    if first_visit_at is not None:
        purchases_since_first_visit = (
            db.query(func.count(Purchase.id))
              .filter(
                  Purchase.book_landing_id == book_landing_id,
                  Purchase.created_at >= first_visit_at
              )
              .scalar()
        ) or 0
    else:
        purchases_since_first_visit = 0

    conversion_all_time_percent = _pct(purchases_since_first_visit, visits_all_time)

    return {
        "landing": {
            "id": book_landing_id,
            "name": landing_name,
            "created_at": landing_created_at,
            "in_advertising": bool(db.query(BookLanding.in_advertising).filter(BookLanding.id == book_landing_id).scalar()),
        },
        "range": {
            "start": start_dt.isoformat() + "Z",
            "end":   end_dt.isoformat() + "Z",
        },
        "granularity": gran,

        "totals_all_time": {
            "visits": visits_all_time,
            "ad_visits": ad_visits_all_time,
            "purchases": purchases_all_time,
            "conversion_percent": conversion_all_time_percent,
            "purchases_first_visit": purchases_since_first_visit,
        },
        "totals_range": {
            "visits": visits_range_total,
            "ad_visits": ad_visits_range_total,
            "purchases": purchases_range_total
        },
        "series": {
            "visits": _fill_series(start_dt, end_dt, gran, visit_map),
            "ad_visits": _fill_series(start_dt, end_dt, gran, ad_visit_map),
            "purchases": _fill_series(start_dt, end_dt, gran, purchase_map),
        },
        "ad_periods": ad_periods
    }

@router.get("/analytics/site-traffic")
def site_traffic(
    language: Optional[str] = Query(
        None,
        description="Фильтр по языку лендинга: EN, RU, ES, IT, AR, PT. Пусто = все языки."
    ),
    start_date: Optional[date] = Query(None, description="Начало (YYYY-MM-DD)"),
    end_date:   Optional[date] = Query(None, description="Конец (YYYY-MM-DD, включительно)"),
    bucket:     Optional[Granularity] = Query(None, description="hour|day; по умолчанию авто"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Агрегированная аналитика по ВСЕМ лендингам (курсы + книги) опционально по языку.
    Показатели: visits, ad_visits, purchases, ad_purchases.
    Формат аналогичен /analytics/landing-traffic.
    """
    # 0) подготовим множества лендингов: is_hidden = False (+ язык, если задан)
    landings_q = db.query(Landing.id).filter(Landing.is_hidden.is_(False))
    book_landings_q = db.query(BookLanding.id).filter(BookLanding.is_hidden.is_(False))
    if language:
        lang = language.upper().strip()
        landings_q = landings_q.filter(Landing.language == lang)
        book_landings_q = book_landings_q.filter(BookLanding.language == lang)
    landing_ids_subq = landings_q.scalar_subquery()
    book_landing_ids_subq = book_landings_q.scalar_subquery()

    # 1) период и гранулярность (та же логика)
    start_dt, end_dt = _resolve_period(start_date, end_date)
    gran = bucket or _auto_granularity(start_dt, end_dt)

    # 2) серии и итоги за диапазон (курсы)
    visit_map_l, visits_range_total_l = _fetch_counts(
        db=db,
        ts_col=LandingVisit.visited_at,
        filters=[LandingVisit.landing_id.in_(landing_ids_subq)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    ad_visit_map_l, ad_visits_range_total_l = _fetch_counts(
        db=db,
        ts_col=LandingVisit.visited_at,
        filters=[
            LandingVisit.landing_id.in_(landing_ids_subq),
            LandingVisit.from_ad.is_(True),
        ],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    purchase_map_l, purchases_range_total_l = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[Purchase.landing_id.in_(landing_ids_subq)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    ad_purchase_map_l, ad_purchases_range_total_l = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[
            Purchase.landing_id.in_(landing_ids_subq),
            Purchase.from_ad.is_(True),
        ],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    # 2b) серии и итоги за диапазон (книги)
    visit_map_b, visits_range_total_b = _fetch_counts(
        db=db,
        ts_col=BookLandingVisit.visited_at,
        filters=[BookLandingVisit.book_landing_id.in_(book_landing_ids_subq)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    ad_visit_map_b, ad_visits_range_total_b = _fetch_counts(
        db=db,
        ts_col=BookLandingVisit.visited_at,
        filters=[
            BookLandingVisit.book_landing_id.in_(book_landing_ids_subq),
            BookLandingVisit.from_ad.is_(True),
        ],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    purchase_map_b, purchases_range_total_b = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[Purchase.book_landing_id.in_(book_landing_ids_subq)],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    ad_purchase_map_b, ad_purchases_range_total_b = _fetch_counts(
        db=db,
        ts_col=Purchase.created_at,
        filters=[
            Purchase.book_landing_id.in_(book_landing_ids_subq),
            Purchase.from_ad.is_(True),
        ],
        start_dt=start_dt,
        end_dt=end_dt,
        granularity=gran,
    )

    # 3) totals «за всё время» (без ограничений по дате)
    visits_all_time = (
        db.query(func.count(LandingVisit.id))
          .filter(LandingVisit.landing_id.in_(landing_ids_subq))
          .scalar()
    ) or 0
    visits_all_time += (
        db.query(func.count(BookLandingVisit.id))
          .filter(BookLandingVisit.book_landing_id.in_(book_landing_ids_subq))
          .scalar()
    ) or 0

    ad_visits_all_time = (
        db.query(func.count(LandingVisit.id))
          .filter(
              LandingVisit.landing_id.in_(landing_ids_subq),
              LandingVisit.from_ad.is_(True),
          )
          .scalar()
    ) or 0
    ad_visits_all_time += (
        db.query(func.count(BookLandingVisit.id))
          .filter(
              BookLandingVisit.book_landing_id.in_(book_landing_ids_subq),
              BookLandingVisit.from_ad.is_(True),
          )
          .scalar()
    ) or 0

    purchases_all_time = (
        db.query(func.count(Purchase.id))
          .filter(Purchase.landing_id.in_(landing_ids_subq))
          .scalar()
    ) or 0
    purchases_all_time += (
        db.query(func.count(Purchase.id))
          .filter(Purchase.book_landing_id.in_(book_landing_ids_subq))
          .scalar()
    ) or 0

    ad_purchases_all_time = (
        db.query(func.count(Purchase.id))
          .filter(
              Purchase.landing_id.in_(landing_ids_subq),
              Purchase.from_ad.is_(True),
          )
          .scalar()
    ) or 0
    ad_purchases_all_time += (
        db.query(func.count(Purchase.id))
          .filter(
              Purchase.book_landing_id.in_(book_landing_ids_subq),
              Purchase.from_ad.is_(True),
          )
          .scalar()
    ) or 0

    # 4) ответ — структура максимально похожа на landing_traffic
    return {
        "scope": {
            "language": language.upper() if language else "ALL"
        },
        "range": {
            "start": start_dt.isoformat() + "Z",
            "end":   end_dt.isoformat() + "Z",
        },
        "granularity": gran,

        "totals_all_time": {
            "visits": visits_all_time,
            "ad_visits": ad_visits_all_time,
            "purchases": purchases_all_time,
            "ad_purchases": ad_purchases_all_time,
        },
        "totals_range": {
            "visits": visits_range_total_l + visits_range_total_b,
            "ad_visits": ad_visits_range_total_l + ad_visits_range_total_b,
            "purchases": purchases_range_total_l + purchases_range_total_b,
            "ad_purchases": ad_purchases_range_total_l + ad_purchases_range_total_b,
        },

        "series": {
            "visits":        _fill_series(start_dt, end_dt, gran, _sum_maps(visit_map_l, visit_map_b)),
            "ad_visits":     _fill_series(start_dt, end_dt, gran, _sum_maps(ad_visit_map_l, ad_visit_map_b)),
            "purchases":     _fill_series(start_dt, end_dt, gran, _sum_maps(purchase_map_l, purchase_map_b)),
            "ad_purchases":  _fill_series(start_dt, end_dt, gran, _sum_maps(ad_purchase_map_l, ad_purchase_map_b)),
        }
    }
