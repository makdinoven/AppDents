import logging
from datetime import timedelta
from typing import List
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status

from ..models.models_v2 import (
    Book, BookFile, BookAudio,
    BookFileFormat, Author, BookLanding, User
)
from ..schemas_v2.book import (
    BookCreate, BookUpdate,
    BookLandingCreate, BookLandingUpdate, BookDetailResponse
)
from ..utils.s3 import generate_presigned_url

log = logging.getLogger(__name__)

# ─────────────────────────── КНИГИ ───────────────────────────────────────────
def _fetch_authors(db: Session, ids: List[int]) -> List[Author]:
    authors = db.query(Author).filter(Author.id.in_(ids)).all()
    if len(authors) != len(ids):
        absent = sorted(set(ids) - {a.id for a in authors})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Authors not found: {absent}",
        )
    return authors

def _user_owns_book(db: Session, user_id: int, book_id: int) -> bool:
    """
    Проверяем факт покупки книги.
    Пока что опираемся на таблицу Purchase (добавим book_id позже).
    """
    from ..models.models_v2 import Purchase           # откладываем import
    return db.query(Purchase).filter(
        Purchase.user_id == user_id,
        Purchase.book_id == book_id                   # поле появится вместе с оплатами книг
    ).first() is not None

def _ensure_unique_slug(db: Session, slug: str, *, exclude_book_id: int | None = None) -> None:
    q = db.query(Book).filter(Book.slug == slug)
    if exclude_book_id:
        q = q.filter(Book.id != exclude_book_id)
    if db.query(q.exists()).scalar():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"slug '{slug}' already exists",
        )

def create_book(db: Session, payload: BookCreate) -> Book:
    _ensure_unique_slug(db, payload.slug)
    log.info("[BOOK] Creating «%s»", payload.title)
    authors = _fetch_authors(db, payload.author_ids)

    book = Book(
        title       = payload.title,
        slug=payload.slug,
        description = payload.description,
        cover_url   = str(payload.cover_url),
        language    = payload.language.upper(),
        authors     = authors,
    )
    db.add(book)
    db.flush()                       # → book.id

    # Файлы разных форматов
    for f in payload.files:
        bf = BookFile(
            book_id     = book.id,
            file_format = BookFileFormat(f.file_format),
            s3_url      = str(f.s3_url),
            size_bytes  = f.size_bytes,
        )
        db.add(bf)

    # Аудиофайлы
    for af in payload.audio_files:
        ba = BookAudio(
            book_id       = book.id,
            chapter_index = af.chapter_index,
            title         = af.title,
            duration_sec  = af.duration_sec,
            s3_url        = str(af.s3_url),
        )
        db.add(ba)

    db.commit()
    db.refresh(book)
    log.info("[BOOK] %s (%d) создана", payload.title, book.id)
    return book

def update_book(db: Session, book_id: int, payload: BookUpdate) -> Book:
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    log.info("[BOOK] Updating id=%d", book_id)

    if payload.title is not None:
        book.title = payload.title
    if payload.description is not None:
        book.description = payload.description
    if payload.cover_url is not None:
        book.cover_url = str(payload.cover_url)
    if payload.language is not None:
        book.language = payload.language.upper()

    if payload.author_ids is not None:
        book.authors = _fetch_authors(db, payload.author_ids)
    if payload.slug is not None and payload.slug != book.slug:
        _ensure_unique_slug(db, payload.slug,
                            exclude_book_id=book.id)
        book.slug = payload.slug

    if payload.files is not None:
        # Полностью заменяем
        db.query(BookFile).filter(BookFile.book_id == book.id).delete()
        for f in payload.files:
            db.add(BookFile(
                book_id     = book.id,
                file_format = BookFileFormat(f.file_format),
                s3_url      = str(f.s3_url),
                size_bytes  = f.size_bytes,
            ))

    if payload.audio_files is not None:
        db.query(BookAudio).filter(BookAudio.book_id == book.id).delete()
        for af in payload.audio_files:
            db.add(BookAudio(
                book_id       = book.id,
                chapter_index = af.chapter_index,
                title         = af.title,
                duration_sec  = af.duration_sec,
                s3_url        = str(af.s3_url),
            ))

    db.commit()
    db.refresh(book)
    return book

def delete_book(db: Session, book_id: int) -> None:
    rows = db.query(Book).filter(Book.id == book_id).delete()
    if not rows:
        raise HTTPException(status_code=404, detail="Book not found")
    db.commit()
    log.warning("[BOOK] id=%d удалена", book_id)

