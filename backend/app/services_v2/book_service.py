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

# >>> app/services_v2/book_service.py — ЗАМЕНИ get_book_landing_by_slug <<<

def get_book_landing_by_slug(
        db: Session, slug: str, language: str | None = None
) -> BookLandingResponse:
    """
    Возвращает первый НЕ скрытый лендинг книги по slug книги.
    • language – опциональный фильтр ('RU','EN',…).
    • preview_* поля приводим к публичным URL (CDN или Signed URL).
    • ВКЛЮЧЕНО: included_books (каждая книга с preview_pdf) и bundle_size.
    """
    # 1) найдём книгу по slug
    book = (
        db.query(Book)
          .options(selectinload(Book.landings))
          .filter(Book.slug == slug)
          .first()
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # 2) найдём её видимый лендинг с нужным языком
    q = (
        db.query(BookLanding)
          .options(
              selectinload(BookLanding.books_bundle),
              selectinload(BookLanding.book),
          )
          .filter(
              BookLanding.book_id == book.id,
              BookLanding.is_hidden.is_(False),
          )
    )
    if language:
        q = q.filter(BookLanding.language == language.upper())

    landing = q.order_by(BookLanding.id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    # 3) подготовим helper для URL
    def _pub(url: str | None) -> str | None:
        # если http/https — вернём как есть; если s3:// — подпишем
        return generate_presigned_url(url, expires=timedelta(hours=24)) if url else None

    # 4) какие книги входят в лендинг (bundle > одиночная)
    books = books_in_landing(db, landing)  # уже есть в этом модуле ниже
    log.info("[BOOK-LANDING] slug=%s landing=%s includes %d book(s)",
             slug, landing.page_name, len(books))

    # 5) сериализуем список книг с превью-PDF каждой книги
    included_books = []
    for b in books:
        included_books.append({
            "id": b.id,
            "title": b.title,
            "slug": b.slug,
            "cover_url": b.cover_url,
            "preview_pdf": _pub(getattr(b, "preview_pdf", None)),
        })

    # 6) собрать итоговый ответ
    return BookLandingResponse(
        id            = landing.id,
        book_id       = landing.book_id,
        page_name     = landing.page_name,
        language      = landing.language,
        landing_name  = landing.landing_name,
        old_price     = landing.old_price,
        new_price     = landing.new_price,
        description   = landing.description,
        preview_photo = _pub(landing.preview_photo),
        preview_pdf   = _pub(landing.preview_pdf),
        preview_imgs  = [_pub(u) for u in (landing.preview_imgs or [])] or None,
        sales_count   = landing.sales_count,
        is_hidden     = landing.is_hidden,

        included_books = included_books,     # ← добавили
        bundle_size    = len(included_books) # ← добавили
    )

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