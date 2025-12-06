"""
Сервис для агрегации фильтров и построения универсальных метаданных.

Предоставляет оптимизированные функции для:
- Построения базовых запросов с фильтрацией
- Агрегации данных для фильтров с учетом текущих фильтров
- Универсальное переиспользование для книг, курсов, авторов
"""

from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, Query, selectinload
from sqlalchemy import func, cast, Integer, and_, or_, exists, select, literal, Numeric as SqlNumeric
from decimal import Decimal

import re

from ..models.models_v2 import (
    BookLanding, Book, Author, Tag, Publisher, Landing, Course,
    BookFile, book_authors, book_tags, book_publishers,
    landing_authors, landing_tags, book_landing_books, landing_course
)
from ..schemas_v2.common import (
    FilterOption, MultiselectFilter, RangeFilter, 
    SortOption, CatalogFiltersMetadata,
    SelectedFilters, SelectedMultiselectValues, SelectedRangeValues
)


def build_book_landing_base_query(
    db: Session,
    language: Optional[str] = None,
    tags: Optional[List[int]] = None,
    formats: Optional[List[str]] = None,
    publisher_ids: Optional[List[int]] = None,
    author_ids: Optional[List[int]] = None,
    year_from: Optional[int] = None,
    year_to: Optional[int] = None,
    price_from: Optional[Decimal] = None,
    price_to: Optional[Decimal] = None,
    pages_from: Optional[int] = None,
    pages_to: Optional[int] = None,
    q: Optional[str] = None,
) -> Query:
    """
    Построение базового запроса BookLanding с применением всех фильтров.
    
    Возвращает Query, к которому можно добавить сортировку и пагинацию.
    """
    # Базовый запрос: только публичные лендинги с установленной ценой
    base = (
        db.query(BookLanding)
        .options(
            selectinload(BookLanding.books).selectinload(Book.authors),
            selectinload(BookLanding.books).selectinload(Book.tags),
            selectinload(BookLanding.books).selectinload(Book.publishers),
            selectinload(BookLanding.books).selectinload(Book.files),
        )
        .filter(BookLanding.is_hidden.is_(False))
        .filter(BookLanding.new_price.isnot(None))  # только с установленной ценой
    )
    
    # Фильтр по языку
    if language:
        base = base.filter(BookLanding.language == language.upper())
    
    # Поиск по названию
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(
            or_(
                BookLanding.landing_name.ilike(like),
                BookLanding.page_name.ilike(like)
            )
        )
    
    # Фильтр по тегам (любой из переданных тегов по ID)
    if tags:
        base = base.filter(
            BookLanding.books.any(
                Book.tags.any(Tag.id.in_(tags))
            )
        )
    
    # Фильтр по форматам (любой из переданных форматов)
    if formats:
        base = base.filter(
            BookLanding.books.any(
                Book.files.any(BookFile.file_format.in_(formats))
            )
        )
    
    # Фильтр по издателям
    if publisher_ids:
        base = base.filter(
            BookLanding.books.any(
                Book.publishers.any(Publisher.id.in_(publisher_ids))
            )
        )
    
    # Фильтр по авторам
    if author_ids:
        base = base.filter(
            BookLanding.books.any(
                Book.authors.any(Author.id.in_(author_ids))
            )
        )
    
    # Фильтр по году публикации
    # Используем and_() для объединения условий внутри .any()
    # и regexp для валидации формата (должен начинаться с 4 цифр)
    if year_from or year_to:
        if year_from:
            # publication_date может быть "2023" или "2023-01-01"
            base = base.filter(
                BookLanding.books.any(
                    and_(
                        Book.publication_date.isnot(None),
                        Book.publication_date.regexp_match('^[0-9]{4}'),
                        cast(func.left(Book.publication_date, 4), Integer) >= year_from
                    )
                )
            )
        if year_to:
            base = base.filter(
                BookLanding.books.any(
                    and_(
                        Book.publication_date.isnot(None),
                        Book.publication_date.regexp_match('^[0-9]{4}'),
                        cast(func.left(Book.publication_date, 4), Integer) <= year_to
                    )
                )
            )
    
    # Фильтр по цене (new_price)
    if price_from is not None:
        base = base.filter(BookLanding.new_price >= price_from)
    if price_to is not None:
        base = base.filter(BookLanding.new_price <= price_to)
    
    # Фильтр по количеству страниц (сумма страниц всех книг лендинга)
    # Это сложнее - нужно использовать подзапрос или having, но SQLAlchemy ORM не поддерживает having без group_by
    # Придется фильтровать после загрузки или использовать более сложный подзапрос
    # Для оптимизации сделаем через EXISTS с подзапросом
    if pages_from is not None or pages_to is not None:
        # Создаём подзапрос для подсчёта суммы страниц
        from ..models.models_v2 import book_landing_books
        
        subq = (
            select(book_landing_books.c.book_landing_id)
            .select_from(book_landing_books)
            .join(Book, book_landing_books.c.book_id == Book.id)
            .group_by(book_landing_books.c.book_landing_id)
        )
        
        if pages_from is not None:
            subq = subq.having(func.sum(func.coalesce(Book.page_count, 0)) >= pages_from)
        if pages_to is not None:
            subq = subq.having(func.sum(func.coalesce(Book.page_count, 0)) <= pages_to)
        
        base = base.filter(BookLanding.id.in_(subq))
    
    return base


def _prepend_selected_options(
    options: List[FilterOption],
    selected_options: List[FilterOption]
) -> List[FilterOption]:
    """
    Добавляет в начало списка только те выбранные опции, которых НЕТ в базовом списке.
    Опции, которые уже есть в базовом списке, остаются на своих местах.
    """
    if not selected_options:
        return options
    
    # Собираем ID/value опций, которые уже есть в базовом списке
    existing_ids = {opt.id for opt in options if opt.id is not None}
    existing_values = {opt.value for opt in options if opt.value is not None}
    
    # Отбираем только те выбранные опции, которых НЕТ в базовом списке
    new_selected_options = [
        opt for opt in selected_options
        if (opt.id is not None and opt.id not in existing_ids) or
           (opt.value is not None and opt.value not in existing_values)
    ]
    
    # Добавляем новые выбранные в начало, базовый список остаётся без изменений
    return new_selected_options + options


