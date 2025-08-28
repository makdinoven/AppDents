import logging
import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlparse, unquote

import boto3
import redis
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models_v2 import Book, BookFile, BookFileFormat
# Берём готовые настройки S3 из твоего окружения (как в ensure_hls):
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")
REDIS_URL      = os.getenv("REDIS_URL", "redis://redis:6379/0")

logger = logging.getLogger(__name__)
rds    = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# S3-клиент (V2 подпись, как в твоих тасках)
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

EBOOK_CONVERT_BIN = os.getenv("EBOOK_CONVERT_BIN", "ebook-convert")

# Какие форматы генерим из PDF
TARGET_FORMATS = [BookFileFormat.EPUB, BookFileFormat.MOBI, BookFileFormat.AZW3, BookFileFormat.FB2]

# Redis-ключи для статусов
def _k_job(book_id: int) -> str:        return f"bookfmt:{book_id}"            # hash: status, started_at, finished_at
def _k_log(book_id: int) -> str:        return f"bookfmt:{book_id}:log"        # list of log lines
def _k_fmt(book_id: int, fmt: str) -> str: return f"bookfmt:{book_id}:fmt:{fmt}"  # hash: status, url, size

def _log(book_id: int, msg: str) -> None:
    line = f"{datetime.utcnow().isoformat()}Z | {msg}"
    rds.lpush(_k_log(book_id), line)
    logger.info("[BOOK-FMT][%s] %s", book_id, msg)

def _set_job_status(book_id: int, status: str) -> None:
    rds.hset(_k_job(book_id), mapping={"status": status, "updated_at": datetime.utcnow().isoformat() + "Z"})

def _set_job_times(book_id: int, started: bool = False, finished: bool = False) -> None:
    if started:
        rds.hset(_k_job(book_id), "started_at", datetime.utcnow().isoformat() + "Z")
    if finished:
        rds.hset(_k_job(book_id), "finished_at", datetime.utcnow().isoformat() + "Z")

def _set_fmt_status(book_id: int, fmt: BookFileFormat, status: str, url: str | None = None, size: int | None = None) -> None:
    data = {"status": status}
    if url is not None:
        data["url"] = url
    if size is not None:
        data["size"] = str(size)
    rds.hset(_k_fmt(book_id, fmt.value), mapping=data)

def _content_type_for(ext: str) -> str:
    ext = ext.lower()
    if ext == "epub": return "application/epub+zip"
    if ext == "mobi": return "application/x-mobipocket-ebook"
    if ext == "azw3": return "application/octet-stream"
    if ext == "fb2":  return "application/x-fictionbook+xml"
    if ext == "pdf":  return "application/pdf"
    return "application/octet-stream"

def _cdn_url_for_key(key: str) -> str:
    key = key.lstrip("/")
    return f"{S3_PUBLIC_HOST}/{key}"

def _key_from_url(url: str) -> str:
    """
    Преобразует:
      • s3://bucket/key         → key
      • https://cdn.host/key    → key
      • https://s3.host/bucket/key → key (если так окажется)
    """
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    # При CDN-origin ключ — это path без первой «/»
    if p.netloc and p.path:
        path = unquote(p.path.lstrip("/"))
        # если путь начинается с имени бакета — сотрём его (на всякий случай)
        if path.startswith(f"{S3_BUCKET}/"):
            return path[len(S3_BUCKET) + 1 :]
        return path
    # если вдруг передали «сырой» key
    return url

def _target_key_for(book: Book, ext: str) -> str:
    return f"books/{book.slug}/{book.slug}.{ext.lower()}"

