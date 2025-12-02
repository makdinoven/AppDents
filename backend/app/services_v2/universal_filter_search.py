"""
Универсальный сервис для поиска по фильтрам.

Поддерживает поиск авторов, издателей, тегов для разных контекстов:
- books (книги)
- courses (курсы)
- authors_page (страница авторов)
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import func
from decimal import Decimal

from ..models.models_v2 import (
    Author, Publisher, Tag, Book, BookLanding,
    book_authors, book_publishers, book_tags
)
from ..schemas_v2.common import FilterSearchResponse, FilterOption, FilterContext
from .filter_aggregation_service import build_book_landing_base_query


# ═══════════════════ Поиск авторов ═══════════════════

def search_authors(
    db: Session,
    context: FilterContext,
    q: Optional[str] = None,
    limit: int = 20,
    **filters
) -> FilterSearchResponse:
    """
    Универсальный поиск авторов с учётом контекста.
    
    Args:
        db: Сессия БД
        context: Контекст поиска (books/courses/authors_page)
        q: Поисковый запрос
        limit: Максимальное количество результатов
        **filters: Дополнительные фильтры в зависимости от контекста
    
    Returns:
        FilterSearchResponse с найденными авторами
    """
    if context == FilterContext.BOOKS:
        return _search_authors_for_books(db, q, limit, **filters)
    elif context == FilterContext.COURSES:
        return _search_authors_for_courses(db, q, limit, **filters)
    elif context == FilterContext.AUTHORS_PAGE:
        return _search_authors_for_authors_page(db, q, limit, **filters)
    else:
        raise ValueError(f"Unknown context: {context}")


def _search_authors_for_books(
    db: Session,
    q: Optional[str],
    limit: int,
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
    formats: Optional[List[str]] = None,
    publisher_ids: Optional[List[int]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[Decimal] = None,
    price_to: Optional[Decimal] = None,
    pages_from: Optional[int] = None,
    pages_to: Optional[int] = None,
) -> FilterSearchResponse:
    """Поиск авторов для каталога книг."""
    
    # Строим базовый запрос без фильтра по авторам
    base_query = build_book_landing_base_query(
        db=db,
        language=language,
        tags=tags,
        formats=formats,
        publisher_ids=publisher_ids,
        author_ids=None,  # Исключаем фильтр по авторам
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        q=None,
    )
    
    landing_ids = [lid.id for lid in base_query.with_entities(BookLanding.id).all()]
    
    if not landing_ids:
        return FilterSearchResponse(total=0, options=[])
    
    from ..models.models_v2 import book_landing_books
    
    # Базовый запрос для авторов
    author_query = (
        db.query(
            Author.id,
            Author.name,
            func.count(func.distinct(BookLanding.id)).label('count')
        )
        .select_from(Author)
        .join(book_authors, Author.id == book_authors.c.author_id)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.id.in_(landing_ids))
    )
    
    # Применяем поисковый запрос
    if q:
        author_query = author_query.filter(Author.name.ilike(f"%{q}%"))
    
    # Подсчет total (до группировки, чтобы избежать MultipleResultsFound)
    total = author_query.with_entities(func.count(func.distinct(Author.id))).scalar() or 0
    
    # Группировка и получение результатов с сортировкой по популярности
    authors_data = (
        author_query
        .group_by(Author.id, Author.name)
        .order_by(func.count(func.distinct(BookLanding.id)).desc(), Author.name)
        .limit(limit)
        .all()
    )
    
    options = [
        FilterOption(id=auth_id, name=auth_name, count=count)
        for auth_id, auth_name, count in authors_data
    ]
    
    return FilterSearchResponse(total=total, options=options)


def _search_authors_for_courses(
    db: Session,
    q: Optional[str],
    limit: int,
    **filters
) -> FilterSearchResponse:
    """
    Поиск авторов (лекторов) для каталога курсов.
    
    TODO: Реализовать когда будет готова логика фильтрации курсов.
    """
    # Заглушка для будущей реализации
    return FilterSearchResponse(total=0, options=[])


def _search_authors_for_authors_page(
    db: Session,
    q: Optional[str],
    limit: int,
    **filters
) -> FilterSearchResponse:
    """
    Поиск авторов для страницы авторов.
    
    TODO: Реализовать когда будет готова страница авторов.
    """
    # Заглушка для будущей реализации
    return FilterSearchResponse(total=0, options=[])


# ═══════════════════ Поиск издателей ═══════════════════

def search_publishers(
    db: Session,
    context: FilterContext,
    q: Optional[str] = None,
    limit: int = 20,
    **filters
) -> FilterSearchResponse:
    """
    Универсальный поиск издателей с учётом контекста.
    """
    if context == FilterContext.BOOKS:
        return _search_publishers_for_books(db, q, limit, **filters)
    elif context == FilterContext.COURSES:
        # Для курсов издателей обычно нет, но можно добавить при необходимости
        return FilterSearchResponse(total=0, options=[])
    else:
        raise ValueError(f"Unknown context: {context}")


def _search_publishers_for_books(
    db: Session,
    q: Optional[str],
    limit: int,
    language: Optional[str] = None,
    tags: Optional[List[str]] = None,
    formats: Optional[List[str]] = None,
    author_ids: Optional[List[int]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[Decimal] = None,
    price_to: Optional[Decimal] = None,
    pages_from: Optional[int] = None,
    pages_to: Optional[int] = None,
) -> FilterSearchResponse:
    """Поиск издателей для каталога книг."""
    
    # Строим базовый запрос без фильтра по издателям
    base_query = build_book_landing_base_query(
        db=db,
        language=language,
        tags=tags,
        formats=formats,
        publisher_ids=None,  # Исключаем фильтр по издателям
        author_ids=author_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        q=None,
    )
    
    landing_ids = [lid.id for lid in base_query.with_entities(BookLanding.id).all()]
    
    if not landing_ids:
        return FilterSearchResponse(total=0, options=[])
    
    from ..models.models_v2 import book_landing_books
    
    # Базовый запрос для издателей
    publisher_query = (
        db.query(
            Publisher.id,
            Publisher.name,
            func.count(func.distinct(BookLanding.id)).label('count')
        )
        .select_from(Publisher)
        .join(book_publishers, Publisher.id == book_publishers.c.publisher_id)
        .join(Book, book_publishers.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.id.in_(landing_ids))
    )
    
    # Применяем поисковый запрос
    if q:
        publisher_query = publisher_query.filter(Publisher.name.ilike(f"%{q}%"))
    
    # Подсчет total (до группировки, чтобы избежать MultipleResultsFound)
    total = publisher_query.with_entities(func.count(func.distinct(Publisher.id))).scalar() or 0
    
    # Группировка и получение результатов с сортировкой по популярности
    publishers_data = (
        publisher_query
        .group_by(Publisher.id, Publisher.name)
        .order_by(func.count(func.distinct(BookLanding.id)).desc(), Publisher.name)
        .limit(limit)
        .all()
    )
    
    options = [
        FilterOption(id=pub_id, name=pub_name, count=count)
        for pub_id, pub_name, count in publishers_data
    ]
    
    return FilterSearchResponse(total=total, options=options)


# ═══════════════════ Поиск тегов ═══════════════════

def search_tags(
    db: Session,
    context: FilterContext,
    q: Optional[str] = None,
    limit: int = 20,
    **filters
) -> FilterSearchResponse:
    """
    Универсальный поиск тегов с учётом контекста.
    """
    if context == FilterContext.BOOKS:
        return _search_tags_for_books(db, q, limit, **filters)
    elif context == FilterContext.COURSES:
        return _search_tags_for_courses(db, q, limit, **filters)
    else:
        raise ValueError(f"Unknown context: {context}")


def _search_tags_for_books(
    db: Session,
    q: Optional[str],
    limit: int,
    language: Optional[str] = None,
    formats: Optional[List[str]] = None,
    publisher_ids: Optional[List[int]] = None,
    author_ids: Optional[List[int]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[Decimal] = None,
    price_to: Optional[Decimal] = None,
    pages_from: Optional[int] = None,
    pages_to: Optional[int] = None,
) -> FilterSearchResponse:
    """Поиск тегов для каталога книг."""
    
    # Строим базовый запрос без фильтра по тегам
    base_query = build_book_landing_base_query(
        db=db,
        language=language,
        tags=None,  # Исключаем фильтр по тегам
        formats=formats,
        publisher_ids=publisher_ids,
        author_ids=author_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        q=None,
    )
    
    landing_ids = [lid.id for lid in base_query.with_entities(BookLanding.id).all()]
    
    if not landing_ids:
        return FilterSearchResponse(total=0, options=[])
    
    from ..models.models_v2 import book_landing_books
    
    # Базовый запрос для тегов
    tag_query = (
        db.query(
            Tag.id,
            Tag.name,
            func.count(func.distinct(BookLanding.id)).label('count')
        )
        .select_from(Tag)
        .join(book_tags, Tag.id == book_tags.c.tag_id)
        .join(Book, book_tags.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.id.in_(landing_ids))
    )
    
    # Применяем поисковый запрос
    if q:
        tag_query = tag_query.filter(Tag.name.ilike(f"%{q}%"))
    
    # Подсчет total (до группировки, чтобы избежать MultipleResultsFound)
    total = tag_query.with_entities(func.count(func.distinct(Tag.id))).scalar() or 0
    
    # Группировка и получение результатов с сортировкой по популярности
    tags_data = (
        tag_query
        .group_by(Tag.id, Tag.name)
        .order_by(func.count(func.distinct(BookLanding.id)).desc(), Tag.name)
        .limit(limit)
        .all()
    )
    
    options = [
        FilterOption(id=tag_id, name=tag_name, count=count)
        for tag_id, tag_name, count in tags_data
    ]
    
    return FilterSearchResponse(total=total, options=options)


def _search_tags_for_courses(
    db: Session,
    q: Optional[str],
    limit: int,
    **filters
) -> FilterSearchResponse:
    """
    Поиск тегов для каталога курсов.
    
    TODO: Реализовать когда будет готова логика фильтрации курсов.
    """
    # Заглушка для будущей реализации
    return FilterSearchResponse(total=0, options=[])

