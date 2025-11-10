import logging
from collections import defaultdict
from datetime import datetime, timedelta, date
from typing import List, Dict, Any

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, selectinload

from ..models.models_v2 import (
    Book, BookFile, BookAudio,
    BookFileFormat, Author, BookLanding, User, Tag,
    BookAdVisit, BookLandingAdPeriod, Purchase
)
from ..schemas_v2.book import (
    BookCreate, BookUpdate,
    BookLandingCreate, BookLandingUpdate, BookDetailResponse, BookLandingResponse, BookResponse
)
from ..utils.s3 import generate_presigned_url

log = logging.getLogger(__name__)

# TTL для флага рекламы (должно совпадать с логикой курсовых лендингов)
BOOK_AD_TTL = timedelta(hours=14)
BOOK_AD_UNIQUE_IP_WINDOW = BOOK_AD_TTL
BOOK_AD_MIN_UNIQUE_IPS = 3

# ─────────────────────────── S3/PDF метаданные ────────────────────────────────
PDF_CACHE_CONTROL = "public, max-age=86400, immutable, no-transform"
PDF_CONTENT_DISPOSITION = "inline"


def _clean_metadata(values: Dict[str, str]) -> Dict[str, str]:
    """
    Убираем пустые значения, чтобы не записывать лишние x-amz-meta-*.
    """
    return {k: v for k, v in values.items() if v}


def pdf_extra_args(metadata: Dict[str, str] | None = None) -> Dict[str, Any]:
    """
    Стандартные ExtraArgs для PDF, чтобы браузеры правильно обрабатывали файл.
    """
    extra: Dict[str, Any] = {
        "ACL": "public-read",
        "ContentType": "application/pdf",
        "ContentDisposition": PDF_CONTENT_DISPOSITION,
        "CacheControl": PDF_CACHE_CONTROL,
    }
    if metadata:
        extra["Metadata"] = metadata
    return extra


def original_pdf_metadata(book: Book) -> Dict[str, str]:
    """
    Базовая метадата для оригинального PDF-файла книги.
    """
    values = {
        "asset": "original",
        "book-id": str(book.id),
        "book-slug": getattr(book, "slug", "") or "",
    }
    return _clean_metadata(values)


def preview_pdf_metadata(book: Book, pages: int) -> Dict[str, str]:
    """
    Метадата для превью PDF (число страниц и ссылка на книгу).
    """
    values = {
        "asset": "preview",
        "book-id": str(book.id),
        "book-slug": getattr(book, "slug", "") or "",
        "pages": str(pages),
    }
    return _clean_metadata(values)

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
        cover_url   = (str(payload.cover_url) if payload.cover_url else None),
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


# ============================================================================
# Функции для аналитики рекламы книжных лендингов
# ============================================================================

def open_book_ad_period_if_needed(db: Session, book_landing_id: int, started_by: int | None):
    """
    Открывает новый рекламный период для книжного лендинга если нет открытого.
    Использует блокировку для избежания гонки.
    """
    # блокируем открытый период, чтобы избежать гонки
    open_exists = (
        db.query(BookLandingAdPeriod.id)
          .filter(
              BookLandingAdPeriod.book_landing_id == book_landing_id,
              BookLandingAdPeriod.ended_at.is_(None),
          )
          .with_for_update()
          .first()
    )
    if open_exists:
        return

    db.add(BookLandingAdPeriod(
        book_landing_id=book_landing_id,
        started_at=datetime.utcnow(),
        ended_at=None,
        started_by=started_by,
        ended_by=None,
    ))


def _close_book_ad_period_if_open(db: Session, book_landing_id: int, ended_by: int | None = None):
    open_period = (
        db.query(BookLandingAdPeriod)
          .filter(
              BookLandingAdPeriod.book_landing_id == book_landing_id,
              BookLandingAdPeriod.ended_at.is_(None),
          )
          .with_for_update()
          .first()
    )
    if open_period:
        open_period.ended_at = datetime.utcnow()
        open_period.ended_by = ended_by


def _unique_ip_count_recent(db: Session, book_landing_id: int, window_end: datetime) -> int:
    window_start = window_end - BOOK_AD_UNIQUE_IP_WINDOW
    count = (
        db.query(func.count(func.distinct(BookAdVisit.ip_address)))
          .filter(
              BookAdVisit.book_landing_id == book_landing_id,
              BookAdVisit.visited_at >= window_start,
              BookAdVisit.ip_address.isnot(None),
              BookAdVisit.ip_address != "",
          )
          .scalar()
    )
    return int(count or 0)


