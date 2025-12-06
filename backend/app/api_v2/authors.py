import re
import unicodedata
from collections import defaultdict
from math import ceil
from typing import List, Optional, Set, Dict

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy import text, func, cast, Numeric as SqlNumeric, or_
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import (
    User, Author, Landing, Book, BookLanding, Tag,
    landing_authors, landing_course, book_authors, book_landing_books,
    landing_tags, book_tags
)
from ..schemas_v2.author import (
    AuthorResponse, AuthorCreate, AuthorUpdate, AuthorResponsePage,
    AuthorFullDetailResponse, AuthorsPage, AuthorCardV2Response, AuthorsCardsV2Response
)
from ..services_v2.author_service import (
    get_author_detail, create_author, update_author,
    delete_author, get_author_full_detail, list_authors_by_page, list_authors_search_paginated
)
from ..services_v2.filter_aggregation_service import (
    build_author_base_query, aggregate_author_filters
)

router = APIRouter()

@router.get(
    "/",
    response_model=AuthorsPage,
    summary="Список авторов с пагинацией по страницам"
)
def get_authors(
    language: Optional[str] = Query(
        None,
        description="Фильтр по языку (EN, RU, ES, PT, IT, AR)"
    ),
    sort: Optional[str] = Query(
        None,
        description="Параметр сортировки: 'id_desc' — по убыванию ID, иначе по популярности"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Номер страницы (начиная с 1)"
    ),
    size: int = Query(
        12,
        ge=1,
        description="Количество возвращаемых записей"
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Возвращает:
    {
        "total": <общее число авторов после фильтра>,
        "total_pages": <общее число страниц>,
        "page": <текущая страница>,
        "size": 12,  # фиксированный размер страницы
        "items": [ ...список авторов... ]
    }
    """
    return list_authors_by_page(db, page=page, size=size, language=language, sort=sort)

@router.get("/detail/{author_id}", response_model=AuthorResponse)
def get_author(author_id: int, db: Session = Depends(get_db)):
    return get_author_detail(db, author_id)

@router.post("/", response_model=AuthorResponse)
def create_new_author(
    author_data: AuthorCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    return create_author(db, author_data)

@router.put("/{author_id}", response_model=AuthorResponse)
def update_author_route(
    author_id: int,
    update_data: AuthorUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    return update_author(db, author_id, update_data)

@router.delete("/{author_id}", response_model=dict)
def delete_author_route(
    author_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    delete_author(db, author_id)
    return {"detail": "Author deleted successfully"}


def basic_clean_name(name: str) -> str:
    """
    Убирает из строки name приставки/суффиксы Dr./Prof. (в любом регистре) и множественные пробелы.
    Примеры:
      "Dr. Enrico Agliardi"  -> "Enrico Agliardi"
      "Filippo Fontana  Dr." -> "Filippo Fontana"
      "Kent HowellDr"        -> "Kent Howell"
      "DrEnrico"             -> "Enrico"
    """
    # Удаляем возможные префиксы Dr./Prof. в начале
    cleaned = re.sub(r'^(?:dr\.?\s*|prof\.?\s*)+', '', name, flags=re.IGNORECASE)
    # Удаляем возможные суффиксы Dr./Prof. в конце
    cleaned = re.sub(r'(?:\s*(?:dr\.?|prof\.?))+$', '', cleaned, flags=re.IGNORECASE)
    # Заменяем множественные пробелы одним
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned

# ----- Шаг 2: функция для «глубокой» нормализации, чтобы учитывать акценты и т. д. -----

def normalize_for_key(s: str) -> str:
    """
    Приводит строку s к виду, который максимально нейтрализует различия,
    которые MySQL колляция (case-insensitive, accent-insensitive и т.п.) может считать «одинаковыми».

    1. Удаляем префиксы Dr./Prof., лишние пробелы (через basic_clean_name).
    2. Приводим к NFKD (или NFKC) unicode формату, чтобы отделить диакритику (акценты) от базовых символов.
    3. Убираем все Combining Marks (напр. акценты, тильды), чтобы "Mãlo" -> "Malo".
    4. Приводим всё к нижнему регистру.
    5. (Опционально) можно убрать и другие невидимые символы (ZERO WIDTH SPACE и пр.).
    """
    # Сначала обычная очистка Dr./Prof.
    cleaned = basic_clean_name(s)

    # Нормализуем в NFKD (или NFKC — смотрите, что подходит для ваших данных)
    normed = unicodedata.normalize('NFKD', cleaned)
    # Убираем символы, принадлежащие категории "Mn" (Mark, Nonspacing), т.е. акценты, тильды и т.д.
    # Превращаем результат обратно в str
    without_accents = ''.join(ch for ch in normed if unicodedata.category(ch) != 'Mn')

    # Приводим к нижнему регистру
    lowercased = without_accents.lower()

    # Можно убрать «длинные» пробелы или невидимые символы, если боитесь, что они затесались:
    # Для простоты ограничимся trim() и заменим множественные пробелы на один
    final = re.sub(r'\s+', ' ', lowercased).strip()

    return final

# ----- Основной роут -----

@router.post("/remove_dr_and_prof_and_merge")
def remove_dr_and_prof_and_merge(db: Session = Depends(get_db), current_admin: User = Depends(require_roles("admin"))):
    """
    1. Считываем всех авторов.
    2. Для каждого считаем «ключ нормализации» (normalize_for_key).
    3. Группируем авторов по этому ключу.
    4. Для каждой группы (т. е. «по сути одинаковые» имена с точки зрения колляции):
       - Определяем «финальное» имя, которое хотим записать в authors.name,
         например: делаем .title() от «очищенной строки без акцентов» (или оставляем как-то иначе).
       - Проверяем, нет ли уже в базе (вне этой группы) автора с таким финальным именем:
         * Если есть, он станет «главным».
         * Если нет, возьмём автора с минимальным id из группы и проставим ему финальное имя.
       - Остальных авторов в группе сливаем: переносим связи landing_authors и удаляем из authors.
    5. Один общий commit в конце.
    """

    all_authors = db.query(Author).all()

    # Сгруппируем их по «ключу нормализации»
    grouped = defaultdict(list)
    for author in all_authors:
        group_key = normalize_for_key(author.name)
        grouped[group_key].append(author)

    # Готовим список всех операций по слиянию
    for group_key, authors_list in grouped.items():
        # Определим «очищенное» имя (без Dr./Prof., без лишних пробелов, но ещё до удаления акцентов)
        # Можно использовать просто basic_clean_name(authors_list[0].name)
        # Но для красоты возьмём «оригинал» первого автора, почистим Dr./Prof., пробелы:
        raw_cleaned = basic_clean_name(authors_list[0].name)

        # Определяем «финальное» имя для записи в БД
        # Например, сделаем каждое слово с заглавной буквы (title).
        # Если вам важен регистр «как в оригинале», можно придумать другую логику.
        final_name = raw_cleaned.title()

        # 1) Сначала проверяем: нет ли уже в БД (среди всех авторов, не только в этой группе)
        #    автора с таким именем. Если он есть, возьмём его как «главного».
        #    Почему это нужно? Потому что могли быть случаи, когда в БД уже существует
        #    какая-то запись c name = "Paulo Malo", а наши авторы были "dr. paulo malo" и "Paulo  Malo" и т.д.
        existing_main = (
            db.query(Author)
              .filter(Author.name == final_name)
              .first()
        )

        if existing_main:
            # Этот existing_main — может быть, даже не в нашей группе,
            # но мы хотим «слить» наших авторов на него.
            main_author = existing_main
        else:
            # Иначе берём автора с минимальным id в группе
            main_author = min(authors_list, key=lambda a: a.id)
            # Если у него имя != final_name, назначаем
            if main_author.name != final_name:
                main_author.name = final_name
                db.add(main_author)
                # Не коммитим пока, делаем всё в одной транзакции

        # 2) Теперь переносим связи у всех остальных авторов в группе на main_author
        for dup in authors_list:
            if dup.id == main_author.id:
                continue
            db.execute(
                text("""
                    UPDATE landing_authors
                    SET author_id = :main_id
                    WHERE author_id = :dup_id
                """),
                {"main_id": main_author.id, "dup_id": dup.id}
            )
            db.delete(dup)

    # Когда все группы обработаны, делаем один общий commit
    try:
        db.commit()
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=500,
            detail=f"Ошибка при финальном сохранении: {exc}"
        )

    return {"detail": "Очистка и слияние авторов завершены."}

@router.get("/full_detail/{author_id}", response_model=AuthorFullDetailResponse)
def full_detail(author_id: int, db: Session = Depends(get_db)):
    """
    Возвращает полную информацию по автору:
      - базовые поля (id, name, description, photo, language)
      - список его лендингов (old/new price, 1‑й тег, имя, slug, картинка, course_ids)
      - все course_ids по всем лендингам
      - суммарную new_price по всем лендингам
      - количество  лендингов
    """
    detail = get_author_full_detail(db, author_id)
    if detail is None:
        raise HTTPException(status_code=404, detail="Author not found")
    return detail

@router.get(
    "/search",
    response_model=AuthorsPage,
    summary="Поиск авторов с пагинацией"
)
def search_authors(
    q: str = Query(..., min_length=1, description="Строка поиска по имени автора"),
    language: Optional[str] = Query(
        None,
        description="Фильтр по языку (EN, RU, ES, PT, IT, AR)"
    ),
    page: int = Query(
        1,
        ge=1,
        description="Номер страницы (начиная с 1)"
    ),
    size: int = Query(
        12,
        ge=1,
        description="Количество возвращаемых записей"
    ),
    db: Session = Depends(get_db),
) -> dict:
    """
    Поиск авторов по подстроке в имени (case-insensitive).
    Возвращает тот же формат, что и обычный список:
    {
      total: <общее число совпадений>,
      total_pages: <число страниц при размере size=12>,
      page: <текущая страница>,
      size: 12,
      items: [ …авторы… ]
    }
    """
    return list_authors_search_paginated(
        db,
        search=q,
        page=page,
        size=size,
        language=language
    )


# ═══════════════════════════════════════════════════════════════════════════════
# ═══════════════════ V2: Карточки авторов с фильтрами ═════════════════════════
# ═══════════════════════════════════════════════════════════════════════════════

def _safe_price(value) -> float:
    """Безопасное преобразование цены в float."""
    try:
        return float(value) if value is not None else float("inf")
    except (ValueError, TypeError):
        return float("inf")


def _calculate_author_stats(
    db: Session,
    author: Author,
    lang_filter: Optional[List[str]] = None
) -> Dict:
    """
    Вычисляет статистику для автора:
    - courses_count: количество уникальных курсов
    - books_count: количество книг с видимыми лендингами
    - total_min_price: минимальная суммарная цена курсов + книг
    - popularity: сумма sales_count из Landing + BookLanding
    - tags: теги из курсов и книг
    """
    # Фильтруем лендинги по видимости и языку
    visible_landings = [
        l for l in (author.landings or [])
        if not l.is_hidden and (not lang_filter or l.language.upper() in lang_filter)
    ]
    
    # 1) Минимальная цена по каждому курсу
    min_price_by_course: Dict[int, float] = {}
    for l in visible_landings:
        price = _safe_price(l.new_price)
        for c in (l.courses or []):
            cid = c.id
            if cid not in min_price_by_course or price < min_price_by_course[cid]:
                min_price_by_course[cid] = price
    
    # 2) Оставляем только «дешёвые» лендинги (без дубликатов по курсам)
    kept_landings: List[Landing] = []
    for l in visible_landings:
        price = _safe_price(l.new_price)
        has_cheaper_alt = any(
            price > min_price_by_course.get(c.id, price)
            for c in (l.courses or [])
        )
        if not has_cheaper_alt:
            kept_landings.append(l)
    
    # 3) Уникальные курсы и теги из курсовых лендингов
    unique_course_ids: Set[int] = {c.id for l in kept_landings for c in (l.courses or [])}
    tags_from_landings: Set[str] = {t.name for l in kept_landings for t in (l.tags or [])}
    
    # 4) Книги с видимыми BookLanding
    visible_books = []
    min_price_by_book: Dict[int, float] = {}
    for b in (author.books or []):
        visible_bl = [
            bl for bl in (b.landings or [])
            if not bl.is_hidden and (not lang_filter or bl.language.upper() in lang_filter)
        ]
        if visible_bl:
            visible_books.append(b)
            # Минимальная цена для этой книги
            min_bl_price = min(_safe_price(bl.new_price) for bl in visible_bl)
            if min_bl_price != float("inf"):
                min_price_by_book[b.id] = min_bl_price
    
    books_count = len(visible_books)
    
    # Теги из книг
    tags_from_books: Set[str] = {t.name for b in (author.books or []) for t in (getattr(b, 'tags', []) or [])}
    all_tags = tags_from_landings | tags_from_books
    
    # 5) Суммарная минимальная цена (курсы + книги)
    total_courses_price = sum(
        p for p in min_price_by_course.values() if p != float("inf")
    )
    total_books_price = sum(
        p for p in min_price_by_book.values() if p != float("inf")
    )
    total_min_price = total_courses_price + total_books_price
    
    # 6) Популярность: сумма sales_count из Landing + BookLanding
    popularity = 0
    for l in kept_landings:
        popularity += (l.sales_count or 0)
    for b in visible_books:
        for bl in (b.landings or []):
            if not bl.is_hidden and (not lang_filter or bl.language.upper() in lang_filter):
                popularity += (bl.sales_count or 0)
    
    return {
        "courses_count": len(unique_course_ids),
        "books_count": books_count,
        "total_min_price": round(total_min_price, 2) if total_min_price > 0 else None,
        "popularity": popularity,
        "tags": sorted(all_tags),
    }


def _serialize_author_card_v2(
    db: Session,
    author: Author,
    lang_filter: Optional[List[str]] = None
) -> AuthorCardV2Response:
    """Сериализует автора в карточку V2."""
    stats = _calculate_author_stats(db, author, lang_filter)
    
    return AuthorCardV2Response(
        id=author.id,
        name=author.name,
        description=author.description or "",
        photo=author.photo or "",
        language=author.language or "",
        courses_count=stats["courses_count"],
        books_count=stats["books_count"],
        tags=stats["tags"],
        total_min_price=stats["total_min_price"],
        popularity=stats["popularity"],
    )


@router.get(
    "/v2/cards",
    response_model=AuthorsCardsV2Response,
    summary="V2: Карточки авторов с расширенными фильтрами и метаданными",
    description="""
    Версия 2 эндпоинта для получения карточек авторов с фильтрами и сортировками.
    
    ## Фильтры:
    
    - **language** - язык автора (EN, RU, ES, IT, AR, PT)
    - **tags** - фильтр по тегам (ID тегов из курсов и книг автора)
    - **courses_from, courses_to** - диапазон количества курсов
    - **books_from, books_to** - диапазон количества книг
    - **q** - поиск по имени автора
    
    ## Сортировки:
    
    - **popular_asc / popular_desc** - по популярности (сумма sales_count)
    - **price_asc / price_desc** - по минимальной суммарной цене курсов + книг
    - **courses_asc / courses_desc** - по количеству курсов
    - **books_asc / books_desc** - по количеству книг
    - **name_asc / name_desc** - по алфавиту
    
    ## Метаданные фильтров:
    
    При **include_filters=true** в ответе будет дополнительное поле `filters` с:
    - Список всех доступных тегов с количеством авторов
    - Диапазоны для количества курсов и книг
    - Список доступных опций сортировки
    
    ## Примеры:
    
    ```
    # Получить первую страницу с метаданными фильтров
    GET /v2/cards?page=1&size=20&include_filters=true
    
    # Авторы с 5+ курсами, отсортированные по популярности
    GET /v2/cards?courses_from=5&sort=popular_desc
    
    # Поиск авторов по имени
    GET /v2/cards?q=smith&sort=name_asc
    ```
    """,
    tags=["public"]
)
def author_cards_v2(
    # Фильтры
    language: Optional[str] = Query(
        None,
        description="Язык автора (EN, RU, ES, IT, AR, PT)",
        regex="^(EN|RU|ES|IT|AR|PT)$"
    ),
    tags: Optional[List[int]] = Query(
        None,
        description="Фильтр по тегам (ID тегов, можно несколько)"
    ),
    courses_from: Optional[int] = Query(
        None,
        ge=0,
        description="Минимальное количество курсов"
    ),
    courses_to: Optional[int] = Query(
        None,
        ge=0,
        description="Максимальное количество курсов"
    ),
    books_from: Optional[int] = Query(
        None,
        ge=0,
        description="Минимальное количество книг"
    ),
    books_to: Optional[int] = Query(
        None,
        ge=0,
        description="Максимальное количество книг"
    ),
    q: Optional[str] = Query(
        None,
        min_length=1,
        description="Поиск по имени автора"
    ),
    # Сортировка
    sort: Optional[str] = Query(
        None,
        description="Сортировка",
        regex="^(popular_asc|popular_desc|price_asc|price_desc|courses_asc|courses_desc|books_asc|books_desc|name_asc|name_desc)$"
    ),
    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, gt=0, le=100, description="Размер страницы"),
    # Метаданные фильтров
    include_filters: bool = Query(
        False,
        description="Включить метаданные фильтров в ответ (tags, courses range, books range)"
    ),
    db: Session = Depends(get_db),
):
    """
    V2 эндпоинт для получения карточек авторов с расширенными фильтрами.
    """
    
    # Собираем все фильтры в словарь
    current_filters = {
        'language': language,
        'tags': tags,
        'courses_from': courses_from,
        'courses_to': courses_to,
        'books_from': books_from,
        'books_to': books_to,
        'q': q,
    }
    
    lang_filter = [language.upper()] if language else None
    
    # Получаем отфильтрованные ID авторов (без selectinload для чистоты)
    filter_query = db.query(Author.id)
    
    # Применяем фильтры
    if language:
        filter_query = filter_query.filter(Author.language == language.upper())
    
    if q:
        like = f"%{q.strip()}%"
        filter_query = filter_query.filter(Author.name.ilike(like))
    
    # Фильтр по тегам
    if tags:
        filter_query = filter_query.filter(
            or_(
                Author.landings.any(
                    Landing.tags.any(Tag.id.in_(tags))
                ),
                Author.books.any(
                    Book.tags.any(Tag.id.in_(tags))
                )
            )
        )
    
    # Фильтр по количеству курсов
    if courses_from is not None or courses_to is not None:
        courses_count_filter = (
            db.query(
                landing_authors.c.author_id,
                func.count(func.distinct(landing_course.c.course_id)).label('courses_cnt')
            )
            .select_from(landing_authors)
            .join(Landing, landing_authors.c.landing_id == Landing.id)
            .join(landing_course, Landing.id == landing_course.c.landing_id)
            .filter(Landing.is_hidden.is_(False))
            .group_by(landing_authors.c.author_id)
            .subquery()
        )
        
        filter_query = filter_query.outerjoin(
            courses_count_filter, 
            Author.id == courses_count_filter.c.author_id
        )
        
        if courses_from is not None:
            filter_query = filter_query.filter(
                func.coalesce(courses_count_filter.c.courses_cnt, 0) >= courses_from
            )
        if courses_to is not None:
            filter_query = filter_query.filter(
                func.coalesce(courses_count_filter.c.courses_cnt, 0) <= courses_to
            )
    
    # Фильтр по количеству книг
    if books_from is not None or books_to is not None:
        books_count_filter = (
            db.query(
                book_authors.c.author_id,
                func.count(func.distinct(Book.id)).label('books_cnt')
            )
            .select_from(book_authors)
            .join(Book, book_authors.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.is_hidden.is_(False))
            .group_by(book_authors.c.author_id)
            .subquery()
        )
        
        filter_query = filter_query.outerjoin(
            books_count_filter,
            Author.id == books_count_filter.c.author_id
        )
        
        if books_from is not None:
            filter_query = filter_query.filter(
                func.coalesce(books_count_filter.c.books_cnt, 0) >= books_from
            )
        if books_to is not None:
            filter_query = filter_query.filter(
                func.coalesce(books_count_filter.c.books_cnt, 0) <= books_to
            )
    
    # Подсчитываем total до применения сортировки
    total = filter_query.distinct().count()
    
    # Теперь строим запрос для сортировки
    # Используем отдельный запрос чтобы избежать конфликтов с фильтрами
    sort_query = db.query(Author.id)
    
    # Применяем те же фильтры
    if language:
        sort_query = sort_query.filter(Author.language == language.upper())
    if q:
        sort_query = sort_query.filter(Author.name.ilike(f"%{q.strip()}%"))
    if tags:
        sort_query = sort_query.filter(
            or_(
                Author.landings.any(Landing.tags.any(Tag.id.in_(tags))),
                Author.books.any(Book.tags.any(Tag.id.in_(tags)))
            )
        )
    
    # Фильтры по количеству курсов для sort_query
    if courses_from is not None or courses_to is not None:
        courses_count_sort = (
            db.query(
                landing_authors.c.author_id,
                func.count(func.distinct(landing_course.c.course_id)).label('courses_cnt')
            )
            .select_from(landing_authors)
            .join(Landing, landing_authors.c.landing_id == Landing.id)
            .join(landing_course, Landing.id == landing_course.c.landing_id)
            .filter(Landing.is_hidden.is_(False))
            .group_by(landing_authors.c.author_id)
            .subquery()
        )
        
        sort_query = sort_query.outerjoin(courses_count_sort, Author.id == courses_count_sort.c.author_id)
        
        if courses_from is not None:
            sort_query = sort_query.filter(func.coalesce(courses_count_sort.c.courses_cnt, 0) >= courses_from)
        if courses_to is not None:
            sort_query = sort_query.filter(func.coalesce(courses_count_sort.c.courses_cnt, 0) <= courses_to)
    
    # Фильтры по количеству книг для sort_query
    if books_from is not None or books_to is not None:
        books_count_sort = (
            db.query(
                book_authors.c.author_id,
                func.count(func.distinct(Book.id)).label('books_cnt')
            )
            .select_from(book_authors)
            .join(Book, book_authors.c.book_id == Book.id)
            .join(book_landing_books, Book.id == book_landing_books.c.book_id)
            .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
            .filter(BookLanding.is_hidden.is_(False))
            .group_by(book_authors.c.author_id)
            .subquery()
        )
        
        sort_query = sort_query.outerjoin(books_count_sort, Author.id == books_count_sort.c.author_id)
        
        if books_from is not None:
            sort_query = sort_query.filter(func.coalesce(books_count_sort.c.books_cnt, 0) >= books_from)
        if books_to is not None:
            sort_query = sort_query.filter(func.coalesce(books_count_sort.c.books_cnt, 0) <= books_to)
    
    # Подзапросы для сортировки
    # Популярность из курсовых лендингов
    popularity_landing_subq = (
        db.query(
            landing_authors.c.author_id,
            func.coalesce(func.sum(func.coalesce(Landing.sales_count, 0)), 0).label('landing_pop')
        )
        .select_from(landing_authors)
        .join(Landing, landing_authors.c.landing_id == Landing.id)
        .filter(Landing.is_hidden.is_(False))
        .group_by(landing_authors.c.author_id)
        .subquery()
    )
    
    # Популярность из книжных лендингов
    popularity_book_subq = (
        db.query(
            book_authors.c.author_id,
            func.coalesce(func.sum(func.coalesce(BookLanding.sales_count, 0)), 0).label('book_pop')
        )
        .select_from(book_authors)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(book_authors.c.author_id)
        .subquery()
    )
    
    courses_subq = (
        db.query(
            landing_authors.c.author_id,
            func.count(func.distinct(landing_course.c.course_id)).label('courses_cnt')
        )
        .select_from(landing_authors)
        .join(Landing, landing_authors.c.landing_id == Landing.id)
        .join(landing_course, Landing.id == landing_course.c.landing_id)
        .filter(Landing.is_hidden.is_(False))
        .group_by(landing_authors.c.author_id)
        .subquery()
    )
    
    books_subq = (
        db.query(
            book_authors.c.author_id,
            func.count(func.distinct(Book.id)).label('books_cnt')
        )
        .select_from(book_authors)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .group_by(book_authors.c.author_id)
        .subquery()
    )
    
    price_courses_subq = (
        db.query(
            landing_authors.c.author_id,
            func.coalesce(func.sum(cast(Landing.new_price, SqlNumeric(10, 2))), 0).label('courses_price')
        )
        .select_from(landing_authors)
        .join(Landing, landing_authors.c.landing_id == Landing.id)
        .filter(Landing.is_hidden.is_(False))
        .filter(Landing.new_price.isnot(None))
        .group_by(landing_authors.c.author_id)
        .subquery()
    )
    
    price_books_subq = (
        db.query(
            book_authors.c.author_id,
            func.coalesce(func.sum(cast(BookLanding.new_price, SqlNumeric(10, 2))), 0).label('books_price')
        )
        .select_from(book_authors)
        .join(Book, book_authors.c.book_id == Book.id)
        .join(book_landing_books, Book.id == book_landing_books.c.book_id)
        .join(BookLanding, book_landing_books.c.book_landing_id == BookLanding.id)
        .filter(BookLanding.is_hidden.is_(False))
        .filter(BookLanding.new_price.isnot(None))
        .group_by(book_authors.c.author_id)
        .subquery()
    )
    
    # Применяем сортировку
    if sort == "popular_desc" or sort is None:
        sort_query = (
            sort_query
            .outerjoin(popularity_landing_subq, Author.id == popularity_landing_subq.c.author_id)
            .outerjoin(popularity_book_subq, Author.id == popularity_book_subq.c.author_id)
            .order_by(
                (func.coalesce(popularity_landing_subq.c.landing_pop, 0) + 
                 func.coalesce(popularity_book_subq.c.book_pop, 0)).desc(),
                Author.id.desc()
            )
        )
    elif sort == "popular_asc":
        sort_query = (
            sort_query
            .outerjoin(popularity_landing_subq, Author.id == popularity_landing_subq.c.author_id)
            .outerjoin(popularity_book_subq, Author.id == popularity_book_subq.c.author_id)
            .order_by(
                (func.coalesce(popularity_landing_subq.c.landing_pop, 0) + 
                 func.coalesce(popularity_book_subq.c.book_pop, 0)).asc(),
                Author.id.asc()
            )
        )
    elif sort == "price_asc":
        sort_query = (
            sort_query
            .outerjoin(price_courses_subq, Author.id == price_courses_subq.c.author_id)
            .outerjoin(price_books_subq, Author.id == price_books_subq.c.author_id)
            .order_by(
                (func.coalesce(price_courses_subq.c.courses_price, 0) + 
                 func.coalesce(price_books_subq.c.books_price, 0)).asc(),
                Author.id.asc()
            )
        )
    elif sort == "price_desc":
        sort_query = (
            sort_query
            .outerjoin(price_courses_subq, Author.id == price_courses_subq.c.author_id)
            .outerjoin(price_books_subq, Author.id == price_books_subq.c.author_id)
            .order_by(
                (func.coalesce(price_courses_subq.c.courses_price, 0) + 
                 func.coalesce(price_books_subq.c.books_price, 0)).desc(),
                Author.id.desc()
            )
        )
    elif sort == "courses_desc":
        sort_query = (
            sort_query
            .outerjoin(courses_subq, Author.id == courses_subq.c.author_id)
            .order_by(func.coalesce(courses_subq.c.courses_cnt, 0).desc(), Author.id.desc())
        )
    elif sort == "courses_asc":
        sort_query = (
            sort_query
            .outerjoin(courses_subq, Author.id == courses_subq.c.author_id)
            .order_by(func.coalesce(courses_subq.c.courses_cnt, 0).asc(), Author.id.asc())
        )
    elif sort == "books_desc":
        sort_query = (
            sort_query
            .outerjoin(books_subq, Author.id == books_subq.c.author_id)
            .order_by(func.coalesce(books_subq.c.books_cnt, 0).desc(), Author.id.desc())
        )
    elif sort == "books_asc":
        sort_query = (
            sort_query
            .outerjoin(books_subq, Author.id == books_subq.c.author_id)
            .order_by(func.coalesce(books_subq.c.books_cnt, 0).asc(), Author.id.asc())
        )
    elif sort == "name_asc":
        sort_query = sort_query.order_by(Author.name.asc(), Author.id.asc())
    elif sort == "name_desc":
        sort_query = sort_query.order_by(Author.name.desc(), Author.id.desc())
    
    # Получаем отсортированные ID с пагинацией
    author_ids = [
        aid for (aid,) in 
        sort_query.distinct().offset((page - 1) * size).limit(size).all()
    ]
    
    # Получаем метаданные фильтров, если запрошено
    filters_metadata = None
    if include_filters:
        base_for_filters = build_author_base_query(
            db=db,
            language=language,
            tags=tags,
            courses_from=courses_from,
            courses_to=courses_to,
            books_from=books_from,
            books_to=books_to,
            q=q,
        )
        filters_metadata = aggregate_author_filters(
            db=db,
            base_query=base_for_filters,
            current_filters=current_filters
        )
    
    # Загружаем авторов с необходимыми связями
    authors = (
        db.query(Author)
        .options(
            selectinload(Author.landings).selectinload(Landing.courses),
            selectinload(Author.landings).selectinload(Landing.tags),
            selectinload(Author.books).selectinload(Book.landings),
            selectinload(Author.books).selectinload(Book.tags),
        )
        .filter(Author.id.in_(author_ids))
        .all()
    ) if author_ids else []
    
    # Сохраняем порядок из запроса
    authors_by_id = {a.id: a for a in authors}
    ordered_authors = [authors_by_id[aid] for aid in author_ids if aid in authors_by_id]
    
    # Сериализуем карточки
    cards = [_serialize_author_card_v2(db, a, lang_filter) for a in ordered_authors]
    
    return AuthorsCardsV2Response(
        total=total,
        total_pages=ceil(total / size) if total > 0 else 0,
        page=page,
        size=size,
        cards=cards,
        filters=filters_metadata
    )