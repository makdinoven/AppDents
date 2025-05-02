from datetime import datetime, timedelta, time, date

from fastapi import APIRouter, Depends, Query, status, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session
from typing import List, Optional
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Tag, Landing, Author
from ..schemas_v2.author import AuthorResponse

from ..services_v2.landing_service import get_landing_detail, create_landing, update_landing, \
    delete_landing, get_landing_cards, get_top_landings_by_sales, \
    get_purchases_by_language, get_landing_cards_pagination, list_landings_paginated, search_landings_paginated
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate, TagResponse, \
    LandingSearchResponse, LandingCardsResponse, LandingItemResponse, LandingCardsResponsePaginations, \
    LandingListPageResponse, LangEnum

router = APIRouter()

@router.get(
    "/list",
    response_model=LandingListPageResponse,
    summary="Список лендингов (пагинация по страницам)"
)
def get_landing_listing(
    page: int = Query(1, ge=1, description="Номер страницы (≥1)"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    language: Optional[LangEnum] = Query(           # 👈 новый параметр
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
def get_landing_by_id(landing_id: int, db: Session = Depends(get_db)):
    landing = get_landing_detail(db, landing_id)
    # Если lessons_info хранится как словарь, преобразуем его в список
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    authors_list = [
        {"id": author.id, "name": author.name, "description": author.description, "photo": author.photo}
        for author in landing.authors
    ] if landing.authors else []
    tags_list = [
        {"id": tag.id, "name": tag.name}
        for tag in landing.tags
    ] if landing.tags else []
    # Собираем итоговый ответ
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
        "author_ids": [author.id for author in landing.authors] if landing.authors else [],
        "course_ids": [course.id for course in landing.courses] if landing.courses else [],
        "tag_ids": [tag.id for tag in landing.tags] if landing.tags else [],
        "authors": authors_list,  # Новое поле с подробностями об авторах
        "tags": tags_list,  # Новое поле с подробностями о тегах
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
    }

@router.get("/detail/by-page/{page_name}", response_model=LandingDetailResponse)
def get_landing_by_page(page_name: str, db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.page_name == page_name).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []
    authors_list = [
        {"id": author.id, "name": author.name, "description": author.description, "photo": author.photo}
        for author in landing.authors
    ] if landing.authors else []
    tags_list = [
        {"id": tag.id, "name": tag.name}
        for tag in landing.tags
    ] if landing.tags else []
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
        "author_ids": [author.id for author in landing.authors] if landing.authors else [],
        "course_ids": [course.id for course in landing.courses] if landing.courses else [],
        "tag_ids": [tag.id for tag in landing.tags] if landing.tags else [],
        "authors": authors_list,
        "tags": tags_list,
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
    }

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
def delete_landing_route(landing_id: int, db: Session = Depends(get_db),current_admin: User = Depends(require_roles("admin"))):
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
    result = get_landing_cards(db, skip, limit, tags, sort, language)
    return result

@router.get(
    "v1/cards",
    response_model=LandingCardsResponsePaginations,
    summary="Карточки лендингов с пагинацией по страницам"
)
def get_cards(
    tags: Optional[List[str]] = Query(
        None, description="Фильтрация по тегам"
    ),
    sort: Optional[str] = Query(
        None, description="Сортировка: popular, discount, new"
    ),
    language: Optional[str] = Query(
        None, description="Язык лендинга: ES, EN, RU"
    ),
    page: int = Query(
        1, ge=1, description="Номер страницы (начиная с 1)"
    ),
    size: int = Query(
        20, gt=0, description="Размер страницы"
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Возвращает:
    {
      total: <общее число лендингов после фильтров>,
      total_pages: <число страниц при данном size>,
      page: <текущая страница>,
      size: <размер страницы>,
      cards: [ ...список карточек... ]
    }
    """
    return get_landing_cards_pagination(
        db,
        page=page,
        size=size,
        tags=tags,
        sort=sort,
        language=language,
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

    data = get_purchases_by_language(db, start_dt, end_dt)
    return {"data": data}

@router.get("/most-popular")
def most_popular_landings(
    language: str = None,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """
    Возвращает самые популярные лендинги (по sales_count),
    опционально отфильтрованные по языку,
    ограничение кол-ва через limit.
    """
    landings = get_top_landings_by_sales(db, language, limit)
    # Тут можно возвращать в формате вашей схемы, например, LandingListResponse или самодельную
    return [
        {
            "id": l.id,
            "landing_name": l.landing_name,
            "slug" : l.page_name,
            "sales_count": l.sales_count,
            "language": l.language,
            "in_advertising": l.in_advertising
        }
        for l in landings
    ]