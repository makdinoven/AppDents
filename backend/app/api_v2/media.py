# app/api_v2/admin_media.py
import os
import uuid
from io import BytesIO
from typing import Literal, Optional
from datetime import datetime
from urllib.parse import quote

from botocore.exceptions import ClientError
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session
from PIL import Image, ImageOps

from ..core.storage import S3_BUCKET, S3_PUBLIC_HOST, public_url_for_key, s3_client
from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import (
    User, Book, Author, Landing, BookLanding,
    BookAudio, BookLandingImage,
)

router = APIRouter()

s3 = s3_client(signature_version="s3v4")

ALLOWED_IMAGE_CT = {"image/jpeg", "image/png", "image/webp", "image/gif"}
ALLOWED_AUDIO_CT = {"audio/mpeg", "audio/ogg", "audio/mp4", "audio/aac", "audio/x-m4a"}

MAX_IMAGE_MB = int(os.getenv("MAX_IMAGE_MB", "25"))
MAX_AUDIO_MB = int(os.getenv("MAX_AUDIO_MB", "200"))

WEBP_QUALITY = int(os.getenv("WEBP_QUALITY", "82"))
WEBP_METHOD  = int(os.getenv("WEBP_METHOD",  "5"))
MAX_DIM      = int(os.getenv("IMAGES_MAX_DIM", "4096"))

def _cdn_url(key: str) -> str:
    # сохраняем публичный URL (cloud.*) в БД
    return public_url_for_key(key, public_host=S3_PUBLIC_HOST)

# ───────────────── entity_type без usage ─────────────────
EntityType = Literal[
    "book_cover",
    "book_landing_preview",
    "book_landing_gallery",  # и добавил правильное написание, чтобы не словить 400
    "landing_preview",
    "author_preview",
]

def _webp_key_by_entity(entity_type: EntityType, entity_id: int) -> str:
    uid = uuid.uuid4().hex
    if entity_type == "book_cover":
        return f"images/books/{entity_id}/cover/{uid}.webp"
    if entity_type == "book_landing_preview":
        return f"images/book_landings/{entity_id}/preview/{uid}.webp"
    if entity_type == "landing_preview":
        return f"images/landings/{entity_id}/preview/{uid}.webp"
    if entity_type == "author_preview":
        return f"images/authors/{entity_id}/{uid}.webp"
    raise HTTPException(400, "Unsupported entity_type")

def _bytes_to_webp(data: bytes) -> bytes:
    try:
        im = Image.open(BytesIO(data))
    except Exception:
        raise HTTPException(400, "Cannot read image")

    # EXIF-ориентация
    try:
        im = ImageOps.exif_transpose(im)
    except Exception:
        pass

    # Если аним. GIF — упрощаем до первого кадра
    try:
        if getattr(im, "is_animated", False) and getattr(im, "n_frames", 1) > 1:
            im.seek(0)
    except Exception:
        pass

    # Цветовые режимы
    if im.mode in ("P", "LA"):
        im = im.convert("RGBA")
    elif im.mode == "CMYK":
        im = im.convert("RGB")

    # Downscale до MAX_DIM по большой стороне
    if max(im.size) > MAX_DIM:
        im.thumbnail((MAX_DIM, MAX_DIM), resample=Image.Resampling.LANCZOS)

    out = BytesIO()
    # Небольшие RGBA/LA → lossless; остальное — lossy
    lossless = False
    if im.mode in ("RGBA", "LA") and (im.width * im.height) <= 5_000_000:
        lossless = True

    save_kwargs = {
        "format": "WEBP",
        "quality": WEBP_QUALITY,
        "method": WEBP_METHOD,
        "lossless": lossless,
    }
    try:
        im.save(out, **save_kwargs)
    except OSError:
        save_kwargs.pop("lossless", None)
        im.save(out, **save_kwargs)

    return out.getvalue()

