# API для файлов и аудио книг:
#  - GET /api/books/{book_id}/assets      — список форматов и аудио; у владельца есть download_url
#  - GET /api/books/{book_id}/download    — выдать presigned URL по формату (PDF/EPUB/...)
#  - GET /api/books/{book_id}/pdf         — потоковая раздача PDF с поддержкой Range (200 OK → 206 Partial)
#  - GET /api/books/audios/{audio_id}/download — presigned URL аудиодорожки
# Требует: users_books, модели Book/BookFile/BookAudio, utils.s3.generate_presigned_url, boto3

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from .users import get_current_user
from ..models.models_v2 import User, Book, BookAudio, BookFileFormat
from ..utils.s3 import generate_presigned_url
from ..services_v2.book_service import PDF_CACHE_CONTROL, PDF_CONTENT_DISPOSITION

# S3 client для стриминга
import os
import boto3
from botocore.config import Config

S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── helpers ─────────────────────────────────────────────────────────────────

def _is_admin(user: User) -> bool:
    return (user.role or "").lower() in {"admin", "superadmin", "owner"}

def _user_owns_book(db: Session, user_id: int, book_id: int) -> bool:
    # быстрый и дешёвый запрос
    row = db.execute(
        "SELECT 1 FROM users_books WHERE user_id=:u AND book_id=:b LIMIT 1",
        {"u": user_id, "b": book_id},
    ).first()
    return bool(row)

def _sign(url: Optional[str], filename: Optional[str] = None) -> Optional[str]:
    if not url:
        return None
    
    # Если указано имя файла, добавляем Content-Disposition для скачивания
    content_disposition = None
    if filename:
        # Экранируем кавычки в имени файла
        safe_filename = filename.replace('"', '\\"')
        content_disposition = f'attachment; filename="{safe_filename}"'
    
    return generate_presigned_url(
        url, 
        expires=timedelta(hours=24),
        response_content_disposition=content_disposition
    )


def _s3_key_from_url(url: str) -> str:
    """Извлекает ключ объекта из публичного/прямого URL."""
    from urllib.parse import urlparse, unquote
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path


def _generate_filename(book: Book, format: str) -> str:
    """
    Генерирует безопасное имя файла для скачивания.
    Использует slug, или очищенный title, или id книги.
    """
    import re
    
    if book.slug:
        base_name = book.slug
    elif book.title:
        # Очищаем title от недопустимых символов для имени файла
        base_name = re.sub(r'[^\w\s-]', '', book.title).strip().replace(' ', '-').lower()[:50]
    else:
        base_name = f"book-{book.id}"
    
    return f"{base_name}.{format.lower()}"


# ── API ─────────────────────────────────────────────────────────────────────

