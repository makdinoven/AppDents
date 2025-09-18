# app/api_v2/books.py

import os
import logging
from typing import Optional

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.auth import get_current_user_optional
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import (
    User,
    Book,
    Author,
    Tag,
    BookLanding,
    BookLandingImage,
)
from ..schemas_v2.book import (
    BookCreate,
    BookUpdate,
    BookResponse,
    BookLandingCreate,
    BookLandingUpdate,
    BookDetailResponse,
    PdfUploadInitResponse,
    PdfUploadInitRequest,
    BookLandingOut,
)
from ..services_v2 import book_service

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
    return f"{S3_PUBLIC_HOST}/books/{book_id}/preview/preview_15p.pdf"


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
        landing_name=payload.landing_name,
        description=payload.description,
        old_price=payload.old_price,
        new_price=payload.new_price,
        is_hidden=payload.is_hidden if payload.is_hidden is not None else False,
        preview_imgs=payload.preview_imgs or None,
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

    for field in (
        "language",
        "page_name",
        "landing_name",
        "description",
        "old_price",
        "new_price",
        "is_hidden",
        "preview_photo",
        "preview_imgs",
    ):
        val = getattr(payload, field, None)
        if val is not None:
            setattr(landing, field, val)

    if payload.book_ids is not None:
        if payload.book_ids:
            books = db.query(Book).filter(Book.id.in_(payload.book_ids)).all()
            if not books or len(books) != len(set(payload.book_ids)):
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
        "is_hidden": bool(landing.is_hidden),
        "preview_photo": landing.preview_photo,
        "preview_imgs": landing.preview_imgs or [],
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
            selectinload(BookLanding.books).selectinload(Book.authors),
            selectinload(BookLanding.books).selectinload(Book.tags),
        )
        .filter(BookLanding.page_name == page_name, BookLanding.is_hidden.is_(False))
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

    # Книги (только превью)
    books = [
        {
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "cover_url": b.cover_url,
            "preview_pdf_url": preview_pdf_url_for_book(b),
            "description": b.description,
        }
        for b in landing.books
    ]

    # Теги лендинга = объединение тегов всех книг (уникально)
    tag_map: dict[int, dict] = {}
    for b in landing.books:
        for t in b.tags:
            tag_map[t.id] = {"id": t.id, "name": t.name}
    tags = list(tag_map.values())

    # Авторы с описанием и «их» тегами (теги автора = теги книг этого автора на данном лендинге)
    authors_map: dict[int, dict] = {}
    author_tags_map: dict[int, dict[int, dict]] = {}
    for b in landing.books:
        for a in b.authors:
            if a.id not in authors_map:
                authors_map[a.id] = {
                    "id": a.id,
                    "name": a.name,
                    "photo": a.photo,
                    "description": getattr(a, "description", None),
                }
                author_tags_map[a.id] = {}
            for t in b.tags:
                author_tags_map[a.id][t.id] = {"id": t.id, "name": t.name}

    authors = []
    for aid, ainfo in authors_map.items():
        ainfo = dict(ainfo)
        ainfo["tags"] = list(author_tags_map.get(aid, {}).values())
        authors.append(ainfo)

    return {
        "id": landing.id,
        "language": landing.language,
        "page_name": landing.page_name,
        "landing_name": landing.landing_name,
        "description": landing.description,
        "old_price": str(landing.old_price) if landing.old_price is not None else None,
        "new_price": str(landing.new_price) if landing.new_price is not None else None,
        "preview_photo": landing.preview_photo,
        "gallery": gallery,
        "books": books,
        "authors": authors,
        "tags": tags,
    }


# ─────────────── КАТАЛОГ (публичный листинг) ────────────────────────────────
logger = logging.getLogger("api.books_catalog")




def _to_float(v) -> float | None:
    try:
        return float(v) if v is not None else None
    except Exception:
        return None

def _serialize_landing(bl: BookLanding) -> dict:
    books = list(bl.books or [])
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
                "preview_pdf": f"{S3_PUBLIC_HOST}/books/{b.id}/preview/preview_15p.pdf",
            } for b in books
        ],
        # авторов теперь также собирай через bl.books:
        "authors": [
            {"id": a.id, "name": a.name, "photo": a.photo}
            for b in books for a in b.authors
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
            selectinload(BookLanding.books).selectinload(Book.authors),
        )
        .filter(BookLanding.is_hidden.is_(False))
    )

    if language:
        qset = qset.filter(BookLanding.language == language.upper())

    # Фильтр по автору: через одиночную book.authors или через bundle (any)
    if author_id:
        qset = qset.filter(BookLanding.books.any(Book.authors.any(Author.id == author_id)))

    if tag_id:
        qset = qset.filter(BookLanding.books.any(Book.tags.any(Tag.id == tag_id)))

    if q:
        like = f"%{q.strip()}%"
        qset = qset.filter(
            or_(
                BookLanding.landing_name.ilike(like),
                BookLanding.description.ilike(like),
                BookLanding.books.any(Book.title.ilike(like)),
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
