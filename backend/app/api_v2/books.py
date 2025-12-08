# app/api_v2/books.py

import os
import logging
from math import ceil
from typing import Optional, List, Dict, Union
from datetime import datetime, date, time, timedelta
from decimal import Decimal

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query, status, Request
from sqlalchemy import or_, desc, func, cast, Integer, Numeric as SqlNumeric
from sqlalchemy.orm import Session, selectinload
from pydantic import BaseModel

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import (
    User,
    Book,
    Author,
    Tag,
    Publisher,
    BookLanding,
    BookLandingImage,
    Landing,
    BookLandingVisit,
    book_authors,
    book_publishers,
    book_tags,
)
from ..utils.ip_utils import is_bot_request
from ..schemas_v2.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookLandingCreate,
    BookLandingUpdate,
    BookDetailResponse,
    PdfUploadInitResponse,
    PdfUploadInitRequest,
    BookLandingOut, BookListPageResponse, BookLandingCatalogPageResponse, CatalogGalleryImage, BookLandingCatalogItem,
    TagMini, BookLandingGalleryItem, BookLandingCardResponse, BookLandingCardsResponse,
    BookLandingCardsResponsePaginations, BookLandingCardsV2Response, UserBookDetailResponse, BookAdminDetailResponse, BookPatch,
)
from ..schemas_v2.landing import LandingListPageResponse, LangEnum, LandingDetailResponse, \
    TagResponse
from ..schemas_v2.common import AuthorCardResponse, FilterSearchResponse, FilterOption
from ..services_v2 import book_service
from ..services_v2.book_service import paginate_like_courses, serialize_book_landing_to_course_item
from ..services_v2.filter_aggregation_service import (
    build_book_landing_base_query,
    aggregate_book_filters
)
from ..utils.s3 import generate_presigned_url

# ─────────────────────────── S3 config ───────────────────────────
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3v4 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

log = logging.getLogger(__name__)
router = APIRouter()


def preview_pdf_url_for_book(book_or_slug) -> str:
    book_id = book_or_slug.id if hasattr(book_or_slug, "id") else str(book_or_slug)
    return f"{S3_PUBLIC_HOST}/books/{book_id}/preview/preview_20p.pdf"


def _client_ip(request: Request) -> str:
    """
    Корректно извлекаем IP клиента, учитывая возможный прокси перед сервисом.
    """
    xfwd = request.headers.get("X-Forwarded-For", "").strip()
    if xfwd:
        first_ip = xfwd.split(",")[0].strip()
        if first_ip:
            return first_ip
    xreal = request.headers.get("X-Real-IP", "").strip()
    if xreal:
        return xreal
    return request.client.host


def _unique_landing_name(db: Session, desired: str | None) -> str:
    base = (desired or "Book landing").strip()
    if not base:
        base = "Book landing"
    name = base
    i = 2
    while db.query(BookLanding.id).filter(BookLanding.landing_name == name).first():
        # «Book landing #2», «Book landing #3», …
        name = f"{base} #{i}"
        i += 1
    return name

