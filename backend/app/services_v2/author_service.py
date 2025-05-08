from math import ceil

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from sqlalchemy import func
from ..models.models_v2 import Author, Landing
from ..schemas_v2.author import AuthorCreate, AuthorUpdate, AuthorResponsePage, AuthorResponse


def list_authors_by_page(
    db: Session,
    *,
    page: int = 1,
    size: int = 12,
    language: Optional[str] = None
) -> dict:
    # 1) Базовый запрос для фильтрации
    base_query = db.query(Author)
    if language:
        base_query = base_query.filter(Author.language == language)

    # 2) Считаем общее число записей под фильтром
    total = db.query(func.count(Author.id)).select_from(Author).filter(
        Author.language == language
    ).scalar() if language else db.query(func.count(Author.id)).select_from(Author).scalar()

    # 3) Вычисляем смещение
    offset = (page - 1) * size

    # 4) Получаем нужный «кусок» данных
    authors = (
        base_query
        .order_by(Author.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    # 5) Подсчитываем общее число страниц
    total_pages = ceil(total / size) if total else 0

    # 6) Формируем список Pydantic-моделей
    authors = (
        base_query
        .options(
            selectinload(Author.landings)
            .selectinload(Landing.courses)
        )
        .order_by(Author.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    def _safe_price(value) -> float:
        try:
            return float(value)
        except Exception:
            return float("inf")  # некорректная цена → бесконечность

    items = []
    for a in authors:
        # ---- 1. минимальная цена по каждому course_id ----
        min_price_by_course: Dict[int, float] = {}
        for l in a.landings:
            price = _safe_price(l.new_price)
            for c in l.courses:
                cid = c.id
                if price < min_price_by_course.get(cid, float("inf")):
                    min_price_by_course[cid] = price

        # ---- 2. оставляем только «дешёвые» лендинги ----
        kept_landings: List[Landing] = []
        for l in a.landings:
            price = _safe_price(l.new_price)
            has_cheaper_alt = any(
                price > min_price_by_course.get(c.id, price)  # хотя бы один дешевле?
                for c in l.courses
            )
            if not has_cheaper_alt:
                kept_landings.append(l)

        # ---- 3. уникальные курсы по отфильтрованным лендингам ----
        unique_course_ids: Set[int] = {c.id for l in kept_landings for c in l.courses}

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids)  # ← корректное число
            )
        )

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }

def get_author_detail(db: Session, author_id: int) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    return author

def create_author(db: Session, author_data: AuthorCreate) -> Author:
    new_author = Author(
        name=author_data.name,
        description=author_data.description,
        photo=author_data.photo,
        language=author_data.language  # устанавливаем язык
    )
    db.add(new_author)
    db.commit()
    db.refresh(new_author)
    return new_author

def update_author(db: Session, author_id: int, update_data: AuthorUpdate) -> Author:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    if update_data.name is not None:
        author.name = update_data.name
    if update_data.description is not None:
        author.description = update_data.description
    if update_data.photo is not None:
        author.photo = update_data.photo
    if update_data.language is not None:
        author.language = update_data.language
    db.commit()
    db.refresh(author)
    return author

def delete_author(db: Session, author_id: int) -> None:
    author = db.query(Author).filter(Author.id == author_id).first()
    if not author:
        raise HTTPException(status_code=404, detail="Author not found")
    # Очистка связи с лендингами (ассоциативная таблица landing_authors)
    author.landings = []
    db.delete(author)
    db.commit()

from sqlalchemy.orm import Session, selectinload
from typing import Dict, Tuple, Set, List