def track_book_ad_visit(db: Session, book_landing_id: int, fbp: str | None, fbc: str | None, ip: str):
    """
    Отслеживает визит с рекламы на книжный лендинг с метаданными (fbp, fbc, ip).
    Загорает флаг только после порога уникальных IP за окно BOOK_AD_UNIQUE_IP_WINDOW.
    Если активная реклама не набирает порог — выключает её.
    """
    now = datetime.utcnow()
    visit = BookAdVisit(
        book_landing_id=book_landing_id,
        fbp=fbp,
        fbc=fbc,
        ip_address=(ip.strip() if ip else None),
        visited_at=now,
    )
    db.add(visit)
    db.flush()

    book_landing = (
        db.query(BookLanding)
          .filter(BookLanding.id == book_landing_id)
          .with_for_update()
          .first()
    )
    if not book_landing:
        db.commit()
        return

    unique_count = _unique_ip_count_recent(db, book_landing_id, now)

    if not book_landing.in_advertising:
        if unique_count >= BOOK_AD_MIN_UNIQUE_IPS:
            book_landing.in_advertising = True
            book_landing.ad_flag_expires_at = now + BOOK_AD_TTL
            open_book_ad_period_if_needed(db, book_landing_id, started_by=None)
        else:
            # не достигли порога — убедимся, что открытых периодов нет
            _close_book_ad_period_if_open(db, book_landing_id, ended_by=None)
    else:
        if unique_count < BOOK_AD_MIN_UNIQUE_IPS:
            book_landing.in_advertising = False
            book_landing.ad_flag_expires_at = None
            _close_book_ad_period_if_open(db, book_landing_id, ended_by=None)
        else:
            open_book_ad_period_if_needed(db, book_landing_id, started_by=None)
            new_exp = now + BOOK_AD_TTL
            if not book_landing.ad_flag_expires_at or book_landing.ad_flag_expires_at < new_exp:
                book_landing.ad_flag_expires_at = new_exp

    db.commit()


def check_and_reset_book_ad_flag(book_landing: BookLanding, db: Session):
    """
    Если у книжного лендинга in_advertising=True, но ad_flag_expires_at < now,
    сбрасываем in_advertising в False.
    """
    if book_landing.in_advertising and book_landing.ad_flag_expires_at:
        now = datetime.utcnow()
        if book_landing.ad_flag_expires_at < now:
            book_landing.in_advertising = False
            book_landing.ad_flag_expires_at = None
            _close_book_ad_period_if_open(db, book_landing.id, ended_by=None)


def reset_expired_book_ad_flags(db: Session):
    """
    Массовый сброс истекших флагов рекламы для книжных лендингов.
    """
    expiring_ids = {
        lid for (lid,) in
        db.query(BookLanding.id)
          .filter(
              BookLanding.in_advertising.is_(True),
              BookLanding.ad_flag_expires_at.isnot(None),
              BookLanding.ad_flag_expires_at < func.utc_timestamp(),
          )
          .all()
    }

    cutoff = datetime.utcnow() - BOOK_AD_TTL
    stale_period_ids = {
        lid for (lid,) in
        db.query(BookLandingAdPeriod.book_landing_id)
          .join(BookLanding, BookLanding.id == BookLandingAdPeriod.book_landing_id)
          .filter(
              BookLanding.in_advertising.is_(True),
              BookLanding.ad_flag_expires_at.is_(None),
              BookLandingAdPeriod.ended_at.is_(None),
              BookLandingAdPeriod.started_at < cutoff,
          )
          .distinct()
          .all()
    }

    target_ids = expiring_ids | stale_period_ids

    if not target_ids:
        return 0

    db.query(BookLandingAdPeriod) \
      .filter(
          BookLandingAdPeriod.book_landing_id.in_(target_ids),
          BookLandingAdPeriod.ended_at.is_(None),
      ) \
      .update(
          {
              BookLandingAdPeriod.ended_at: func.utc_timestamp(),
              BookLandingAdPeriod.ended_by: None,
          },
          synchronize_session=False,
      )

    db.query(BookLanding) \
      .filter(BookLanding.id.in_(target_ids)) \
      .update(
          {
              BookLanding.in_advertising: False,
              BookLanding.ad_flag_expires_at: None,
          },
          synchronize_session=False,
      )

    db.commit()
    return len(target_ids)


# ============================================================================
# Аналитика продаж книжных лендингов
# ============================================================================

def get_book_purchases_by_language(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
):
    """
    Возвращает агрегированную статистику покупок книжных лендингов по языкам
    за период [start_dt, end_dt).
    """
    rows = (
        db.query(
            BookLanding.language.label("language"),
            func.count(Purchase.id).label("purchase_count"),
            func.coalesce(func.sum(Purchase.amount), 0).label("total_amount"),
        )
        .join(Purchase, Purchase.book_landing_id == BookLanding.id)
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at < end_dt,
        )
        .group_by(BookLanding.language)
        .all()
    )

    return [
        {
            "language": row.language,
            "count": row.purchase_count,
            "total_amount": f"{row.total_amount:.2f} $",
        }
        for row in rows
    ]


def get_book_purchases_by_language_per_day(
    db: Session,
    start_dt: datetime,
    end_dt: datetime,
):
    """
    Возвращает статистику покупок книжных лендингов по языкам с разбивкой по дням
    за период [start_dt, end_dt).
    """
    day_col = func.date(Purchase.created_at)

    rows = (
        db.query(
            day_col.label("day"),
            BookLanding.language.label("language"),
            func.count(Purchase.id).label("purchase_count"),
            func.coalesce(func.sum(Purchase.amount), 0).label("total_amount"),
        )
        .join(Purchase, Purchase.book_landing_id == BookLanding.id)
        .filter(
            Purchase.created_at >= start_dt,
            Purchase.created_at < end_dt,
        )
        .group_by(day_col, BookLanding.language)
        .order_by(day_col)
        .all()
    )

    stats: dict[date, dict[str, dict[str, str | int]]] = defaultdict(dict)

    for row in rows:
        stats[row.day][row.language] = {
            "language": row.language,
            "count": row.purchase_count,
            "total_amount": f"{row.total_amount:.2f} $",
        }

    data = []
    current = start_dt.date()
    last = end_dt.date()

    while current < last:
        languages = list(stats.get(current, {}).values())
        data.append(
            {
                "date": current.isoformat(),
                "languages": languages,
            }
        )
        current += timedelta(days=1)

    return data
