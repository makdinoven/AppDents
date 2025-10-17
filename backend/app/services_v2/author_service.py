from math import ceil
import os, logging
from fastapi import HTTPException
from sqlalchemy.orm import Session, selectinload
from typing import List, Optional
from sqlalchemy import func, literal_column

from .book_service import books_in_landing
from ..models.models_v2 import Author, Landing, Book, BookLanding
from ..schemas_v2.author import AuthorCreate, AuthorUpdate, AuthorResponsePage, AuthorResponse

DISCOUNT_COURSES         = float(os.getenv("DISCOUNT_COURSES",         0.80))  # 20 %
DISCOUNT_BOOKS           = float(os.getenv("DISCOUNT_BOOKS",           0.85))  # 15 %
DISCOUNT_COURSES_BOOKS   = float(os.getenv("DISCOUNT_COURSES_BOOKS",   0.75))  # 25 %
log = logging.getLogger(__name__)

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
            selectinload(Author.books).selectinload(Book.landings),
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

    items: List[AuthorResponse] = []
    for a in authors:
        # 1) минимальная цена по каждому course_id
        min_price_by_course: Dict[int, float] = {}
        for l in a.landings:
            price = safe_price(l.new_price)
            for c in l.courses:
                cid = c.id
                if price < min_price_by_course.get(cid, float("inf")):
                    min_price_by_course[cid] = price

        # 2) оставляем только «дешёвые» лендинги
        kept_landings: List[Landing] = []
        for l in a.landings:
            price = safe_price(l.new_price)
            has_cheaper_alt = any(
                price > min_price_by_course.get(c.id, price)
                for c in l.courses
            )
            if not has_cheaper_alt:
                kept_landings.append(l)

        # 3) уникальные курсы и теги
        unique_course_ids: Set[int] = {c.id for l in kept_landings for c in l.courses}
        unique_tags: Set[str] = {t.name for l in kept_landings for t in l.tags}

        # 4) КНИГИ: считаем только те, у которых есть хотя бы один видимый BookLanding
        visible_books_count = len({
            b.id
            for b in a.books
            if any(not bl.is_hidden for bl in b.landings)
        })

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids),
                books_count=visible_books_count or None,
                tags=sorted(unique_tags),
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

from sqlalchemy.orm import selectinload
from typing import Dict, List, Optional, Set