def get_author_full_detail(db: Session, author_id: int) -> dict:
    # 1. Автор и все связи одним запросом
    author = (
        db.query(Author)
          .options(
              selectinload(Author.landings)
                .selectinload(Landing.courses),
              selectinload(Author.landings)
                .selectinload(Landing.tags),
              selectinload(Author.landings)
                .selectinload(Landing.authors),
          )
          .filter(Author.id == author_id)
          .first()
    )
    if not author:
        return None

    # 2. Минимальная цена по каждому курсу среди всех лендингов автора
    min_price_by_course: Dict[int, float] = {}
    for l in author.landings:
        try:
            price = float(l.new_price)
        except Exception:
            price = float("inf")
        for c in l.courses:
            cid = c.id
            cur = min_price_by_course.get(cid, float("inf"))
            if price < cur:
                min_price_by_course[cid] = price

    # 3. Фильтруем лендинги:
    #    исключаем, если нашлась хотя бы одна позиция дешевле
    kept_landings = []
    for l in author.landings:
        try:
            price = float(l.new_price)
        except Exception:
            price = float("inf")
        # есть ли курс, у которого эта цена НЕ минимальна?
        has_cheaper_alt = any(
            price > min_price_by_course.get(c.id, price)  # строго > !!!
            for c in l.courses
        )
        if not has_cheaper_alt:
            kept_landings.append(l)

    # 4. Формируем агрегаты по отфильтрованному набору
    landings_data: List[dict] = []
    all_course_ids: Set[int] = set()
    total_new_price = 0.0
    total_old_price = 0.0

    for l in kept_landings:
        try:
            p_new = float(l.new_price)
            p_old = float(l.old_price)
        except Exception:
            p_new = p_old = 0.0

        total_new_price += p_new
        total_old_price += p_old

        course_ids = [c.id for c in l.courses]
        all_course_ids.update(course_ids)

        authors_info = [
            {"id": a.id, "name": a.name, "photo": a.photo or ""}
            for a in l.authors
        ]

        landings_data.append({
            "id": l.id,
            "landing_name": l.landing_name,
            "slug": l.page_name,
            "old_price": l.old_price,
            "new_price": l.new_price,
            "main_image": l.preview_photo,
            "first_tag": l.tags[0].name if l.tags else None,
            "lessons_count": l.lessons_count,
            "course_ids": course_ids,
            "authors": authors_info,
        })

    # упорядочим по id для стабильности
    landings_data.sort(key=lambda x: x["id"])

    return {
        "id": author.id,
        "name": author.name,
        "description": author.description,
        "photo": author.photo,
        "language": author.language,
        "landings": landings_data,
        "course_ids": list(all_course_ids),
        "total_new_price": int(total_new_price * 0.8),
        "total_old_price": total_old_price,
        "landing_count": len(landings_data),
    }


def _search_authors_query(
    db: Session,
    *,
    search: str,
    language: Optional[str]
):
    """
    Возвращает базовый query с фильтрами по строке поиска и языку.
    """
    q = db.query(Author)
    # Поиск в поле name (case-insensitive)
    q = q.filter(Author.name.ilike(f"%{search}%"))
    if language:
        q = q.filter(Author.language == language)
    return q

def list_authors_search_paginated(
    db: Session,
    *,
    search: str,
    page: int = 1,
    size: int = 12,
    language: Optional[str] = None
) -> dict:
    # 1) Готовим базовый запрос
    base_query = _search_authors_query(db, search=search, language=language)

    # 2) Считаем общее число под этот запрос
    total = db.query(func.count(Author.id))\
              .select_from(Author)\
              .filter(Author.name.ilike(f"%{search}%"))\
              .filter(Author.language == language) if language else \
            db.query(func.count(Author.id))\
              .select_from(Author)\
              .filter(Author.name.ilike(f"%{search}%"))
    total = total.scalar()

    # 3) Пагинация
    offset = (page - 1) * size
    authors = base_query.offset(offset).limit(size).all()

    # 4) Подсчёт страниц
    total_pages = ceil(total / size) if total else 0

    # 5) Формируем список Pydantic-моделей
    authors = (
        base_query
        .options(
            selectinload(Author.landings)
            .selectinload(Landing.courses)
        )
        .order_by(Author.id.desc())
        .offset(offset)
        .limit(size)
        .all()
    )

    def _safe_price(value) -> float:
        try:
            return float(value)
        except Exception:
            return float("inf")  # некорректная цена → бесконечность

    items = []
    for a in authors:
        # ---- 1. минимальная цена по каждому course_id ----
        min_price_by_course: Dict[int, float] = {}
        for l in a.landings:
            price = _safe_price(l.new_price)
            for c in l.courses:
                cid = c.id
                if price < min_price_by_course.get(cid, float("inf")):
                    min_price_by_course[cid] = price

        # ---- 2. оставляем только «дешёвые» лендинги ----
        kept_landings: List[Landing] = []
        for l in a.landings:
            price = _safe_price(l.new_price)
            has_cheaper_alt = any(
                price > min_price_by_course.get(c.id, price)  # хотя бы один дешевле?
                for c in l.courses
            )
            if not has_cheaper_alt:
                kept_landings.append(l)

        # ---- 3. уникальные курсы по отфильтрованным лендингам ----
        unique_course_ids: Set[int] = {c.id for l in kept_landings for c in l.courses}

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids)  # ← корректное число
            )
        )

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }