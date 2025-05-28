from math import ceil

from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from sqlalchemy import func, literal_column
from ..models.models_v2 import Author, Landing
from ..schemas_v2.author import AuthorCreate, AuthorUpdate, AuthorResponsePage, AuthorResponse


def list_authors_by_page(
    db: Session,
    *,
    page: int = 1,
    size: int = 12,
    language: Optional[str] = None
) -> dict:
    popularity_sub = (
        db.query(
            Author.id.label("author_id"),
            func.coalesce(func.sum(func.coalesce(Landing.sales_count, 0)), 0)
            .label("popularity")
        )
        .outerjoin(Author.landings)  # LEFT JOIN landing_authors + landings
        .group_by(Author.id)
    ).subquery()

    # 1) Базовый запрос для фильтрации
    base_query = (
        db.query(Author)
        .join(popularity_sub, popularity_sub.c.author_id == Author.id)
        .options(  # нужны курсы для courses_count
            selectinload(Author.landings)
            .selectinload(Landing.courses),
            selectinload(Author.landings)
            .selectinload(Landing.tags),
        )
        .order_by(
            popularity_sub.c.popularity.desc(),  # ← сортировка
            Author.id.desc()
        )
    )
    if language:
        base_query = base_query.filter(Author.language == language)

    # 2) Считаем общее число записей под фильтром
    total = base_query.with_entities(func.count(literal_column("1"))).scalar()
    # 3) Вычисляем смещение
    offset = (page - 1) * size

    # 4) Получаем нужный «кусок» данных
    authors = base_query.offset(offset).limit(size).all()

    # 5) Подсчитываем общее число страниц
    total_pages = ceil(total / size) if total else 0

    def safe_price(value) -> float:
        try:
            return float(value)
        except Exception:
            return float("inf")  # некорректная цена → бесконечность


    items : List[AuthorResponse] = []
    for a in authors:
        # ---- 1. минимальная цена по каждому course_id ----
        min_price_by_course: Dict[int, float] = {}
        for l in a.landings:
            price = safe_price(l.new_price)
            for c in l.courses:
                cid = c.id
                if price < min_price_by_course.get(cid, float("inf")):
                    min_price_by_course[cid] = price

        # ---- 2. оставляем только «дешёвые» лендинги ----
        kept_landings: List[Landing] = []
        for l in a.landings:
            price = safe_price(l.new_price)
            has_cheaper_alt = any(
                price > min_price_by_course.get(c.id, price)  # хотя бы один дешевле?
                for c in l.courses
            )
            if not has_cheaper_alt:
                kept_landings.append(l)

        # ---- 3. уникальные курсы по отфильтрованным лендингам ----
        unique_course_ids: Set[int] = {c.id for l in kept_landings for c in l.courses}
        unique_tags: Set[str] = {
            t.name for l in kept_landings for t in l.tags
        }

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids),
                tags=sorted(unique_tags)
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
        "tags": sorted({t.name for l in kept_landings for t in l.tags}),
    }
def safe_price(v) -> float:
        try:
            return float(v)
        except Exception:
            return float("inf")


def list_authors_search_paginated(
    db: Session,
    *,
    search: str,
    page: int = 1,
    size: int = 12,
    language: Optional[str] = None
) -> dict:
    # ---------- 1. подзапрос популярности ----------------------------------
    popularity_sub = (
        db.query(
            Author.id.label("author_id"),
            func.coalesce(func.sum(func.coalesce(Landing.sales_count, 0)), 0)
                .label("popularity")
        )
        .outerjoin(Author.landings)
        .group_by(Author.id)
    ).subquery()

    # ---------- 2. базовый запрос c поиском + языком ------------------------
    base_query = (
        db.query(Author)
          .join(popularity_sub, popularity_sub.c.author_id == Author.id)
          .options(
              selectinload(Author.landings)
                .selectinload(Landing.courses),
              selectinload(Author.landings)
                .selectinload(Landing.tags),
          )
          .filter(Author.name.ilike(f"%{search}%"))
          .order_by(
              popularity_sub.c.popularity.desc(),
              Author.id.desc()
          )
    )
    if language:
        base_query = base_query.filter(Author.language == language)

    # ---------- 3. всего записей -------------------------------------------
    total = base_query.with_entities(func.count(literal_column("1"))).scalar()

    # ---------- 4. пагинация в БД ------------------------------------------
    offset = (page - 1) * size
    authors = base_query.offset(offset).limit(size).all()

    # ---------- 5. вычисляем courses_count ---------------------------------
    items: List[AuthorResponse] = []
    for a in authors:
        # a) минимальная цена по каждому курсу
        min_price_by_course: Dict[int, float] = {}
        for l in a.landings:
            price = safe_price(l.new_price)
            for c in l.courses:
                if price < min_price_by_course.get(c.id, float("inf")):
                    min_price_by_course[c.id] = price

        # b) «дорогие» дубликаты отбрасываем
        kept_landings = [
            l for l in a.landings
            if not any(
                safe_price(l.new_price) > min_price_by_course.get(c.id, safe_price(l.new_price))
                for c in l.courses
            )
        ]

        # c) уникальные курсы
        unique_course_ids: Set[int] = {
            c.id for l in kept_landings for c in l.courses
        }
        unique_tags: Set[str] = {
            t.name for l in kept_landings for t in l.tags
        }

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids),
                tags = sorted(unique_tags)
        )
        )

    # ---------- 6. финальный ответ -----------------------------------------
    total_pages = ceil(total / size) if total else 0
    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }