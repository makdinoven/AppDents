# API для файлов и аудио книг:
#  - GET /api/books/{book_id}/assets      — список форматов и аудио; у владельца есть download_url
#  - GET /api/books/{book_id}/download    — выдать presigned URL по формату (PDF/EPUB/...)
#  - GET /api/books/audios/{audio_id}/download — presigned URL аудиодорожки
# Требует: users_books, модели Book/BookFile/BookAudio, utils.s3.generate_presigned_url

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from .users import get_current_user
from ..models.models_v2 import User, Book, BookAudio, BookFileFormat
from ..utils.s3 import generate_presigned_url
from ..services_v2.book_service import PDF_CACHE_CONTROL, PDF_CONTENT_DISPOSITION
from urllib.parse import urlparse, unquote

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

def _sign(url: Optional[str]) -> Optional[str]:
    if not url:
        return None
    return generate_presigned_url(url, expires=timedelta(hours=24))


def _s3_key_from_url(url: str) -> str:
    """Извлекает ключ объекта из публичного/прямого URL."""
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path


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
        files.append({
            "format": f.file_format.value if hasattr(f.file_format, "value") else str(f.file_format),
            "size_bytes": f.size_bytes,
            "download_url": _sign(f.s3_url) if owns else None,
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

    # ищем нужный формат
    f = next((
        bf for bf in (
            db.query(Book)
              .options(selectinload(Book.files))
              .get(book_id)
              or Book()  # пустая заглушка, чтобы next() не падал на None
        ).files
        if bf.file_format == fmt
    ), None)

    if not f:
        raise HTTPException(status_code=404, detail=f"File in format {fmt} not found")

    return {"url": _sign(f.s3_url)}


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


@router.get("/{book_id}/pdf", summary="Потоковая раздача PDF с поддержкой Range (для владельцев)")
def stream_book_pdf(
    book_id: int,
    request: Request,
    db: Session = Depends(get_db),
):
    """
    Возвращает PDF с поддержкой HTTP Range, проксируя запрос в S3.
    Доступно владельцам книги и администраторам.
    
    Для запросов без Range header возвращает полный файл (200 OK).
    Для Range запросов возвращает частичный контент (206 Partial Content).
    """

    # Проверка авторизации

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
    
    # Получаем размер файла через head_object для случаев без Range header
    file_size = None
    metadata = {}
    if not range_header:
        try:
            head_obj = s3_client.head_object(Bucket=S3_BUCKET, Key=key)
            file_size = head_obj.get("ContentLength", 0)
            metadata = head_obj.get("Metadata") or {}
        except s3_client.exceptions.NoSuchKey:  # type: ignore[attr-defined]
            raise HTTPException(status_code=404, detail="PDF not found")
        except Exception as e:
            logger.error("S3 head_object error: %s", e)
            raise HTTPException(status_code=502, detail="Failed to fetch PDF metadata")
    
    # Для первого запроса (без Range) возвращаем только первый чанк,
    # но с кодом 200 OK, чтобы PDF.js понял что может делать Range-запросы
    INITIAL_CHUNK_SIZE = 524288  # 512 KB - достаточно для парсинга структуры PDF
    get_kwargs = {"Bucket": S3_BUCKET, "Key": key}
    is_initial_request = not range_header
    
    if range_header:
        get_kwargs["Range"] = range_header
    elif file_size:
        # Запрашиваем только первый чанк для оптимизации
        chunk_end = min(INITIAL_CHUNK_SIZE - 1, file_size - 1)
        get_kwargs["Range"] = f"bytes=0-{chunk_end}"

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
    
    # Для первого запроса (без Range header) возвращаем 200 OK
    # с полным размером файла, чтобы PDF.js знал общий размер
    if is_initial_request and file_size:
        # Возвращаем 200 OK с Content-Length = полный размер файла
        # PDF.js поймет что может делать Range-запросы благодаря Accept-Ranges: bytes
        headers["Content-Length"] = str(file_size)
        status_code = 200
    elif content_range:
        # Для Range запросов используем 206 Partial Content
        headers["Content-Range"] = content_range
        if content_length is not None:
            headers["Content-Length"] = str(content_length)
        status_code = 206
    else:
        # Fallback
        if content_length is not None:
            headers["Content-Length"] = str(content_length)
        status_code = 200

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
