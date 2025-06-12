from datetime import time, datetime, timedelta, date
from math import ceil

from sqlalchemy import func, or_, desc, Date, cast, select
from sqlalchemy.types import Float
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session, Query
from fastapi import HTTPException
from typing import List, Optional
from ..models.models_v2 import Landing, Author, Course, Tag, Purchase, AdVisit
from ..schemas_v2.landing import LandingCreate, LandingUpdate, LangEnum


def _paginate(query: Query, *, page: int, size: int) -> dict:
    total = query.count()
    items = (query
             .offset((page - 1) * size)
             .limit(size)
             .all())
    return {
        "total": total,
        "total_pages": ceil(total / size) if total else 0,
        "page": page,
        "size": size,
        "items": items,
    }

def list_landings_paginated(
    db: Session, *, language: Optional[LangEnum], page: int = 1, size: int = 10
) -> dict:
    q = db.query(Landing).order_by(desc(Landing.id))        # новые сверху
    if language:                                                # фильтр, если задан
        q = q.filter(Landing.language == language.value)
    return _paginate(q, page=page, size=size)

def search_landings_paginated(
    db: Session, *, q: str, language: Optional[LangEnum], page: int = 1, size: int = 10
) -> dict:
    q_base = (db.query(Landing)
                .filter(or_(
                    Landing.landing_name.ilike(f"%{q}%"),
                    Landing.page_name.ilike(f"%{q}%")
                ))
                .order_by(desc(Landing.id)))
    if language:
        q_base = q_base.filter(Landing.language == language.value)
    return _paginate(q_base, page=page, size=size)


def get_landing_detail(db: Session, landing_id: int) -> Landing:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    return landing

def create_landing(db: Session, landing_data: LandingCreate) -> Landing:
    new_landing = Landing(
        page_name = landing_data.page_name,
        language = landing_data.language,
        landing_name = landing_data.landing_name,
        old_price = landing_data.old_price,
        new_price = landing_data.new_price,
        course_program = landing_data.course_program,
        lessons_info = landing_data.lessons_info,
        preview_photo = landing_data.preview_photo,
        sales_count = landing_data.sales_count,
        duration = landing_data.duration,
        lessons_count = landing_data.lessons_count,
        is_hidden=landing_data.is_hidden or False,
    )
    db.add(new_landing)
    db.commit()
    db.refresh(new_landing)
    # Привязка авторов через ассоциативную таблицу landing_authors
    if landing_data.author_ids:
        authors = db.query(Author).filter(Author.id.in_(landing_data.author_ids)).all()
        new_landing.authors = authors
    # Привязка курсов через ассоциативную таблицу landing_course
    if landing_data.course_ids:
        courses = db.query(Course).filter(Course.id.in_(landing_data.course_ids)).all()
        new_landing.courses = courses
    db.commit()
    db.refresh(new_landing)
    if landing_data.tag_ids:
        tags = db.query(Tag).filter(Tag.id.in_(landing_data.tag_ids)).all()
        new_landing.tags = tags
    # Если landing_name не задано, обновляем его автоматически
    if not new_landing.landing_name:
        new_landing.landing_name = f"Landing name {new_landing.id}"
        db.commit()
        db.refresh(new_landing)
    return new_landing