@router.post("/upload-image", status_code=status.HTTP_201_CREATED)
async def upload_image(
    entity_type: EntityType = Form(..., description="book_cover | book_landing_preview | book_landing_galary | book_landing_gallery | landing_preview | author_preview"),
    entity_id:   int        = Form(...),
    # метаданные для галереи (используются только когда entity_type = *_galary/gallery)
    alt:         Optional[str] = Form(None),
    caption:     Optional[str] = Form(None),
    sort_index:  Optional[int] = Form(0),
    file: UploadFile = File(...),
    current_admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    ct_in = (file.content_type or "").lower()
    if ct_in not in ALLOWED_IMAGE_CT:
        raise HTTPException(400, f"Unsupported image content-type: {ct_in}")

    size_hdr = file.headers.get("content-length")
    if size_hdr and int(size_hdr) > MAX_IMAGE_MB * 1024 * 1024:
        raise HTTPException(413, f"Image too large (>{MAX_IMAGE_MB}MB)")

    src_bytes = await file.read()
    webp_bytes = _bytes_to_webp(src_bytes)

    key = _webp_key_by_entity(entity_type, entity_id)
    try:
        s3.upload_fileobj(
            BytesIO(webp_bytes),
            S3_BUCKET,
            key,
            ExtraArgs={"ACL": "public-read", "ContentType": "image/webp"},
        )

        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        raise HTTPException(500, f"S3 upload failed: {e}")

    url  = _cdn_url(key)
    size = int(head.get("ContentLength") or 0)

    # Привязки к БД
    if entity_type == "book_cover":
        book = db.query(Book).get(entity_id)
        if not book:
            raise HTTPException(404, "Book not found")
        book.cover_url = url
        db.commit()
        return {"attached": "book_cover", "book_id": entity_id, "url": url, "size": size, "content_type": "image/webp"}

    if entity_type == "book_landing_gallery":
        bl = db.query(BookLanding).get(entity_id)
        if not bl:
            raise HTTPException(404, "BookLanding not found")
        img = BookLandingImage(
            landing_id=entity_id,
            s3_url=url,
            alt=alt,
            caption=caption,
            sort_index=sort_index or 0,
            size_bytes=size,
            content_type="image/webp",
            created_at=datetime.utcnow(),
        )
        db.add(img)
        db.commit()
        db.refresh(img)
        return {
            "attached": "book_landing_gallery",
            "image_id": img.id,
            "landing_id": entity_id,
            "url": url,
            "size": size,
            "content_type": "image/webp",
        }

    if entity_type == "landing_preview":
        landing = db.query(Landing).get(entity_id)
        if not landing:
            raise HTTPException(404, "Landing not found")
        landing.preview_photo = url
        db.commit()
        return {"attached": "course_landing_preview", "landing_id": entity_id, "url": url, "size": size, "content_type": "image/webp"}

    if entity_type == "author_preview":
        a = db.query(Author).get(entity_id)
        if not a:
            raise HTTPException(404, "Author not found")
        a.photo = url
        db.commit()
        return {"attached": "author_preview", "author_id": entity_id, "url": url, "size": size, "content_type": "image/webp"}

    # сюда не дойдём из-за Literal, но пусть будет
    raise HTTPException(400, "Unsupported entity_type")

# ─────────────── Аудио (без изменений) ───────────────
AudioVariant = Literal["full", "sample_5m", "chapter"]

def _audio_key(book_id: int, filename: str, variant: AudioVariant, chapter_index: Optional[int]) -> str:
    import os as _os
    ext = (_os.path.splitext(filename)[1] or "").lower()
    uid = uuid.uuid4().hex
    if variant == "full":
        return f"books/{book_id}/audio/{uid}-full{ext}"
    if variant == "sample_5m":
        return f"books/{book_id}/audio/{uid}-sample-5m{ext}"
    if variant == "chapter":
        if chapter_index is None:
            raise HTTPException(400, "chapter_index required for variant=chapter")
        return f"books/{book_id}/audio/{uid}-chapter-{chapter_index:03d}{ext}"
    raise HTTPException(400, "Unsupported audio variant")

@router.post("/upload-audio", status_code=status.HTTP_201_CREATED)
async def upload_audio(
    book_id: int = Form(...),
    variant: AudioVariant = Form("full"),
    chapter_index: Optional[int] = Form(None),
    title: Optional[str] = Form(None),
    duration_sec: Optional[int] = Form(None),
    file: UploadFile = File(...),
    current_admin: User = Depends(require_roles("admin")),
    db: Session = Depends(get_db),
):
    ct = (file.content_type or "").lower()
    if ct not in ALLOWED_AUDIO_CT:
        raise HTTPException(400, f"Unsupported audio content-type: {ct}")

    size_hdr = file.headers.get("content-length")
    if size_hdr and int(size_hdr) > MAX_AUDIO_MB * 1024 * 1024:
        raise HTTPException(413, f"Audio too large (>{MAX_AUDIO_MB}MB)")

    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")

    key = _audio_key(book_id, file.filename, variant, chapter_index)

    try:
        s3.upload_fileobj(
            file.file,
            S3_BUCKET,
            key,
            ExtraArgs={"ACL": "public-read", "ContentType": ct},
        )
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        raise HTTPException(500, f"S3 upload failed: {e}")

    url  = _cdn_url(key)
    size = int(head.get("ContentLength") or 0)

    ba = BookAudio(
        book_id=book_id,
        chapter_index=(None if variant != "chapter" else chapter_index),
        title=title or (
            "Full" if variant == "full" else
            "Sample 5 min" if variant == "sample_5m" else
            f"Chapter {chapter_index}"
        ),
        duration_sec=duration_sec,
        s3_url=url,
    )
    db.add(ba)
    db.commit()
    db.refresh(ba)

    return {
        "attached": "book_audio",
        "book_audio_id": ba.id,
        "book_id": book_id,
        "variant": variant,
        "chapter_index": ba.chapter_index,
        "url": url,
        "size": size,
        "content_type": ct,
    }
