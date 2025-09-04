import logging
import os
import tempfile
from datetime import datetime
from urllib.parse import quote

import redis
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form
from sqlalchemy import text
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, Book, BookFile, BookFileFormat, BookAudio, Tag
from ..services_v2.book_service import books_in_landing
from ..tasks.book_formats import _k_job as fmt_k_job, _k_log as fmt_k_log, _k_fmt

from ..celery_app import celery

# S3/Redis
import boto3
from botocore.config import Config

S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")
REDIS_URL      = os.getenv("REDIS_URL", "redis://redis:6379/0")

rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)
s3  = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

router = APIRouter()
log = logging.getLogger(__name__)

def _pdf_key(book: Book) -> str:
    return f"books/{book.slug}/{book.slug}.pdf"

def _cdn_url(key: str) -> str:
    # кодируем path, чтобы URL был валидным (пробелы → %20 и т.д.)
    safe_key = quote(key.lstrip('/'), safe="/-._~()")
    return f"{S3_PUBLIC_HOST}/{safe_key}"

@router.post("/{book_id}/upload-pdf", summary="Загрузить PDF книги и запустить генерацию форматов")
def upload_pdf_and_generate(
    book_id: int,
    file: UploadFile = File(..., description="PDF-файл"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    if not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Only .pdf allowed")

    # 1) заливаем PDF в S3 (public-read)
    with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    key = _pdf_key(book)
    s3.upload_file(tmp_path, S3_BUCKET, key, ExtraArgs={"ACL": "public-read", "ContentType": "application/pdf"})
    os.unlink(tmp_path)
    cdn_url = _cdn_url(key)

    # 2) фиксируем/обновляем PDF в book_files (сохраняем CDN-URL)
    pdf_row = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    size_bytes = None
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        size_bytes = int(head.get("ContentLength") or 0)
    except Exception:
        pass

    if pdf_row:
        pdf_row.s3_url = cdn_url
        pdf_row.size_bytes = size_bytes
    else:
        db.add(BookFile(book_id=book.id, file_format=BookFileFormat.PDF, s3_url=cdn_url, size_bytes=size_bytes))
    db.commit()

    # 3) подготавливаем Redis-статусы и стартуем таску
    rds.hset(fmt_k_job(book.id), mapping={
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
    })
    rds.delete(fmt_k_log(book.id))
    for fmt in ("EPUB", "MOBI", "AZW3", "FB2"):
        rds.delete(_k_fmt(book.id, fmt))
    rds.hset(prev_k_job(book.id), mapping={
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
    })
    rds.delete(prev_k_log(book.id))

    # 4) пинаем Celery
    celery.send_task("app.tasks.book_formats.generate_book_formats", args=[book.id], queue="book")
    celery.send_task("app.tasks.book_previews.generate_book_preview", args=[book.id], queue="book")
    log.info("[ADMIN] PDF uploaded for book_id=%s, task queued", book.id)
    return {"message": "PDF uploaded, conversion started", "book_id": book.id, "pdf_url": cdn_url}

@router.post("/{book_id}/generate-formats", summary="Запустить конвертацию (если PDF уже загружен)")
def start_generation(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    pdf = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    if not pdf:
        raise HTTPException(status_code=400, detail="No PDF file found for this book")

    rds.hset(fmt_k_job(book.id), mapping={"status": "pending", "created_at": datetime.utcnow().isoformat() + "Z"})
    rds.delete(fmt_k_log(book.id))
    for fmt in ("EPUB", "MOBI", "AZW3", "FB2"):
        rds.delete(_k_fmt(book.id, fmt))

    celery.send_task("app.tasks.book_formats.generate_book_formats", args=[book.id], queue="book")
    return {"message": "Conversion started", "book_id": book.id}

@router.get("/{book_id}/format-status", summary="Статус конвертации книги (Redis)")
def get_format_status(
    book_id: int,
    current_admin: User = Depends(require_roles("admin")),
):
    job = rds.hgetall(fmt_k_job(book_id)) or {}
    formats = {}
    for fmt in ("PDF", "EPUB", "MOBI", "AZW3", "FB2"):
        formats[fmt] = rds.hgetall(_k_fmt(book_id, fmt)) or {}
    logs = rds.lrange(fmt_k_log(book_id), 0, 100) # последние 100 строк
    return {"job": job, "formats": formats, "logs": logs}

@router.post("/{user_id}/books/{book_id}", summary="Выдать книгу пользователю (Админ)")
def grant_book_to_user(
    user_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin"))
):
    user = db.query(User).get(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # Идемпотентная выдача доступа
    db.execute(
        text("INSERT IGNORE INTO users_books (user_id, book_id, granted_at) VALUES (:u,:b,UTC_TIMESTAMP())"),
        {"u": user_id, "b": book_id}
    )
    db.commit()
    logging.getLogger("admin.grant_book").info("Admin %s granted book %s to user %s", current_admin.id, book_id, user_id)
    return {"message": "Книга выдана пользователю", "user_id": user_id, "book_id": book_id}

from pydantic import BaseModel, Field
from ..models.models_v2 import BookLanding

class BundleSetPayload(BaseModel):
    book_ids: list[int]

class FinalizeUploadPayload(BaseModel):
    # Ключ объекта в бакете, который вы вернули из /upload-pdf-url
    key: str = Field(..., description="S3 object key (например books/3/original/book.pdf)")

@router.put("/book-landings/{landing_id}/books", summary="Задать полный список книг для лендинга (заменяет старый)")
def set_bundle_for_landing(
    landing_id: int,
    payload: BundleSetPayload,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    bl = db.query(BookLanding).get(landing_id)
    if not bl:
        raise HTTPException(status_code=404, detail="Book landing not found")

    books = db.query(Book).filter(Book.id.in_(payload.book_ids or [-1])).all()
    if len(books) != len(set(payload.book_ids or [])):
        raise HTTPException(status_code=400, detail="Some book_ids not found")

    bl.books_bundle = books
    db.commit()
    db.refresh(bl)

    return {
        "landing_id": bl.id,
        "bundle_size": len(books),
        "book_ids": [b.id for b in books],
    }

@router.post("/book-landings/{landing_id}/books/{book_id}", summary="Добавить книгу в бандл лендинга (idempotent)")
def add_book_to_bundle(
    landing_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    bl = db.query(BookLanding).get(landing_id)
    if not bl:
        raise HTTPException(status_code=404, detail="Book landing not found")
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    if book not in bl.books_bundle:
        bl.books_bundle.append(book)
        db.commit()

    return {"landing_id": bl.id, "book_ids": [b.id for b in bl.books_bundle]}

@router.delete("/book-landings/{landing_id}/books/{book_id}", summary="Удалить книгу из бандла лендинга")
def remove_book_from_bundle(
    landing_id: int,
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    bl = db.query(BookLanding).get(landing_id)
    if not bl:
        raise HTTPException(status_code=404, detail="Book landing not found")
    bl.books_bundle = [b for b in bl.books_bundle if b.id != book_id]
    db.commit()
    return {"landing_id": bl.id, "book_ids": [b.id for b in bl.books_bundle]}

@router.post("/{book_id}/audios", summary="Загрузить аудио для книги (целиком или по главам)")
def upload_book_audio(
    book_id: int,
    file: UploadFile = File(..., description="Аудиофайл (mp3/ogg/...)"),
    chapter_index: int | None = Form(None, description="Номер главы (опционально)"),
    title: str | None = Form(None, description="Название главы/записи"),
    duration_sec: int | None = Form(None, description="Длительность, сек"),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # сохраняем файл в S3: books/<slug>/audio/<fname>
    import os, tempfile
    from uuid import uuid4

    ext = os.path.splitext(file.filename or "")[1].lower() or ".mp3"
    fname = f"{uuid4().hex}{ext}"

    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
        tmp.write(file.file.read())
        tmp_path = tmp.name

    key = f"books/{book.slug}/audio/{fname}"
    ct = "audio/mpeg" if ext == ".mp3" else "application/octet-stream"
    s3.upload_file(tmp_path, S3_BUCKET, key, ExtraArgs={"ACL": "public-read", "ContentType": ct})
    os.unlink(tmp_path)

    cdn_url = f"{S3_PUBLIC_HOST}/{key}"

    audio = BookAudio(
        book_id=book.id,
        chapter_index=chapter_index,
        title=title,
        duration_sec=duration_sec,
        s3_url=cdn_url,
    )
    db.add(audio)
    db.commit()
    db.refresh(audio)

    return {
        "message": "Аудио загружено",
        "audio": {
            "id": audio.id,
            "chapter_index": audio.chapter_index,
            "title": audio.title,
            "duration_sec": audio.duration_sec,
            "url": cdn_url,
        }
    }

@router.delete("/audios/{audio_id}", summary="Удалить аудиозапись книги")
def delete_book_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    a = db.query(BookAudio).get(audio_id)
    if not a:
        raise HTTPException(status_code=404, detail="Audio not found")
    # файл оставляем на CDN или можно попытаться удалить из S3 — по желанию.
    db.delete(a)
    db.commit()
    return {"message": "Аудио удалено", "audio_id": audio_id}

from pydantic import BaseModel

class BookTagsPayload(BaseModel):
    tag_ids: list[int]

@router.put("/{book_id}/tags", summary="Задать полный список тегов книги (замена)")
def set_book_tags(
    book_id: int,
    payload: BookTagsPayload,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    tags = db.query(Tag).filter(Tag.id.in_(payload.tag_ids or [-1])).all()
    if len(tags) != len(set(payload.tag_ids or [])):
        raise HTTPException(status_code=400, detail="Some tag_ids not found")

    book.tags = tags
    db.commit()
    db.refresh(book)
    return {"book_id": book.id, "tag_ids": [t.id for t in book.tags]}

@router.post("/{book_id}/tags/{tag_id}", summary="Добавить тег книге")
def add_book_tag(
    book_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    tag = db.query(Tag).get(tag_id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    if tag not in book.tags:
        book.tags.append(tag)
        db.commit()
    return {"book_id": book.id, "tag_ids": [t.id for t in book.tags]}

@router.delete("/{book_id}/tags/{tag_id}", summary="Удалить тег у книги")
def remove_book_tag(
    book_id: int,
    tag_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    book.tags = [t for t in book.tags if t.id != tag_id]
    db.commit()
    return {"book_id": book.id, "tag_ids": [t.id for t in book.tags]}

from ..celery_app import celery
# ключи статусов для превью (первые 10–15 страниц)
from ..tasks.book_previews import _k_job as prev_k_job, _k_log as prev_k_log


@router.post("/{book_id}/generate-preview", summary="Сгенерировать превью PDF (первые 15 страниц)")
def start_book_preview(
    book_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # подготовим статус и очистим логи
    rds.hset(prev_k_job(book.id), mapping={"status": "pending", "created_at": datetime.utcnow().isoformat() + "Z"})
    rds.delete(prev_k_log(book.id))

    celery.send_task("app.tasks.book_previews.generate_book_preview", args=[book.id], queue="book")
    return {"message": "Preview generation started", "book_id": book.id}

@router.get("/{book_id}/preview-status", summary="Статус генерации превью (Redis)")
def book_preview_status(
    book_id: int,
    current_admin: User = Depends(require_roles("admin")),
):
    job = rds.hgetall(prev_k_job(book_id)) or {}
    logs = rds.lrange(prev_k_log(book_id), 0, 100)
    return {"job": job, "logs": logs}


@router.post("/book-landings/{landing_id}/generate-previews", summary="Сгенерировать превью для всех книг лендинга")
def start_landing_previews(
    landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    bl = (
        db.query(BookLanding)
          .options(selectinload(BookLanding.books_bundle), selectinload(BookLanding.book))
          .get(landing_id)
    )
    if not bl:
        raise HTTPException(status_code=404, detail="Book landing not found")

    books = list(bl.books_bundle or [])
    if not books and getattr(bl, "book", None):
        books = [bl.book]
    if not books:
        raise HTTPException(status_code=400, detail="No books bound to this landing")

    queued = []
    for b in books:
        rds.hset(prev_k_job(b.id), mapping={"status": "pending", "created_at": datetime.utcnow().isoformat() + "Z"})
        rds.delete(prev_k_log(b.id))
        celery.send_task("app.tasks.book_previews.generate_book_preview", args=[b.id], queue="book")
        queued.append(b.id)

    return {"message": "Preview tasks queued", "landing_id": landing_id, "book_ids": queued}


@router.post("/admin/{user_id}/book-landings/{landing_id}",
             summary="Выдать пользователю все книги из книжного лендинга (Админ)")
def grant_books_from_landing(
    user_id: int,
    landing_id: int,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Добавляет пользователю все книги, входящие в указанный книжный лендинг (bundle или одиночная).
    Использует INSERT IGNORE в users_books, чтобы не было ошибок при повторной выдаче.
    """
    logger = logging.getLogger("admin.grant_books")

    bl = db.query(BookLanding).get(landing_id)
    if not bl:
        raise HTTPException(status_code=404, detail="Landing not found")

    books = books_in_landing(db, bl)
    if not books:
        raise HTTPException(status_code=400, detail="No books bound to this landing")

    # INSERT IGNORE для MySQL — безопасно при повторной выдаче
    values_sql = ",".join(f"({user_id},{b.id})" for b in books)
    db.execute(text(f"INSERT IGNORE INTO users_books (user_id, book_id) VALUES {values_sql}"))
    db.commit()

    logger.info("[ADMIN][GRANT] user_id=%s landing_id=%s -> books=%s",
                user_id, landing_id, [b.id for b in books])

    return {
        "message": "Books granted",
        "user_id": user_id,
        "landing_id": landing_id,
        "book_ids": [b.id for b in books],
        "count": len(books),
    }

@router.post("/admin/books/{book_id}/upload-pdf-finalize",
             summary="Завершить загрузку PDF: зафиксировать в БД, запустить превью и конвертацию форматов")
def finalize_pdf_upload(
    book_id: int,
    payload: FinalizeUploadPayload,
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Что делает:
      1) Проверяет, что объект `key` существует в S3, берёт размер.
      2) Сохраняет/обновляет запись BookFile(PDF) у книги, с CDN-URL и size_bytes.
      3) Инициализирует статусы в Redis.
      4) Ставит две Celery-таски:
         - app.tasks.book_previews.generate_book_preview
         - app.tasks.book_formats.generate_book_formats
    """
    # 0) Валидации
    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    key = (payload.key or "").lstrip("/")
    if not key or not key.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Key must point to a .pdf object")

    # Не строго, но подсветим возможный промах книгой
    # (напр., ключ содержит другой id/slug) — это только warn в лог.
    if f"/{book_id}/" not in f"/{key}/" and f"/{book.slug}/" not in f"/{key}/":
        log.warning("[BOOK][FINALIZE] key %s не выглядит относящимся к книге id=%s slug=%s",
                    key, book_id, book.slug)

    # 1) head_object — убеждаемся, что файл на месте и берём размер
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    except Exception as e:
        log.error("[BOOK][FINALIZE] S3 head_object error for key=%s: %s", key, e)
        raise HTTPException(status_code=400, detail="S3 object not found (key invalid?)")

    size_bytes = int(head.get("ContentLength") or 0)
    cdn_url = _cdn_url(key)  # публичный адрес для фронта / для скачивания без подписи

    # 2) UPSERT BookFile(PDF)
    pdf_row = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    if pdf_row:
        pdf_row.s3_url = cdn_url
        pdf_row.size_bytes = size_bytes
    else:
        db.add(BookFile(
            book_id=book.id,
            file_format=BookFileFormat.PDF,
            s3_url=cdn_url,
            size_bytes=size_bytes,
        ))
    db.commit()

    # 3) Инициализация статусов в Redis
    # --- превью (первые 10–15 страниц) ---
    rds.hset(prev_k_job(book.id), mapping={
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "note": "awaiting preview generation",
    })
    rds.delete(prev_k_log(book.id))  # чистим логи предыдущих попыток

    # --- форматы (EPUB/MOBI/AZW3/FB2) ---
    rds.hset(fmt_k_job(book.id), mapping={
        "status": "pending",
        "created_at": datetime.utcnow().isoformat() + "Z",
        "note": "awaiting calibre conversion",
    })
    rds.delete(fmt_k_log(book.id))
    for fmt in ("EPUB", "MOBI", "AZW3", "FB2"):
        rds.delete(_k_fmt(book.id, fmt))

    # 4) Ставим Celery-таски (queue="special" как в конфиге)
    celery.send_task("app.tasks.book_previews.generate_book_preview",
                     args=[book.id], queue="book")
    celery.send_task("app.tasks.book_formats.generate_book_formats",
                     args=[book.id], queue="book")

    log.info("[BOOK][FINALIZE] book_id=%s key=%s size=%sB → tasks queued", book.id, key, size_bytes)
    return {
        "message": "PDF finalized, preview & formats generation started",
        "book_id": book.id,
        "pdf_cdn_url": cdn_url,
        "size_bytes": size_bytes,
        "tasks": {
            "preview": "queued",
            "formats": "queued",
        }
    }
