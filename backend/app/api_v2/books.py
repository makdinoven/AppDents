# app/api_v2/books.py

import os
import logging
from math import ceil
from typing import Optional

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_, desc, func
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
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
    TagMini,
)
from ..schemas_v2.landing import LandingListPageResponse, LangEnum, LandingDetailResponse
from ..services_v2 import book_service
from ..services_v2.book_service import paginate_like_courses, serialize_book_landing_to_course_item

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

    for field in (
        "language",
        "page_name",
        "landing_name",
        "description",
        "old_price",
        "new_price",
        "is_hidden",
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
            "slug": b.slug,
            "cover_url": b.cover_url,
            "preview_pdf_url": preview_pdf_url_for_book(b),
            "publication_date": (b.publication_date.isoformat() if b.publication_date else None),
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
    q = db.query(Book)
    if language:
        q = q.filter(Book.language == language.upper())
    books = (
        q.order_by(Book.id.desc())
         .offset(offset)
         .limit(size)
         .all()
    )
    total_pages = ceil(total / size) if total else 0
    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": books,  # благодаря orm_mode/from_attributes схеме, можно отдавать ORM
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

    base = db.query(Book)
    if language:
        base = base.filter(Book.language == language.upper())

    like = f"%{q.strip()}%"
    base = base.filter(or_(
        Book.title.ilike(like),
        Book.slug.ilike(like),
    ))

    total = base.with_entities(func.count()).scalar()
    items = (
        base.order_by(desc(Book.id))
            .offset(offset)
            .limit(size)
            .all()
    )
    total_pages = ceil(total / size) if total else 0

    return {
        "total": total,
        "total_pages": total_pages,
        "page": page,
        "size": size,
        "items": items,
    }

@router.get(
    "/landing/catalog",
    response_model=BookLandingCatalogPageResponse,
    summary="Каталог книжных лендингов (галерея/цены/регион/теги). Поддержка page и cursor пагинации"
)
def catalog_book_landings(
    mode: str = Query("page", pattern="^(page|cursor)$",
                      description="Тип пагинации: page или cursor"),
    # page-пагинация
    page: int | None = Query(1, ge=1),
    size: int = Query(12, gt=0, le=200),
    # cursor-пагинация
    after: int | None = Query(None, description="ID последнего элемента для 'see more'"),
    limit: int | None = Query(None, gt=0, le=200),
    # фильтры (минимум – язык как 'регион')
    language: Optional[str] = Query(None, description="EN,RU,ES,PT,AR,IT"),
    db: Session = Depends(get_db),
):
    base = (
        db.query(BookLanding)
          .options(
              selectinload(BookLanding.books).selectinload(Book.tags)  # для тегов
          )
          .filter(BookLanding.is_hidden.is_(False))
    )
    if language:
        base = base.filter(BookLanding.language == language.upper())

    # ── выбор режима
    if mode == "cursor":
        lim = limit or size
        q = base.order_by(BookLanding.id.desc())
        if after is not None:
            q = q.filter(BookLanding.id < after)
        rows = q.limit(lim).all()

        # галерея пачкой
        ids = [r.id for r in rows]
        gallery_map: dict[int, list[CatalogGalleryImage]] = {i: [] for i in ids}
        if ids:
            imgs = (
                db.query(BookLandingImage)
                  .filter(BookLandingImage.landing_id.in_(ids))
                  .order_by(BookLandingImage.landing_id.asc(),
                            BookLandingImage.sort_index.asc(),
                            BookLandingImage.id.asc())
                  .all()
            )
            for g in imgs:
                gallery_map[g.landing_id].append(CatalogGalleryImage(
                    id=g.id, url=g.s3_url, alt=g.alt,
                    caption=g.caption, sort_index=g.sort_index or 0
                ))

        # собираем теги из книг лендинга (уникально)
        items: list[BookLandingCatalogItem] = []
        for r in rows:
            tag_seen: dict[int, TagMini] = {}
            for b in r.books:
                for t in b.tags:
                    tag_seen[t.id] = TagMini(id=t.id, name=t.name)
            items.append(BookLandingCatalogItem(
                id=r.id,
                page_name=r.page_name,
                landing_name=r.landing_name,
                language=r.language,
                old_price=float(r.old_price) if r.old_price is not None else None,
                new_price=float(r.new_price) if r.new_price is not None else None,
                tags=list(tag_seen.values()),
                gallery=gallery_map.get(r.id, []),
            ))

        # посчитать next_cursor / has_more
        next_cursor = items[-1].id if items else None
        has_more = False
        if next_cursor is not None:
            has_more = db.query(BookLanding.id)\
                         .filter(BookLanding.is_hidden.is_(False),
                                 BookLanding.id < next_cursor)\
                         .first() is not None

        return BookLandingCatalogPageResponse(
            # поля page-пагинации опускаем
            total=None, total_pages=None, page=None, size=None,
            # курсорная
            next_cursor=next_cursor,
            has_more=has_more,
            items=items,
        )

    # ── режим страницы (page)
    total = base.with_entities(func.count()).scalar() or 0
    offset = ((page or 1) - 1) * size
    rows = (
        base.order_by(BookLanding.updated_at.desc().nullslast(), BookLanding.id.desc())
            .offset(offset).limit(size).all()
    )

    ids = [r.id for r in rows]
    gallery_map: dict[int, list[CatalogGalleryImage]] = {i: [] for i in ids}
    if ids:
        imgs = (
            db.query(BookLandingImage)
              .filter(BookLandingImage.landing_id.in_(ids))
              .order_by(BookLandingImage.landing_id.asc(),
                        BookLandingImage.sort_index.asc(),
                        BookLandingImage.id.asc())
              .all()
        )
        for g in imgs:
            gallery_map[g.landing_id].append(CatalogGalleryImage(
                id=g.id, url=g.s3_url, alt=g.alt,
                caption=g.caption, sort_index=g.sort_index or 0
            ))

    items: list[BookLandingCatalogItem] = []
    for r in rows:
        tag_seen: dict[int, TagMini] = {}
        for b in r.books:
            for t in b.tags:
                tag_seen[t.id] = TagMini(id=t.id, name=t.name)
        items.append(BookLandingCatalogItem(
            id=r.id,
            page_name=r.page_name,
            landing_name=r.landing_name,
            language=r.language,
            old_price=float(r.old_price) if r.old_price is not None else None,
            new_price=float(r.new_price) if r.new_price is not None else None,
            tags=list(tag_seen.values()),
            gallery=gallery_map.get(r.id, []),
        ))

    return BookLandingCatalogPageResponse(
        total=total,
        total_pages=(ceil(total / size) if total else 0),
        page=page or 1,
        size=size,
        # курсорные поля можно отдать как None
        next_cursor=None,
        has_more=None,
        items=items,
    )
