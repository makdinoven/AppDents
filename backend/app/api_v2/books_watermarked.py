import logging
import tempfile
from pathlib import Path
from typing import Literal

import requests
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.auth import get_current_user
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User, BookFile
from ..utils.watermarked import apply_watermark
from ..utils.s3 import generate_presigned_url  # если понадобится

from botocore.config import Config
import boto3
import os

log = logging.getLogger(__name__)
router = APIRouter(prefix="/books-watermark", tags=["books-watermark"])

# ─────────────────────────── S3 config (та же, что в books.py) ───────────────────────────
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3v4 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

# ─────────────────────────── Watermark config ───────────────────────────

DENT_S_LOGO = Path("frontend/public/apple-touch-icon.png")
MED_G_LOGO  = Path("frontend/public/apple-touch-icon-medg.png")

SITE_CONFIG = {
    "dent-s": {
        "logo": DENT_S_LOGO,
        "text": "Dent.S Dental Online School",
    },
    "med-g": {
        "logo": MED_G_LOGO,
        "text": "Med.G Online Medical Group",
    },
}


def _watermark_single_book(
    db: Session,
    book_id: int,
    site: str,
    opacity: float,
) -> dict:
    cfg = SITE_CONFIG.get(site)
    if not cfg:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Unknown site")

    # 1. Находим исходный PDF для книги
    pdf_file: BookFile | None = (
        db.query(BookFile)
        .filter(
            BookFile.book_id == book_id,
            BookFile.file_format == "PDF",
            BookFile.s3_url.contains("/original/"),
        )
        .first()
    )
    if not pdf_file:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "PDF for this book not found")

    original_url = pdf_file.s3_url

    # 2. Скачиваем PDF во временный файл
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        in_path = tmpdir_path / "in.pdf"
        out_path = tmpdir_path / "out.pdf"

        resp = requests.get(original_url, timeout=60)
        if resp.status_code != 200:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                f"Failed to download original PDF: {resp.status_code}",
            )
        in_path.write_bytes(resp.content)

        # 3. Накладываем вотермарку
        apply_watermark(
            input_path=in_path,
            output_path=out_path,
            logo_path=cfg["logo"],
            text=cfg["text"],
            opacity=opacity,
        )

        # 4. Готовим ключ на S3: /original/ -> /watermarked/
        rel = original_url.replace(S3_PUBLIC_HOST + "/", "")
        rel = rel.replace("/original/", "/watermarked/")
        s3_key = rel

        # Заливаем результат
        s3v4.upload_file(
            str(out_path),
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ACL": "public-read"},
        )

    watermarked_url = f"{S3_PUBLIC_HOST}/{s3_key}"

    # 5. Создаём новую запись в book_files
    new_file = BookFile(
        book_id=pdf_file.book_id,
        file_format="PDF",
        s3_url=watermarked_url,
        size_bytes=None,
    )
    db.add(new_file)
    db.commit()
    db.refresh(new_file)

    return {
        "book_id": book_id,
        "original_url": original_url,
        "watermarked_url": watermarked_url,
        "book_file_id": new_file.id,
    }


@router.post(
    "/book/{book_id}",
    status_code=status.HTTP_200_OK,
)
def watermark_book_endpoint(
    book_id: int,
    site: Literal["dent-s", "med-g"] = Query(...),
    opacity: float = Query(0.3, ge=0.05, le=1.0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Наложить вотермарку (логотип + текст) на каждую 10-ю страницу PDF книги
    и сохранить копию в /watermarked/.
    """
    return _watermark_single_book(db, book_id, site, opacity)


@router.post(
    "/all",
    status_code=status.HTTP_200_OK,
)
def watermark_all_books_endpoint(
    site: Literal["dent-s", "med-g"] = Query(...),
    opacity: float = Query(0.3, ge=0.05, le=1.0),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Применить вотермарку ко всем PDF (батчом по limit/offset).
    """
    pdf_files: list[BookFile] = (
        db.query(BookFile)
        .filter(
            BookFile.file_format == "PDF",
            BookFile.s3_url.contains("/original/"),
        )
        .order_by(BookFile.book_id)
        .offset(offset)
        .limit(limit)
        .all()
    )

    results: list[dict] = []
    seen_books: set[int] = set()

    for bf in pdf_files:
        if bf.book_id in seen_books:
            continue
        seen_books.add(bf.book_id)

        try:
            res = _watermark_single_book(db, bf.book_id, site, opacity)
            results.append(res)
        except Exception as exc:
            log.exception("Failed to watermark book %s: %s", bf.book_id, exc)
            results.append(
                {
                    "book_id": bf.book_id,
                    "error": str(exc),
                }
            )

    return {
        "site": site,
        "opacity": opacity,
        "processed": len(results),
        "items": results,
    }