def get_author_full_detail(db: Session, author_id: int) -> dict | None:
    author = (
        db.query(Author)
        .options(
            # лендинги курсов
            selectinload(Author.landings).selectinload(Landing.courses),
            selectinload(Author.landings).selectinload(Landing.tags),
            selectinload(Author.landings).selectinload(Landing.authors),

            # книги автора + их связи
            selectinload(Author.books),  # сами книги
            selectinload(Author.books).selectinload(Book.landings),  # их книжные лендинги
            selectinload(Author.books).selectinload(Book.tags),  # теги книги

            # теги у книжных лендингов
            selectinload(Author.books)
            .selectinload(Book.landings)
            .selectinload(BookLanding.tags),
        )
        .filter(Author.id == author_id)
        .first()
    )
    if not author:
        return None

    # 1) Курсовые лендинги: фильтруем скрытые
    author.landings = [l for l in author.landings if not l.is_hidden]


    # 2) Минимальная new-цена по каждому курсу
    min_price_by_course: Dict[int, float] = {}
    for l in author.landings:
        price = safe_price(l.new_price)
        for c in l.courses:
            cid = c.id
            min_price_by_course[cid] = min(min_price_by_course.get(cid, float("inf")), price)

    # 3) Оставляем самые дешёвые лендинги по курсам
    kept_landings: List[Landing] = []
    for l in author.landings:
        price = safe_price(l.new_price)
        if not any(price > min_price_by_course[c.id] for c in l.courses):
            kept_landings.append(l)

    # 4) Собираем карточки курсовых лендингов
    landings_data, all_course_ids = [], set()
    total_new_price_courses = total_old_price_courses = 0.0
    landing_ids: List[int] = []

    for l in kept_landings:
        p_new = safe_price(l.new_price)
        p_old = safe_price(l.old_price)

        total_new_price_courses += p_new
        total_old_price_courses += p_old

        course_ids = [c.id for c in l.courses]
        all_course_ids.update(course_ids)
        landing_ids.append(l.id)

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
            "authors": [
                {"id": a.id, "name": a.name, "photo": a.photo or ""}
                for a in l.authors
            ],
        })

    landings_data.sort(key=lambda x: x["id"])

    # 5) КНИГИ автора → минимальные цены по видимым книжным лендингам каждой книги
    books_data: List[dict] = []
    total_books_new_raw = 0.0
    total_books_old_raw = 0.0
    all_book_landings: dict[int, BookLanding] = {}  # id → объект
    book_landing_ids: List[int] = []
    all_book_ids: set[int] = set()
    for b in author.books:
        if any(not bl.is_hidden for bl in b.landings):
            all_book_ids.add(b.id)

    for b in author.books:
        books_data.append({
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "cover_url": b.cover_url,
        })

        visible_bl = [bl for bl in (b.landings or []) if not bl.is_hidden]
        # накапливаем все видимые book-лендинги автора (для карточек)
        for bl in visible_bl:
            if bl.id not in all_book_landings:
                all_book_landings[bl.id] = bl

        # минимальные цены по этой книге
        new_candidates = [safe_price(bl.new_price) for bl in visible_bl]
        old_candidates = [safe_price(bl.old_price) for bl in visible_bl]

        new_candidates = [p for p in new_candidates if p != float("inf")]
        old_candidates = [p for p in old_candidates if p != float("inf")]

        if new_candidates:
            total_books_new_raw += min(new_candidates)
        if old_candidates:
            total_books_old_raw += min(old_candidates)

    # подготовим список ids для ответа
    book_landing_ids = sorted(all_book_landings.keys())

    # 6) Карточки книжных лендингов
    def _landing_authors(bl: BookLanding):
        return [{"id": a.id, "name": a.name, "photo": a.photo or ""} for a in (b.authors or [])]

    def _landing_tags(bl: BookLanding):
        return [{"id": t.id, "name": t.name, "slug": getattr(t, "slug", None)} for t in (b.tags or [])]

    # если у BookLanding есть галерея — адаптируй под свою модель;
    # здесь предполагается, что у тебя есть bl.gallery (список объектов/диктов)
    def _landing_gallery(bl: BookLanding):
        return getattr(bl, "gallery", []) or []

    book_landings_cards: List[dict] = []
    for bl_id in book_landing_ids:
        bl = all_book_landings[bl_id]
        book_ids_for_bl = [bk.id for bk in books_in_landing(db, bl)]
        books_for_bl = books_in_landing(db, bl)
        main_image = None
        if books_for_bl and getattr(books_for_bl[0], "cover_url", None):
            main_image = books_for_bl[0].cover_url
        else:
            # фолбэк на превью лендинга
            main_image = getattr(bl, "preview_photo", None)

        book_landings_cards.append({
            "id": bl.id,
            "landing_name": bl.landing_name,
            "slug": bl.page_name,
            "language": bl.language,
            "old_price": bl.old_price,
            "new_price": bl.new_price,
            "authors": _landing_authors(bl),
            "tags": _landing_tags(bl),
            "first_tag": bl.tags[0].name if getattr(bl, "tags", None) else None,
            "gallery": _landing_gallery(bl),
            "main_image": main_image,
            "book_ids": book_ids_for_bl,
        })

    # 7) Скидки (как было для new), + «old» суммы по сценариям
    courses_old_sum = 0.0
    books_old_sum = 0.0

    courses_price_discounted = round(total_new_price_courses * DISCOUNT_COURSES, 2)

    books_price_discounted = (
        round(total_books_new_raw * DISCOUNT_BOOKS, 2) if total_books_new_raw else None
    )
    combo_price_discounted = (
        round((total_new_price_courses + total_books_new_raw) * DISCOUNT_COURSES_BOOKS, 2)
        if total_books_new_raw else None
    )

    total_books_old_price = round(total_books_old_raw, 2) if total_books_old_raw else None
    total_courses_books_old_price = (
        round(total_old_price_courses + total_books_old_raw, 2)
        if total_books_old_raw else None
    )

    books_old_raw = 0.0
    for b in author.books:
        old_candidates = [
            safe_price(l.old_price)
            for l in b.landings
            if not l.is_hidden
        ]
        old_candidates = [p for p in old_candidates if p != float("inf")]
        if old_candidates:
            books_old_raw += min(old_candidates)

    # 8) Теги
    tags_from_landings = {t.name for l in kept_landings for t in l.tags}
    tags_from_books    = {t.name for b in author.books for t in getattr(b, "tags", [])}
    all_tags = tags_from_landings | tags_from_books

    # 9) Ответ
    return {
        "id": author.id,
        "name": author.name,
        "description": author.description,
        "photo": author.photo,
        "language": author.language,

        # курсовые лендинги
        "landings": landings_data,
        "landing_ids": landing_ids,

        # книжные лендинги
        "book_landings": book_landings_cards,
        "book_landing_ids": book_landing_ids,

        "course_ids": list(all_course_ids),
        "book_ids": sorted(all_book_ids),

        # книги (простые карточки книг — как было)
        "books": books_data or None,
        "books_count": len(all_book_ids) or None,

        # new (discounted)
        "total_new_price": courses_price_discounted,
        "total_books_price": books_price_discounted,
        "total_courses_books_price": combo_price_discounted,

        # old (без скидок)
        "total_old_price": round(total_old_price_courses, 2),
        "total_books_old_price": total_books_old_price,
        "total_courses_books_old_price": round(total_books_old_price + total_old_price_courses,2),
        "landing_count": len(landings_data),
        "tags": sorted(all_tags),
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
                selectinload(Author.books).selectinload(Author.landings),
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
        visible_books_count = len({
            b.id
            for b in a.books
            if any(not bl.is_hidden for bl in b.landings)
        })

        items.append(
            AuthorResponse(
                id=a.id,
                name=a.name,
                description=a.description,
                language=a.language,
                photo=a.photo,
                courses_count=len(unique_course_ids),
                books_count=visible_books_count or None,
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