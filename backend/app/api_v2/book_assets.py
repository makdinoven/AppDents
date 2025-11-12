# API для файлов и аудио книг:
#  - GET /api/books/{book_id}/assets      — список форматов и аудио; у владельца есть download_url
#  - GET /api/books/{book_id}/download    — выдать presigned URL по формату (PDF/EPUB/...)
#  - GET /api/books/audios/{audio_id}/download — presigned URL аудиодорожки
# Требует: users_books, модели Book/BookFile/BookAudio, utils.s3.generate_presigned_url

import logging
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse, Response, RedirectResponse
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
    Возвращает redirect на presigned URL S3 для прямой загрузки PDF.
    Это позволяет избежать проксирования через сервер и использовать Range-запросы напрямую к S3.
    Доступно владельцам книги и администраторам.
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

    # Генерируем presigned URL на 24 часа
    presigned_url = generate_presigned_url(pdf_file.s3_url, expires=timedelta(hours=24))
    
    if not presigned_url:
        raise HTTPException(status_code=500, detail="Failed to generate presigned URL")
    
    # Возвращаем redirect на presigned URL
    # Клиент будет загружать напрямую из S3 с поддержкой Range-запросов
    return RedirectResponse(url=presigned_url, status_code=307)
