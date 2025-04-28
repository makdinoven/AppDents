from datetime import time, datetime, timedelta
from math import ceil

from sqlalchemy import func, or_
from sqlalchemy.types import Float
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List, cast, Optional
from ..models.models_v2 import Landing, Author, Course, Tag, Purchase
from ..schemas_v2.landing import LandingCreate, LandingUpdate

def list_landings_paginated(
    db: Session,
    *,
    page: int = 1,
    size: int = 10,
) -> dict:
    # 1. общее число
    total = db.query(func.count(Landing.id)).scalar()
    # 2. смещение
    offset = (page - 1) * size
    # 3. сами записи
    landings = (
        db.query(Landing)
          .offset(offset)
          .limit(size)
          .all()
    )
    # 4. считаем страницы
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": landings,   # ORM-объекты, pydantic orm_mode сделает остальное
    }

def search_landings_paginated(
    db: Session,
    *,
    q: str,
    page: int = 1,
    size: int = 10,
) -> dict:
    # 1. базовый фильтр по подстроке в landing_name или page_name
    base_q = (
        db.query(Landing)
          .filter(
             or_(
               Landing.landing_name.ilike(f"%{q}%"),
               Landing.page_name.ilike(f"%{q}%")
             )
          )
    )
    # 2. общее число по фильтру
    total = base_q.count()
    # 3. смещение и лимит
    offset = (page - 1) * size
    landings = base_q.offset(offset).limit(size).all()
    # 4. страницы
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": landings,
    }


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
            "first_tag": first_tag,
            "landing_name": landing.landing_name,
            "authors": authors,
            "slug": landing.page_name,
            "lessons_count": landing.lessons_count,
            "main_image": landing.preview_photo,
            "old_price": landing.old_price,
            "new_price": landing.new_price,
        }
        cards.append(card)

    return {"total": total, "cards": cards}

def get_landing_cards_pagination(
    db: Session,
    *,
    page: int = 1,
    size: int = 20,
    tags: Optional[List[str]] = None,
    sort: Optional[str] = None,  # "popular", "discount", "new"
    language: Optional[str] = None,
) -> dict:
    # 1) Базовый запрос и фильтры
    query = db.query(Landing).filter(Landing.is_hidden == False)
    if language:
        query = query.filter(Landing.language == language.upper().strip())
    if tags:
        query = query.join(Landing.tags).filter(Tag.name.in_(tags))
    # 2) Считаем общее число (без пагинации)
    total = query.distinct(Landing.id).count()
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
            "first_tag": first_tag,
            "landing_name": landing.landing_name,
            "authors": authors,
            "slug": landing.page_name,
            "lessons_count": landing.lessons_count,
            "main_image": landing.preview_photo,
            "old_price": landing.old_price,
            "new_price": landing.new_price,
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
        {"language": row.language, "count": row.purchase_count, "total_amount": row.total_amount}
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

def get_top_landings_by_sales(db: Session, language: str = None, limit: int = 10):
    query = db.query(Landing).order_by(Landing.sales_count.desc())
    # Если вы хотите показывать только is_hidden=False:
    query = query.filter(Landing.is_hidden == False)
    if language:
        query = query.filter(Landing.language == language)
    landings = query.limit(limit).all()

    # Ленивая проверка in_advertising
    for landing in landings:
        check_and_reset_ad_flag(landing, db)
    # Возможно, не хотите коммитить на каждый проход,
    # тогда можете делать один общий commit после цикла
    db.commit()

    return landings