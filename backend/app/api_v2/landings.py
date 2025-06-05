from datetime import datetime, timedelta, time, date

from fastapi import APIRouter, Depends, Query, status, HTTPException, Request
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional, Dict
from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Tag, Landing, Author
from ..schemas_v2.author import AuthorResponse

from ..services_v2.landing_service import get_landing_detail, create_landing, update_landing, \
    delete_landing, get_landing_cards, get_top_landings_by_sales, \
    get_purchases_by_language, get_landing_cards_pagination, list_landings_paginated, search_landings_paginated, \
    track_ad_visit
from ..schemas_v2.landing import LandingListResponse, LandingDetailResponse, LandingCreate, LandingUpdate, TagResponse, \
    LandingSearchResponse, LandingCardsResponse, LandingItemResponse, LandingCardsResponsePaginations, \
    LandingListPageResponse, LangEnum, FreeAccessRequest
from ..services_v2.user_service import add_partial_course_to_user, create_access_token, create_user, \
    generate_random_password, get_user_by_email
from ..utils.email_sender import send_password_to_user

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
        raise HTTPException(status_code=404, detail="Landing not found")

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

@router.get("/detail/by-page/{page_name}", response_model=LandingDetailResponse)
def get_landing_by_page(
    page_name: str,
    db: Session = Depends(get_db)
):
    # 1) забираем лендинг по page_name + нужные связи
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
          .filter(Landing.page_name == page_name)    # <-- фильтр по page_name
          .first()
    )
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # 2) приводим lessons_info к списку
    lessons = landing.lessons_info
    if isinstance(lessons, dict):
        lessons_list = [{k: v} for k, v in lessons.items()]
    elif isinstance(lessons, list):
        lessons_list = lessons
    else:
        lessons_list = []

    # 3) вспомогательный safe_price
    def _safe_price(v) -> float:
        try:
            return float(v)
        except:
            return float("inf")

    # 4) строим authors_list с нужными полями
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
            "tags": sorted(unique_tags),
        })

    # 5) детали самого лендинга
    tags_list   = [{"id": t.id, "name": t.name} for t in landing.tags]
    course_ids  = [c.id for c in landing.courses]
    author_ids  = [a.id for a in landing.authors]
    tag_ids     = [t.id for t in landing.tags]

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
        "authors": authors_list,   # <-- только id, courses_count и tags
        "tags": tags_list,
        "duration": landing.duration,
        "lessons_count": landing.lessons_count,
        "is_hidden": landing.is_hidden,
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
    result = get_landing_cards(db, skip, limit, tags, sort, language)
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
    language: Optional[str] = Query(None),
    limit: int = Query(10, gt=0, le=500),
    start_date: Optional[date] = Query(
        None, description="Начало периода (YYYY-MM-DD)"
    ),
    end_date: Optional[date] = Query(
        None, description="Конец периода (YYYY-MM-DD, включительно)"
    ),
    db: Session = Depends(get_db),
):
    """
    • Если нет дат — используется агрегированное поле sales_count.
    • Если есть только start_date — все продажи от start_date до сегодня.
    • Если есть обе даты — все продажи за каждый день от start_date до end_date включительно.
    • end_date без start_date — ошибка.
    """
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

    rows = get_top_landings_by_sales(
        db=db,
        language=language,
        limit=limit,
        start_date=sd,
        end_date=ed,
    )

    return [
        {
            "id": l.id,
            "landing_name": l.landing_name,
            "slug": l.page_name,
            "sales_count": sales,
            "language": l.language,
            "in_advertising": l.in_advertising,
        }
        for l, sales in rows
    ]

@router.post("/track-ad/{slug}")
def track_ad(slug: str,
             request: Request,
             db: Session = Depends(get_db)):
    landing = db.query(Landing).filter(Landing.page_name == slug).first()
    if not landing:
        raise HTTPException(404)
    track_ad_visit(
        db=db,
        landing_id=landing.id,
        fbp=request.cookies.get("_fbp"),
        fbc=request.cookies.get("_fbc"),
        ip=request.client.host
    )
    return {"ok": True}

@router.post("/free-access/{landing_id}")
def grant_free_access(
    landing_id: int,
    data: FreeAccessRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user),
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

    # ----- определяем / создаём пользователя -----
    random_pass = None
    if current_user:
        user = current_user
    else:
        if not data.email:
            raise HTTPException(400, "email_required")
        user = get_user_by_email(db, data.email)
        if not user:
            random_pass = generate_random_password()
            user = create_user(db, data.email, random_pass)
            send_password_to_user(user.email, random_pass, data.region)
        # автологин
        token = create_access_token({"user_id": user.id})

    # ----- пытаемся выдать partial -----
    for course in landing.courses:
        try:
            add_partial_course_to_user(db, user.id, course.id)
        except ValueError as e:
            if str(e) == "free_course_already_taken":
                raise HTTPException(409, "Free course already used")
            # дубликат бесплатного доступа к тому же курсу — молча игнорируем

    resp = {
        "detail": "Partial access granted",
        "course_ids": [c.id for c in landing.courses],
    }
    if not current_user:
        resp["access_token"] = token
        if random_pass:
            resp["password"] = random_pass   # фронт покажет и сразу затрёт

    return resp