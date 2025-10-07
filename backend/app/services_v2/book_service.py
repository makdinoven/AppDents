import logging
from datetime import timedelta
from typing import List
from sqlalchemy.orm import Session, selectinload
from fastapi import HTTPException, status

from ..models.models_v2 import (
    Book, BookFile, BookAudio,
    BookFileFormat, Author, BookLanding, User, Tag
)
from ..schemas_v2.book import (
    BookCreate, BookUpdate,
    BookLandingCreate, BookLandingUpdate, BookDetailResponse, BookLandingResponse, BookResponse
)
from ..utils.s3 import generate_presigned_url

log = logging.getLogger(__name__)

def _serialize_book_file(bf: BookFile) -> dict:
    return {
        "file_format": bf.file_format.value,
        "s3_url": bf.s3_url,
        "size_bytes": bf.size_bytes,
    }

def _serialize_book_audio(ba: BookAudio) -> dict:
    return {
        "chapter_index": ba.chapter_index,
        "title": ba.title,
        "duration_sec": ba.duration_sec,
        "s3_url": ba.s3_url,
    }

def _book_to_response(book: Book) -> BookResponse:
    """
    Преобразует ORM Book → BookResponse для ответов create/update.
    Делает нужные списки словарей и author_ids.
    """
    return BookResponse(
        id=book.id,
        title=book.title,
        description=book.description,
        cover_url=book.cover_url,
        language=book.language,
        author_ids=[a.id for a in (book.authors or [])],
        files=[_serialize_book_file(f) for f in (book.files or [])],
        audio_files=[_serialize_book_audio(a) for a in (book.audio_files or [])],
        created_at=book.created_at,
        updated_at=book.updated_at,
        publication_date=book.publication_date,
    )

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

def _fetch_tags(db: Session, ids: list[int]) -> list[Tag]:
    if not ids:
        return []
    tags = db.query(Tag).filter(Tag.id.in_(ids)).all()
    if len(tags) != len(ids):
        absent = sorted(set(ids) - {t.id for t in tags})
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Tags not found: {absent}",
        )
    return tags

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
        tags=_fetch_tags(db, payload.tag_ids),
        authors     = authors,
        publication_date=payload.publication_date,
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
    return _book_to_response(book)

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
    if payload.publication_date is not None:
        book.publication_date = payload.publication_date
    if payload.author_ids is not None:
        book.authors = _fetch_authors(db, payload.author_ids)
    if payload.slug is not None and payload.slug != book.slug:
        _ensure_unique_slug(db, payload.slug,
                            exclude_book_id=book.id)
        book.slug = payload.slug
    if payload.tag_ids is not None:
        book.tags = _fetch_tags(db, payload.tag_ids)
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
    return _book_to_response(book)

def delete_book(db: Session, book_id: int) -> None:
    rows = db.query(Book).filter(Book.id == book_id).delete()
    if not rows:
        raise HTTPException(status_code=404, detail="Book not found")
    db.commit()
    log.warning("[BOOK] id=%d удалена", book_id)

def delete_book_landing(db: Session, landing_id: int) -> None:
    rows = db.query(BookLanding).filter(BookLanding.id == landing_id).delete()
    if not rows:
        raise HTTPException(status_code=404, detail="Landing not found")
    db.commit()
    log.warning("[BOOK-LANDING] id=%d удалён", landing_id)

def books_in_landing(db: Session, bl: BookLanding) -> list[Book]:
    """
    Возвращает список книг, которые покупатель получит при покупке этого книжного лендинга.
    Если M2M-бандл задан — он приоритетен. Иначе — одиночная книга из bl.book.
    """
    if bl.books_bundle:
        return list(bl.books_bundle)
    if getattr(bl, "book", None):
        return [bl.book]
    log.warning("[BOOKS] Landing %s has no books bound", bl.id)
    return []

def paginate_like_courses(query, page: int, size: int, serializer) -> dict:
    total = query.count()
    rows = query.offset((page - 1) * size).limit(size).all()
    return {
        "page": page,
        "size": size,
        "total": total,
        "total_pages": (total + size - 1) // size,
        "items": [serializer(bl) for bl in rows],
    }

def to_float(v):
    try:
        return float(v) if v is not None else None
    except Exception:
        return None

def serialize_book_landing_to_course_item(bl: BookLanding) -> dict:
    """
    Возвращаем ровно те же поля, что ожидает LandingListItem (как в курсовых листингах).
    Лишних ключей не добавляем.
    """
    return {
        "id": bl.id,
        "page_name": bl.page_name,
        "landing_name": bl.landing_name,
        "language": bl.language,
        "is_hidden": bool(bl.is_hidden),
        "sales_count": bl.sales_count or 0,
        "new_price": to_float(bl.new_price),
        "old_price": to_float(bl.old_price),
    }
