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

from ..models.models_v2 import (
    BookLanding, Book, Author, Tag, Publisher, 
    BookFile, book_authors, book_tags, book_publishers
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
    Добавляет выбранные опции в начало списка, убирая дубликаты.
    """
    if not selected_options:
        return options
    
    # Собираем ID/value выбранных опций
    selected_ids = {opt.id for opt in selected_options if opt.id is not None}
    selected_values = {opt.value for opt in selected_options if opt.value is not None}
    
    # Фильтруем существующие опции, убирая дубликаты
    filtered_options = [
        opt for opt in options
        if (opt.id is None or opt.id not in selected_ids) and
           (opt.value is None or opt.value not in selected_values)
    ]
    
    # Возвращаем выбранные первыми
    return selected_options + filtered_options


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
        # Получаем полные данные по выбранным издателям с count
        if publisher_landing_ids:
            selected_publishers_data = (
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
                .filter(Publisher.id.in_(selected_publisher_ids))
                .filter(BookLanding.id.in_(publisher_landing_ids))
                .group_by(Publisher.id, Publisher.name)
                .all()
            )
        else:
            selected_publishers_data = (
                db.query(Publisher.id, Publisher.name, literal(0).label('count'))
                .filter(Publisher.id.in_(selected_publisher_ids))
                .all()
            )
        
        selected_publisher_options = [
            FilterOption(id=pub_id, name=pub_name, count=int(count))
            for pub_id, pub_name, count in selected_publishers_data
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
        # Получаем полные данные по выбранным авторам с count
        if author_landing_ids:
            selected_authors_data = (
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
                .filter(Author.id.in_(selected_author_ids))
                .filter(BookLanding.id.in_(author_landing_ids))
                .group_by(Author.id, Author.name)
                .all()
            )
        else:
            selected_authors_data = (
                db.query(Author.id, Author.name, literal(0).label('count'))
                .filter(Author.id.in_(selected_author_ids))
                .all()
            )
        
        selected_author_options = [
            FilterOption(id=auth_id, name=auth_name, count=int(count))
            for auth_id, auth_name, count in selected_authors_data
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
        # Получаем полные данные по выбранным тегам с count
        if tag_landing_ids:
            selected_tags_data = (
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
                .filter(Tag.id.in_(selected_tag_ids))
                .filter(BookLanding.id.in_(tag_landing_ids))
                .group_by(Tag.id, Tag.name)
                .all()
            )
        else:
            selected_tags_data = (
                db.query(Tag.id, Tag.name, literal(0).label('count'))
                .filter(Tag.id.in_(selected_tag_ids))
                .all()
            )
        
        selected_tag_options = [
            FilterOption(id=tag_id, name=tag_name, count=int(count))
            for tag_id, tag_name, count in selected_tags_data
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