# ────────────────────── ЛЕНДИНГИ КНИГИ ───────────────────────────────────────
def create_book_landing(db: Session, payload: BookLandingCreate) -> BookLanding:
    log.info("[BOOK-LANDING] Creating slug=%s", payload.page_name)
    if db.query(BookLanding).filter_by(page_name=payload.page_name).first():
        raise HTTPException(status_code=400, detail="page_name already exists")

    landing = BookLanding(
        book_id       = payload.book_id,
        language      = payload.language.upper(),
        page_name     = payload.page_name,
        landing_name  = payload.landing_name,
        old_price     = payload.old_price,
        new_price     = payload.new_price,
        description   = payload.description,
        preview_photo = str(payload.preview_photo) if payload.preview_photo else None,
        preview_pdf   = str(payload.preview_pdf)   if payload.preview_pdf   else None,
        preview_imgs  = payload.preview_imgs,
        is_hidden     = payload.is_hidden,
    )
    db.add(landing)
    db.commit()
    db.refresh(landing)
    return landing

def update_book_landing(db: Session, landing_id: int,
                        payload: BookLandingUpdate) -> BookLanding:
    landing = db.query(BookLanding).get(landing_id)
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    if payload.page_name and payload.page_name != landing.page_name:
        if db.query(BookLanding).filter_by(page_name=payload.page_name).first():
            raise HTTPException(status_code=400, detail="page_name already exists")
        landing.page_name = payload.page_name

    for field in (
        "book_id", "language", "landing_name", "old_price", "new_price",
        "description", "preview_photo", "preview_pdf", "preview_imgs",
        "is_hidden",
    ):
        val = getattr(payload, field)
        if val is not None:
            setattr(landing, field, val)

    db.commit()
    db.refresh(landing)
    return landing

def delete_book_landing(db: Session, landing_id: int) -> None:
    rows = db.query(BookLanding).filter(BookLanding.id == landing_id).delete()
    if not rows:
        raise HTTPException(status_code=404, detail="Landing not found")
    db.commit()
    log.warning("[BOOK-LANDING] id=%d удалён", landing_id)

def get_book_landing_by_slug(
        db: Session, slug: str, language: str | None = None
) -> BookLanding:
    """Возвращает первый доступный (is_hidden=False) лендинг по slug книги.
    Если передан language – пытаемся подобрать лендинг на нужном языке,
    иначе берём первый попавшийся."""
    book = db.query(Book).filter(Book.slug == slug).first()
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    q = db.query(BookLanding).filter(
        BookLanding.book_id == book.id,
        BookLanding.is_hidden.is_(False),
    )
    if language:
        q = q.filter(BookLanding.language == language.upper())

    landing = q.order_by(BookLanding.id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    return landing

def get_book_detail(
    db: Session,
    book_id: int,
    current_user: User | None = None
) -> dict:
    """Полная информация о книге + ссылки для скачивания (signed URLs)."""
    book = (
        db.query(Book)
          .options(
              selectinload(Book.files),
              selectinload(Book.audio_files),
              selectinload(Book.landings),
              selectinload(Book.authors),
          )
          .filter(Book.id == book_id)
          .first()
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # ---- доступ ------------------------------------------------------------
    is_admin   = current_user and current_user.role == "admin"
    is_owner   = current_user and _user_owns_book(db, current_user.id, book_id)
    if not is_admin and not is_owner:
        raise HTTPException(status_code=403, detail="Access denied")

    # ---- Signed-URL для файлов --------------------------------------------
    expires = timedelta(hours=12)                      # 12 ч – хватит на загрузку
    files_dl = [
        {
            "file_format": f.file_format.value,
            "download_url": generate_presigned_url(f.s3_url, expires),
            "size_bytes": f.size_bytes,
        }
        for f in book.files
    ]
    audio_dl = [
        {
            "chapter_index": a.chapter_index,
            "title": a.title,
            "duration_sec": a.duration_sec,
            "download_url": generate_presigned_url(a.s3_url, expires),
        }
        for a in book.audio_files
    ]

    # ---- сериализация ------------------------------------------------------
    return BookDetailResponse(
        id          = book.id,
        slug        = book.slug,
        title       = book.title,
        description = book.description,
        cover_url   = book.cover_url,
        language    = book.language,
        author_ids  = [au.id for au in book.authors],
        files       = [  # «сырые» записи без ссылок
            {"file_format": f.file_format.value,
             "s3_url": f.s3_url,
             "size_bytes": f.size_bytes}
            for f in book.files
        ],
        audio_files = [
            {"chapter_index": a.chapter_index,
             "title": a.title,
             "duration_sec": a.duration_sec,
             "s3_url": a.s3_url}
            for a in book.audio_files
        ],
        landings        = book.landings,
        files_download  = files_dl,
        audio_download  = audio_dl,
        created_at      = book.created_at,
        updated_at      = book.updated_at,
    )
