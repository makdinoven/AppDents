import logging
import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from pathlib import PurePosixPath
from urllib.parse import urlparse, unquote, quote

import boto3
import redis
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models_v2 import Book, BookFile, BookFileFormat
from ..services_v2.book_service import pdf_extra_args, preview_pdf_metadata

logger = logging.getLogger(__name__)

# ENV / S3 / Redis
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

# Redis-ключи
def _k_job(book_id: int) -> str:        return f"bookprev:{book_id}"          # hash: status, started_at, finished_at
def _k_log(book_id: int) -> str:        return f"bookprev:{book_id}:log"      # list of log lines

def _log(book_id: int, msg: str) -> None:
    line = f"{datetime.utcnow().isoformat()}Z | {msg}"
    rds.lpush(_k_log(book_id), line)
    logger.info("[BOOK-PREVIEW][%s] %s", book_id, msg)

def _set_job_status(book_id: int, status: str) -> None:
    rds.hset(_k_job(book_id), mapping={"status": status, "updated_at": datetime.utcnow().isoformat() + "Z"})

def _set_job_times(book_id: int, started=False, finished=False) -> None:
    if started:
        rds.hset(_k_job(book_id), "started_at", datetime.utcnow().isoformat() + "Z")
    if finished:
        rds.hset(_k_job(book_id), "finished_at", datetime.utcnow().isoformat() + "Z")

def _key_from_url(url: str) -> str:
    """
    Принимаем CDN-URL или s3:// и возвращаем S3 key.
    """
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path

def _target_key_for(book: Book) -> str:
    # Схема хранения превью: books/<book.id>/preview/preview_20p.pdf
    return f"books/{book.id}/preview/preview_20p.pdf"

def _run(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out, err

def _cdn_url_for_key(key: str) -> str:
    key = key.lstrip("/")
    return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

def _preview_key_from_src(src_key: str, pages: int) -> str:
    p = PurePosixPath(src_key)          # books/<ID>/original/<File.pdf>
    base = p.parent.parent              # → books/<ID>
    return str(base / "preview" / f"preview_{pages}p.pdf")

@shared_task(name="app.tasks.book_previews.generate_book_preview", rate_limit="20/m")
def generate_book_preview(book_id: int, pages: int = 20) -> dict:
    """
    Вырезает первые `pages` (по умолчанию 20) страниц из PDF книги, загружает превью на CDN,
    пишет URL в books.preview_pdf (+ отметку времени) и статусы/логи в Redis.
    """
    db: Session = SessionLocal()
    try:
        _set_job_status(book_id, "running")
        _set_job_times(book_id, started=True)
        _log(book_id, f"start (pages={pages})")

        book = db.query(Book).get(book_id)
        if not book:
            _set_job_status(book_id, "failed")
            _log(book_id, "book not found")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "book_not_found"}

        # Проверка на существование превью уже в S3 убрана — всегда генерируем заново при запросе

        # Ищем исходный PDF
        pdf = (
            db.query(BookFile)
              .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
              .first()
        )
        if not pdf:
            _set_job_status(book_id, "failed")
            _log(book_id, "no source PDF")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "no_pdf"}

        src_key = _key_from_url(pdf.s3_url)
        _log(book_id, f"source key: {src_key}")

        with tempfile.TemporaryDirectory(prefix=f"book-prev-{book.id}-") as tmp:
            in_pdf  = os.path.join(tmp, "in.pdf")
            out_pdf = os.path.join(tmp, "preview.pdf")

            try:
                s3.download_file(S3_BUCKET, src_key, in_pdf)
            except ClientError as e:
                _set_job_status(book_id, "failed")
                _log(book_id, f"s3 download failed: {e}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "s3_download_failed"}

            # Ghostscript: первые N страниц → out.pdf
            cmd = f'gs -q -dNOPAUSE -dBATCH -sDEVICE=pdfwrite -dFirstPage=1 -dLastPage={pages} -sOutputFile="{out_pdf}" "{in_pdf}"'
            rc, out, err = _run(cmd)
            if rc != 0 or not os.path.exists(out_pdf) or os.path.getsize(out_pdf) == 0:
                _set_job_status(book_id, "failed")
                _log(book_id, f"ghostscript failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "gs_failed"}

            # Загрузка превью на CDN
            key = _preview_key_from_src(src_key, pages)
            metadata = preview_pdf_metadata(book, pages)
            extra_args = pdf_extra_args(metadata)
            try:
                s3.upload_file(out_pdf, S3_BUCKET, key, ExtraArgs=extra_args)
            except ClientError as e:
                _set_job_status(book_id, "failed")
                _log(book_id, f"s3 upload failed: {e}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "s3_upload_failed"}

            cdn_url = _cdn_url_for_key(key)
        
        # БД не обновляем — URL генерируется динамически по slug
        _set_job_status(book_id, "success")
        _set_job_times(book_id, finished=True)
        _log(book_id, f"done → {cdn_url}")

        return {"ok": True, "url": cdn_url}

    except Exception as exc:
        logger.exception("[BOOK-PREVIEW] unhandled")
        try:
            _set_job_status(book_id, "failed")
            _set_job_times(book_id, finished=True)
            _log(book_id, f"exception: {exc!r}")
        except Exception:
            pass
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()
