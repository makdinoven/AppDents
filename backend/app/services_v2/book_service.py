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
        page_count=book.page_count,
        publishers=[{"id": p.id, "name": p.name} for p in (book.publishers or [])],
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


def create_book(db: Session, payload: BookCreate) -> Book:
    log.info("[BOOK] Creating «%s»", payload.title)
    authors = _fetch_authors(db, payload.author_ids)

    book = Book(
        title       = payload.title,
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
    Возвращает список книг для книжного лендинга `bl`, читая из M2M-таблицы `book_landing_books`.
    - Если relationship `bl.books` настроен, используем его.
    - Иначе явно джойним через таблицу-связку.
    - Дубликаты удаляем, порядок сохраняем.
    """
    # 1) Если у модели уже настроен relationship на книги — используем
    try:
        if hasattr(bl, "books") and bl.books:
            # удалим дубликаты, сохраняя порядок
            seen, out = set(), []
            for b in bl.books:
                if b.id not in seen:
                    seen.add(b.id)
                    out.append(b)
            return out
    except Exception:
        pass

    # 2) Явный запрос через таблицу-связку
    try:
        # Импортируем саму таблицу-связку (SQLAlchemy Table)
        from ..models.models_v2 import book_landing_books  # Table с колонками: book_landing_id, book_id

        books = (
            db.query(Book)
              .join(book_landing_books, book_landing_books.c.book_id == Book.id)
              .filter(book_landing_books.c.book_landing_id == bl.id)
              .all()
        )

        # Дедупликат, сохранение порядка
        seen, out = set(), []
        for b in books:
            if b.id not in seen:
                seen.add(b.id)
                out.append(b)

        if not out:
            log.warning("[BOOKS] Landing %s: no rows in book_landing_books", getattr(bl, "id", "?"))
        return out

    except Exception as e:
        log.exception("[BOOKS] Failed to read books for landing %s via book_landing_books: %s", getattr(bl, "id", "?"), e)

    # 3) Фолбэк (на случай старых схем)
    if getattr(bl, "book", None):
        return [bl.book]

    log.warning("[BOOKS] Landing %s has no bound books", getattr(bl, "id", "?"))
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
