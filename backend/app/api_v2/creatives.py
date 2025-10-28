from typing import Optional, Dict

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Book, BookCreative, CreativeStatus, BookFile, BookFileFormat
from ..services_v2.creative_service import generate_all_creatives
from ..core.config import settings

import requests

router = APIRouter(prefix="/api/v2")


class ManualV1(BaseModel):
    hight_description: Optional[str] = None
    medium_description: Optional[str] = None
    down_description: Optional[str] = None
    tag_1: Optional[str] = None
    tag_2: Optional[str] = None
    tag_3: Optional[str] = None


class ManualV2(BaseModel):
    hight_description: Optional[str] = None
    down_description: Optional[str] = None
    tag_1: Optional[str] = None
    tag_2: Optional[str] = None
    tag_3: Optional[str] = None


class ManualCreatives(BaseModel):
    language: str
    v1: Optional[ManualV1] = None
    v2: Optional[ManualV2] = None


@router.post("/books/{book_id}/ai-process")
def ai_process(book_id: int, language: str = Query(...), db: Session = Depends(get_db), current_admin=Depends(require_roles("admin"))):
    import os
    from urllib.parse import urlparse, unquote, quote

    S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
    S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

    def _key_from_url(url: str) -> str:
        if url.startswith("s3://"):
            return urlparse(url).path.lstrip("/")
        p = urlparse(url)
        path = unquote(p.path.lstrip("/"))
        if path.startswith(f"{S3_BUCKET}/"):
            return path[len(S3_BUCKET) + 1 :]
        return path

    def _preview_key_from_src(src_key: str, pages: int) -> str:
        # books/<ID>/original/File.pdf  → books/<ID>/preview/preview_{pages}p.pdf
        from pathlib import PurePosixPath
        p = PurePosixPath(src_key)
        base = p.parent.parent
        return str(base / "preview" / f"preview_{pages}p.pdf")

    def _cdn_url_for_key(key: str) -> str:
        key = key.lstrip("/")
        return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

    book = db.query(Book).get(book_id)
    if not book:
        raise HTTPException(404, "Book not found")

    pdf = (
        db.query(BookFile)
          .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
          .first()
    )
    if not pdf:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, "No source PDF for the book")

    src_key = _key_from_url(pdf.s3_url)
    prev_key = _preview_key_from_src(src_key, 20)
    preview_pdf_url = _cdn_url_for_key(prev_key)

    # Проверяем доступность превью 20p, иначе fallback на исходный PDF (подпись/прямая ссылка)
    try:
        head = requests.head(preview_pdf_url, timeout=5, allow_redirects=True)
        if head.status_code != 200:
            raise RuntimeError("not ready")
    except Exception:
        # Fallback: используем исходный PDF URL (как есть)
        preview_pdf_url = pdf.s3_url

    r = requests.post(
        f"{settings.BOOKAI_BASE_URL}/process",
        json={"s3_url": preview_pdf_url, "language": language, "book_id": book_id},
        timeout=30,
    )
    if r.status_code >= 300:
        raise HTTPException(r.status_code, r.text[:500])
    return r.json()


@router.get("/books/{book_id}/creatives")
def get_or_create_creatives(
    book_id: int,
    language: str = Query(...),
    regen: bool = Query(False),
    db: Session = Depends(get_db),
    current_admin=Depends(require_roles("admin")),
):
    q = db.query(BookCreative).filter_by(book_id=book_id, language=language)
    items = q.all()
    ready = {x.creative_code: x for x in items if x.status == CreativeStatus.READY}
    needed = {"kbhccvksoprg7", "ktawlyumyeaw7", "uoshaoahss0al"}

    if not regen and needed.issubset(set(ready.keys())):
        return {
            "items": [
                {"code": x.creative_code, "status": x.status, "s3_url": x.s3_url}
                for x in ready.values()
            ],
            "overall": "ready",
        }

    # Генерация (синхронно)
    try:
        results = generate_all_creatives(db, book_id, language)
        return {
            "items": [
                {"code": x.creative_code, "status": x.status, "s3_url": x.s3_url}
                for x in results
            ],
            "overall": "ready",
        }
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))


@router.post("/books/{book_id}/creatives/manual")
def manual_creatives(book_id: int, body: ManualCreatives, db: Session = Depends(get_db), current_admin=Depends(require_roles("admin"))):
    mp: Dict[str, Dict] = {}
    if body.v1:
        mp["v1"] = body.v1.dict(exclude_none=True)
    if body.v2:
        mp["v2"] = body.v2.dict(exclude_none=True)
    try:
        results = generate_all_creatives(db, book_id, body.language, manual_payload=mp or None)
        return {
            "items": [
                {"code": x.creative_code, "status": x.status, "s3_url": x.s3_url}
                for x in results
            ],
            "overall": "ready",
        }
    except ValueError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY, str(e))
    except Exception as e:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, str(e))


