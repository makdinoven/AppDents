"""
Универсальные эндпоинты для поиска по фильтрам.

Поддерживает поиск авторов, издателей, тегов для разных контекстов:
- books (книги)
- courses (курсы)  
- authors (страница авторов)
"""

from typing import Optional, List
from decimal import Decimal

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..schemas_v2.common import FilterSearchResponse, FilterContext
from ..services_v2 import universal_filter_search

router = APIRouter(prefix="/filters", tags=["filters"])


# ═══════════════════ Поиск авторов ═══════════════════

@router.get(
    "/authors/search",
    response_model=FilterSearchResponse,
    summary="Универсальный поиск авторов",
    description="""
    Универсальный поиск авторов с автокомплитом для использования в фильтрах.
    
    ## Контексты:
    
    ### books - каталог книг
    Возвращает авторов с количеством книжных лендингов.
    Поддерживает фильтры: language, tags, formats, publisher_ids, year_from, year_to, 
    price_from, price_to, pages_from, pages_to.
    
    ### courses - каталог курсов
    Возвращает лекторов с количеством курсовых лендингов.
    Поддерживает фильтры: language, tags, price_from, price_to.
    
    ### authors - страница авторов (будущая реализация)
    Возвращает авторов с общей статистикой.
    
    ## Параметры:
    - **context** - контекст поиска (обязательный): books | courses | authors
    - **q** - поисковый запрос (опционально, минимум 1 символ)
    - **limit** - максимальное количество результатов (по умолчанию 20)
    - Фильтры зависят от контекста
    
    ## Примеры:
    ```
    # Поиск авторов для каталога книг
    GET /filters/authors/search?context=books&q=smith&limit=10&language=EN
    
    # Все авторы с английскими книгами по хирургии
    GET /filters/authors/search?context=books&language=EN&tags=surgery&limit=50
    
    # Поиск лекторов для курсов (будущее)
    GET /filters/authors/search?context=courses&q=john&limit=10
    ```
    """
)
def search_authors_endpoint(
    context: FilterContext = Query(..., description="Контекст поиска: books, courses, authors"),
    q: Optional[str] = Query(None, min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, gt=0, le=100, description="Максимальное количество результатов"),
    # Фильтры для контекста "books"
    language: Optional[str] = Query(None, regex="^(EN|RU|ES|IT|AR|PT)$", description="[books] Язык"),
    tags: Optional[List[int]] = Query(None, description="[books] ID тегов"),
    formats: Optional[List[str]] = Query(None, description="[books] Форматы"),
    publisher_ids: Optional[List[int]] = Query(None, description="[books] ID издателей"),
    year_from: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год от"),
    year_to: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год до"),
    price_from: Optional[Decimal] = Query(None, ge=0, description="[books] Цена от"),
    price_to: Optional[Decimal] = Query(None, ge=0, description="[books] Цена до"),
    pages_from: Optional[int] = Query(None, ge=0, description="[books] Страниц от"),
    pages_to: Optional[int] = Query(None, ge=0, description="[books] Страниц до"),
    # Фильтры для контекста "courses"
    lessons_from: Optional[int] = Query(None, ge=0, description="[courses] Уроков от"),
    lessons_to: Optional[int] = Query(None, ge=0, description="[courses] Уроков до"),
    db: Session = Depends(get_db),
):
    """
    Универсальный эндпоинт для поиска авторов в различных контекстах.
    """
    return universal_filter_search.search_authors(
        db=db,
        context=context,
        q=q,
        limit=limit,
        # Фильтры для books и courses
        language=language,
        tags=tags,
        formats=formats,
        publisher_ids=publisher_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        lessons_from=lessons_from,
        lessons_to=lessons_to,
    )


# ═══════════════════ Поиск издателей ═══════════════════