def _run(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out, err


@shared_task(name="app.tasks.book_formats.generate_book_formats", rate_limit="8/m")
def generate_book_formats(book_id: int) -> dict:
    """
    Главная таска: из PDF генерит EPUB/MOBI/AZW3/FB2, грузит в S3 (public-read),
    в БД кладёт CDN-URL, Redis — статусы/лог.
    """
    db: Session = SessionLocal()
    try:
        _set_job_status(book_id, "running")
        _set_job_times(book_id, started=True)
        _log(book_id, "start")

        book = db.query(Book).get(book_id)
        if not book:
            _set_job_status(book_id, "failed")
            _log(book_id, "book not found")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "book_not_found"}

        # ищем исходный PDF
        pdf_file = (
            db.query(BookFile)
              .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.PDF)
              .first()
        )
        if not pdf_file:
            _set_job_status(book_id, "failed")
            _log(book_id, "no PDF file in DB")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "no_pdf"}

        pdf_key = _key_from_url(pdf_file.s3_url)
        _log(book_id, f"source pdf key: {pdf_key}")

        created, failed = [], []

        with tempfile.TemporaryDirectory(prefix=f"book-{book.id}-") as tmp:
            src_pdf = os.path.join(tmp, "in.pdf")
            # скачиваем PDF из S3
            try:
                s3.download_file(S3_BUCKET, pdf_key, src_pdf)
            except ClientError as e:
                _set_job_status(book_id, "failed")
                _log(book_id, f"s3 download failed: {e}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "s3_download_failed"}

            for fmt in TARGET_FORMATS:
                ext = fmt.value.lower()
                out_path = os.path.join(tmp, f"out.{ext}")

                # если уже есть запись в БД — пропускаем
                exists = (
                    db.query(BookFile)
                      .filter(BookFile.book_id == book.id, BookFile.file_format == fmt)
                      .first()
                )
                if exists:
                    _set_fmt_status(book_id, fmt, "skipped", url=exists.s3_url, size=exists.size_bytes or 0)
                    _log(book_id, f"{ext}: skipped (already in DB)")
                    created.append({"format": fmt.value, "skipped": True, "url": exists.s3_url})
                    continue

                _set_fmt_status(book_id, fmt, "running")
                cmd = f'{EBOOK_CONVERT_BIN} "{src_pdf}" "{out_path}"'
                _log(book_id, f"{ext}: convert start")
                rc, out, err = _run(cmd)
                if rc != 0 or not os.path.exists(out_path):
                    msg = f"convert failed (rc={rc})"
                    _set_fmt_status(book_id, fmt, "failed")
                    _log(book_id, f"{ext}: {msg}\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                    failed.append({"format": fmt.value, "error": msg})
                    continue

                key = _target_key_for(book, ext)
                ct  = _content_type_for(ext)
                try:
                    s3.upload_file(out_path, S3_BUCKET, key, ExtraArgs={"ACL": "public-read", "ContentType": ct})
                except ClientError as e:
                    _set_fmt_status(book_id, fmt, "failed")
                    _log(book_id, f"{ext}: s3 upload failed: {e}")
                    failed.append({"format": fmt.value, "error": "s3_upload_failed"})
                    continue

                size = os.path.getsize(out_path)
                cdn_url = _cdn_url_for_key(key)

                # фиксируем в БД CDN-URL
                db.add(BookFile(book_id=book.id, file_format=fmt, s3_url=cdn_url, size_bytes=size))
                db.commit()

                _set_fmt_status(book_id, fmt, "success", url=cdn_url, size=size)
                _log(book_id, f"{ext}: uploaded → {cdn_url}")
                created.append({"format": fmt.value, "url": cdn_url, "size": size})

        # финальный статус
        status = "failed" if failed and not created else "success"
        _set_job_status(book_id, status)
        _set_job_times(book_id, finished=True)
        _log(book_id, f"done: created={len(created)} failed={len(failed)}")
        return {"ok": status == "success", "created": created, "failed": failed}

    except Exception as exc:
        logger.exception("[BOOK-FMT] unhandled")
        try:
            _set_job_status(book_id, "failed")
            _set_job_times(book_id, finished=True)
            _log(book_id, f"exception: {exc!r}")
        except Exception:
            pass
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()