def update_landing(db: Session, landing_id: int, update_data: LandingUpdate) -> Landing:
    max_retries = 3
    for attempt in range(max_retries):
        try:
            # Используем with_for_update() для явной блокировки строки
            landing = db.query(Landing).filter(Landing.id == landing_id).with_for_update().first()
            if not landing:
                raise HTTPException(status_code=404, detail="Landing not found")

            if update_data.page_name is not None:
                landing.page_name = update_data.page_name
            if update_data.landing_name is not None:
                landing.landing_name = update_data.landing_name
            if update_data.old_price is not None:
                landing.old_price = update_data.old_price
            if update_data.new_price is not None:
                landing.new_price = update_data.new_price
            if update_data.course_program is not None:
                landing.course_program = update_data.course_program
            if update_data.lessons_info is not None:
                landing.lessons_info = [
                    {k: v.dict() if hasattr(v, "dict") else v for k, v in lesson_item.items()}
                    for lesson_item in update_data.lessons_info
                ]
            if update_data.preview_photo is not None:
                landing.preview_photo = update_data.preview_photo
            if update_data.sales_count is not None:
                landing.sales_count = update_data.sales_count
            if update_data.language is not None:
                landing.language = update_data.language
            if update_data.author_ids is not None:
                authors = db.query(Author).filter(Author.id.in_(update_data.author_ids)).all()
                landing.authors = authors
            if update_data.course_ids is not None:
                courses = db.query(Course).filter(Course.id.in_(update_data.course_ids)).all()
                landing.courses = courses
            if update_data.tag_ids is not None:
                tags = db.query(Tag).filter(Tag.id.in_(update_data.tag_ids)).all()
                landing.tags = tags
            if update_data.duration is not None:
                landing.duration = update_data.duration
            if update_data.lessons_count is not None:
                landing.lessons_count = update_data.lessons_count
            if update_data.is_hidden is not None:
                landing.is_hidden = update_data.is_hidden
            db.commit()
            db.refresh(landing)
            return landing
        except OperationalError as e:
            db.rollback()
            if "Lock wait timeout exceeded" in str(e):
                if attempt < max_retries - 1:
                    time.sleep(1)  # небольшая задержка перед повторной попыткой
                    continue
            raise HTTPException(status_code=500, detail=f"Update failed: {e}")
    raise HTTPException(status_code=500, detail="Unable to update landing due to lock wait timeout")


def delete_landing(db: Session, landing_id: int) -> None:
    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")
    # Очистка связей с курсами (через landing_course) и с авторами (через landing_authors)
    landing.courses = []
    landing.authors = []
    landing.tags = []
    db.delete(landing)
    db.commit()


def get_landing_cards(
        db: Session,
        skip: int = 0,
        limit: int = 20,
        tags: Optional[List[str]] = None,
        sort: Optional[str] = None,  # Возможные значения: "popular", "discount", "new"
        language: Optional[str] = None
) -> dict:
    query = db.query(Landing).filter(Landing.is_hidden == False)

    if language:
        language = language.upper().strip()
        query = query.filter(Landing.language == language)

    # Фильтрация по тегам (если передан список тегов)
    if tags:
        query = query.join(Landing.tags).filter(Tag.name.in_(tags))

    # Применяем сортировку
    if sort:
        if sort == "popular":
            query = query.order_by(Landing.sales_count.desc())
        elif sort == "discount":
            old_price_expr = func.cast(Landing.__table__.c.old_price, Float())
            new_price_expr = func.cast(Landing.__table__.c.new_price, Float())
            discount_expr = ((old_price_expr - new_price_expr) / old_price_expr) * 100
            query = query.order_by(discount_expr.desc())
        elif sort == "new":
            query = query.order_by(Landing.id.desc())
    else:
        query = query.order_by(Landing.id)

    # Подсчитываем общее число записей по фильтрам (без offset/limit)
    total = query.distinct(Landing.id).count()

    # Применяем пагинацию
    landings = query.offset(skip).limit(limit).all()

    # Формируем карточки с нужными полями
    cards = []
    for landing in landings:
        first_tag = landing.tags[0].name if landing.tags else None
        authors = [
            {"id": author.id, "name": author.name, "photo": author.photo}
            for author in landing.authors
        ]
        card = {
            "id": landing.id,
            "first_tag": first_tag,
            "landing_name": landing.landing_name,
            "authors": authors,
            "slug": landing.page_name,
            "lessons_count": landing.lessons_count,
            "main_image": landing.preview_photo,
            "old_price": landing.old_price,
            "new_price": landing.new_price,
            "course_ids": [c.id for c in landing.courses],
        }
        cards.append(card)

    return {"total": total, "cards": cards}