@router.get("/{book_id}/assets", summary="Список форматов и аудио по книге")
def get_book_assets(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Отдаёт метаданные по доступным файлам и аудио.
    • Если пользователь владеет книгой (или админ) — добавляем presigned `download_url`.
    • Иначе — только список форматов/аудио без ссылок (для UI).
    """
    book = (
        db.query(Book)
          .options(
              selectinload(Book.files),
              selectinload(Book.audio_files),
          )
          .get(book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    owns = _is_admin(user) or _user_owns_book(db, user.id, book_id)

    files = []
    for f in book.files:
        format_value = f.file_format.value if hasattr(f.file_format, "value") else str(f.file_format)
        filename = _generate_filename(book, format_value) if owns else None
        
        files.append({
            "format": format_value,
            "size_bytes": f.size_bytes,
            "download_url": _sign(f.s3_url, filename=filename) if owns else None,
        })

    audios = []
    for a in book.audio_files:
        audios.append({
            "id": a.id,
            "chapter_index": a.chapter_index,
            "title": a.title,
            "duration_sec": a.duration_sec,
            "download_url": _sign(a.s3_url) if owns else None,
        })

    return {
        "book": {
            "id": book.id,
            "title": book.title,
            "slug": book.slug,
            "cover_url": book.cover_url,
        },
        "owned": owns,
        "files": files,
        "audios": audios,
    }


@router.get("/{book_id}/download", summary="Скачать книгу в выбранном формате (только для владельцев)")
def download_book_file(
    book_id: int,
    fmt: BookFileFormat = Query(..., description="Формат файла: PDF/EPUB/MOBI/AZW3/FB2"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Возвращает presigned URL на файл книги `fmt`.
    Доступно владельцам книги и администраторам.
    """
    if not (_is_admin(user) or _user_owns_book(db, user.id, book_id)):
        raise HTTPException(status_code=403, detail="No access to this book")

    # ищем книгу и нужный формат
    book = db.query(Book).options(selectinload(Book.files)).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")
    
    f = next((bf for bf in book.files if bf.file_format == fmt), None)
    if not f:
        raise HTTPException(status_code=404, detail=f"File in format {fmt} not found")

    # Генерируем имя файла для скачивания
    filename = _generate_filename(book, fmt.value)
    
    return {"url": _sign(f.s3_url, filename=filename)}


@router.get("/audios/{audio_id}/download", summary="Скачать аудиоглаву/аудиокнигу (только для владельцев)")
def download_book_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Возвращает presigned URL на аудиофайл книги (глава или полная версия).
    Доступ только у владельца соответствующей книги и у администратора.
    """
    audio = (
        db.query(BookAudio)
          .options(selectinload(BookAudio.book))
          .get(audio_id)
    )
    if not audio:
        raise HTTPException(status_code=404, detail="Audio not found")

    book_id = audio.book_id
    if not (_is_admin(user) or _user_owns_book(db, user.id, book_id)):
        raise HTTPException(status_code=403, detail="No access to this audio")

    return {"url": _sign(audio.s3_url)}


@router.get("/{book_id}/pdf", summary="Потоковая раздача PDF с поддержкой Range")
def stream_book_pdf(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Возвращает PDF с поддержкой HTTP Range, проксируя запрос в S3.
    
    Для запросов без Range header возвращает полный файл (200 OK).
    Для Range запросов возвращает частичный контент (206 Partial Content).
    """
    book = (
        db.query(Book)
          .options(selectinload(Book.files))
          .get(book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    # ищем PDF
    pdf_file = next((f for f in (book.files or []) if f.file_format == BookFileFormat.PDF), None)
    if not pdf_file or not pdf_file.s3_url:
        raise HTTPException(status_code=404, detail="PDF not found")

    key = _s3_key_from_url(pdf_file.s3_url)

    range_header = request.headers.get("range") or request.headers.get("Range")
    logger.info(f"PDF request for book {book_id}: Range header = {range_header}")
    
    # Всегда получаем размер файла через head_object
    try:
        head_obj = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
        file_size = head_obj.get("ContentLength", 0)
        metadata = head_obj.get("Metadata") or {}
        logger.info(f"PDF file size: {file_size} bytes ({file_size / 1024 / 1024:.2f} MB)")
    except s3_client.exceptions.NoSuchKey:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="PDF not found")
    except Exception as e:
        logger.error("S3 head_object error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch PDF metadata")
    
    get_kwargs = {"Bucket": S3_BUCKET, "Key": key}
    
    if range_header:
        # Если есть Range header от клиента - используем его
        get_kwargs["Range"] = range_header
        logger.info(f"Using client Range: {range_header}")
    else:
        # Первый запрос без Range - стримим весь файл
        # PDF.js увидит Accept-Ranges: bytes и МОЖЕТ начать делать Range-запросы
        # (но это не гарантировано - зависит от настроек PDF.js)
        logger.info(f"Request without Range header, streaming full file ({file_size} bytes)")

    try:
        obj = s3_client.get_object(**get_kwargs)
    except s3_client.exceptions.NoSuchKey:  # type: ignore[attr-defined]
        raise HTTPException(status_code=404, detail="PDF not found")
    except Exception as e:
        logger.error("S3 get_object error: %s", e)
        raise HTTPException(status_code=502, detail="Failed to fetch PDF")

    body = obj["Body"]
    content_type = obj.get("ContentType") or "application/pdf"
    content_length = obj.get("ContentLength")
    content_range = obj.get("ContentRange")
    
    # Если metadata не получена из head_object, пробуем из get_object
    if not metadata:
        metadata = obj.get("Metadata") or {}

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
        "Content-Disposition": PDF_CONTENT_DISPOSITION,
        "Cache-Control": PDF_CACHE_CONTROL,
    }
    
    # Если был Range запрос - возвращаем 206 Partial Content
    # Если не было Range - возвращаем 200 OK, PDF.js увидит Accept-Ranges и начнет делать Range-запросы
    if content_range:
        headers["Content-Range"] = content_range
        headers["Content-Length"] = str(content_length) if content_length else str(0)
        status_code = 206
        logger.info(f"Returning 206 Partial Content: {content_range}")
    else:
        headers["Content-Length"] = str(file_size)
        status_code = 200
        logger.info(f"Returning 200 OK with full Content-Length: {file_size}, PDF.js will use Range requests")

    if metadata.get("asset"):
        headers["X-Book-Pdf-Asset"] = metadata["asset"]
    if metadata.get("pages"):
        headers["X-Book-Preview-Pages"] = metadata["pages"]
    if metadata.get("book-id"):
        headers["X-Book-Id"] = metadata["book-id"]
    if metadata.get("book-slug"):
        headers["X-Book-Slug"] = metadata["book-slug"]

    # У объекта StreamingBody нет iter_chunks в старых версиях botocore; используем iter_chunks/iter_lines fallbacks
    iterator = getattr(body, "iter_chunks", None)
    if callable(iterator):
        stream_iter = body.iter_chunks()
    else:
        stream_iter = iter(lambda: body.read(8192), b"")

    return StreamingResponse(
        stream_iter,
        status_code=status_code,
        headers=headers,
        media_type=content_type,
    )
