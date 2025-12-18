import logging
import os
import tempfile
from pathlib import Path, PurePosixPath
from urllib.parse import urlparse, unquote, quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy.orm import Session
from sqlalchemy.exc import OperationalError

from ..db.database import SessionLocal
from ..models.models_v2 import BookFile, BookFileFormat
from ..utils.watermarked import apply_watermark

logger = logging.getLogger(__name__)

# ENV / S3
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)


def _key_from_url(url: str) -> str:
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path


def _watermarked_key_from_src(src_key: str) -> str:
    # books/<ID>/original/File.pdf -> books/<ID>/watermarked/File.pdf
    p = PurePosixPath(src_key)
    if p.parent.name == "original":
        base = p.parent.parent  # books/<ID>
        return str(base / "watermarked" / p.name)
    # fallback: просто вставляем /watermarked/ перед именем файла
    return str(p.parent / "watermarked" / p.name)


def _cdn_url_for_key(key: str) -> str:
    key = key.lstrip("/")
    return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

BACKEND_APP_DIR = Path(__file__).resolve().parent.parent  # /app/app
ICON_DIR = BACKEND_APP_DIR / "icon"

DENT_S_LOGO = ICON_DIR / "logo-dents-transparent.svg"
MED_G_LOGO  = ICON_DIR / "logo-medg.png"


SITE_CONFIG = {
    "dent-s": {
        "logo": DENT_S_LOGO,
        "text": "dent-s.com Dental Online School",
    },
    "med-g": {
        "logo": MED_G_LOGO,
        "text": "med-g.com Medical Group",
    },
}


@shared_task(name="app.tasks.pdf_watermark.watermark_book_task", rate_limit="10/m")
def watermark_book_task(book_id: int, site: str, opacity: float = 0.3) -> dict:
    """
    Ставит логотип+текст на каждую 10-ю страницу PDF книги и заливает
    watermarked-версию на CDN. Создаёт новую запись в book_files.
    """
    cfg = SITE_CONFIG.get(site)
    if not cfg:
        return {"ok": False, "error": f"unknown_site:{site}"}

    # ===== 1. Короткая сессия: найти исходный PDF =====
    db: Session = SessionLocal()
    try:
        pdf: BookFile | None = (
            db.query(BookFile)
            .filter(
                BookFile.book_id == book_id,
                BookFile.file_format == BookFileFormat.PDF,
                BookFile.s3_url.contains("/original/"),
            )
            .first()
        )
        if not pdf:
            return {"ok": False, "error": "no_pdf"}

        src_key = _key_from_url(pdf.s3_url)
        original_url = pdf.s3_url
    except Exception as exc:
        logger.exception("[BOOK-WATERMARK][%s] DB select failed", book_id)
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()

    logger.info("[BOOK-WATERMARK][%s] source key: %s", book_id, src_key)

    # ===== 2. IO: скачать PDF, наложить вотермарку, залить в S3 =====
    with tempfile.TemporaryDirectory(prefix=f"book-watermark-{book_id}-") as tmp:
        in_pdf = os.path.join(tmp, "in.pdf")
        out_pdf = os.path.join(tmp, "watermarked.pdf")

        # 2.1 Скачиваем исходный PDF
        try:
            s3.download_file(S3_BUCKET, src_key, in_pdf)
        except ClientError:
            logger.exception("[BOOK-WATERMARK][%s] s3 download failed", book_id)
            return {"ok": False, "error": "s3_download_failed"}

        # 2.2 Накладываем водяной знак
        try:
            apply_watermark(
                input_path=Path(in_pdf),
                output_path=Path(out_pdf),
                logo_path=cfg["logo"],
                text=cfg["text"],
                opacity=opacity,
            )
        except Exception:
            logger.exception("[BOOK-WATERMARK][%s] watermark apply failed", book_id)
            return {"ok": False, "error": "watermark_failed"}

        # 2.3 Заливаем watermarked-версию
        key = _watermarked_key_from_src(src_key)
        try:
            s3.upload_file(out_pdf, S3_BUCKET, key, ExtraArgs={"ACL": "public-read"})
        except ClientError:
            logger.exception("[BOOK-WATERMARK][%s] s3 upload failed", book_id)
            return {"ok": False, "error": "s3_upload_failed"}

        cdn_url = _cdn_url_for_key(key)

    # ===== 3. Отдельная короткая сессия: INSERT book_files =====
    db = SessionLocal()
    try:
        new_file = BookFile(
            book_id=book_id,
            file_format=BookFileFormat.PDF,
            s3_url=cdn_url,
            size_bytes=None,
        )
        db.add(new_file)
        db.commit()
        db.refresh(new_file)
    except OperationalError as exc:
        logger.exception("[BOOK-WATERMARK][%s] DB insert operational error", book_id)
        db.rollback()
        return {"ok": False, "error": str(exc)}
    except Exception as exc:
        logger.exception("[BOOK-WATERMARK][%s] DB insert failed", book_id)
        db.rollback()
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()

    logger.info("[BOOK-WATERMARK][%s] done -> %s", book_id, cdn_url)
    return {
        "ok": True,
        "book_id": book_id,
        "original_url": original_url,
        "watermarked_url": cdn_url,
        "book_file_id": new_file.id,
    }