@router.get(
    "/publishers/search",
    response_model=FilterSearchResponse,
    summary="Универсальный поиск издателей",
    description="""
    Универсальный поиск издателей с автокомплитом для использования в фильтрах.
    
    ## Контексты:
    
    ### books - каталог книг
    Возвращает издателей с количеством книжных лендингов.
    Поддерживает фильтры: language, tags, formats, author_ids, year_from, year_to, 
    price_from, price_to, pages_from, pages_to.
    
    ## Примеры:
    ```
    GET /filters/publishers/search?context=books&q=quintessence&limit=10
    GET /filters/publishers/search?context=books&language=EN&limit=50
    ```
    """
)
def search_publishers_endpoint(
    context: FilterContext = Query(..., description="Контекст поиска: books, courses, authors"),
    q: Optional[str] = Query(None, min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, gt=0, le=100, description="Максимальное количество результатов"),
    # Фильтры для контекста "books"
    language: Optional[str] = Query(None, regex="^(EN|RU|ES|IT|AR|PT)$", description="[books] Язык"),
    tags: Optional[List[int]] = Query(None, description="[books] ID тегов"),
    formats: Optional[List[str]] = Query(None, description="[books] Форматы"),
    author_ids: Optional[List[int]] = Query(None, description="[books] ID авторов"),
    year_from: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год от"),
    year_to: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год до"),
    price_from: Optional[Decimal] = Query(None, ge=0, description="[books] Цена от"),
    price_to: Optional[Decimal] = Query(None, ge=0, description="[books] Цена до"),
    pages_from: Optional[int] = Query(None, ge=0, description="[books] Страниц от"),
    pages_to: Optional[int] = Query(None, ge=0, description="[books] Страниц до"),
    db: Session = Depends(get_db),
):
    """
    Универсальный эндпоинт для поиска издателей в различных контекстах.
    """
    return universal_filter_search.search_publishers(
        db=db,
        context=context,
        q=q,
        limit=limit,
        # Фильтры для books
        language=language,
        tags=tags,
        formats=formats,
        author_ids=author_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
    )


# ═══════════════════ Поиск тегов ═══════════════════

@router.get(
    "/tags/search",
    response_model=FilterSearchResponse,
    summary="Универсальный поиск тегов",
    description="""
    Универсальный поиск тегов с автокомплитом для использования в фильтрах.
    
    ## Контексты:
    
    ### books - каталог книг
    Возвращает теги с количеством книжных лендингов.
    Поддерживает фильтры: language, formats, publisher_ids, author_ids, year_from, year_to, 
    price_from, price_to, pages_from, pages_to.
    
    ### courses - каталог курсов
    Возвращает теги с количеством курсовых лендингов.
    Поддерживает фильтры: language, author_ids, price_from, price_to.
    
    ### authors - страница авторов
    Возвращает теги с количеством авторов (из курсов и книг).
    Поддерживает фильтры: language, courses_from, courses_to, books_from, books_to.
    
    ## Примеры:
    ```
    GET /filters/tags/search?context=books&q=surgery&limit=10
    GET /filters/tags/search?context=courses&q=implant&limit=20
    GET /filters/tags/search?context=authors&q=implant&language=EN&limit=20
    ```
    """
)
def search_tags_endpoint(
    context: FilterContext = Query(..., description="Контекст поиска: books, courses, authors"),
    q: Optional[str] = Query(None, min_length=1, description="Поисковый запрос"),
    limit: int = Query(20, gt=0, le=100, description="Максимальное количество результатов"),
    # Фильтры для контекста "books"
    language: Optional[str] = Query(None, regex="^(EN|RU|ES|IT|AR|PT)$", description="[books/authors] Язык"),
    formats: Optional[List[str]] = Query(None, description="[books] Форматы"),
    publisher_ids: Optional[List[int]] = Query(None, description="[books] ID издателей"),
    author_ids: Optional[List[int]] = Query(None, description="[books] ID авторов"),
    year_from: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год от"),
    year_to: Optional[int] = Query(None, ge=1900, le=2100, description="[books] Год до"),
    price_from: Optional[Decimal] = Query(None, ge=0, description="[books] Цена от"),
    price_to: Optional[Decimal] = Query(None, ge=0, description="[books] Цена до"),
    pages_from: Optional[int] = Query(None, ge=0, description="[books] Страниц от"),
    pages_to: Optional[int] = Query(None, ge=0, description="[books] Страниц до"),
    # Фильтры для контекста "courses"
    lessons_from: Optional[int] = Query(None, ge=0, description="[courses] Уроков от"),
    lessons_to: Optional[int] = Query(None, ge=0, description="[courses] Уроков до"),
    # Фильтры для контекста "authors"
    courses_from: Optional[int] = Query(None, ge=0, description="[authors] Мин. курсов"),
    courses_to: Optional[int] = Query(None, ge=0, description="[authors] Макс. курсов"),
    books_from: Optional[int] = Query(None, ge=0, description="[authors] Мин. книг"),
    books_to: Optional[int] = Query(None, ge=0, description="[authors] Макс. книг"),
    db: Session = Depends(get_db),
):
    """
    Универсальный эндпоинт для поиска тегов в различных контекстах.
    """
    return universal_filter_search.search_tags(
        db=db,
        context=context,
        q=q,
        limit=limit,
        # Фильтры для books
        language=language,
        formats=formats,
        publisher_ids=publisher_ids,
        author_ids=author_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        # Фильтры для courses
        lessons_from=lessons_from,
        lessons_to=lessons_to,
        # Фильтры для authors
        courses_from=courses_from,
        courses_to=courses_to,
        books_from=books_from,
        books_to=books_to,
    )