def get_landing_cards_pagination(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    tags: Optional[List[str]] = None,
    sort: Optional[str] = None,      # "popular", "discount", "new"
    language: Optional[str] = None,
    q: Optional[str] = None,
    single_course: bool = False,     # ← новый параметр
) -> dict:
    # 1) Базовый запрос и фильтры
    query = db.query(Landing).filter(Landing.is_hidden == False)
    if language:
        query = query.filter(Landing.language == language.upper().strip())
    if tags:
        query = query.join(Landing.tags).filter(Tag.name.in_(tags))
    if q:
        ilike_q = f"%{q}%"
        query = query.filter(
            or_(Landing.landing_name.ilike(ilike_q),
                Landing.page_name.ilike(ilike_q))
        )

    # 1.1) Группируем по лендингу и, если нужно, оставляем ровно один курс
    query = query.join(Landing.courses).group_by(Landing.id)
    if single_course:
        query = query.having(func.count(Course.id) == 1)

    # 2) Общее число
    total = query.count()
    # 3) Сортировка
    if sort == "popular":
        query = query.order_by(Landing.sales_count.desc())
    elif sort == "discount":
        old_p = func.cast(Landing.__table__.c.old_price, Float())
        new_p = func.cast(Landing.__table__.c.new_price, Float())
        discount = ((old_p - new_p) / old_p) * 100
        query = query.order_by(discount.desc())
    elif sort == "new":
        query = query.order_by(Landing.id.desc())
    else:
        query = query.order_by(Landing.id)
    # 4) Пагинация по страницам
    offset = (page - 1) * size
    items = query.offset(offset).limit(size).all()
    # 5) Формируем карточки
    cards = []
    for landing in items:
        first_tag = landing.tags[0].name if landing.tags else None
        authors = [
            {"id": a.id, "name": a.name, "photo": a.photo}
            for a in landing.authors
        ]
        cards.append({
            "id": landing.id,
            "first_tag": first_tag,
            "landing_name": landing.landing_name,
            "authors": authors,
            "slug": landing.page_name,
            "lessons_count": landing.lessons_count,
            "main_image": landing.preview_photo,
            "old_price": landing.old_price,
            "new_price": landing.new_price,
            "course_ids": [c.id for c in landing.courses]
        })
    # 6) Подсчёт общего числа страниц
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "cards": cards,
    }


def get_purchases_by_language(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
):
    """
    Возвращает список словарей:
      [ {"language": "EN", "count": 10}, "total_amount": 1234.56 ]
    за период [start_dt, end_dt).
    """
    query = (
        db.query(
            Landing.language.label("language"),
            func.count(Purchase.id).label("purchase_count"),
            func.coalesce(func.sum(Purchase.amount), 0).label("total_amount"),
        )
        .join(Purchase, Purchase.landing_id == Landing.id)
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at < end_dt,
        )
        .group_by(Landing.language)
    )
    results = query.all()

    return [
        {"language": row.language, "count": row.purchase_count, "total_amount": f"{row.total_amount:.2f} $"}
        for row in results
    ]

def check_and_reset_ad_flag(landing: Landing, db: Session):
    """
    Если у лендинга in_advertising=True, но ad_flag_expires_at < now,
    сбрасываем in_advertising в False.
    """
    if landing.in_advertising and landing.ad_flag_expires_at:
        now = datetime.utcnow()
        if landing.ad_flag_expires_at < now:
            landing.in_advertising = False
            landing.ad_flag_expires_at = None

def reset_expired_ad_flags(db: Session):
    """
    Сбрасывает in_advertising у лендингов,
    у которых истёк ad_flag_expires_at.
    """
    updated = db.query(Landing).filter(
        Landing.in_advertising.is_(True),
        Landing.ad_flag_expires_at < func.utc_timestamp()
    ).update(
        {
            Landing.in_advertising: False,
            Landing.ad_flag_expires_at: None
        },
        synchronize_session=False      # быстрее, чем проход по каждому объекту
    )
    if updated:
        db.commit()


