# app/api_v2/books.py

import os
import logging
from math import ceil
from typing import Optional, List, Dict, Union

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, desc, func
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.auth import get_current_user
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
    BookLandingOut, BookListPageResponse, BookLandingCatalogPageResponse, CatalogGalleryImage, BookLandingCatalogItem,
    TagMini, BookLandingGalleryItem, BookLandingCardResponse, BookLandingCardsResponse,
    BookLandingCardsResponsePaginations, UserBookDetailResponse, BookAdminDetailResponse, BookPatch,
)
from ..schemas_v2.landing import LandingListPageResponse, LangEnum, LandingDetailResponse, \
    TagResponse
from ..schemas_v2.common import AuthorCardResponse
from ..services_v2 import book_service
from ..services_v2.book_service import paginate_like_courses, serialize_book_landing_to_course_item
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
    return f"{S3_PUBLIC_HOST}/books/{book_id}/preview/preview_15p.pdf"

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
            "cover_url": b.cover_url,
            "preview_pdf_url": preview_pdf_url_for_book(b),
            "publication_date": (b.publication_date if b.publication_date else None),
            "description": b.description,
            "page_count": getattr(b, "page_count", None),
        }
        for b in landing.books
    ]

    # Теги лендинга = объединение тегов всех книг (уникально)
    tags: list[str] = list({t.name for b in landing.books for t in b.tags})

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
        "gallery": gallery,
        "books": books,
        "authors": authors,
        "tags": tags,
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
    conditions = [
        {"bucket": S3_BUCKET},
        ["starts-with", "$key", f"books/{book_id}/original/"],
        {"acl": "public-read"},
        {"Content-Type": "application/pdf"},
        ["content-length-range", 1, max_size],
        {"Cache-Control": "public, max-age=14400, immutable, no-transform"},
        {"Content-Disposition": "inline"},
    ]
    fields = {
        "acl": "public-read",
        "Content-Type": "application/pdf",
        "Cache-Control": "public, max-age=14400, immutable, no-transform",
        "Content-Disposition": "inline",
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

    return {
        "id": bl.id,
        "landing_name": bl.landing_name or "",
        "slug": bl.page_name,                 # у карточки «slug» = page_name лендинга
        "language": bl.language,
        "old_price": (str(bl.old_price) if bl.old_price is not None else None),
        "new_price": (str(bl.new_price) if bl.new_price is not None else None),
        "authors": authors,
        "tags": tags,
        "first_tag": first_tag,
        "main_image": _landing_main_image_from_books(bl),
        "book_ids": book_ids,
    }


@router.get(
    "/landing/cards",
    response_model=Union[BookLandingCardsResponsePaginations, BookLandingCardsResponse],
    summary="Карточки книжных лендингов (mode=cursor|page). Пагинация — как у курсов; карточки — книжные."
)
def book_landing_cards(
    mode: str = Query("cursor", regex="^(cursor|page)$"),
    tags: Optional[List[str]] = Query(None, description="Фильтр по тегам (имена)"),
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
        base = base.filter(BookLanding.books.any(Book.tags.any(Tag.name.in_(tags))))

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

from datetime import timedelta

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
          .options(selectinload(Book.files), selectinload(Book.audio_files))
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
                  .options(selectinload(Book.files), selectinload(Book.audio_files), selectinload(Book.publishers))
                  .filter(Book.id == book_id)
                  .first()
            )
        if not book:
            raise HTTPException(status_code=403, detail="You don't own this book")

    def _sign(url: str | None) -> str | None:
        if not url:
            return None
        try:
            return generate_presigned_url(url, expires=timedelta(hours=24))
        except Exception:
            return None

    files_download = []
    for f in (book.files or []):
        fmt = getattr(f.file_format, "value", f.file_format)
        files_download.append({
            "file_format": fmt,
            "download_url": _sign(f.s3_url),
            "size_bytes": f.size_bytes,
        })

    audio_download = []
    for a in (book.audio_files or []):
        audio_download.append({
            "chapter_index": a.chapter_index,
            "title": a.title,
            "duration_sec": a.duration_sec,
            "download_url": _sign(a.s3_url),
        })

    return {
        "id": book.id,
        "title": book.title,
        "cover_url": book.cover_url,
        "description": book.description,
        "publication_date": getattr(book, "publication_date", None),
        "page_count": getattr(book, "page_count", None),
        "publishers": [{"id": p.id, "name": p.name} for p in (book.publishers or [])],
        "files_download": files_download,
        "audio_download": audio_download,
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

    # авторы / теги
    if "author_ids" in data and data["author_ids"] is not None:
        book.authors = book_service._fetch_authors(db, data["author_ids"])
    if "tag_ids" in data and data["tag_ids"] is not None:
        book.tags = book_service._fetch_tags(db, data["tag_ids"])

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