def aggregate_book_filters(
    db: Session,
    base_query: Query,
    current_filters: Dict[str, Any],
    filter_limit: int = 50
) -> CatalogFiltersMetadata:
    """
    Агрегация метаданных фильтров для книжных лендингов.
    
    Считает количество элементов для каждого фильтра с учетом текущих фильтров.
    
    Args:
        db: Сессия БД
        base_query: Базовый запрос с примененными фильтрами
        current_filters: Словарь текущих фильтров для исключения при агрегации
    
    Returns:
        CatalogFiltersMetadata с заполненными фильтрами и сортировками
    """
    filters = {}
    selected = SelectedFilters()
    
    # Получаем ID лендингов, попадающих под текущие фильтры
    filtered_landing_ids = [landing.id for landing in base_query.with_entities(BookLanding.id).all()]
    
    # Даже если filtered_landing_ids пустой, продолжаем - покажем фильтры с count=0
    
    # ═══════════════════ Publishers ═══════════════════
    # Строим запрос без фильтра по publishers для агрегации
    query_without_publishers = build_book_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=current_filters.get('tags'),
        formats=current_filters.get('formats'),
        publisher_ids=None,  # Исключаем этот фильтр
        author_ids=current_filters.get('author_ids'),
        year_from=current_filters.get('year_from'),
        year_to=current_filters.get('year_to'),
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        pages_from=current_filters.get('pages_from'),
        pages_to=current_filters.get('pages_to'),
        q=current_filters.get('q'),
    )
    
    publisher_landing_ids = [lid.id for lid in query_without_publishers.with_entities(BookLanding.id).all()]
    
    # ═══════════════════ Publishers (с сохранением опций count=0) ═══════════════════
    from ..models.models_v2 import book_landing_books
    
    # Подсчет общего количества всех издателей
    total_publishers = db.query(func.count(Publisher.id)).scalar() or 0
    
    # Шаг 1: Получаем топ-N издателей по ОБЩЕМУ количеству книг (без фильтров)
    top_publishers_subq = (
        db.query(
            Publisher.id.label('publisher_id'),
            func.count(func.distinct(BookLanding.id)).label('total_cnt')
        )
        .select_from(Publisher)
        .join(book_publishers, Publisher.id == book_publishers.c.publisher_id)
        .join(Book, book_publishers.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(Publisher.id)
        .order_by(func.count(func.distinct(BookLanding.id)).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    # Шаг 2: Для этих топ-N считаем count с учётом текущих фильтров
    if publisher_landing_ids:
        filtered_counts_subq = (
            db.query(
                Publisher.id.label('publisher_id'),
                func.count(func.distinct(BookLanding.id)).label('filtered_cnt')
            )
            .select_from(Publisher)
            .join(book_publishers, Publisher.id == book_publishers.c.publisher_id)
            .join(Book, book_publishers.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.id.in_(publisher_landing_ids))
            .group_by(Publisher.id)
            .subquery()
        )
        
        # Объединяем: берём топ-N издателей и показываем их filtered count
        publishers_data = (
            db.query(
                Publisher.id,
                Publisher.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_publishers_subq, Publisher.id == top_publishers_subq.c.publisher_id)
            .outerjoin(filtered_counts_subq, Publisher.id == filtered_counts_subq.c.publisher_id)
            .order_by(top_publishers_subq.c.total_cnt.desc(), Publisher.name)
            .all()
        )
    else:
        # Если нет результатов фильтрации, показываем топ-N издателей с count=0
        publishers_data = (
            db.query(
                Publisher.id,
                Publisher.name,
                literal(0).label('count')
            )
            .join(top_publishers_subq, Publisher.id == top_publishers_subq.c.publisher_id)
            .order_by(top_publishers_subq.c.total_cnt.desc(), Publisher.name)
            .all()
        )
    
    # Получаем выбранные издатели из current_filters
    selected_publisher_ids = current_filters.get('publisher_ids') or []
    selected_publisher_options = []
    
    if selected_publisher_ids:
        # Получаем полные данные по выбранным издателям
        # Сначала получаем имена всех выбранных издателей (независимо от фильтров)
        selected_publishers_names = {
            row.id: row.name 
            for row in db.query(Publisher.id, Publisher.name).filter(Publisher.id.in_(selected_publisher_ids)).all()
        }
        
        # Затем получаем count с учётом текущих фильтров (кроме publisher_ids)
        selected_publishers_counts = {}
        if publisher_landing_ids:
            counts_data = (
                db.query(
                    Publisher.id,
                    func.count(func.distinct(BookLanding.id)).label('count')
                )
                .select_from(Publisher)
                .join(book_publishers, Publisher.id == book_publishers.c.publisher_id)
                .join(Book, book_publishers.c.book_id == Book.id)
                .join(book_landing_books, Book.id == book_landing_books.c.book_id)
                .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
                .filter(Publisher.id.in_(selected_publisher_ids))
                .filter(BookLanding.id.in_(publisher_landing_ids))
                .group_by(Publisher.id)
                .all()
            )
            selected_publishers_counts = {row.id: int(row.count) for row in counts_data}
        
        # Формируем опции: для каждого выбранного издателя показываем имя и count
        selected_publisher_options = [
            FilterOption(id=pub_id, name=pub_name, count=selected_publishers_counts.get(pub_id, 0))
            for pub_id, pub_name in selected_publishers_names.items()
        ]
        selected.publishers = SelectedMultiselectValues(options=selected_publisher_options)
    
    # Базовые опции издателей
    base_publisher_options = [
        FilterOption(id=pub_id, name=pub_name, count=int(count))
        for pub_id, pub_name, count in publishers_data
    ]
    
    # Добавляем выбранные в начало списка
    final_publisher_options = _prepend_selected_options(base_publisher_options, selected_publisher_options)
    
    filters['publishers'] = MultiselectFilter(
        label="Издатели",
        param_name="publisher_ids",
        options=final_publisher_options,
        has_more=total_publishers > filter_limit,
        total_count=total_publishers,
        search_endpoint="/api/filters/publishers/search?context=books"
    )
    
    # ═══════════════════ Authors (с сохранением опций count=0) ═══════════════════
    query_without_authors = build_book_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=current_filters.get('tags'),
        formats=current_filters.get('formats'),
        publisher_ids=current_filters.get('publisher_ids'),
        author_ids=None,  # Исключаем этот фильтр
        year_from=current_filters.get('year_from'),
        year_to=current_filters.get('year_to'),
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        pages_from=current_filters.get('pages_from'),
        pages_to=current_filters.get('pages_to'),
        q=current_filters.get('q'),
    )
    
    author_landing_ids = [lid.id for lid in query_without_authors.with_entities(BookLanding.id).all()]
    
    # Подсчет общего количества всех авторов
    total_authors = db.query(func.count(Author.id)).scalar() or 0
    
    # Шаг 1: Получаем топ-N авторов по ОБЩЕМУ количеству книг (без фильтров)
    top_authors_subq = (
        db.query(
            Author.id.label('author_id'),
            func.count(func.distinct(BookLanding.id)).label('total_cnt')
        )
        .select_from(Author)
        .join(book_authors, Author.id == book_authors.c.author_id)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(Author.id)
        .order_by(func.count(func.distinct(BookLanding.id)).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    # Шаг 2: Для этих топ-N считаем count с учётом текущих фильтров
    if author_landing_ids:
        filtered_counts_subq = (
            db.query(
                Author.id.label('author_id'),
                func.count(func.distinct(BookLanding.id)).label('filtered_cnt')
            )
            .select_from(Author)
            .join(book_authors, Author.id == book_authors.c.author_id)
            .join(Book, book_authors.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.id.in_(author_landing_ids))
            .group_by(Author.id)
            .subquery()
        )
        
        # Объединяем: берём топ-N авторов и показываем их filtered count
        authors_data = (
            db.query(
                Author.id,
                Author.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_authors_subq, Author.id == top_authors_subq.c.author_id)
            .outerjoin(filtered_counts_subq, Author.id == filtered_counts_subq.c.author_id)
            .order_by(top_authors_subq.c.total_cnt.desc(), Author.name)
            .all()
        )
    else:
        # Если нет результатов фильтрации, показываем топ-N авторов с count=0
        authors_data = (
            db.query(
                Author.id,
                Author.name,
                literal(0).label('count')
            )
            .join(top_authors_subq, Author.id == top_authors_subq.c.author_id)
            .order_by(top_authors_subq.c.total_cnt.desc(), Author.name)
            .all()
        )
    
    # Получаем выбранные авторы из current_filters
    selected_author_ids = current_filters.get('author_ids') or []
    selected_author_options = []
    
    if selected_author_ids:
        # Получаем полные данные по выбранным авторам
        # Сначала получаем имена всех выбранных авторов (независимо от фильтров)
        selected_authors_names = {
            row.id: row.name 
            for row in db.query(Author.id, Author.name).filter(Author.id.in_(selected_author_ids)).all()
        }
        
        # Затем получаем count с учётом текущих фильтров (кроме author_ids)
        selected_authors_counts = {}
        if author_landing_ids:
            counts_data = (
                db.query(
                    Author.id,
                    func.count(func.distinct(BookLanding.id)).label('count')
                )
                .select_from(Author)
                .join(book_authors, Author.id == book_authors.c.author_id)
                .join(Book, book_authors.c.book_id == Book.id)
                .join(book_landing_books, Book.id == book_landing_books.c.book_id)
                .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
                .filter(Author.id.in_(selected_author_ids))
                .filter(BookLanding.id.in_(author_landing_ids))
                .group_by(Author.id)
                .all()
            )
            selected_authors_counts = {row.id: int(row.count) for row in counts_data}
        
        # Формируем опции: для каждого выбранного автора показываем имя и count
        selected_author_options = [
            FilterOption(id=auth_id, name=auth_name, count=selected_authors_counts.get(auth_id, 0))
            for auth_id, auth_name in selected_authors_names.items()
        ]
        selected.authors = SelectedMultiselectValues(options=selected_author_options)
    
    # Базовые опции авторов
    base_author_options = [
        FilterOption(id=auth_id, name=auth_name, count=int(count))
        for auth_id, auth_name, count in authors_data
    ]
    
    # Добавляем выбранные в начало списка
    final_author_options = _prepend_selected_options(base_author_options, selected_author_options)
    
    filters['authors'] = MultiselectFilter(
        label="Авторы",
        param_name="author_ids",
        options=final_author_options,
        has_more=total_authors > filter_limit,
        total_count=total_authors,
        search_endpoint="/api/filters/authors/search?context=books"
    )
    
    # ═══════════════════ Tags (с сохранением опций count=0) ═══════════════════
    query_without_tags = build_book_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=None,  # Исключаем этот фильтр
        formats=current_filters.get('formats'),
        publisher_ids=current_filters.get('publisher_ids'),
        author_ids=current_filters.get('author_ids'),
        year_from=current_filters.get('year_from'),
        year_to=current_filters.get('year_to'),
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        pages_from=current_filters.get('pages_from'),
        pages_to=current_filters.get('pages_to'),
        q=current_filters.get('q'),
    )
    
    tag_landing_ids = [lid.id for lid in query_without_tags.with_entities(BookLanding.id).all()]
    
    # Подсчет общего количества всех тегов
    total_tags = db.query(func.count(Tag.id)).scalar() or 0
    
    # Шаг 1: Получаем топ-N тегов по ОБЩЕМУ количеству книг (без фильтров)
    top_tags_subq = (
        db.query(
            Tag.id.label('tag_id'),
            func.count(func.distinct(BookLanding.id)).label('total_cnt')
        )
        .select_from(Tag)
        .join(book_tags, Tag.id == book_tags.c.tag_id)
        .join(Book, book_tags.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(Tag.id)
        .order_by(func.count(func.distinct(BookLanding.id)).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    # Шаг 2: Для этих топ-N считаем count с учётом текущих фильтров
    if tag_landing_ids:
        filtered_counts_subq = (
            db.query(
                Tag.id.label('tag_id'),
                func.count(func.distinct(BookLanding.id)).label('filtered_cnt')
            )
            .select_from(Tag)
            .join(book_tags, Tag.id == book_tags.c.tag_id)
            .join(Book, book_tags.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.id.in_(tag_landing_ids))
            .group_by(Tag.id)
            .subquery()
        )
        
        # Объединяем: берём топ-N тегов и показываем их filtered count
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .outerjoin(filtered_counts_subq, Tag.id == filtered_counts_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    else:
        # Если нет результатов фильтрации, показываем топ-N тегов с count=0
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                literal(0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    
    # Получаем выбранные теги из current_filters
    selected_tag_ids = current_filters.get('tags') or []
    selected_tag_options = []
    
    if selected_tag_ids:
        # Получаем полные данные по выбранным тегам
        # Сначала получаем имена всех выбранных тегов (независимо от фильтров)
        selected_tags_names = {
            row.id: row.name 
            for row in db.query(Tag.id, Tag.name).filter(Tag.id.in_(selected_tag_ids)).all()
        }
        
        # Затем получаем count с учётом текущих фильтров (кроме tags)
        selected_tags_counts = {}
        if tag_landing_ids:
            counts_data = (
                db.query(
                    Tag.id,
                    func.count(func.distinct(BookLanding.id)).label('count')
                )
                .select_from(Tag)
                .join(book_tags, Tag.id == book_tags.c.tag_id)
                .join(Book, book_tags.c.book_id == Book.id)
                .join(book_landing_books, Book.id == book_landing_books.c.book_id)
                .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
                .filter(Tag.id.in_(selected_tag_ids))
                .filter(BookLanding.id.in_(tag_landing_ids))
                .group_by(Tag.id)
                .all()
            )
            selected_tags_counts = {row.id: int(row.count) for row in counts_data}
        
        # Формируем опции: для каждого выбранного тега показываем имя и count
        selected_tag_options = [
            FilterOption(id=tag_id, name=tag_name, count=selected_tags_counts.get(tag_id, 0))
            for tag_id, tag_name in selected_tags_names.items()
        ]
        selected.tags = SelectedMultiselectValues(options=selected_tag_options)
    
    # Базовые опции тегов
    base_tag_options = [
        FilterOption(id=tag_id, name=tag_name, count=int(count))
        for tag_id, tag_name, count in tags_data
    ]
    
    # Добавляем выбранные в начало списка
    final_tag_options = _prepend_selected_options(base_tag_options, selected_tag_options)
    
    filters['tags'] = MultiselectFilter(
        label="Теги",
        param_name="tags",
        options=final_tag_options,
        has_more=total_tags > filter_limit,
        total_count=total_tags,
        search_endpoint="/api/filters/tags/search?context=books"
    )
    
    # ═══════════════════ Formats (с сохранением опций count=0) ═══════════════════
    query_without_formats = build_book_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=current_filters.get('tags'),
        formats=None,  # Исключаем этот фильтр
        publisher_ids=current_filters.get('publisher_ids'),
        author_ids=current_filters.get('author_ids'),
        year_from=current_filters.get('year_from'),
        year_to=current_filters.get('year_to'),
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        pages_from=current_filters.get('pages_from'),
        pages_to=current_filters.get('pages_to'),
        q=current_filters.get('q'),
    )
    
    format_landing_ids = [lid.id for lid in query_without_formats.with_entities(BookLanding.id).all()]
    
    from ..models.models_v2 import book_landing_books, BookFileFormat
    
    # Получаем все доступные форматы из enum
    all_formats = [fmt.value for fmt in BookFileFormat]
    
    if format_landing_ids:
        # Считаем count для каждого формата с учётом фильтров
        formats_data_dict = {}
        formats_data_raw = (
            db.query(
                BookFile.file_format,
                func.count(func.distinct(BookLanding.id)).label('count')
            )
            .select_from(BookFile)
            .join(Book, BookFile.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.id.in_(format_landing_ids))
            .filter(BookFile.s3_url.isnot(None))
            .group_by(BookFile.file_format)
            .all()
        )
        
        for fmt, count in formats_data_raw:
            fmt_value = fmt.value if hasattr(fmt, 'value') else str(fmt)
            formats_data_dict[fmt_value] = count
        
        # Формируем опции для всех форматов, даже если count=0
        formats_options = [
            FilterOption(
                value=fmt,
                name=fmt,
                count=formats_data_dict.get(fmt, 0)
            )
            for fmt in all_formats
        ]
    else:
        # Если нет результатов фильтрации, показываем все форматы с count=0
        formats_options = [
            FilterOption(value=fmt, name=fmt, count=0)
            for fmt in all_formats
        ]
    
    # Получаем выбранные форматы из current_filters
    selected_format_values = current_filters.get('formats') or []
    selected_format_options = []
    
    if selected_format_values:
        # Для форматов используем value вместо id
        selected_format_options = [
            opt for opt in formats_options
            if opt.value in selected_format_values
        ]
        selected.formats = SelectedMultiselectValues(options=selected_format_options)
    
    # Добавляем выбранные в начало списка
    final_format_options = _prepend_selected_options(formats_options, selected_format_options)
    
    filters['formats'] = MultiselectFilter(
        label="Форматы",
        param_name="formats",
        options=final_format_options
    )
    
    # ═══════════════════ Year Range (всегда показываем) ═══════════════════
    # Получаем общий диапазон годов из ВСЕХ книг (без фильтров)
    # Добавляем проверку на валидный формат года (начинается с 4 цифр)
    year_range = (
        db.query(
            func.min(cast(func.left(Book.publication_date, 4), Integer)).label('min_year'),
            func.max(cast(func.left(Book.publication_date, 4), Integer)).label('max_year')
        )
        .select_from(Book)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .filter(Book.publication_date.isnot(None))
        .filter(Book.publication_date.regexp_match('^[0-9]{4}'))
        .first()
    )
    
    if year_range and year_range.min_year and year_range.max_year:
        filters['year'] = RangeFilter(
            label="Год публикации",
            param_name_from="year_from",
            param_name_to="year_to",
            min=int(year_range.min_year),
            max=int(year_range.max_year),
            unit="year"
        )
    
    # Сохраняем выбранные значения для year
    year_from_val = current_filters.get('year_from')
    year_to_val = current_filters.get('year_to')
    if year_from_val is not None or year_to_val is not None:
        selected.year = SelectedRangeValues(
            value_from=year_from_val,
            value_to=year_to_val
        )
    
    # ═══════════════════ Price Range (всегда показываем) ═══════════════════
    # Получаем общий диапазон цен из ВСЕХ книжных лендингов (без фильтров)
    # Явный CAST к DECIMAL для корректного числового сравнения (избегаем строковой сортировки)
    price_range = (
        db.query(
            func.min(cast(BookLanding.new_price, SqlNumeric(10, 2))).label('min_price'),
            func.max(cast(BookLanding.new_price, SqlNumeric(10, 2))).label('max_price')
        )
        .filter(BookLanding.is_hidden.is_(False))
        .filter(BookLanding.new_price.isnot(None))
        .first()
    )
    
    if price_range and price_range.min_price and price_range.max_price:
        filters['price'] = RangeFilter(
            label="Цена",
            param_name_from="price_from",
            param_name_to="price_to",
            min=float(price_range.min_price),
            max=float(price_range.max_price),
            unit="USD"
        )
    
    # Сохраняем выбранные значения для price
    price_from_val = current_filters.get('price_from')
    price_to_val = current_filters.get('price_to')
    if price_from_val is not None or price_to_val is not None:
        selected.price = SelectedRangeValues(
            value_from=float(price_from_val) if price_from_val is not None else None,
            value_to=float(price_to_val) if price_to_val is not None else None
        )
    
    # ═══════════════════ Pages Range (всегда показываем) ═══════════════════
    # Получаем общий диапазон страниц из ВСЕХ книжных лендингов (без фильтров)
    # Сначала создаём подзапрос для подсчёта суммы страниц по каждому лендингу
    subq = (
        db.query(
            func.sum(func.coalesce(Book.page_count, 0)).label('total_pages')
        )
        .select_from(book_landing_books)
        .join(Book, book_landing_books.c.book_id == Book.id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(book_landing_books.c.book_landing_id)
        .subquery()
    )
    
    # Теперь берём MIN и MAX от этих сумм
    pages_range = (
        db.query(
            func.min(subq.c.total_pages).label('min_pages'),
            func.max(subq.c.total_pages).label('max_pages')
        )
        .first()
    )
    
    if pages_range and pages_range.min_pages is not None and pages_range.max_pages is not None:
        filters['pages'] = RangeFilter(
            label="Количество страниц",
            param_name_from="pages_from",
            param_name_to="pages_to",
            min=int(pages_range.min_pages) if pages_range.min_pages else 0,
            max=int(pages_range.max_pages) if pages_range.max_pages else 0,
            unit="pages"
        )
    
    # Сохраняем выбранные значения для pages
    pages_from_val = current_filters.get('pages_from')
    pages_to_val = current_filters.get('pages_to')
    if pages_from_val is not None or pages_to_val is not None:
        selected.pages = SelectedRangeValues(
            value_from=pages_from_val,
            value_to=pages_to_val
        )
    
    # Проверяем, есть ли хотя бы один выбранный фильтр
    has_selected = any([
        selected.publishers, selected.authors, selected.tags, selected.formats,
        selected.year, selected.price, selected.pages
    ])
    
    return CatalogFiltersMetadata(
        filters=filters,
        available_sorts=_get_sort_options(),
        selected=selected if has_selected else None
    )


def _get_sort_options() -> List[SortOption]:
    """Возвращает список доступных опций сортировки для книжных лендингов."""
    return [
        SortOption(value="price_asc", label="Цена: по возрастанию"),
        SortOption(value="price_desc", label="Цена: по убыванию"),
        SortOption(value="pages_asc", label="Страниц: по возрастанию"),
        SortOption(value="pages_desc", label="Страниц: по убыванию"),
        SortOption(value="year_asc", label="Год: сначала старые"),
        SortOption(value="year_desc", label="Год: сначала новые"),
        SortOption(value="new_asc", label="Новизна: сначала старые"),
        SortOption(value="new_desc", label="Новизна: сначала новые"),
        SortOption(value="popular_asc", label="Популярность: по возрастанию"),
        SortOption(value="popular_desc", label="Популярность: по убыванию"),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════ АВТОРЫ: Фильтры и агрегация ═══════════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════


def build_author_base_query(
    db: Session,
    language: Optional[str] = None,
    tags: Optional[List[int]] = None,
    courses_from: Optional[int] = None,
    courses_to: Optional[int] = None,
    books_from: Optional[int] = None,
    books_to: Optional[int] = None,
    q: Optional[str] = None,
) -> Query:
    """
    Построение базового запроса Author с применением всех фильтров.
    
    Возвращает Query[Author], к которому можно добавить сортировку и пагинацию.
    
    Фильтры:
    - language: язык автора
    - tags: ID тегов (из курсовых лендингов или книг автора)
    - courses_from/courses_to: диапазон количества уникальных курсов
    - books_from/books_to: диапазон количества книг с видимыми лендингами
    - q: поиск по имени автора
    """
    from ..models.models_v2 import Course, landing_course
    
    base = (
        db.query(Author)
        .options(
            selectinload(Author.landings).selectinload(Landing.courses),
            selectinload(Author.landings).selectinload(Landing.tags),
            selectinload(Author.books).selectinload(Book.landings),
            selectinload(Author.books).selectinload(Book.tags),
        )
    )
    
    # Фильтр по языку автора
    if language:
        base = base.filter(Author.language == language.upper())
    
    # Поиск по имени
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(Author.name.ilike(like))
    
    # Фильтр по тегам (автор связан с тегом через Landing.tags или Book.tags)
    if tags:
        # Автор имеет тег, если:
        # 1. Любой из его курсовых лендингов содержит этот тег
        # 2. Или любая из его книг содержит этот тег
        base = base.filter(
            or_(
                Author.landings.any(
                    Landing.tags.any(Tag.id.in_(tags))
                ),
                Author.books.any(
                    Book.tags.any(Tag.id.in_(tags))
                )
            )
        )
    
    # Фильтр по количеству курсов (уникальных, с учётом языка лендинга)
    # Нужен подзапрос для подсчёта уникальных курсов
    if courses_from is not None or courses_to is not None:
        # Подзапрос: считаем уникальные курсы для каждого автора
        # через landing_authors → landings → landing_course → courses
        courses_q = (
            db.query(
                landing_authors.c.author_id,
                func.count(func.distinct(landing_course.c.course_id)).label('courses_cnt')
            )
            .select_from(landing_authors)
            .join(Landing, landing_authors.c.landing_id == Landing.id)
            .join(landing_course, Landing.id == landing_course.c.landing_id)
            .filter(Landing.is_hidden.is_(False))
        )
        # Фильтруем по языку лендинга, если передан language
        if language:
            courses_q = courses_q.filter(Landing.language == language.upper())
        courses_count_subq = courses_q.group_by(landing_authors.c.author_id).subquery()
        
        base = base.outerjoin(courses_count_subq, Author.id == courses_count_subq.c.author_id)
        
        if courses_from is not None:
            base = base.filter(func.coalesce(courses_count_subq.c.courses_cnt, 0) >= courses_from)
        if courses_to is not None:
            base = base.filter(func.coalesce(courses_count_subq.c.courses_cnt, 0) <= courses_to)
    
    # Фильтр по количеству книг (с видимыми BookLanding, с учётом языка)
    if books_from is not None or books_to is not None:
        # Подзапрос: считаем книги автора, у которых есть хотя бы один видимый BookLanding
        books_q = (
            db.query(
                book_authors.c.author_id,
                func.count(func.distinct(Book.id)).label('books_cnt')
            )
            .select_from(book_authors)
            .join(Book, book_authors.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.is_hidden.is_(False))
        )
        # Фильтруем по языку книжного лендинга, если передан language
        if language:
            books_q = books_q.filter(BookLanding.language == language.upper())
        books_count_subq = books_q.group_by(book_authors.c.author_id).subquery()
        
        base = base.outerjoin(books_count_subq, Author.id == books_count_subq.c.author_id)
        
        if books_from is not None:
            base = base.filter(func.coalesce(books_count_subq.c.books_cnt, 0) >= books_from)
        if books_to is not None:
            base = base.filter(func.coalesce(books_count_subq.c.books_cnt, 0) <= books_to)
    
    return base


def aggregate_author_filters(
    db: Session,
    base_query: Query,
    current_filters: Dict[str, Any],
    filter_limit: int = 50
) -> CatalogFiltersMetadata:
    """
    Агрегация метаданных фильтров для страницы авторов.
    
    Считает количество авторов для каждого фильтра с учетом текущих фильтров.
    
    Фильтры для авторов:
    - tags: теги (из курсов и книг)
    - courses: диапазон количества курсов
    - books: диапазон количества книг
    """
    from ..models.models_v2 import Course, landing_course
    
    filters = {}
    selected = SelectedFilters()
    
    # Получаем ID авторов, попадающих под текущие фильтры
    filtered_author_ids = [a.id for a in base_query.with_entities(Author.id).all()]
    
    # ═══════════════════ Tags ═══════════════════
    # Строим запрос без фильтра по tags для агрегации
    query_without_tags = build_author_base_query(
        db,
        language=current_filters.get('language'),
        tags=None,  # Исключаем этот фильтр
        courses_from=current_filters.get('courses_from'),
        courses_to=current_filters.get('courses_to'),
        books_from=current_filters.get('books_from'),
        books_to=current_filters.get('books_to'),
        q=current_filters.get('q'),
    )
    
    tag_author_ids = [a.id for a in query_without_tags.with_entities(Author.id).all()]
    
    # Подсчет общего количества всех тегов
    total_tags = db.query(func.count(Tag.id)).scalar() or 0
    
    # Теги приходят из двух источников: Landing.tags и Book.tags
    # Для каждого тега считаем количество авторов, у которых он есть
    
    # Шаг 1: Получаем топ-N тегов по ОБЩЕМУ количеству авторов (без фильтров)
    # Объединяем теги из курсовых лендингов и книг
    tags_from_landings = (
        db.query(
            Tag.id.label('tag_id'),
            func.count(func.distinct(Author.id)).label('author_cnt')
        )
        .select_from(Tag)
        .join(landing_tags, Tag.id == landing_tags.c.tag_id)
        .join(Landing, landing_tags.c.landing_id == Landing.id)
        .join(landing_authors, Landing.id == landing_authors.c.landing_id)
        .join(Author, landing_authors.c.author_id == Author.id)
        .filter(Landing.is_hidden.is_(False))
        .group_by(Tag.id)
    )
    
    tags_from_books = (
        db.query(
            Tag.id.label('tag_id'),
            func.count(func.distinct(Author.id)).label('author_cnt')
        )
        .select_from(Tag)
        .join(book_tags, Tag.id == book_tags.c.tag_id)
        .join(Book, book_tags.c.book_id == Book.id)
        .join(book_authors, Book.id == book_authors.c.book_id)
        .join(Author, book_authors.c.author_id == Author.id)
        .group_by(Tag.id)
    )
    
    # Объединяем и суммируем (union с группировкой)
    combined_tags = tags_from_landings.union_all(tags_from_books).subquery()
    
    top_tags_subq = (
        db.query(
            combined_tags.c.tag_id,
            func.sum(combined_tags.c.author_cnt).label('total_cnt')
        )
        .group_by(combined_tags.c.tag_id)
        .order_by(func.sum(combined_tags.c.author_cnt).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    # Шаг 2: Для этих топ-N считаем count с учётом текущих фильтров
    if tag_author_ids:
        # Теги из курсовых лендингов отфильтрованных авторов
        filtered_tags_landings = (
            db.query(
                Tag.id.label('tag_id'),
                func.count(func.distinct(Author.id)).label('author_cnt')
            )
            .select_from(Tag)
            .join(landing_tags, Tag.id == landing_tags.c.tag_id)
            .join(Landing, landing_tags.c.landing_id == Landing.id)
            .join(landing_authors, Landing.id == landing_authors.c.landing_id)
            .join(Author, landing_authors.c.author_id == Author.id)
            .filter(Landing.is_hidden.is_(False))
            .filter(Author.id.in_(tag_author_ids))
            .group_by(Tag.id)
        )
        
        filtered_tags_books = (
            db.query(
                Tag.id.label('tag_id'),
                func.count(func.distinct(Author.id)).label('author_cnt')
            )
            .select_from(Tag)
            .join(book_tags, Tag.id == book_tags.c.tag_id)
            .join(Book, book_tags.c.book_id == Book.id)
            .join(book_authors, Book.id == book_authors.c.book_id)
            .join(Author, book_authors.c.author_id == Author.id)
            .filter(Author.id.in_(tag_author_ids))
            .group_by(Tag.id)
        )
        
        combined_filtered = filtered_tags_landings.union_all(filtered_tags_books).subquery()
        
        filtered_counts_subq = (
            db.query(
                combined_filtered.c.tag_id,
                func.sum(combined_filtered.c.author_cnt).label('filtered_cnt')
            )
            .group_by(combined_filtered.c.tag_id)
            .subquery()
        )
        
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .outerjoin(filtered_counts_subq, Tag.id == filtered_counts_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    else:
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                literal(0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    
    # Получаем выбранные теги из current_filters
    selected_tag_ids = current_filters.get('tags') or []
    selected_tag_options = []
    
    if selected_tag_ids:
        selected_tags_names = {
            row.id: row.name 
            for row in db.query(Tag.id, Tag.name).filter(Tag.id.in_(selected_tag_ids)).all()
        }
        
        # count для выбранных тегов (без фильтра по tags)
        selected_tags_counts = {}
        if tag_author_ids:
            # Аналогично основному подсчёту
            sel_tags_landings = (
                db.query(
                    Tag.id.label('tag_id'),
                    func.count(func.distinct(Author.id)).label('author_cnt')
                )
                .select_from(Tag)
                .join(landing_tags, Tag.id == landing_tags.c.tag_id)
                .join(Landing, landing_tags.c.landing_id == Landing.id)
                .join(landing_authors, Landing.id == landing_authors.c.landing_id)
                .join(Author, landing_authors.c.author_id == Author.id)
                .filter(Landing.is_hidden.is_(False))
                .filter(Tag.id.in_(selected_tag_ids))
                .filter(Author.id.in_(tag_author_ids))
                .group_by(Tag.id)
            )
            
            sel_tags_books = (
                db.query(
                    Tag.id.label('tag_id'),
                    func.count(func.distinct(Author.id)).label('author_cnt')
                )
                .select_from(Tag)
                .join(book_tags, Tag.id == book_tags.c.tag_id)
                .join(Book, book_tags.c.book_id == Book.id)
                .join(book_authors, Book.id == book_authors.c.book_id)
                .join(Author, book_authors.c.author_id == Author.id)
                .filter(Tag.id.in_(selected_tag_ids))
                .filter(Author.id.in_(tag_author_ids))
                .group_by(Tag.id)
            )
            
            combined_sel = sel_tags_landings.union_all(sel_tags_books).subquery()
            counts_data = (
                db.query(
                    combined_sel.c.tag_id,
                    func.sum(combined_sel.c.author_cnt).label('count')
                )
                .group_by(combined_sel.c.tag_id)
                .all()
            )
            selected_tags_counts = {row.tag_id: int(row.count) for row in counts_data}
        
        selected_tag_options = [
            FilterOption(id=tag_id, name=tag_name, count=selected_tags_counts.get(tag_id, 0))
            for tag_id, tag_name in selected_tags_names.items()
        ]
        selected.tags = SelectedMultiselectValues(options=selected_tag_options)
    
    base_tag_options = [
        FilterOption(id=tag_id, name=tag_name, count=int(count))
        for tag_id, tag_name, count in tags_data
    ]
    
    final_tag_options = _prepend_selected_options(base_tag_options, selected_tag_options)
    
    filters['tags'] = MultiselectFilter(
        label="Теги",
        param_name="tags",
        options=final_tag_options,
        has_more=total_tags > filter_limit,
        total_count=total_tags,
        search_endpoint="/api/filters/tags/search?context=authors"
    )
    
    # ═══════════════════ Courses Range ═══════════════════
    # Диапазон количества курсов у авторов (с учётом языка лендинга)
    language = current_filters.get('language')
    
    courses_per_author_q = (
        db.query(
            landing_authors.c.author_id,
            func.count(func.distinct(landing_course.c.course_id)).label('courses_cnt')
        )
        .select_from(landing_authors)
        .join(Landing, landing_authors.c.landing_id == Landing.id)
        .join(landing_course, Landing.id == landing_course.c.landing_id)
        .filter(Landing.is_hidden.is_(False))
    )
    if language:
        courses_per_author_q = courses_per_author_q.filter(Landing.language == language.upper())
    courses_per_author = courses_per_author_q.group_by(landing_authors.c.author_id).subquery()
    
    courses_range = (
        db.query(
            func.min(courses_per_author.c.courses_cnt).label('min_courses'),
            func.max(courses_per_author.c.courses_cnt).label('max_courses')
        )
        .first()
    )
    
    if courses_range and courses_range.min_courses is not None and courses_range.max_courses is not None:
        filters['courses'] = RangeFilter(
            label="Количество курсов",
            param_name_from="courses_from",
            param_name_to="courses_to",
            min=int(courses_range.min_courses) if courses_range.min_courses else 0,
            max=int(courses_range.max_courses) if courses_range.max_courses else 0,
            unit="courses"
        )
    
    # Сохраняем выбранные значения для courses
    courses_from_val = current_filters.get('courses_from')
    courses_to_val = current_filters.get('courses_to')
    if courses_from_val is not None or courses_to_val is not None:
        # Используем общее поле для range-фильтров - добавим в SelectedFilters
        # Но в текущей схеме нет courses, поэтому используем расширение
        pass  # Пока не сохраняем, т.к. нет поля в SelectedFilters
    
    # ═══════════════════ Books Range ═══════════════════
    # Диапазон количества книг у авторов (с учётом языка книжного лендинга)
    books_per_author_q = (
        db.query(
            book_authors.c.author_id,
            func.count(func.distinct(Book.id)).label('books_cnt')
        )
        .select_from(book_authors)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
    )
    if language:
        books_per_author_q = books_per_author_q.filter(BookLanding.language == language.upper())
    books_per_author = books_per_author_q.group_by(book_authors.c.author_id).subquery()
    
    books_range = (
        db.query(
            func.min(books_per_author.c.books_cnt).label('min_books'),
            func.max(books_per_author.c.books_cnt).label('max_books')
        )
        .first()
    )
    
    if books_range and books_range.min_books is not None and books_range.max_books is not None:
        filters['books'] = RangeFilter(
            label="Количество книг",
            param_name_from="books_from",
            param_name_to="books_to",
            min=int(books_range.min_books) if books_range.min_books else 0,
            max=int(books_range.max_books) if books_range.max_books else 0,
            unit="books"
        )
    
    # Проверяем, есть ли хотя бы один выбранный фильтр
    has_selected = any([selected.tags])
    
    return CatalogFiltersMetadata(
        filters=filters,
        available_sorts=_get_author_sort_options(),
        selected=selected if has_selected else None
    )


def _get_author_sort_options() -> List[SortOption]:
    """Возвращает список доступных опций сортировки для страницы авторов."""
    return [
        SortOption(value="popular_desc", label="Популярность: по убыванию"),
        SortOption(value="popular_asc", label="Популярность: по возрастанию"),
        SortOption(value="price_asc", label="Цена: по возрастанию"),
        SortOption(value="price_desc", label="Цена: по убыванию"),
        SortOption(value="courses_desc", label="Курсов: по убыванию"),
        SortOption(value="courses_asc", label="Курсов: по возрастанию"),
        SortOption(value="books_desc", label="Книг: по убыванию"),
        SortOption(value="books_asc", label="Книг: по возрастанию"),
        SortOption(value="name_asc", label="По алфавиту: А-Я"),
        SortOption(value="name_desc", label="По алфавиту: Я-А"),
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════ КУРСЫ (ЛЕНДИНГИ): Фильтры и агрегация ═════════════════════
# ═══════════════════════════════════════════════════════════════════════════════

def count_lessons_from_sections(sections: dict | list | None) -> int:
    """
    Подсчитывает количество уроков (lesson_name) из JSON поля sections курса.
    
    Структура sections может быть:
    - dict: {"1": {"section_name": "...", "lessons": [...]}, ...}
    - list: [{"section_name": "...", "lessons": [...]}, ...]
    
    Возвращает суммарное количество уроков.
    """
    if not sections:
        return 0
    
    total = 0
    try:
        if isinstance(sections, dict):
            for sec_data in sections.values():
                if isinstance(sec_data, dict):
                    lessons = sec_data.get("lessons", [])
                    if isinstance(lessons, list):
                        total += len(lessons)
        elif isinstance(sections, list):
            for sec_data in sections:
                if isinstance(sec_data, dict):
                    lessons = sec_data.get("lessons", [])
                    if isinstance(lessons, list):
                        total += len(lessons)
    except Exception:
        pass
    
    return total


def parse_duration_to_minutes(duration_str: str | None) -> int:
    """
    Парсит строку длительности в минуты.
    
    Примеры:
    - "13 h 39 min" -> 819
    - "10 h 30 min" -> 630
    - "20 hours" -> 1200
    - "10 ore e 50 minuti" -> 650 (итальянский)
    - "11 hours 54 minutes" -> 714
    - "19 ч 38 мин" -> 1178 (русский)
    - "19 часов 45 минут" -> 1185
    
    Возвращает 0 если не удалось распарсить.
    """
    if not duration_str:
        return 0
    
    duration_str = duration_str.strip().lower()
    
    # Паттерны для часов в разных языках
    hour_patterns = [
        r'(\d+)\s*(?:h|hours?|hrs?|ч|час[а-я]*|ore?|horas?)',
    ]
    
    # Паттерны для минут в разных языках
    minute_patterns = [
        r'(\d+)\s*(?:m|min|mins?|minutes?|мин[а-я]*|minuti?|minutos?)',
    ]
    
    hours = 0
    minutes = 0
    
    # Ищем часы
    for pattern in hour_patterns:
        match = re.search(pattern, duration_str)
        if match:
            hours = int(match.group(1))
            break
    
    # Ищем минуты
    for pattern in minute_patterns:
        match = re.search(pattern, duration_str)
        if match:
            minutes = int(match.group(1))
            break
    
    return hours * 60 + minutes


def calculate_landing_lessons_count(db: Session, landing_id: int) -> int:
    """
    Подсчитывает количество уроков для лендинга через связанные курсы.
    
    Перебирает все курсы лендинга и суммирует уроки из JSON поля sections.
    """
    courses = (
        db.query(Course.sections)
        .join(landing_course, Course.id == landing_course.c.course_id)
        .filter(landing_course.c.landing_id == landing_id)
        .all()
    )
    
    total = 0
    for (sections,) in courses:
        total += count_lessons_from_sections(sections)
    
    return total


def calculate_landing_duration_minutes(db: Session, landing_id: int) -> int:
    """
    Возвращает длительность лендинга в минутах.
    
    Берёт поле duration из лендинга и парсит его.
    """
    landing = db.query(Landing.duration).filter(Landing.id == landing_id).first()
    if not landing or not landing.duration:
        return 0
    
    return parse_duration_to_minutes(landing.duration)


def build_landing_base_query(
    db: Session,
    language: Optional[str] = None,
    tags: Optional[List[int]] = None,
    author_ids: Optional[List[int]] = None,
    price_from: Optional[float] = None,
    price_to: Optional[float] = None,
    lessons_from: Optional[int] = None,
    lessons_to: Optional[int] = None,
    q: Optional[str] = None,
) -> Query:
    """
    Построение базового запроса Landing с применением всех фильтров.
    
    Возвращает Query, к которому можно добавить сортировку и пагинацию.
    """
    # Базовый запрос: только публичные лендинги
    base = (
        db.query(Landing)
        .options(
            selectinload(Landing.authors),
            selectinload(Landing.tags),
            selectinload(Landing.courses),
        )
        .filter(Landing.is_hidden.is_(False))
    )
    
    # Фильтр по языку
    if language:
        base = base.filter(Landing.language == language.upper())
    
    # Поиск по названию
    if q:
        like = f"%{q.strip()}%"
        base = base.filter(
            or_(
                Landing.landing_name.ilike(like),
                Landing.page_name.ilike(like)
            )
        )
    
    # Фильтр по тегам (любой из переданных тегов по ID)
    if tags:
        base = base.filter(
            Landing.tags.any(Tag.id.in_(tags))
        )
    
    # Фильтр по авторам
    if author_ids:
        base = base.filter(
            Landing.authors.any(Author.id.in_(author_ids))
        )
    
    # Фильтр по цене (new_price - строка, кастим к числу)
    if price_from is not None:
        base = base.filter(
            cast(Landing.new_price, SqlNumeric(10, 2)) >= price_from
        )
    if price_to is not None:
        base = base.filter(
            cast(Landing.new_price, SqlNumeric(10, 2)) <= price_to
        )
    
    # Фильтр по количеству уроков
    # Уроки считаются из JSON поля sections связанных курсов
    if lessons_from is not None or lessons_to is not None:
        # Получаем ID лендингов, соответствующих фильтру по урокам
        landing_ids_with_lessons = _get_landing_ids_by_lessons_count(
            db, lessons_from, lessons_to
        )
        if landing_ids_with_lessons is not None:
            base = base.filter(Landing.id.in_(landing_ids_with_lessons))
    
    return base


def _get_landing_ids_by_lessons_count(
    db: Session,
    lessons_from: Optional[int],
    lessons_to: Optional[int],
) -> Optional[List[int]]:
    """
    Возвращает список ID лендингов, у которых сумма уроков попадает в диапазон.
    
    Уроки считаются из JSON поля sections всех связанных курсов.
    """
    if lessons_from is None and lessons_to is None:
        return None
    
    # Получаем все видимые лендинги с их курсами
    landings_data = (
        db.query(Landing.id, Course.sections)
        .join(landing_course, Landing.id == landing_course.c.landing_id)
        .join(Course, landing_course.c.course_id == Course.id)
        .filter(Landing.is_hidden.is_(False))
        .all()
    )
    
    # Группируем по landing_id и считаем уроки
    from collections import defaultdict
    landing_lessons: Dict[int, int] = defaultdict(int)
    
    for landing_id, sections in landings_data:
        lessons_count = count_lessons_from_sections(sections)
        landing_lessons[landing_id] += lessons_count
    
    # Фильтруем по диапазону
    result_ids = []
    for landing_id, total_lessons in landing_lessons.items():
        if lessons_from is not None and total_lessons < lessons_from:
            continue
        if lessons_to is not None and total_lessons > lessons_to:
            continue
        result_ids.append(landing_id)
    
    return result_ids


def _calculate_lessons_range(db: Session) -> Dict[str, Optional[int]]:
    """
    Подсчитывает диапазон количества уроков для всех видимых лендингов.
    
    Возвращает: {'min': N, 'max': M}
    """
    from collections import defaultdict
    
    # Получаем все видимые лендинги с их курсами
    landings_data = (
        db.query(Landing.id, Course.sections)
        .join(landing_course, Landing.id == landing_course.c.landing_id)
        .join(Course, landing_course.c.course_id == Course.id)
        .filter(Landing.is_hidden.is_(False))
        .all()
    )
    
    if not landings_data:
        return {'min': None, 'max': None}
    
    # Группируем по landing_id и считаем уроки
    landing_lessons: Dict[int, int] = defaultdict(int)
    
    for landing_id, sections in landings_data:
        lessons_count = count_lessons_from_sections(sections)
        landing_lessons[landing_id] += lessons_count
    
    if not landing_lessons:
        return {'min': None, 'max': None}
    
    lessons_counts = list(landing_lessons.values())
    return {
        'min': min(lessons_counts),
        'max': max(lessons_counts)
    }


def aggregate_landing_filters(
    db: Session,
    base_query: Query,
    current_filters: Dict[str, Any],
    filter_limit: int = 50,
    include_recommend: bool = False,
) -> CatalogFiltersMetadata:
    """
    Агрегация метаданных фильтров для курсовых лендингов.
    
    Считает количество элементов для каждого фильтра с учетом текущих фильтров.
    
    Args:
        db: Сессия БД
        base_query: Базовый запрос с примененными фильтрами
        current_filters: Словарь текущих фильтров для исключения при агрегации
        include_recommend: Включить сортировку "Рекомендации" (только для авторизованных)
    
    Returns:
        CatalogFiltersMetadata с заполненными фильтрами и сортировками
    """
    filters = {}
    selected = SelectedFilters()
    
    # Получаем ID лендингов, попадающих под текущие фильтры
    filtered_landing_ids = [landing.id for landing in base_query.with_entities(Landing.id).all()]
    
    # ═══════════════════ Authors ═══════════════════
    query_without_authors = build_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=current_filters.get('tags'),
        author_ids=None,  # Исключаем этот фильтр
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        lessons_from=current_filters.get('lessons_from'),
        lessons_to=current_filters.get('lessons_to'),
        q=current_filters.get('q'),
    )
    
    author_landing_ids = [lid.id for lid in query_without_authors.with_entities(Landing.id).all()]
    
    # Подсчет общего количества всех авторов
    total_authors = db.query(func.count(Author.id)).scalar() or 0
    
    # Топ-N авторов по ОБЩЕМУ количеству лендингов (без фильтров)
    top_authors_subq = (
        db.query(
            Author.id.label('author_id'),
            func.count(func.distinct(Landing.id)).label('total_cnt')
        )
        .select_from(Author)
        .join(landing_authors, Author.id == landing_authors.c.author_id)
        .join(Landing, landing_authors.c.landing_id == Landing.id)
        .filter(Landing.is_hidden.is_(False))
        .group_by(Author.id)
        .order_by(func.count(func.distinct(Landing.id)).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    if author_landing_ids:
        filtered_counts_subq = (
            db.query(
                Author.id.label('author_id'),
                func.count(func.distinct(Landing.id)).label('filtered_cnt')
            )
            .select_from(Author)
            .join(landing_authors, Author.id == landing_authors.c.author_id)
            .join(Landing, landing_authors.c.landing_id == Landing.id)
            .filter(Landing.id.in_(author_landing_ids))
            .group_by(Author.id)
            .subquery()
        )
        
        authors_data = (
            db.query(
                Author.id,
                Author.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_authors_subq, Author.id == top_authors_subq.c.author_id)
            .outerjoin(filtered_counts_subq, Author.id == filtered_counts_subq.c.author_id)
            .order_by(top_authors_subq.c.total_cnt.desc(), Author.name)
            .all()
        )
    else:
        authors_data = (
            db.query(
                Author.id,
                Author.name,
                literal(0).label('count')
            )
            .join(top_authors_subq, Author.id == top_authors_subq.c.author_id)
            .order_by(top_authors_subq.c.total_cnt.desc(), Author.name)
            .all()
        )
    
    # Получаем выбранные авторы из current_filters
    selected_author_ids = current_filters.get('author_ids') or []
    selected_author_options = []
    
    if selected_author_ids:
        selected_authors_names = {
            row.id: row.name 
            for row in db.query(Author.id, Author.name).filter(Author.id.in_(selected_author_ids)).all()
        }
        
        selected_authors_counts = {}
        if author_landing_ids:
            counts_data = (
                db.query(
                    Author.id,
                    func.count(func.distinct(Landing.id)).label('count')
                )
                .select_from(Author)
                .join(landing_authors, Author.id == landing_authors.c.author_id)
                .join(Landing, landing_authors.c.landing_id == Landing.id)
                .filter(Author.id.in_(selected_author_ids))
                .filter(Landing.id.in_(author_landing_ids))
                .group_by(Author.id)
                .all()
            )
            selected_authors_counts = {row.id: int(row.count) for row in counts_data}
        
        selected_author_options = [
            FilterOption(id=auth_id, name=auth_name, count=selected_authors_counts.get(auth_id, 0))
            for auth_id, auth_name in selected_authors_names.items()
        ]
        selected.authors = SelectedMultiselectValues(options=selected_author_options)
    
    base_author_options = [
        FilterOption(id=auth_id, name=auth_name, count=int(count))
        for auth_id, auth_name, count in authors_data
    ]
    
    final_author_options = _prepend_selected_options(base_author_options, selected_author_options)
    
    filters['authors'] = MultiselectFilter(
        label="Авторы",
        param_name="author_ids",
        options=final_author_options,
        has_more=total_authors > filter_limit,
        total_count=total_authors,
        search_endpoint="/api/filters/authors/search?context=courses"
    )
    
    # ═══════════════════ Tags ═══════════════════
    query_without_tags = build_landing_base_query(
        db,
        language=current_filters.get('language'),
        tags=None,  # Исключаем этот фильтр
        author_ids=current_filters.get('author_ids'),
        price_from=current_filters.get('price_from'),
        price_to=current_filters.get('price_to'),
        lessons_from=current_filters.get('lessons_from'),
        lessons_to=current_filters.get('lessons_to'),
        q=current_filters.get('q'),
    )
    
    tag_landing_ids = [lid.id for lid in query_without_tags.with_entities(Landing.id).all()]
    
    total_tags = db.query(func.count(Tag.id)).scalar() or 0
    
    top_tags_subq = (
        db.query(
            Tag.id.label('tag_id'),
            func.count(func.distinct(Landing.id)).label('total_cnt')
        )
        .select_from(Tag)
        .join(landing_tags, Tag.id == landing_tags.c.tag_id)
        .join(Landing, landing_tags.c.landing_id == Landing.id)
        .filter(Landing.is_hidden.is_(False))
        .group_by(Tag.id)
        .order_by(func.count(func.distinct(Landing.id)).desc())
        .limit(filter_limit)
        .subquery()
    )
    
    if tag_landing_ids:
        filtered_counts_subq = (
            db.query(
                Tag.id.label('tag_id'),
                func.count(func.distinct(Landing.id)).label('filtered_cnt')
            )
            .select_from(Tag)
            .join(landing_tags, Tag.id == landing_tags.c.tag_id)
            .join(Landing, landing_tags.c.landing_id == Landing.id)
            .filter(Landing.id.in_(tag_landing_ids))
            .group_by(Tag.id)
            .subquery()
        )
        
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                func.coalesce(filtered_counts_subq.c.filtered_cnt, 0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .outerjoin(filtered_counts_subq, Tag.id == filtered_counts_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    else:
        tags_data = (
            db.query(
                Tag.id,
                Tag.name,
                literal(0).label('count')
            )
            .join(top_tags_subq, Tag.id == top_tags_subq.c.tag_id)
            .order_by(top_tags_subq.c.total_cnt.desc(), Tag.name)
            .all()
        )
    
    selected_tag_ids = current_filters.get('tags') or []
    selected_tag_options = []
    
    if selected_tag_ids:
        selected_tags_names = {
            row.id: row.name 
            for row in db.query(Tag.id, Tag.name).filter(Tag.id.in_(selected_tag_ids)).all()
        }
        
        selected_tags_counts = {}
        if tag_landing_ids:
            counts_data = (
                db.query(
                    Tag.id,
                    func.count(func.distinct(Landing.id)).label('count')
                )
                .select_from(Tag)
                .join(landing_tags, Tag.id == landing_tags.c.tag_id)
                .join(Landing, landing_tags.c.landing_id == Landing.id)
                .filter(Tag.id.in_(selected_tag_ids))
                .filter(Landing.id.in_(tag_landing_ids))
                .group_by(Tag.id)
                .all()
            )
            selected_tags_counts = {row.id: int(row.count) for row in counts_data}
        
        selected_tag_options = [
            FilterOption(id=tag_id, name=tag_name, count=selected_tags_counts.get(tag_id, 0))
            for tag_id, tag_name in selected_tags_names.items()
        ]
        selected.tags = SelectedMultiselectValues(options=selected_tag_options)
    
    base_tag_options = [
        FilterOption(id=tag_id, name=tag_name, count=int(count))
        for tag_id, tag_name, count in tags_data
    ]
    
    final_tag_options = _prepend_selected_options(base_tag_options, selected_tag_options)
    
    filters['tags'] = MultiselectFilter(
        label="Теги",
        param_name="tags",
        options=final_tag_options,
        has_more=total_tags > filter_limit,
        total_count=total_tags,
        search_endpoint="/api/filters/tags/search?context=courses"
    )
    
    # ═══════════════════ Price Range ═══════════════════
    # Явный CAST для числового сравнения
    price_range = (
        db.query(
            func.min(cast(Landing.new_price, SqlNumeric(10, 2))).label('min_price'),
            func.max(cast(Landing.new_price, SqlNumeric(10, 2))).label('max_price')
        )
        .filter(Landing.is_hidden.is_(False))
        .filter(Landing.new_price.isnot(None))
        .filter(Landing.new_price != '')
        .first()
    )
    
    if price_range and price_range.min_price is not None and price_range.max_price is not None:
        filters['price'] = RangeFilter(
            label="Цена",
            param_name_from="price_from",
            param_name_to="price_to",
            min=float(price_range.min_price),
            max=float(price_range.max_price),
            unit="USD"
        )
    
    price_from_val = current_filters.get('price_from')
    price_to_val = current_filters.get('price_to')
    if price_from_val is not None or price_to_val is not None:
        selected.price = SelectedRangeValues(
            value_from=float(price_from_val) if price_from_val is not None else None,
            value_to=float(price_to_val) if price_to_val is not None else None
        )
    
    # ═══════════════════ Lessons Range ═══════════════════
    # Подсчитываем диапазон количества уроков из JSON sections курсов
    lessons_range_data = _calculate_lessons_range(db)
    
    if lessons_range_data and lessons_range_data['min'] is not None and lessons_range_data['max'] is not None:
        filters['lessons'] = RangeFilter(
            label="Количество уроков",
            param_name_from="lessons_from",
            param_name_to="lessons_to",
            min=lessons_range_data['min'],
            max=lessons_range_data['max'],
            unit="lessons"
        )
    
    lessons_from_val = current_filters.get('lessons_from')
    lessons_to_val = current_filters.get('lessons_to')
    if lessons_from_val is not None or lessons_to_val is not None:
        selected.lessons = SelectedRangeValues(
            value_from=int(lessons_from_val) if lessons_from_val is not None else None,
            value_to=int(lessons_to_val) if lessons_to_val is not None else None
        )
    
    # Проверяем, есть ли хотя бы один выбранный фильтр
    has_selected = any([selected.authors, selected.tags, selected.price, selected.lessons])
    
    return CatalogFiltersMetadata(
        filters=filters,
        available_sorts=_get_landing_sort_options(include_recommend=include_recommend),
        selected=selected if has_selected else None
    )


def _get_landing_sort_options(include_recommend: bool = False) -> List[SortOption]:
    """
    Возвращает список доступных опций сортировки для курсовых лендингов.
    
    Args:
        include_recommend: Включить сортировку "Рекомендации" (только для авторизованных)
    """
    options = [
        SortOption(value="popular_desc", label="Популярность: по убыванию"),
        SortOption(value="popular_asc", label="Популярность: по возрастанию"),
        SortOption(value="price_asc", label="Цена: по возрастанию"),
        SortOption(value="price_desc", label="Цена: по убыванию"),
        SortOption(value="duration_asc", label="Длительность: по возрастанию"),
        SortOption(value="duration_desc", label="Длительность: по убыванию"),
        SortOption(value="new_asc", label="Новизна: сначала старые"),
        SortOption(value="new_desc", label="Новизна: сначала новые"),
        SortOption(value="lessons_asc", label="Уроков: по возрастанию"),
        SortOption(value="lessons_desc", label="Уроков: по убыванию"),
    ]
    
    # Добавляем рекомендации в начало списка, если пользователь авторизован
    if include_recommend:
        options.insert(0, SortOption(value="recommend", label="Рекомендации"))
    
    return options