def get_top_landings_by_sales(
    db: Session,
    language: Optional[str] = None,
    limit: int = 10,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    reset_expired_ad_flags(db)

    # если есть хотя бы одна дата — считаем реальный sales
    if start_date or end_date:
        subq = (
            db.query(
                Purchase.landing_id.label("landing_id"),
                func.count(Purchase.id).label("sales"),
            )
            .filter(Purchase.landing_id.isnot(None))
        )

        # приводим created_at → date и фильтруем
        if start_date:
            subq = subq.filter(
                cast(Purchase.created_at, Date) >= start_date
            )
        if end_date:
            subq = subq.filter(
                cast(Purchase.created_at, Date) <= end_date
            )

        subq = subq.group_by(Purchase.landing_id).subquery()

        q = (
            db.query(Landing, subq.c.sales)
            .join(subq, subq.c.landing_id == Landing.id)
            .filter(Landing.is_hidden.is_(False))
        )
        if language:
            q = q.filter(Landing.language == language)

        result = q.order_by(subq.c.sales.desc()).limit(limit).all()

    else:
        # старое поведение: агрегированное поле
        q = (
            db.query(Landing, Landing.sales_count.label("sales"))
            .filter(Landing.is_hidden.is_(False))
        )
        if language:
            q = q.filter(Landing.language == language)

        result = q.order_by(Landing.sales_count.desc()).limit(limit).all()

    db.commit()
    return result


# services_v2/landing_service.py
AD_TTL = timedelta(hours=3)

def track_ad_visit(db: Session, landing_id: int, fbp: str | None, fbc: str | None, ip: str):
    visit = AdVisit(
        landing_id=landing_id,
        fbp=fbp,
        fbc=fbc,
        ip_address=ip,
    )
    db.add(visit)

    landing = db.query(Landing).filter(Landing.id == landing_id).first()
    if landing:
        landing.in_advertising = True
        landing.ad_flag_expires_at = datetime.utcnow() + AD_TTL
    db.commit()

def get_cheapest_landing_for_course(db: Session, course_id: int) -> Landing | None:
    """
    Возвращает объект Landing с минимальным new_price
    для заданного course_id. Скрытые лендинги (is_hidden=True)
    игнорируются.  new_price приводим к float для корректного сравнения.
    """
    rows = (
        db.query(Landing)
          .join(Landing.courses)
          .filter(
              Course.id == course_id,
              Landing.is_hidden == False,
          )
          .all()
    )
    if not rows:
        return None

    def _price(landing: Landing) -> float:
        try:
            return float(landing.new_price)
        except Exception:
            return float("inf")

    return min(rows, key=_price)

def get_recommended_landing_cards(
    db: Session,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    language: str | None = None,
) -> dict:
    """
    Карточки лендингов, рекомендованных пользователю.
    Алгоритм       : частотные co-purchases.
    Фоллбэк        : самые популярные (sales_count DESC).
    Формат ответа  : тот же, что get_landing_cards().
    """
    # 1) курсы, которые уже есть у пользователя
    user_courses_subq = (
        db.query(Purchase.course_id)
          .filter(
              Purchase.user_id == user_id,
              Purchase.course_id.isnot(None)
          )
          .subquery()
    )

    # если у пользователя нет покупок – сразу уходим в fallback
    if not db.query(user_courses_subq).first():
        return _fallback_landing_cards(db, user_id, skip, limit, language)

    # 2) похожие пользователи
    similar_users_subq = (
        db.query(Purchase.user_id)
          .filter(Purchase.course_id.in_(select(user_courses_subq)))
          .filter(Purchase.user_id != user_id)
          .distinct()
          .subquery()
    )

    # 3) какие ещё курсы они брали, рейтинг по частоте
    recommended_courses_subq = (
        db.query(
            Purchase.course_id.label("course_id"),
            func.count(Purchase.id).label("cnt")
        )
        .filter(
            Purchase.user_id.in_(select(similar_users_subq)),
            Purchase.course_id.isnot(None),
            ~Purchase.course_id.in_(select(user_courses_subq))
        )
        .group_by(Purchase.course_id)
        .order_by(func.count(Purchase.id).desc())
        .subquery()
    )

    # 4) ограничиваем и превращаем в список id
    recommended_ids = [
        row.course_id
        for row in db.query(recommended_courses_subq.c.course_id)
                      .offset(skip)
                      .limit(limit*2)           # берём небольшой запас
    ]

    cards: list[dict] = []
    for cid in recommended_ids:
        landing = get_cheapest_landing_for_course(db, cid)
        if not landing:
            continue
        if language and landing.language != language.upper():
            continue
        # — формируем карточку ровно как в get_landing_cards —
        cards.append({
            "id":      landing.id,
            "first_tag": landing.tags[0].name if landing.tags else None,
            "landing_name": landing.landing_name,
            "authors": [
                {"id": a.id, "name": a.name, "photo": a.photo}
                for a in landing.authors
            ],
            "slug":     landing.page_name,
            "lessons_count": landing.lessons_count,
            "main_image":    landing.preview_photo,
            "old_price": landing.old_price,
            "new_price": landing.new_price,
            "course_ids": [c.id for c in landing.courses],
        })
        if len(cards) == limit:
            break

    # 5) докидываем fallback, если рекомендаций мало
    if len(cards) < limit:
        need = limit - len(cards)
        backup = _fallback_landing_cards(
            db, user_id, skip=0, limit=need, language=language
        )["cards"]
        cards.extend(backup)

    return {"total": len(cards), "cards": cards}


# ---------------------------------------------------------------------------
def _fallback_landing_cards(
    db: Session,
    user_id: int,
    skip: int,
    limit: int,
    language: str | None,
) -> dict:
    """
    Бэкап-логика: top-seller'ы, которых пользователь ещё не купил.
    """
    purchased_course_ids = (
        db.query(Purchase.course_id)
          .filter(
              Purchase.user_id == user_id,
              Purchase.course_id.isnot(None)
          )
          .subquery()
    )

    query = (
        db.query(Landing)
          .filter(Landing.is_hidden.is_(False))
          .filter(~Landing.courses.any(Course.id.in_(select(purchased_course_ids))))
          .order_by(Landing.sales_count.desc())
    )
    if language:
        query = query.filter(Landing.language == language.upper())

    landings = query.offset(skip).limit(limit).all()

    cards = []
    for l in landings:
        cards.append({
            "id": l.id,
            "first_tag": l.tags[0].name if l.tags else None,
            "landing_name": l.landing_name,
            "authors": [
                {"id": a.id, "name": a.name, "photo": a.photo}
                for a in l.authors
            ],
            "slug": l.page_name,
            "lessons_count": l.lessons_count,
            "main_image": l.preview_photo,
            "old_price": l.old_price,
            "new_price": l.new_price,
            "course_ids": [c.id for c in l.courses],
        })

    return {"total": len(cards), "cards": cards}

def get_personalized_landing_cards(
    db: Session,
    *,
    user_id: int,
    skip: int = 0,
    limit: int = 20,
    tags: Optional[List[str]] = None,
    sort: str = "popular",                      # popular | new | discount | reccomend
    language: Optional[str] = None,
) -> dict:
    """
    Старые сортировки (popular/new/discount) + новая reccomend,
    причём курсы, уже купленные пользователем, не попадают в выдачу.
    """
    sort = (sort or "popular").lower()

    # 1. «Умная» выдача
    if sort == "reccomend":
        return get_recommended_landing_cards(
            db,
            user_id=user_id,
            skip=skip,
            limit=limit,
            language=language,
        )

    # 2. Базовый список с фильтрами + исключение покупок
    query = db.query(Landing).filter(Landing.is_hidden.is_(False))

    if language:
        query = query.filter(Landing.language == language.upper().strip())

    if tags:
        query = query.join(Landing.tags).filter(Tag.name.in_(tags)).distinct()

    purchased_subq = (
        db.query(Purchase.course_id)
          .filter(Purchase.user_id == user_id, Purchase.course_id.isnot(None))
          .subquery()
    )
    query = query.filter(~Landing.courses.any(Course.id.in_(select(purchased_subq))))

    # 3. Сортировки
    if sort == "popular":
        query = query.order_by(Landing.sales_count.desc())
    elif sort == "discount":
        query = query.order_by((Landing.old_price - Landing.new_price).desc())
    elif sort == "new":
        query = query.order_by(Landing.created_at.desc())

    landings = query.offset(skip).limit(limit).all()

    cards: list[dict] = []
    for l in landings:
        cards.append({
            "id": l.id,
            "first_tag": l.tags[0].name if l.tags else None,
            "landing_name": l.landing_name,
            "authors": [
                {"id": a.id, "name": a.name, "photo": a.photo}
                for a in l.authors
            ],
            "slug": l.page_name,
            "lessons_count": l.lessons_count,
            "main_image": l.preview_photo,
            "old_price": l.old_price,
            "new_price": l.new_price,
            "course_ids": [c.id for c in l.courses],
        })

    return {"total": len(cards), "cards": cards}