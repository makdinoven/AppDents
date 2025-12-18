# API для файлов и аудио книг:
# - GET /api/books/{book_id}/assets — список форматов и аудио; у владельца есть download_url
# - GET /api/books/{book_id}/download — выдать presigned URL по формату (PDF/EPUB/...)
# - GET /api/books/{book_id}/pdf — потоковая раздача PDF с поддержкой Range (200 OK → 206 Partial)
# - GET /api/books/audios/{audio_id}/download — presigned URL аудиодорожки

import logging
import os
from collections import defaultdict
from datetime import timedelta
from typing import Optional, List
from urllib.parse import urlparse, unquote

import boto3
from botocore.config import Config
from fastapi import APIRouter, Depends, HTTPException, Query, Request
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session, selectinload

from ..db.database import get_db
from .users import get_current_user
from ..models.models_v2 import (
    User,
    Book,
    BookAudio,
    BookFile,
    BookFileFormat,
)
from ..utils.s3 import generate_presigned_url
from ..services_v2.book_service import PDF_CACHE_CONTROL, PDF_CONTENT_DISPOSITION

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION = os.getenv("S3_REGION", "ru-1")

s3_client = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(
        signature_version="s3",
        s3={"addressing_style": "path"},
        max_pool_connections=50,
    ),
)

logger = logging.getLogger(__name__)
router = APIRouter()


# ── helpers ─────────────────────────────────────────────────────────────────

def _is_admin(user: User) -> bool:
    return (user.role or "").lower() in {"admin", "superadmin", "owner"}


def _user_owns_book(db: Session, user_id: int, book_id: int) -> bool:
    row = db.execute(
        "SELECT 1 FROM users_books WHERE user_id=:u AND book_id=:b LIMIT 1",
        {"u": user_id, "b": book_id},
    ).first()
    return bool(row)


def _sign(url: Optional[str], filename: Optional[str] = None) -> Optional[str]:
    if not url:
        return None

    content_disposition = None
    if filename:
        safe_filename = filename.replace('"', '\\"')
        content_disposition = f'attachment; filename="{safe_filename}"'

    return generate_presigned_url(
        url,
        expires=timedelta(hours=24),
        response_content_disposition=content_disposition,
    )


def _s3_key_from_url(url: str) -> str:
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path


def _generate_filename(book: Book, fmt: str) -> str:
    import re

    if getattr(book, "slug", None):
        base_name = book.slug
    elif book.title:
        base_name = (
            re.sub(r"[^\w\s-]", "", book.title)
            .strip()
            .replace(" ", "-")
            .lower()[:50]
        )
    else:
        base_name = f"book-{book.id}"

    return f"{base_name}.{fmt.lower()}"


def _choose_pdf_file(files: list[BookFile]) -> BookFile | None:
    """Вернуть один PDF: watermarked → original → None."""
    pdfs = [f for f in files if f.file_format == BookFileFormat.PDF]
    if not pdfs:
        return None
    wm = next((f for f in pdfs if "/watermarked/" in (f.s3_url or "")), None)
    if wm:
        return wm
    return next((f for f in pdfs if "/original/" in (f.s3_url or "")), None)



# ── API ─────────────────────────────────────────────────────────────────────

