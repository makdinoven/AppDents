import os

import boto3
import logging
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, BookFileFormat, BookFile
from ..schemas_v2.book import (
    BookCreate, BookUpdate, BookResponse,
    BookLandingCreate, BookLandingUpdate, BookLandingResponse, BookDetailResponse, PdfUploadInitResponse,
    PdfUploadInitRequest, PdfUploadFinalizeRequest,
)
from ..services_v2 import book_service


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

# ─────────────── ЛЕНДИНГИ КНИГИ ─────────────────────────────────────────────
@router.post("/landing", response_model=BookLandingResponse)
def create_book_landing_route(
    payload: BookLandingCreate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.create_book_landing(db, payload)

@router.put("/landing/{landing_id}", response_model=BookLandingResponse)
def update_book_landing_route(
    landing_id: int,
    payload: BookLandingUpdate,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    return book_service.update_book_landing(db, landing_id, payload)

@router.delete("/landing/{landing_id}", response_model=dict)
def delete_book_landing_route(
    landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book_service.delete_book_landing(db, landing_id)
    return {"detail": "Book landing deleted successfully"}


@router.get("/landing/{slug}", response_model=BookLandingResponse,
            tags=["public"], summary="Открыть лендинг книги по slug")
def public_book_landing(
    slug: str,
    language: str | None = None,
    db: Session = Depends(get_db),
):
    """
    Публичный (не требует авторизации) роут.
    Возвращает данные лендинга, скрытые лендинги не выдаются.
    """
    return book_service.get_book_landing_by_slug(db, slug, language)

@router.get("/{book_id}", response_model=BookDetailResponse,
            summary="Полная информация о книге + download-ссылки")
def api_get_book_detail(
    book_id: int,
    db: Session = Depends(get_db),
    current: User | None = Depends(get_current_user_optional),
):
    """
    • **Админ** – полный доступ.
    • **Пользователь-владелец** – скачивание доступно.
    • Остальным – 403.
    """
    return book_service.get_book_detail(db, book_id, current)

# app/api/books_catalog.py
# Публичный каталог книжных лендингов (без авторизации).
# Фильтры: язык, автор, тег, поиск; сортировка; пагинация.

import logging
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, joinedload, selectinload
from sqlalchemy import func, or_, and_

from ..db.database import get_db
from ..models.models_v2 import (
    BookLanding, Book, Author, Tag,
    book_landing_books,
)

logger = logging.getLogger("api.books_catalog")

def _to_float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except Exception:
        return None

def _serialize_landing(bl: BookLanding) -> dict:
    # Список книг, которые продаёт лендинг: bundle > одиночная book
    books = list(bl.books_bundle or [])
    if not books and getattr(bl, "book", None):
        books = [bl.book]

    return {
        "id": bl.id,
        "page_name": bl.page_name,
        "landing_name": bl.landing_name,
        "new_price": _to_float(bl.new_price),
        "old_price": _to_float(bl.old_price),
        "preview_photo": bl.preview_photo,
        "sales_count": bl.sales_count or 0,
        "language": bl.language,
        "books": [
            {
                "id": b.id,
                "title": b.title,
                "slug": b.slug,
                "cover_url": b.cover_url,
                "preview_pdf": getattr(b, "preview_pdf", None),  # ← ДОБАВЛЕНО
            } for b in books
        ],
        "authors": [
            {
                "id": a.id,
                "name": a.name,
                "photo": a.photo,
            } for a in (bl.book.authors if getattr(bl, "book", None) else [])
        ],
    }


@router.get("", summary="Каталог книжных лендингов (листинг)")
def list_book_landings(
    page: int = Query(1, ge=1),
    size: int = Query(12, ge=1, le=100),
    language: Optional[str] = Query(None, description="EN,RU,ES,PT,AR,IT"),
    author_id: Optional[int] = Query(None),
    tag_id: Optional[int] = Query(None),
    q: Optional[str] = Query(None, description="Поиск по названию книги/лендинга"),
    sort: str = Query("new", description="new|price|sales|name"),
    db: Session = Depends(get_db),
):
    """
    Возвращает страницу книжных лендингов (is_hidden = FALSE).
    """
    qset = (
        db.query(BookLanding)
          .options(
              selectinload(BookLanding.books_bundle),
              selectinload(BookLanding.book).selectinload(Book.authors),
          )
          .filter(BookLanding.is_hidden.is_(False))
    )

    if language:
        qset = qset.filter(BookLanding.language == language.upper())

    # Фильтр по автору: через одиночную book.authors или через bundle (any)
    if author_id:
        # LEFT JOIN book (single)
        qset = qset.join(BookLanding.book, isouter=True)
        # LEFT JOIN bundle association
        qset = qset.join(book_landing_books, book_landing_books.c.book_landing_id == BookLanding.id, isouter=True)\
                   .join(Book, Book.id == book_landing_books.c.book_id, isouter=True)
        qset = qset.join(Author, or_(
            Author.id.in_(db.query(Author.id).join(Author.books).filter(Book.id == BookLanding.book_id)),
            Author.id.in_(db.query(Author.id).join(Author.books).filter(Author.id == author_id))
        ), isouter=True)
        # Упростим выражение: оставим лендинги, где есть совпадение по автору в любой из связей
        qset = qset.filter(
            or_(
                BookLanding.book.has(Book.authors.any(Author.id == author_id)),
                BookLanding.books_bundle.any(Book.authors.any(Author.id == author_id)),
            )
        )

    # Фильтр по тегу (теги на самой КНИГЕ, не на лендинге)
    if tag_id:
        qset = qset.filter(
            or_(
                BookLanding.book.has(Book.tags.any(Tag.id == tag_id)),
                BookLanding.books_bundle.any(Book.tags.any(Tag.id == tag_id)),
            )
        )

    if q:
        like = f"%{q.strip()}%"
        qset = qset.filter(
            or_(
                BookLanding.landing_name.ilike(like),
                BookLanding.description.ilike(like),
                BookLanding.book.has(Book.title.ilike(like)),
            )
        )

    # Сортировка
    if sort == "price":
        qset = qset.order_by(BookLanding.new_price.asc().nullslast())
    elif sort == "sales":
        qset = qset.order_by(BookLanding.sales_count.desc().nullslast())
    elif sort == "name":
        qset = qset.order_by(BookLanding.landing_name.asc().nullslast())
    else:
        # по умолчанию — новизна (updated_at ↓, затем id ↓)
        qset = qset.order_by(BookLanding.updated_at.desc().nullslast(), BookLanding.id.desc())

    total = qset.count()
    items = qset.offset((page - 1) * size).limit(size).all()

    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [_serialize_landing(bl) for bl in items],
    }

@router.get("/{page_name}", summary="Книжный лендинг по slug (для проверок)")
def get_book_landing_by_slug(
    page_name: str,
    db: Session = Depends(get_db),
):
    bl = (
        db.query(BookLanding)
          .options(
              selectinload(BookLanding.books_bundle),
              selectinload(BookLanding.book).selectinload(Book.authors),
          )
          .filter(BookLanding.page_name == page_name, BookLanding.is_hidden.is_(False))
          .first()
    )
    if not bl:
        raise HTTPException(status_code=404, detail="Book landing not found")
    return _serialize_landing(bl)


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
    conditions = [
        {"bucket": S3_BUCKET},
        ["starts-with", "$key", f"books/{book_id}/original/"],
        {"acl": "public-read"},
        {"Content-Type": payload.content_type},
        ["content-length-range", 1, max_size],
    ]
    fields = {
        "acl": "public-read",
        "Content-Type": payload.content_type,
        # можно добавить x-amz-meta-*, если нужно
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
