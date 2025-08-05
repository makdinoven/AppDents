import logging
from typing import List
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from ..models.models_v2 import (
    Book, BookFile, BookAudio,
    BookFileFormat, Author, BookLanding
)
from ..schemas_v2.book import (
    BookCreate, BookUpdate,
    BookLandingCreate, BookLandingUpdate
)

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

def create_book(db: Session, payload: BookCreate) -> Book:
    log.info("[BOOK] Creating «%s»", payload.title)
    authors = _fetch_authors(db, payload.author_ids)

    book = Book(
        title       = payload.title,
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