# ─────────────── КНИГИ ───────────────────────────────────────────────────────
@router.post("/", response_model=BookResponse)
def create_new_book(
    payload: BookCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.create_book(db, payload)


@router.put("/{book_id}", response_model=BookResponse)
def update_book_route(
    book_id: int,
    payload: BookUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.update_book(db, book_id, payload)


@router.delete("/{book_id}", response_model=dict)
def delete_book_route(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book_service.delete_book(db, book_id)
    return {"detail": "Book deleted successfully"}


# ─────────────── ЛЕНДИНГИ КНИГ ───────────────────────────────────────────────
@router.post("/landing", response_model=BookLandingOut, status_code=status.HTTP_201_CREATED)
def create_book_landing(
    payload: BookLandingCreate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    landing = BookLanding(
        language=payload.language,
        page_name=payload.page_name,
        landing_name=payload.landing_name or _unique_landing_name(db, payload.page_name),
        description=payload.description,
        old_price=payload.old_price,
        new_price=payload.new_price,
        is_hidden=payload.is_hidden if payload.is_hidden is not None else False,
    )
    db.add(landing)
    db.flush()

    if payload.book_ids:
        books = db.query(Book).filter(Book.id.in_(payload.book_ids)).all()
        if not books or len(books) != len(set(payload.book_ids)):
            raise HTTPException(400, "Some book_ids not found")
        landing.books = books

    db.commit()
    db.refresh(landing)
    return landing


@router.patch("/landing/{landing_id}", response_model=BookLandingOut)
def update_book_landing(
    landing_id: int,
    payload: BookLandingUpdate,
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    landing = db.query(BookLanding).get(landing_id)
    if not landing:
        raise HTTPException(404, "Landing not found")

    data = payload.dict(exclude_unset=True)

    for field in ("language", "page_name", "landing_name", "description",
                  "old_price", "new_price", "is_hidden"):
        if field in data:
            setattr(landing, field, data[field])

    if "book_ids" in data:
        ids = data["book_ids"] or []
        if ids:
            books = db.query(Book).filter(Book.id.in_(ids)).all()
            if len(books) != len(set(ids)):
                raise HTTPException(400, "Some book_ids not found")
            landing.books = books
        else:
            landing.books = []

    db.commit()
    db.refresh(landing)
    return landing



@router.delete("/landing/{landing_id}", response_model=dict)
def delete_book_landing_route(
    landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book_service.delete_book_landing(db, landing_id)
    return {"detail": "Book landing deleted successfully"}


@router.post("/track-ad/{slug}")
def track_book_ad(slug: str,
                  request: Request,
                  db: Session = Depends(get_db)):
    """
    Отслеживает визит с рекламы на книжный лендинг с метаданными (fbp, fbc, ip).
    Устанавливает флаг in_advertising и TTL.
    """
    from ..services_v2.book_service import track_book_ad_visit
    
    book_landing = db.query(BookLanding).filter(BookLanding.page_name == slug).first()
    if not book_landing:
        raise HTTPException(404, "Book landing not found")
    track_book_ad_visit(
        db=db,
        book_landing_id=book_landing.id,
        fbp=request.cookies.get("_fbp"),
        fbc=request.cookies.get("_fbc"),
        ip=_client_ip(request),
        user_agent=request.headers.get("User-Agent"),
    )
    return {"ok": True}


class BookVisitIn(BaseModel):
    from_ad: bool = False


@router.post("/landing/{book_landing_id}/visit", status_code=201)
def track_book_landing_visit(
    book_landing_id: int,
    request: Request,
    payload: BookVisitIn | None = None,
    db: Session = Depends(get_db),
):
    """
    Отслеживает визит на книжный лендинг.
    Если from_ad=True и реклама включена, продлевает TTL и открывает период.
    Визиты от ботов Facebook/Meta игнорируются.
    """
    from ..services_v2.book_service import open_book_ad_period_if_needed, BOOK_AD_TTL
    
    exists = db.query(BookLanding.id).filter(BookLanding.id == book_landing_id).first()
    if not exists:
        raise HTTPException(status_code=404, detail="Book landing not found")

    # Фильтруем ботов (по IP и User-Agent)
    if is_bot_request(request):
        return {"ok": True, "skipped": "bot"}

    payload = payload or BookVisitIn()
    from_ad = bool(payload.from_ad)

    # 1) фиксируем визит в book_landing_visits
    db.add(BookLandingVisit(
        book_landing_id=book_landing_id,
        from_ad=from_ad,
    ))

    # 2) если визит рекламный — продлеваем TTL ТОЛЬКО если реклама уже включена
    if from_ad:
        from sqlalchemy.exc import OperationalError
        now = datetime.utcnow()
        try:
            book_landing = (
                db.query(BookLanding)
                  .filter(BookLanding.id == book_landing_id)
                  .with_for_update(nowait=True)
                  .first()
            )
        except OperationalError:
            # Блокировка занята — коммитим визит, пропускаем TTL-обновление
            db.commit()
            return {"ok": True}
        
        if book_landing and book_landing.in_advertising:
            # гарантируем открытый период, если вдруг его нет
            open_book_ad_period_if_needed(db, book_landing_id, started_by=None)

            # продлеваем TTL
            new_ttl = now + BOOK_AD_TTL
            if not book_landing.ad_flag_expires_at or book_landing.ad_flag_expires_at < new_ttl:
                book_landing.ad_flag_expires_at = new_ttl

        # ВАЖНО: если in_advertising == False, НИЧЕГО не включаем и не трогаем период/TTL

    db.commit()
    return {"ok": True}


@router.get(
    "/landing/list",
    response_model=LandingListPageResponse,
    summary="Список книжных лендингов (как у курсов; пагинация)"
)
def list_book_landings_like_courses(
    page: int = Query(1, ge=1, description="Номер страницы (≥1)"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    language: Optional[LangEnum] = Query(
        None, description="Фильтр по языку: EN, RU, ES, IT, AR, PT"
    ),
    db: Session = Depends(get_db),
):
    q = (
        db.query(BookLanding)
          .options(selectinload(BookLanding.books))  # чтобы не словить N+1 при будущих расширениях
          .order_by(desc(BookLanding.id))
    )
    if language:
        q = q.filter(BookLanding.language == language.value)

    return paginate_like_courses(q, page=page, size=size,
                                  serializer=serialize_book_landing_to_course_item)


@router.get(
    "/landing/list/search",
    response_model=LandingListPageResponse,
    summary="Поиск книжных лендингов (как у курсов; пагинация)"
)
def search_book_landings_like_courses(
    q: str = Query(..., min_length=1, description="Подстрока для поиска"),
    page: int = Query(1, ge=1),
    size: int = Query(10, gt=0),
    language: Optional[LangEnum] = Query(
        None, description="Фильтр по языку: EN, RU, ES, IT, AR, PT"
    ),
    db: Session = Depends(get_db),
):
    like = f"%{q.strip()}%"
    query = (
        db.query(BookLanding)
          .options(selectinload(BookLanding.books))
          .filter(
              or_(
                  BookLanding.landing_name.ilike(like),
                  BookLanding.page_name.ilike(like),
                  BookLanding.description.ilike(like),
                  BookLanding.books.any(Book.title.ilike(like)),
              )
          )
          .order_by(desc(BookLanding.id))
    )
    if language:
        query = query.filter(BookLanding.language == language.value)

    return paginate_like_courses(query, page=page, size=size,
                                  serializer=serialize_book_landing_to_course_item)


# ─────────────── ADMIN: DETAIL для редактирования ────────────────────────────
@router.get("/{landing_id}/detail", response_model=dict)
def get_book_landing_detail(landing_id: int, db: Session = Depends(get_db)):
    """
    Админ-деталка: возвращает данные, из которых можно прямо собрать PATCH.
    """
    landing = (
        db.query(BookLanding)
        .options(
            selectinload(BookLanding.books).selectinload(Book.authors),
            selectinload(BookLanding.books).selectinload(Book.files),
        )
        .get(landing_id)
    )
    if not landing:
        raise HTTPException(404, "Landing not found")

    # gallery
    gallery_rows = (
        db.query(BookLandingImage)
        .filter(BookLandingImage.landing_id == landing.id)
        .order_by(BookLandingImage.sort_index.asc(), BookLandingImage.id.asc())
        .all()
    )
    gallery = [
        {
            "id": g.id,
            "url": g.s3_url,
            "alt": g.alt,
            "caption": g.caption,
            "sort_index": g.sort_index,
            "size_bytes": g.size_bytes,
            "content_type": g.content_type,
        }
        for g in gallery_rows
    ]

    # book_ids (для PATCH)
    book_ids = [b.id for b in landing.books]

    # авторам для UI (удобно показать)
    authors_map: dict[int, dict] = {}
    for b in landing.books:
        for a in b.authors:
            if a.id not in authors_map:
                authors_map[a.id] = {
                    "id": a.id,
                    "name": a.name,
                    "photo": a.photo,
                    "description": getattr(a, "description", None),
                }

    return {
        "id": landing.id,
        "language": landing.language,
        "page_name": landing.page_name,
        "landing_name": landing.landing_name,
        "description": landing.description,
        "old_price": str(landing.old_price) if landing.old_price is not None else None,
        "new_price": str(landing.new_price) if landing.new_price is not None else None,
        "sales_count": landing.sales_count or 0,
        "is_hidden": bool(landing.is_hidden),
        "book_ids": book_ids,
        "gallery": gallery,
        "authors": list(authors_map.values()),
    }


# ─────────────── PUBLIC: лендинг по slug (ТОЛЬКО превью книг) ────────────────
@router.get("/landing/slug/{page_name}", tags=["public"])
def public_book_landing_by_slug(page_name: str, db: Session = Depends(get_db)):
    """
    Публичный эндпойнт (без авторизации).
    Возвращает:
      • общие поля лендинга,
      • галерею,
      • список книг (title, slug, cover_url, preview_pdf_url),
      • авторов (name, photo, description, tags по автору из тегов его книг на этом лендинге),
      • теги лендинга (агрегируются из тегов всех книг лендинга, уникально).
    Никаких ссылок на скачивание/форматы книг здесь нет.
    """
    landing = (
        db.query(BookLanding)
        .options(
            selectinload(BookLanding.books).selectinload(Book.authors)
                .selectinload(Author.landings).selectinload(Landing.courses),
            selectinload(BookLanding.books).selectinload(Book.authors)
                .selectinload(Author.books).selectinload(Book.landings),
            selectinload(BookLanding.books).selectinload(Book.tags),
            selectinload(BookLanding.books).selectinload(Book.publishers),
            selectinload(BookLanding.books).selectinload(Book.files),
        )
        .filter(BookLanding.page_name == page_name)
        .first()
    )
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # Галерея
    gallery_rows = (
        db.query(BookLandingImage)
        .filter(BookLandingImage.landing_id == landing.id)
        .order_by(BookLandingImage.sort_index.asc(), BookLandingImage.id.asc())
        .all()
    )
    gallery = [
        {
            "id": g.id,
            "url": g.s3_url,
            "alt": g.alt,
            "caption": g.caption,
            "sort_index": g.sort_index,
        }
        for g in gallery_rows
    ]

    # Подсчёт общего количества страниц
    total_pages = sum(getattr(b, "page_count", 0) or 0 for b in landing.books)
    
    # Агрегируем доступные форматы из всех книг лендинга
    available_formats_set = set()
    for b in landing.books:
        for f in (getattr(b, "files", []) or []):
            if f.s3_url:
                fmt = getattr(f.file_format, "value", f.file_format)
                available_formats_set.add(fmt)
    available_formats = sorted(list(available_formats_set))
    
    # Книги (только превью)
    books = [
        {
            "id": b.id,
            "title": b.title,
            "cover_url": b.cover_url,
            "preview_pdf_url": preview_pdf_url_for_book(b),
            "publication_date": (b.publication_date if b.publication_date else None),
            "description": b.description,
            "publishers": [{"id": p.id, "name": p.name} for p in (b.publishers or [])],
        }
        for b in landing.books
    ]

    # Теги лендинга = объединение тегов всех книг (уникально)
    tags: list[str] = list({t.name for b in landing.books for t in b.tags})

    # Авторы с полной информацией (как в детальном роуте)
    def safe_price(val) -> float:
        try:
            return float(val) if val is not None else float("inf")
        except (ValueError, TypeError):
            return float("inf")
    
    authors_map: dict[int, Author] = {}
    author_tags_set: dict[int, set[str]] = {}  # теги автора из его курсов и книг
    
    for b in landing.books:
        for a in b.authors:
            if a.id not in authors_map:
                authors_map[a.id] = a
                author_tags_set[a.id] = set()
            # собираем теги из книг автора
            for book in (a.books or []):
                for tag in (book.tags or []):
                    author_tags_set[a.id].add(tag.name)
            # собираем теги из курсов автора
            for landing_item in (a.landings or []):
                for tag in (getattr(landing_item, 'tags', []) or []):
                    author_tags_set[a.id].add(tag.name)

    authors = []
    lang_filter = [landing.language.upper()] if landing.language else None
    
    for aid, author in authors_map.items():
        # Подсчёт courses_count и books_count
        visible_landings = [l for l in (author.landings or []) 
                           if not l.is_hidden and (not lang_filter or l.language.upper() in lang_filter)]
        
        min_price_by_course = {}
        for l in visible_landings:
            price = safe_price(l.new_price)
            for c in (l.courses or []):
                cid = c.id
                if cid not in min_price_by_course or price < min_price_by_course[cid]:
                    min_price_by_course[cid] = price
        
        kept_landings = []
        for l in visible_landings:
            price = safe_price(l.new_price)
            if not any(price > min_price_by_course.get(c.id, float("inf")) for c in (l.courses or [])):
                kept_landings.append(l)
        
        course_ids = set()
        for l in kept_landings:
            for c in (l.courses or []):
                if c.id:
                    course_ids.add(c.id)
        courses_count = len(course_ids)
        
        # Подсчёт books_count
        books_count = 0
        for book in (author.books or []):
            visible_bl = [bl for bl in (book.landings or []) 
                         if not bl.is_hidden and (not lang_filter or bl.language.upper() in lang_filter)]
            if visible_bl:
                price_min = min(safe_price(bl.new_price) for bl in visible_bl)
                if price_min != float("inf"):
                    books_count += 1
        
        authors.append({
            "id": author.id,
            "name": author.name,
            "description": author.description or None,
            "photo": author.photo,
            "language": author.language or None,
            "courses_count": courses_count,
            "books_count": books_count,
            "tags": sorted(list(author_tags_set.get(aid, set()))),
        })

    return {
        "id": landing.id,
        "language": landing.language,
        "page_name": landing.page_name,
        "landing_name": landing.landing_name,
        "description": landing.description,
        "old_price": str(landing.old_price) if landing.old_price is not None else None,
        "new_price": str(landing.new_price) if landing.new_price is not None else None,
        "sales_count": landing.sales_count or 0,
        "total_pages": total_pages if total_pages > 0 else None,
        "gallery": gallery,
        "books": books,
        "authors": authors,
        "tags": tags,
        "available_formats": available_formats,
    }


# ─────────────── КАТАЛОГ (публичный листинг) ────────────────────────────────
logger = logging.getLogger("api.books_catalog")
@router.patch(
    "/landing/set-hidden/{landing_id}",
    response_model=LandingDetailResponse,
    summary="Скрыть/показать книжный лендинг (is_hidden)"
)
def set_book_landing_is_hidden(
    landing_id: int,
    is_hidden: bool = Query(..., description="True — скрыть, False — показать"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    bl = db.query(BookLanding).filter(BookLanding.id == landing_id).first()
    if not bl:
        raise HTTPException(status_code=404, detail="Landing not found")
    bl.is_hidden = is_hidden
    db.commit()
    db.refresh(bl)
    return bl


# ── ДОБАВИТЬ В НИЗ ФАЙЛА (после CRUD), не меняя существующие роуты ────────────
@router.post("/admin/books/{book_id}/upload-pdf-url",
             response_model=PdfUploadInitResponse,
             summary="Сгенерировать pre-signed POST для загрузки PDF напрямую в S3 (Админ)")
def get_presigned_pdf_upload_url(
    book_id: int,
    payload: PdfUploadInitRequest,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Возвращает pre-signed POST, чтобы загрузить PDF **напрямую** в S3.
    После успешной загрузки **обязательно** вызвать finalize-роут (см. ниже),
    чтобы сохранить запись BookFile в БД.
    """
    # проверим, что книга существует
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # путь в бакете, куда кладём оригиналы PDF
    # (форматируем имя, но сохраняем расширение .pdf)
    filename = payload.filename.strip().replace("\\", "/").split("/")[-1]
    if not filename:
        raise HTTPException(status_code=400, detail="Bad filename")
    if not filename.lower().endswith(".pdf"):
        # жёстко ограничим PDF: так проще для админки и последующих конвертаций
        raise HTTPException(status_code=400, detail="Only .pdf allowed")
    key = f"books/{book_id}/original/{filename}"

    # Политика и поля для POST-загрузки
    # Лимит размера — до 2 ГБ (подправь при необходимости).
    max_size = 2 * 1024 * 1024 * 1024
    metadata = book_service.original_pdf_metadata(book)
    meta_fields = {f"x-amz-meta-{k}": v for k, v in metadata.items()}
    conditions = [
        {"bucket": S3_BUCKET},
        ["starts-with", "$key", f"books/{book_id}/original/"],
        {"acl": "public-read"},
        {"Content-Type": "application/pdf"},
        {"Content-Disposition": book_service.PDF_CONTENT_DISPOSITION},
        {"Cache-Control": book_service.PDF_CACHE_CONTROL},
        ["content-length-range", 1, max_size],
    ]
    for meta_key, meta_value in meta_fields.items():
        conditions.append({meta_key: meta_value})
    fields = {
        "acl": "public-read",
        "Content-Type": "application/pdf",
        "Cache-Control": book_service.PDF_CACHE_CONTROL,
        "Content-Disposition": book_service.PDF_CONTENT_DISPOSITION,
        **meta_fields,
    }

    post = s3v4.generate_presigned_post(
        Bucket=S3_BUCKET,
        Key=key,
        Fields=fields,
        Conditions=conditions,
        ExpiresIn=3600,   # ссылка на загрузку активна 1 час
    )

    cdn_url = f"{S3_PUBLIC_HOST}/{key}"
    log.info("[UPLOAD-PDF][INIT] book_id=%s key=%s url=%s", book_id, key, post["url"])
    return PdfUploadInitResponse(
        url=post["url"],
        fields=post["fields"],
        key=key,
        cdn_url=cdn_url,
    )

@router.get(
    "/books/list",
    response_model=BookListPageResponse,
    summary="Список книг (пагинация по страницам)"
)
def get_book_listing(
    page: int = Query(1, ge=1, description="Номер страницы, начиная с 1"),
    size: int = Query(10, gt=0, description="Размер страницы"),
    language: Optional[str] = Query(None, description="EN,RU,ES,PT,AR,IT"),
    db: Session = Depends(get_db),
) -> dict:
    total = db.query(func.count(Book.id)).scalar()
    offset = (page - 1) * size
    q = db.query(Book).options(selectinload(Book.publishers))
    if language:
        q = q.filter(Book.language == language.upper())
    books = (
        q.order_by(Book.id.desc())
         .offset(offset)
         .limit(size)
         .all()
    )
    total_pages = ceil(total / size) if total else 0
    
    # Сериализуем publishers вручную
    items = []
    for b in books:
        items.append({
            "id": b.id,
            "title": b.title,
            "language": b.language,
            "cover_url": b.cover_url,
            "publication_date": b.publication_date,
            "page_count": b.page_count,
            "publishers": [{"id": p.id, "name": p.name} for p in (b.publishers or [])],
        })
    
    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }


@router.get(
    "/books/list/search",
    response_model=BookListPageResponse,
    summary="Поиск книг по названию или slug с пагинацией"
)
def search_book_listing(
    q: str = Query(..., min_length=1, description="Подстрока для поиска"),
    page: int = Query(1, ge=1),
    size: int = Query(10, gt=0),
    language: Optional[str] = Query(None, description="EN,RU,ES,PT,AR,IT"),
    db: Session = Depends(get_db),
) -> dict:
    offset = (page - 1) * size

    base = db.query(Book).options(selectinload(Book.publishers))
    if language:
        base = base.filter(Book.language == language.upper())

    like = f"%{q.strip()}%"
    base = base.filter(or_(
        Book.title.ilike(like),
    ))

    total = base.with_entities(func.count()).scalar()
    books = (
        base.order_by(desc(Book.id))
            .offset(offset)
            .limit(size)
            .all()
    )
    total_pages = ceil(total / size) if total else 0
    
    # Сериализуем publishers вручную
    items = []
    for b in books:
        items.append({
            "id": b.id,
            "title": b.title,
            "language": b.language,
            "cover_url": b.cover_url,
            "publication_date": b.publication_date,
            "page_count": b.page_count,
            "publishers": [{"id": p.id, "name": p.name} for p in (b.publishers or [])],
        })

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }

def _gallery_for_landings(db: Session, landing_ids: List[int]) -> Dict[int, List[BookLandingGalleryItem]]:
    if not landing_ids:
        return {}
    rows = (
        db.query(BookLandingImage)
          .filter(BookLandingImage.landing_id.in_(landing_ids))
          .order_by(BookLandingImage.landing_id.asc(),
                    BookLandingImage.sort_index.asc(),
                    BookLandingImage.id.asc())
          .all()
    )
    out: Dict[int, List[BookLandingGalleryItem]] = {lid: [] for lid in landing_ids}
    for g in rows:
        out.setdefault(g.landing_id, []).append(
            BookLandingGalleryItem(
                id=g.id, url=g.s3_url, alt=g.alt, caption=g.caption, sort_index=g.sort_index or 0
            )
        )
    return out

def _landing_main_image_from_books(bl: BookLanding) -> str | None:
    # Берём обложку первой книги в списке
    for b in (bl.books or []):
        if b.cover_url:
            return b.cover_url
    return None

def _serialize_book_card(bl: BookLanding) -> dict:
    # авторы — уникально из всех книг лендинга
    authors_map = {}
    for b in (bl.books or []):
        for a in (b.authors or []):
            if a.id not in authors_map:
                authors_map[a.id] = {"id": a.id, "name": a.name, "photo": a.photo}
    authors = list(authors_map.values())

    # теги — агрегируем с книг (уникально)
    tag_map = {}
    for b in (bl.books or []):
        for t in (b.tags or []):
            tag_map[t.id] = {"id": t.id, "name": t.name}
    tags = list(tag_map.values())
    first_tag = tags[0]["name"] if tags else None

    book_ids = [b.id for b in (bl.books or [])]
    
    # Подсчёт общего количества страниц
    total_pages = sum(getattr(b, "page_count", 0) or 0 for b in (bl.books or []))
    
    # publishers — уникально из всех книг лендинга
    publishers_map = {}
    for b in (bl.books or []):
        for p in (getattr(b, "publishers", []) or []):
            if p.id not in publishers_map:
                publishers_map[p.id] = {"id": p.id, "name": p.name}
    publishers = list(publishers_map.values())

    # Агрегируем доступные форматы из всех книг лендинга
    available_formats_set = set()
    for b in (bl.books or []):
        for f in (getattr(b, "files", []) or []):
            if f.s3_url:
                fmt = getattr(f.file_format, "value", f.file_format)
                available_formats_set.add(fmt)
    available_formats = sorted(list(available_formats_set))

    # Берём дату публикации из первой книги лендинга, у которой она есть
    publication_date = None
    for b in (bl.books or []):
        if getattr(b, "publication_date", None):
            publication_date = b.publication_date
            break

    return {
        "id": bl.id,
        "landing_name": bl.landing_name or "",
        "slug": bl.page_name,                 # у карточки «slug» = page_name лендинга
        "language": bl.language,
        "old_price": (str(bl.old_price) if bl.old_price is not None else None),
        "new_price": (str(bl.new_price) if bl.new_price is not None else None),
        "total_pages": total_pages if total_pages > 0 else None,
        "publishers": publishers,
        "authors": authors,
        "tags": tags,
        "first_tag": first_tag,
        "main_image": _landing_main_image_from_books(bl),
        "book_ids": book_ids,
        "available_formats": available_formats,
        "publication_date": publication_date,
    }


@router.get(
    "/landing/cards",
    response_model=Union[BookLandingCardsResponsePaginations, BookLandingCardsResponse],
    summary="Карточки книжных лендингов (mode=cursor|page). Пагинация — как у курсов; карточки — книжные."
)
def book_landing_cards(
    mode: str = Query("cursor", regex="^(cursor|page)$"),
    tags: Optional[List[int]] = Query(None, description="Фильтр по тегам (ID)"),
    sort: Optional[str] = Query(None, description="popular | discount | new"),
    language: Optional[str] = Query(None, description="EN, RU, ES, IT, AR, PT"),
    q: Optional[str] = Query(None, min_length=1, description="Поиск по landing_name/page_name"),
    # cursor-параметры
    limit: int = Query(20, gt=0, le=100),
    skip: int  = Query(0, ge=0),
    # page-параметры
    page: int = Query(1, ge=1),
    size: int = Query(20, gt=0, le=100),
    db: Session = Depends(get_db),
):
    # базовый запрос: только публичные (is_hidden = FALSE)
    base = (
        db.query(BookLanding)
          .options(
              selectinload(BookLanding.books).selectinload(Book.authors),
              selectinload(BookLanding.books).selectinload(Book.tags),
              selectinload(BookLanding.books).selectinload(Book.publishers),
              selectinload(BookLanding.books).selectinload(Book.files),
          )
          .filter(BookLanding.is_hidden.is_(False))
    )
    if language:
        base = base.filter(BookLanding.language == language.upper())
    if q:
        like = f"%{q.strip()}%"
        base = base.filter((BookLanding.landing_name.ilike(like)) |
                           (BookLanding.page_name.ilike(like)))
    if tags:
        # Ленд, где у любой книги есть любой из переданных тегов (по имени)
        base = base.filter(BookLanding.books.any(Book.tags.any(Tag.id.in_(tags))))

    # сортировка (как у курсов: popular/discount/new)
    if sort == "popular":
        # Было: sales_count.desc().nullslast()
        base = base.order_by(
            BookLanding.sales_count.is_(None),  # NULL'ы в конец
            BookLanding.sales_count.desc(),
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc(),
        )
    elif sort == "discount":
        # Было: разность с NULLS LAST
        # В MySQL делаем COALESCE/IFNULL → NULL превращаем в 0, и сортировка работает без NULLS LAST
        discount = func.ifnull(BookLanding.old_price, 0) - func.ifnull(BookLanding.new_price, 0)
        base = base.order_by(
            discount.desc(),
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc(),
        )
    elif sort == "new":
        # Было: updated_at.desc().nullslast()
        base = base.order_by(
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc(),
        )
    else:
        base = base.order_by(
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc(),
        )
    # total — с теми же фильтрами
    total = base.order_by(None).with_entities(func.count()).scalar() or 0

    if mode == "cursor":
        rows = base.offset(skip).limit(limit).all()
        #gal_map = _gallery_for_landings(db, [r.id for r in rows])
        cards = [_serialize_book_card(r) for r in rows]
        # ПОЛЯ ПАГИНАЦИИ КАК У КУРСОВ /recommend/cards:
        return {"total": total, "cards": cards}

    # mode == "page"
    rows = base.offset((page - 1) * size).limit(size).all()
     #gal_map = _gallery_for_landings(db, [r.id for r in rows])
    cards = [_serialize_book_card(r) for r in rows]
    # ПОЛЯ ПАГИНАЦИИ КАК У КУРСОВ /v1/cards:
    return {
        "total": total,
        "total_pages": (ceil(total / size) if total else 0),
        "page": page,
        "size": size,
        "cards": cards,
    }


# ═══════════════════ V2: Карточки с расширенными фильтрами ═══════════════════

@router.get(
    "/landing/v2/cards",
    response_model=BookLandingCardsV2Response,
    summary="V2: Карточки книжных лендингов с расширенными фильтрами и метаданными",
    description="""
    Версия 2 эндпоинта для получения карточек книжных лендингов.
    
    ## Основные возможности:
    
    ### Фильтрация:
    - **language** - фильтр по языку (EN, RU, ES, IT, AR, PT)
    - **tags** - фильтр по тегам (можно передать несколько)
    - **formats** - фильтр по форматам файлов (PDF, EPUB, MOBI, AZW3, FB2)
    - **publisher_ids** - фильтр по ID издателей
    - **author_ids** - фильтр по ID авторов
    - **year_from, year_to** - диапазон года публикации
    - **price_from, price_to** - диапазон цены (new_price)
    - **pages_from, pages_to** - диапазон количества страниц
    - **q** - поисковый запрос по названию
    
    ### Сортировка:
    - **price_asc** / **price_desc** - по цене
    - **pages_asc** / **pages_desc** - по количеству страниц
    - **year_asc** / **year_desc** - по году публикации
    - **new_asc** / **new_desc** - по новизне на сайте (updated_at)
    - **popular_asc** / **popular_desc** - по популярности (sales_count)
    
    ### Метаданные фильтров:
    При **include_filters=true** в ответе будет дополнительное поле `filters` с метаданными:
    - Список всех доступных издателей с количеством книг
    - Список всех доступных авторов с количеством книг
    - Список всех доступных тегов с количеством книг
    - Список всех доступных форматов с количеством книг
    - Диапазоны для цены, года публикации и количества страниц
    - Список доступных опций сортировки
    
    Все counts учитывают текущие фильтры (кроме соответствующего исключенного).
    
    ### Примеры использования:
    
    1. Получить первую страницу с метаданными фильтров:
       ```
       GET /landing/v2/cards?page=1&size=20&include_filters=true
       ```
    
    2. Фильтрация по издателю и году:
       ```
       GET /landing/v2/cards?publisher_ids=1&year_from=2020&year_to=2024
       ```
    
    3. Поиск с сортировкой по цене:
       ```
       GET /landing/v2/cards?q=implant&sort=price_asc
       ```
    
    4. Диапазон цены и страниц:
       ```
       GET /landing/v2/cards?price_from=10&price_to=50&pages_from=100&pages_to=500
       ```
    """,
    tags=["public"]
)
def book_landing_cards_v2(
    # Фильтры
    language: Optional[str] = Query(
        None,
        description="Язык лендинга (EN, RU, ES, IT, AR, PT)",
        regex="^(EN|RU|ES|IT|AR|PT)$"
    ),
    tags: Optional[List[int]] = Query(
        None,
        description="Фильтр по тегам (ID тегов, можно несколько)"
    ),
    formats: Optional[List[str]] = Query(
        None,
        description="Фильтр по форматам файлов (PDF, EPUB, MOBI, AZW3, FB2)"
    ),
    publisher_ids: Optional[List[int]] = Query(
        None,
        description="Фильтр по ID издателей (можно несколько)"
    ),
    author_ids: Optional[List[int]] = Query(
        None,
        description="Фильтр по ID авторов (можно несколько)"
    ),
    year_from: Optional[int] = Query(
        None,
        ge=1900,
        le=2100,
        description="Год публикации от (включительно)"
    ),
    year_to: Optional[int] = Query(
        None,
        ge=1900,
        le=2100,
        description="Год публикации до (включительно)"
    ),
    price_from: Optional[Decimal] = Query(
        None,
        ge=0,
        description="Цена от (new_price)"
    ),
    price_to: Optional[Decimal] = Query(
        None,
        ge=0,
        description="Цена до (new_price)"
    ),
    pages_from: Optional[int] = Query(
        None,
        ge=0,
        description="Количество страниц от (сумма всех книг лендинга)"
    ),
    pages_to: Optional[int] = Query(
        None,
        ge=0,
        description="Количество страниц до (сумма всех книг лендинга)"
    ),
    q: Optional[str] = Query(
        None,
        min_length=1,
        description="Поиск по landing_name или page_name"
    ),
    # Сортировка
    sort: Optional[str] = Query(
        None,
        description="Сортировка",
        regex="^(price_asc|price_desc|pages_asc|pages_desc|year_asc|year_desc|new_asc|new_desc|popular_asc|popular_desc)$"
    ),
    # Пагинация
    page: int = Query(1, ge=1, description="Номер страницы"),
    size: int = Query(20, gt=0, le=100, description="Размер страницы"),
    # Метаданные фильтров
    include_filters: bool = Query(
        False,
        description="Включить метаданные фильтров в ответ (publishers, authors, tags, formats, ranges)"
    ),
    db: Session = Depends(get_db),
):
    """
    V2 эндпоинт для получения карточек книжных лендингов с расширенными фильтрами.
    
    Поддерживает:
    - Множественные фильтры (издатели, авторы, теги, форматы)
    - Фильтры по диапазонам (цена, год, страницы)
    - Расширенные сортировки (в обе стороны)
    - Опциональные метаданные фильтров с актуальными counts
    """
    
    # Собираем все фильтры в словарь для удобства
    current_filters = {
        'language': language,
        'tags': tags,
        'formats': formats,
        'publisher_ids': publisher_ids,
        'author_ids': author_ids,
        'year_from': year_from,
        'year_to': year_to,
        'price_from': price_from,
        'price_to': price_to,
        'pages_from': pages_from,
        'pages_to': pages_to,
        'q': q,
    }
    
    # Строим базовый запрос с применением всех фильтров
    base = build_book_landing_base_query(
        db=db,
        language=language,
        tags=tags,
        formats=formats,
        publisher_ids=publisher_ids,
        author_ids=author_ids,
        year_from=year_from,
        year_to=year_to,
        price_from=price_from,
        price_to=price_to,
        pages_from=pages_from,
        pages_to=pages_to,
        q=q,
    )
    
    # Применяем сортировку
    # Явный CAST к DECIMAL для корректной числовой сортировки в MySQL
    if sort == "price_asc":
        base = base.order_by(
            cast(BookLanding.new_price, SqlNumeric(10, 2)).asc(),
            BookLanding.id.asc()
        )
    elif sort == "price_desc":
        base = base.order_by(
            cast(BookLanding.new_price, SqlNumeric(10, 2)).desc(),
            BookLanding.id.desc()
        )
    elif sort == "pages_asc":
        # Сортировка по сумме страниц - сложнее, используем подзапрос
        from ..models.models_v2 import book_landing_books
        subq = (
            db.query(
                book_landing_books.c.book_landing_id,
                func.sum(func.coalesce(Book.page_count, 0)).label('total_pages')
            )
            .join(Book, book_landing_books.c.book_id == Book.id)
            .group_by(book_landing_books.c.book_landing_id)
            .subquery()
        )
        base = base.outerjoin(subq, BookLanding.id == subq.c.book_landing_id)
        base = base.order_by(
            func.coalesce(subq.c.total_pages, 0).asc(),
            BookLanding.id.asc()
        )
    elif sort == "pages_desc":
        from ..models.models_v2 import book_landing_books
        subq = (
            db.query(
                book_landing_books.c.book_landing_id,
                func.sum(func.coalesce(Book.page_count, 0)).label('total_pages')
            )
            .join(Book, book_landing_books.c.book_id == Book.id)
            .group_by(book_landing_books.c.book_landing_id)
            .subquery()
        )
        base = base.outerjoin(subq, BookLanding.id == subq.c.book_landing_id)
        base = base.order_by(
            func.coalesce(subq.c.total_pages, 0).desc(),
            BookLanding.id.desc()
        )
    elif sort == "year_asc":
        # Сортировка по году публикации (из первой книги)
        from ..models.models_v2 import book_landing_books
        # Берем минимальный год из всех книг лендинга
        subq = (
            db.query(
                book_landing_books.c.book_landing_id,
                func.min(cast(func.left(Book.publication_date, 4), Integer)).label('min_year')
            )
            .join(Book, book_landing_books.c.book_id == Book.id)
            .filter(Book.publication_date.isnot(None))
            .group_by(book_landing_books.c.book_landing_id)
            .subquery()
        )
        base = base.outerjoin(subq, BookLanding.id == subq.c.book_landing_id)
        base = base.order_by(
            subq.c.min_year.is_(None),
            subq.c.min_year.asc(),
            BookLanding.id.asc()
        )
    elif sort == "year_desc":
        from ..models.models_v2 import book_landing_books
        subq = (
            db.query(
                book_landing_books.c.book_landing_id,
                func.max(cast(func.left(Book.publication_date, 4), Integer)).label('max_year')
            )
            .join(Book, book_landing_books.c.book_id == Book.id)
            .filter(Book.publication_date.isnot(None))
            .group_by(book_landing_books.c.book_landing_id)
            .subquery()
        )
        base = base.outerjoin(subq, BookLanding.id == subq.c.book_landing_id)
        base = base.order_by(
            subq.c.max_year.is_(None),
            subq.c.max_year.desc(),
            BookLanding.id.desc()
        )
    elif sort == "new_asc":
        base = base.order_by(
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.asc(),
            BookLanding.id.asc()
        )
    elif sort == "new_desc":
        base = base.order_by(
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc()
        )
    elif sort == "popular_asc":
        base = base.order_by(
            BookLanding.sales_count.is_(None),
            BookLanding.sales_count.asc(),
            BookLanding.id.asc()
        )
    elif sort == "popular_desc":
        base = base.order_by(
            BookLanding.sales_count.is_(None),
            BookLanding.sales_count.desc(),
            BookLanding.id.desc()
        )
    else:
        # Дефолтная сортировка - по новизне
        base = base.order_by(
            BookLanding.updated_at.is_(None),
            BookLanding.updated_at.desc(),
            BookLanding.id.desc()
        )
    
    # Подсчитываем total (для кнопки "Показать XXX результатов")
    total = base.order_by(None).with_entities(func.count()).scalar() or 0
    
    # Получаем метаданные фильтров, если запрошено
    filters_metadata = None
    if include_filters:
        filters_metadata = aggregate_book_filters(
            db=db,
            base_query=base.order_by(None),  # Убираем сортировку для агрегации
            current_filters=current_filters
        )
    
    # Применяем пагинацию и получаем карточки
    rows = base.offset((page - 1) * size).limit(size).all()
    cards = [_serialize_book_card(r) for r in rows]
    
    # Формируем ответ
    return BookLandingCardsV2Response(
        total=total,
        total_pages=ceil(total / size) if total > 0 else 0,
        page=page,
        size=size,
        cards=cards,
        filters=filters_metadata
    )


# ─────────────── АНАЛИТИКА КНИГ ───────────────────────────────────────────────
@router.get("/analytics/language-stats")
def book_language_stats(
    start_date: Optional[date] = Query(
        None,
        description="Дата начала (YYYY-MM-DD).",
    ),
    end_date: Optional[date] = Query(
        None,
        description="Дата конца (YYYY-MM-DD, включительно).",
    ),
    detailed: bool = Query(True, description="Нужна ли разбивка по дням"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Возвращает статистику покупок книжных лендингов по языкам за выбранный период.

    Период вычисляется по тем же правилам, что и для курсовых лендингов.
    """
    now = datetime.utcnow()

    if start_date is None and end_date is None:
        start_dt = datetime(now.year, now.month, now.day)
        end_dt = now
    elif start_date is not None and end_date is None:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = now
    elif start_date is not None and end_date is not None:
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(end_date + timedelta(days=1), time.min)
    else:
        raise HTTPException(
            status_code=400,
            detail="Если указываете end_date,  нужно обязательно передать start_date."
        )

    total = book_service.get_book_purchases_by_language(db, start_dt, end_dt)

    daily: list[dict] = []
    if detailed:
        daily = book_service.get_book_purchases_by_language_per_day(db, start_dt, end_dt)

    return {"total": total, "daily": daily}


@router.get("/me/books/{book_id}", response_model=UserBookDetailResponse,
            summary="Детали купленной книги для пользователя (форматы + ссылки на скачивание)")
def get_my_book_detail(
    book_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    # проверка владения: join к m2m user.books
    book = (
        db.query(Book)
          .options(selectinload(Book.files), selectinload(Book.audio_files), selectinload(Book.authors), selectinload(Book.publishers))
          .join(User.books)
          .filter(User.id == current_user.id, Book.id == book_id)
          .first()
    )

    # при желании пускаем админа даже без покупки:
    if not book:
        is_admin = db.query(User).get(current_user.id).role == "admin" if getattr(current_user, "id", None) else False
        if is_admin:
            book = (
                db.query(Book)
                  .options(selectinload(Book.files), selectinload(Book.audio_files), selectinload(Book.authors), selectinload(Book.publishers))
                  .filter(Book.id == book_id)
                  .first()
            )
        if not book:
            raise HTTPException(status_code=403, detail="You don't own this book")

    def _sign_with_filename(url: str | None, filename: str | None = None) -> str | None:
        if not url:
            return None
        try:
            content_disposition = None
            if filename:
                safe_filename = filename.replace('"', '\\"')
                content_disposition = f'attachment; filename="{safe_filename}"'
            
            return generate_presigned_url(
                url, 
                expires=timedelta(hours=24),
                response_content_disposition=content_disposition
            )
        except Exception:
            return None

    def _generate_filename(format: str) -> str:
        """Генерирует безопасное имя файла для скачивания"""
        import re
        if book.slug:
            base_name = book.slug
        elif book.title:
            base_name = re.sub(r'[^\w\s-]', '', book.title).strip().replace(' ', '-').lower()[:50]
        else:
            base_name = f"book-{book.id}"
        return f"{base_name}.{format.lower()}"
    
    files_download = []
    for f in (book.files or []):
        fmt = getattr(f.file_format, "value", f.file_format)
        filename = _generate_filename(fmt)
        files_download.append({
            "file_format": fmt,
            "download_url": _sign_with_filename(f.s3_url, filename),
            "size_bytes": f.size_bytes,
        })

    audio_download = []
    for a in (book.audio_files or []):
        audio_download.append({
            "chapter_index": a.chapter_index,
            "title": a.title,
            "duration_sec": a.duration_sec,
            "download_url": _sign_with_filename(a.s3_url),
        })

    available_formats = []
    for f in (book.files or []):
        if f.s3_url:  # только существующие файлы
            fmt = getattr(f.file_format, "value", f.file_format)
            if fmt not in available_formats:
                available_formats.append(fmt)

    # Найдем reader_url - публичную ссылку на PDF (без подписи)
    reader_url = None
    for f in (book.files or []):
        fmt = getattr(f.file_format, "value", f.file_format)
        if fmt == "PDF" and f.s3_url:
            reader_url = f.s3_url
            break

    return {
        "id": book.id,
        "title": book.title,
        "cover_url": book.cover_url,
        "description": book.description,
        "publication_date": getattr(book, "publication_date", None),
        "page_count": getattr(book, "page_count", None),
        "publishers": [{"id": p.id, "name": p.name} for p in (book.publishers or [])],
        "authors": [{"id": a.id, "name": a.name, "photo": a.photo} for a in (book.authors or [])],
        "reader_url": reader_url,
        "files_download": files_download,
        "audio_download": audio_download,
        "available_formats": available_formats,
    }


@router.patch("/admin/books/{book_id}",
              response_model=BookAdminDetailResponse,
              summary="Админ: частичное редактирование книги")
def patch_book(
    book_id: int,
    payload: BookPatch,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = (
        db.query(Book)
          .options(
              selectinload(Book.authors),
              selectinload(Book.tags),
              selectinload(Book.files),
              selectinload(Book.audio_files),
              selectinload(Book.publishers),
          )
          .get(book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    data = payload.dict(exclude_unset=True)

    # простые поля:
    for field in ("title", "description", "cover_url", "language", "publication_date"):
        if field in data:
            setattr(book, field, data[field])

    # авторы / теги / издатели
    if "author_ids" in data and data["author_ids"] is not None:
        book.authors = book_service._fetch_authors(db, data["author_ids"])
    if "tag_ids" in data and data["tag_ids"] is not None:
        book.tags = book_service._fetch_tags(db, data["tag_ids"])
    if "publisher_ids" in data and data["publisher_ids"] is not None:
        book.publishers = book_service._fetch_publishers(db, data["publisher_ids"])

    db.commit()
    db.refresh(book)

    files = []
    for f in (book.files or []):
        fmt = getattr(f.file_format, "value", f.file_format)
        files.append({"file_format": fmt, "s3_url": f.s3_url, "size_bytes": f.size_bytes})

    audio_files = []
    for a in (book.audio_files or []):
        audio_files.append({
            "id": a.id,
            "chapter_index": a.chapter_index,
            "title": a.title,
            "duration_sec": a.duration_sec,
            "s3_url": a.s3_url,
        })

    return {
        "id": book.id,
        "title": book.title,
        "description": book.description,
        "cover_url": book.cover_url,
        "language": book.language,
        "publication_date": getattr(book, "publication_date", None),
        "page_count": getattr(book, "page_count", None),
        "publishers": [{"id": p.id, "name": p.name} for p in (book.publishers or [])],

        "author_ids": [a.id for a in (book.authors or [])],
        "tag_ids": [t.id for t in (book.tags or [])],

        "files": files,
        "audio_files": audio_files,
    }