@router.get("/{book_id}/assets", summary="Список форматов и аудио по книге")
def get_book_assets(
    book_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Отдаёт метаданные по доступным файлам и аудио.
    • Если пользователь владеет книгой (или админ) — добавляем presigned download_url.
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

    # Группируем файлы по формату, чтобы не дублировать
    by_format: dict[BookFileFormat, list[BookFile]] = defaultdict(list)
    for f in book.files or []:
        by_format[f.file_format].append(f)

    files = []
    for fmt, flist in by_format.items():
        fmt_val = fmt.value if hasattr(fmt, "value") else str(fmt)

        if fmt == BookFileFormat.PDF:
            chosen = _choose_pdf_file(flist)
        else:
            chosen = flist[0] if flist else None

        if not chosen:
            continue

        filename = _generate_filename(book, fmt_val) if owns else None
        files.append(
            {
                "format": fmt_val,
                "size_bytes": chosen.size_bytes,
                "download_url": _sign(chosen.s3_url, filename=filename) if owns else None,
            }
        )

    audios = []
    for a in book.audio_files or []:
        audios.append(
            {
                "id": a.id,
                "chapter_index": a.chapter_index,
                "title": a.title,
                "duration_sec": a.duration_sec,
                "download_url": _sign(a.s3_url) if owns else None,
            }
        )

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


@router.get(
    "/{book_id}/download",
    summary="Скачать книгу в выбранном формате (только для владельцев)",
)
def download_book_file(
    book_id: int,
    fmt: BookFileFormat = Query(..., description="Формат файла: PDF/EPUB/MOBI/AZW3/FB2"),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Возвращает presigned URL на файл книги `fmt`.
    Для PDF выбирает сначала watermarked, затем original.
    """
    if not (_is_admin(user) or _user_owns_book(db, user.id, book_id)):
        raise HTTPException(status_code=403, detail="No access to this book")

    book = db.query(Book).options(selectinload(Book.files)).get(book_id)
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    f: Optional[BookFile]
    if fmt == BookFileFormat.PDF:
        f = _choose_pdf_file(book.files or [])
    else:
        f = next((bf for bf in (book.files or []) if bf.file_format == fmt), None)

    if not f:
        raise HTTPException(status_code=404, detail=f"File in format {fmt} not found")

    filename = _generate_filename(book, fmt.value)
    return {"url": _sign(f.s3_url, filename=filename)}


@router.get(
    "/audios/{audio_id}/download",
    summary="Скачать аудиоглаву/аудиокнигу (только для владельцев)",
)
def download_book_audio(
    audio_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """
    Возвращает presigned URL на аудиофайл книги (глава или полная версия).
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
    Для PDF выбирается watermarked → иначе original.
    """
    book = (
        db.query(Book)
        .options(selectinload(Book.files))
        .get(book_id)
    )
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    pdf_file = _choose_pdf_file(book.files or [])
    if not pdf_file or not pdf_file.s3_url:
        raise HTTPException(status_code=404, detail="PDF not found")

    s3_url = pdf_file.s3_url
    db.close()

    key = _s3_key_from_url(s3_url)
    range_header = request.headers.get("range") or request.headers.get("Range")
    logger.info(f"PDF request for book {book_id}: Range header = {range_header}")

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
        get_kwargs["Range"] = range_header
        logger.info(f"Using client Range: {range_header}")
    else:
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

    if not metadata:
        metadata = obj.get("Metadata") or {}

    headers = {
        "Accept-Ranges": "bytes",
        "Content-Type": content_type,
        "Content-Disposition": PDF_CONTENT_DISPOSITION,
        "Cache-Control": PDF_CACHE_CONTROL,
    }

    if content_range:
        headers["Content-Range"] = content_range
        headers["Content-Length"] = str(content_length or 0)
        status_code = 206
        logger.info(f"Returning 206 Partial Content: {content_range}")
    else:
        headers["Content-Length"] = str(file_size)
        status_code = 200
        logger.info(
            f"Returning 200 OK with full Content-Length: {file_size}, "
            "PDF.js will use Range requests"
        )

    if metadata.get("asset"):
        headers["X-Book-Pdf-Asset"] = metadata["asset"]
    if metadata.get("pages"):
        headers["X-Book-Preview-Pages"] = metadata["pages"]
    if metadata.get("book-id"):
        headers["X-Book-Id"] = metadata["book-id"]
    if metadata.get("book-slug"):
        headers["X-Book-Slug"] = metadata["book-slug"]

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


@router.get(
    "/watermark/status",
    summary="Статус вотермарки по книгам",
)
def watermark_status(
    book_ids: Optional[List[int]] = Query(
        None,
        description="Список ID книг; если не указан, берём последние N",
    ),
    limit: int = Query(100, ge=1, le=1000, description="Сколько книг вернуть, если book_ids не заданы"),
    db: Session = Depends(get_db),
):
    """
    Для каждой книги показывает, есть ли watermarked / original PDF.
    """
    query = db.query(Book).options(selectinload(Book.files))

    if book_ids:
        query = query.filter(Book.id.in_(book_ids))
    else:
        query = query.order_by(Book.id.desc()).limit(limit)

    books = query.all()

    items = []
    for b in books:
        files = b.files or []
        has_watermarked = any(
            f.file_format == BookFileFormat.PDF and "/watermarked/" in (f.s3_url or "")
            for f in files
        )
        has_original = any(
            f.file_format == BookFileFormat.PDF and "/original/" in (f.s3_url or "")
            for f in files
        )
        pdf_file = _choose_pdf_file(files)

        items.append(
            {
                "book_id": b.id,
                "title": b.title,
                "slug": b.slug,
                "has_watermarked_pdf": has_watermarked,
                "has_original_pdf": has_original,
                "effective_pdf_url": pdf_file.s3_url if pdf_file else None,
            }
        )

    return {"items": items}
