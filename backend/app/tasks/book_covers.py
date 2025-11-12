import logging
import os
import shlex
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import quote, urlparse, unquote
import base64

import boto3
import redis
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models_v2 import Book, BookFile, BookFileFormat

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
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

# Redis-ключи
def _k_job(book_id: int) -> str:        return f"bookcover:{book_id}"       # hash: status, started_at, finished_at, candidates_count
def _k_log(book_id: int) -> str:        return f"bookcover:{book_id}:log"   # list of log lines
def _k_cand(book_id: int, idx: int) -> str: return f"bookcover:{book_id}:cand:{idx}"  # string (base64 JPEG)

# TTL для кандидатов (секунд)
DEFAULT_TTL_SECONDS = int(os.getenv("BOOK_COVER_CANDIDATE_TTL", "600"))  # 1 час

def _log(book_id: int, msg: str) -> None:
    line = f"{datetime.utcnow().isoformat()}Z | {msg}"
    rds.lpush(_k_log(book_id), line)
    logger.info("[BOOK-COVER][%s] %s", book_id, msg)

def _set_job_status(book_id: int, status: str) -> None:
    rds.hset(_k_job(book_id), mapping={"status": status, "updated_at": datetime.utcnow().isoformat() + "Z"})

def _set_job_times(book_id: int, started=False, finished=False) -> None:
    if started:
        rds.hset(_k_job(book_id), "started_at", datetime.utcnow().isoformat() + "Z")
    if finished:
        rds.hset(_k_job(book_id), "finished_at", datetime.utcnow().isoformat() + "Z")

def _key_from_url(url: str) -> str:
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    path = unquote(p.path.lstrip("/"))
    if path.startswith(f"{S3_BUCKET}/"):
        return path[len(S3_BUCKET) + 1 :]
    return path

def _cdn_url_for_key(key: str) -> str:
    key = key.lstrip("/")
    return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

def _run(cmd: str) -> tuple[int, str, str]:
    proc = subprocess.Popen(shlex.split(cmd), stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    out, err = proc.communicate()
    return proc.returncode, out, err

def _covers_dir_for(book: Book) -> str:
    return f"books/{book.slug}/covers/"

@shared_task(name="app.tasks.book_covers.generate_cover_candidates", rate_limit="20/m")
def generate_cover_candidates(book_id: int, pages: int = 3, dpi: int = 150, jpeg_quality: int = 90) -> dict:
    """
    Рендерит первые `pages` страниц PDF в JPEG и загружает как кандидаты обложки:
      books/<slug>/covers/candidate_1.jpg, candidate_2.jpg, candidate_3.jpg
    Сохраняет список URL'ов и статус в Redis.
    """
    db: Session = SessionLocal()
    try:
        _set_job_status(book_id, "running")
        _set_job_times(book_id, started=True)
        _log(book_id, f"start (pages={pages}, dpi={dpi}, q={jpeg_quality})")

        book = db.query(Book).get(book_id)
        if not book:
            _set_job_status(book_id, "failed")
            _log(book_id, "book not found")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "book_not_found"}

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

        produced = 0
        with tempfile.TemporaryDirectory(prefix=f"book-covers-{book.id}-") as tmp:
            in_pdf  = os.path.join(tmp, "in.pdf")
            try:
                s3.download_file(S3_BUCKET, src_key, in_pdf)
            except ClientError as e:
                _set_job_status(book_id, "failed")
                _log(book_id, f"s3 download failed: {e}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "s3_download_failed"}

            # Ghostscript: JPEG рендер каждой страницы отдельно
            # Рендерим каждую страницу отдельной командой, чтобы избежать склеивания страниц
            for page_num in range(1, pages + 1):
                out_file = os.path.join(tmp, f"out_{page_num}.jpg")
                # -dAutoRotatePages=/None предотвращает автоповорот
                # -dUseCropBox использует правильные границы страницы
                cmd = (
                    f'gs -q -dNOPAUSE -dBATCH -sDEVICE=jpeg -r{dpi} '
                    f'-dJPEGQ={jpeg_quality} -dAutoRotatePages=/None -dUseCropBox '
                    f'-dFirstPage={page_num} -dLastPage={page_num} '
                    f'-sOutputFile="{out_file}" "{in_pdf}"'
                )
                rc, out, err = _run(cmd)
                if rc != 0:
                    _log(book_id, f"ghostscript failed for page {page_num} (rc={rc})\nSTDERR:\n{err}")
                    continue  # Пропускаем эту страницу, но продолжаем с остальными

                # Сохраняем кандидата в Redis (base64 JPEG)
                if os.path.exists(out_file):
                    try:
                        with open(out_file, "rb") as fh:
                            b64 = base64.b64encode(fh.read()).decode("ascii")
                        rds.set(_k_cand(book.id, page_num), b64, ex=DEFAULT_TTL_SECONDS)
                        produced += 1
                        _log(book_id, f"page {page_num} rendered successfully")
                    except Exception as e:
                        _log(book_id, f"store candidate {page_num} failed: {e}")

        # Сохраняем счётчик и TTL на джобу/логи
        if produced:
            rds.hset(_k_job(book.id), mapping={"candidates_count": str(produced)})
            rds.expire(_k_job(book.id), DEFAULT_TTL_SECONDS)
            rds.expire(_k_log(book.id), DEFAULT_TTL_SECONDS)
            _set_job_status(book_id, "success")
            _log(book_id, f"done → {produced} candidates (TTL {DEFAULT_TTL_SECONDS}s)")
        else:
            _set_job_status(book_id, "failed")
            _log(book_id, "no candidates produced")

        _set_job_times(book_id, finished=True)
        return {"ok": produced > 0, "count": produced, "ttl": DEFAULT_TTL_SECONDS}

    except Exception as exc:
        logger.exception("[BOOK-COVER] unhandled")
        try:
            _set_job_status(book_id, "failed")
            _set_job_times(book_id, finished=True)
            _log(book_id, f"exception: {exc!r}")
        except Exception:
            pass
        return {"ok": False, "error": str(exc)}
    finally:
        db.close()


