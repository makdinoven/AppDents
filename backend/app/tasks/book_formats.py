import logging
import os
import re
import selectors
import shlex
import subprocess
import tempfile
import time
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

# ──────────────────── ENV / S3 / Redis ────────────────────
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")
REDIS_URL      = os.getenv("REDIS_URL", "redis://redis:6379/0")

# Внешние бинарники
EBOOK_CONVERT_BIN = os.getenv("EBOOK_CONVERT_BIN", "ebook-convert")

# Умеренные флаги (качество ок, память экономим)
# PDF → EPUB
PDF2EPUB_OPTS  = " "
# EPUB → AZW3 (под Kindle)
EPUB2AZW3_OPTS = ""
# EPUB → MOBI (KF8/new)
EPUB2MOBI_OPTS = ""
# EPUB → FB2
EPUB2FB2_OPTS  = ""

logger = logging.getLogger(__name__)
rds    = redis.Redis.from_url(REDIS_URL, decode_responses=True)
s3     = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

_PROGRESS_RE = re.compile(r"(\d{1,3})%")
CALIBRE_LOG_LEVEL = os.getenv("CALIBRE_CONVERT_LOG_LEVEL", "INFO")


def _calibre_jobs() -> int | None:
    override = os.getenv("CALIBRE_CONVERT_JOBS")
    if override:
        try:
            jobs = max(1, int(override))
        except ValueError:
            logger.warning("Invalid CALIBRE_CONVERT_JOBS=%s, falling back to auto", override)
        else:
            return jobs
    cpu_count = os.cpu_count() or 2
    # оставляем минимум одно ядро свободным, максимум 8 параллельных задач
    return max(1, min(8, max(1, cpu_count - 1)))


_JOB_PROGRESS_STEPS: dict[BookFileFormat, tuple[int, int]] = {
    BookFileFormat.EPUB: (0, 45),
    BookFileFormat.MOBI: (45, 20),
    BookFileFormat.AZW3: (65, 20),
    BookFileFormat.FB2: (85, 15),
}

# ───────────────── Redis-ключи статусов ──────────────────
def _k_job(book_id: int) -> str:           return f"bookfmt:{book_id}"
def _k_log(book_id: int) -> str:           return f"bookfmt:{book_id}:log"
def _k_fmt(book_id: int, fmt: str) -> str: return f"bookfmt:{book_id}:fmt:{fmt}"

def _log(book_id: int, msg: str) -> None:
    line = f"{datetime.utcnow().isoformat()}Z | {msg}"
    rds.lpush(_k_log(book_id), line)
    logger.info("[BOOK-FMT][%s] %s", book_id, msg)

def _set_job_status(book_id: int, status: str) -> None:
    rds.hset(_k_job(book_id), mapping={"status": status, "updated_at": datetime.utcnow().isoformat() + "Z"})

def _set_job_times(book_id: int, *, started: bool = False, finished: bool = False) -> None:
    if started:
        rds.hset(_k_job(book_id), "started_at", datetime.utcnow().isoformat() + "Z")
    if finished:
        rds.hset(_k_job(book_id), "finished_at", datetime.utcnow().isoformat() + "Z")

def _set_fmt_status(
    book_id: int,
    fmt: BookFileFormat,
    status: str,
    url: str | None = None,
    size: int | None = None,
    progress: int | None = None,
) -> None:
    data: dict[str, str] = {}
    if status is not None:
        data["status"] = status
    if url is not None:
        data["url"] = url
    if size is not None:
        data["size"] = str(size)
    if progress is not None:
        data["progress"] = str(progress)
    rds.hset(_k_fmt(book_id, fmt.value), mapping=data)


def _set_job_progress(book_id: int, progress: int | None = None, note: str | None = None) -> None:
    data: dict[str, str] = {}
    if progress is not None:
        data["progress"] = str(max(0, min(100, progress)))
    if note is not None:
        data["note"] = note
    if data:
        rds.hset(_k_job(book_id), mapping=data)


def _update_job_progress_from_fmt(book_id: int, fmt: BookFileFormat, fmt_progress: int) -> None:
    base, span = _JOB_PROGRESS_STEPS.get(fmt, (0, 0))
    fmt_progress = max(0, min(100, fmt_progress))
    job_progress = min(100, base + (fmt_progress * span) // 100)
    _set_job_progress(book_id, job_progress)


_progress_cache: dict[tuple[int, BookFileFormat], int] = {}


def _fmt_label(fmt: BookFileFormat) -> str:
    return fmt.value.lower()


def _remember_progress(book_id: int, fmt: BookFileFormat, progress: int) -> bool:
    key = (book_id, fmt)
    prev = _progress_cache.get(key)
    if prev is None or abs(progress - prev) >= 5 or progress in (0, 100):
        _progress_cache[key] = progress
        return True
    return False


def _clear_progress(book_id: int, fmt: BookFileFormat) -> None:
    _progress_cache.pop((book_id, fmt), None)


def _handle_convert_output(book_id: int, fmt: BookFileFormat, line: str, *, stream: str) -> None:
    stripped = line.strip()
    if not stripped:
        return

    match = _PROGRESS_RE.search(stripped)
    if match:
        progress = max(0, min(100, int(match.group(1))))
        if _remember_progress(book_id, fmt, progress):
            _set_fmt_status(book_id, fmt, "running", progress=progress)
            _update_job_progress_from_fmt(book_id, fmt, progress)
            _log(book_id, f"{_fmt_label(fmt)}: progress {progress}%")
        return

    lowered = stripped.lower()
    if stream == "stderr":
        _log(book_id, f"{_fmt_label(fmt)} stderr: {stripped}")
    elif any(lowered.startswith(prefix) for prefix in ("input ", "output ", "parsed", "converting", "rendering", "creating", "processing")):
        _log(book_id, f"{_fmt_label(fmt)}: {stripped}")


def _build_convert_args(src_path: str, dst_path: str, extra_opts: str | None = None) -> list[str]:
    args = [EBOOK_CONVERT_BIN, src_path, dst_path]
    opts = shlex.split(extra_opts or "")

    if "--jobs" not in opts:
        jobs = _calibre_jobs()
        if jobs:
            args.extend(["--jobs", str(jobs)])

    if "--log-level" not in opts and "--verbose" not in opts:
        args.extend(["--log-level", CALIBRE_LOG_LEVEL])

    args.extend(opts)
    return args

# ──────────────────── Вспомогательные ────────────────────
def _content_type_for(ext: str) -> str:
    ext = ext.lower()
    if ext == "epub": return "application/epub+zip"
    if ext == "mobi": return "application/x-mobipocket-ebook"
    if ext == "azw3": return "application/octet-stream"
    if ext == "fb2":  return "application/x-fictionbook+xml"
    if ext == "pdf":  return "application/pdf"
    return "application/octet-stream"

def _safe_cdn_url(key: str) -> str:
    key = key.lstrip("/")
    return f"{S3_PUBLIC_HOST}/{quote(key, safe='/-._~()')}"

def _key_from_url(url: str) -> str:
    """
    s3://bucket/key                  → key
    https://cdn.host/key             → key
    https://s3.host/bucket/key       → key
    (или уже «сырой» key)
    """
    if url.startswith("s3://"):
        return urlparse(url).path.lstrip("/")
    p = urlparse(url)
    if p.netloc and p.path:
        path = unquote(p.path.lstrip("/"))
        if path.startswith(f"{S3_BUCKET}/"):
            return path[len(S3_BUCKET) + 1 :]
        return path
    return url

def _dir_base_from_pdf_key(pdf_key: str) -> PurePosixPath:
    # books/<ID>/original/<File.pdf> → books/<ID>
    p = PurePosixPath(pdf_key)
    return p.parent.parent

def _formats_key_from_pdf(pdf_key: str, ext: str) -> str:
    base = _dir_base_from_pdf_key(pdf_key)  # books/<ID>
    stem = PurePosixPath(pdf_key).stem      # File
    return str(base / "formats" / f"{stem}.{ext.lower()}")

def _run(
    cmd: str | list[str],
    *,
    book_id: int | None = None,
    fmt: BookFileFormat | None = None,
    phase: str | None = None,
) -> tuple[int, str, str]:
    if isinstance(cmd, str):
        args = shlex.split(cmd)
    else:
        args = cmd

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
    )

    stdout_lines: list[str] = []
    stderr_lines: list[str] = []

    def _log_phase(message: str) -> None:
        if book_id is not None and fmt is not None:
            prefix = _fmt_label(fmt)
            if phase:
                _log(book_id, f"{prefix}:{phase} {message}")
            else:
                _log(book_id, f"{prefix}: {message}")

    if book_id is not None and fmt is not None and phase:
        _log_phase("started")

    sel = selectors.DefaultSelector()
    if proc.stdout:
        sel.register(proc.stdout, selectors.EVENT_READ, ("stdout", proc.stdout))
    if proc.stderr:
        sel.register(proc.stderr, selectors.EVENT_READ, ("stderr", proc.stderr))

    while sel.get_map():
        for key, _ in sel.select():
            stream_name, stream = key.data
            line = stream.readline()
            if line:
                if stream_name == "stdout":
                    stdout_lines.append(line)
                else:
                    stderr_lines.append(line)
                if book_id is not None and fmt is not None:
                    _handle_convert_output(book_id, fmt, line, stream=stream_name)
            else:
                sel.unregister(stream)

        if proc.poll() is not None and not sel.get_map():
            break

    rc = proc.wait()

    if book_id is not None and fmt is not None and phase:
        _log_phase(f"finished rc={rc}")

    return rc, "".join(stdout_lines), "".join(stderr_lines)

def _tmp_dir() -> str | None:
    # Уважает выделенный большой tmp-раздел, если настроен
    return os.getenv("CALIBRE_TEMP_DIR") or os.getenv("TMPDIR") or None

# ───────────────────── Основная таска ─────────────────────
@shared_task(name="app.tasks.book_formats.generate_book_formats", rate_limit="8/m")
def generate_book_formats(book_id: int) -> dict:
    """
    Конверсия «в 2 шага»:
      1) PDF → EPUB (один раз; умеренные флаги качества)
      2) EPUB → MOBI, AZW3, FB2

    Результаты → S3: books/<ID>/formats/<stem>.<ext>
    В БД создаются/обновляются BookFile, в Redis — статусы/лог.
    """
    db: Session = SessionLocal()
    created, failed = [], []

    try:
        _set_job_status(book_id, "running")
        _set_job_times(book_id, started=True)
        rds.hdel(_k_job(book_id), "finished_at")
        _set_job_progress(book_id, 0, note="инициализация")
        _log(book_id, "start")

        book = db.query(Book).get(book_id)
        if not book:
            _set_job_status(book_id, "failed")
            _log(book_id, "book not found")
            _set_job_times(book_id, finished=True)
            return {"ok": False, "error": "book_not_found"}

        # Ищем исходный PDF
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

        # Выделяем временную директорию (можно перенаправить через CALIBRE_TEMP_DIR)
        with tempfile.TemporaryDirectory(prefix=f"book-{book.id}-", dir=_tmp_dir()) as tmp:
            # Скачиваем PDF локально
            src_pdf = os.path.join(tmp, "in.pdf")
            download_started = time.monotonic()
            try:
                s3.download_file(S3_BUCKET, pdf_key, src_pdf)
            except ClientError as e:
                _set_job_status(book_id, "failed")
                _log(book_id, f"s3 download failed: {e}")
                _set_job_times(book_id, finished=True)
                return {"ok": False, "error": "s3_download_failed"}
            else:
                elapsed = time.monotonic() - download_started
                size_bytes = os.path.getsize(src_pdf)
                size_mb = size_bytes / (1024 * 1024)
                _log(book_id, f"pdf: downloaded {size_mb:.2f} MiB in {elapsed:.1f}s")
                _set_job_progress(book_id, 5, note="pdf загружен локально")

            # ───────────── 1) EPUB (PDF → EPUB, 1 раз) ─────────────
            base_epub_local = os.path.join(tmp, "base.epub")
            epub_row = (
                db.query(BookFile)
                  .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.EPUB)
                  .first()
            )
            if epub_row:
                # Пытаемся скачать уже существующий EPUB — используем как базу для остальных
                try:
                    s3.download_file(S3_BUCKET, _key_from_url(epub_row.s3_url), base_epub_local)
                    local_size = os.path.getsize(base_epub_local)
                    _set_fmt_status(
                        book_id,
                        BookFileFormat.EPUB,
                        "skipped",
                        url=epub_row.s3_url,
                        size=local_size or epub_row.size_bytes or 0,
                        progress=100,
                    )
                    _update_job_progress_from_fmt(book_id, BookFileFormat.EPUB, 100)
                    _clear_progress(book.id, BookFileFormat.EPUB)
                    _log(book_id, f"epub: reuse (already in DB, {local_size / (1024 * 1024):.2f} MiB)")
                except Exception as e:
                    _log(book_id, f"epub: reuse failed → rebuild: {e}")
                    epub_row = None  # Будем пересобирать

            if not epub_row:
                _set_job_progress(book_id, 10, note="конвертация PDF→EPUB")
                _set_fmt_status(book_id, BookFileFormat.EPUB, "running", progress=0)
                _update_job_progress_from_fmt(book_id, BookFileFormat.EPUB, 0)
                _log(book_id, "epub: convert start (pdf → epub)")
                stage_started = time.monotonic()
                rc, out, err = _run(
                    _build_convert_args(src_pdf, base_epub_local, PDF2EPUB_OPTS),
                    book_id=book.id,
                    fmt=BookFileFormat.EPUB,
                    phase="convert",
                )
                if rc != 0 or not os.path.exists(base_epub_local) or os.path.getsize(base_epub_local) == 0:
                    _set_fmt_status(book_id, BookFileFormat.EPUB, "failed")
                    _log(book_id, f"epub: convert failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                    _clear_progress(book.id, BookFileFormat.EPUB)
                    failed.append({"format": "EPUB", "error": f"convert failed (rc={rc})"})
                    # Без EPUB дальше шансов мало — но аккуратно завершим.
                else:
                    convert_elapsed = time.monotonic() - stage_started
                    epub_key = _formats_key_from_pdf(pdf_key, "epub")
                    try:
                        s3.upload_file(
                            base_epub_local, S3_BUCKET, epub_key,
                            ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for("epub")}
                        )
                        size = os.path.getsize(base_epub_local)
                        epub_url = _safe_cdn_url(epub_key)
                        db.add(BookFile(book_id=book.id, file_format=BookFileFormat.EPUB,
                                        s3_url=epub_url, size_bytes=size))
                        db.commit()
                        _set_fmt_status(
                            book_id,
                            BookFileFormat.EPUB,
                            "success",
                            url=epub_url,
                            size=size,
                            progress=100,
                        )
                        _update_job_progress_from_fmt(book_id, BookFileFormat.EPUB, 100)
                        _clear_progress(book.id, BookFileFormat.EPUB)
                        _log(
                            book_id,
                            f"epub: uploaded → {epub_url} ({size / (1024 * 1024):.2f} MiB, {convert_elapsed:.1f}s)",
                        )
                        created.append({"format": "EPUB", "url": epub_url, "size": size})
                    except ClientError as e:
                        _set_fmt_status(book_id, BookFileFormat.EPUB, "failed")
                        _log(book_id, f"epub: s3 upload failed: {e}")
                        _clear_progress(book.id, BookFileFormat.EPUB)
                        failed.append({"format": "EPUB", "error": "s3_upload_failed"})

            have_epub_local = os.path.exists(base_epub_local)

            # ───────────── 2) MOBI (EPUB → MOBI) ─────────────
            mobi_row = (
                db.query(BookFile)
                  .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.MOBI)
                  .first()
            )
            if mobi_row:
                _set_fmt_status(
                    book_id,
                    BookFileFormat.MOBI,
                    "skipped",
                    url=mobi_row.s3_url,
                    size=mobi_row.size_bytes or 0,
                    progress=100,
                )
                _update_job_progress_from_fmt(book_id, BookFileFormat.MOBI, 100)
                _clear_progress(book.id, BookFileFormat.MOBI)
                _log(book_id, "mobi: skipped (already in DB)")
            else:
                if have_epub_local:
                    _set_job_progress(book_id, 55, note="конвертация EPUB→MOBI")
                    _set_fmt_status(book_id, BookFileFormat.MOBI, "running", progress=0)
                    _update_job_progress_from_fmt(book_id, BookFileFormat.MOBI, 0)
                    out_mobi = os.path.join(tmp, "out.mobi")
                    _log(book_id, "mobi: convert start (epub → mobi)")
                    stage_started = time.monotonic()
                    rc, out, err = _run(
                        _build_convert_args(base_epub_local, out_mobi, EPUB2MOBI_OPTS),
                        book_id=book.id,
                        fmt=BookFileFormat.MOBI,
                        phase="convert",
                    )
                    if rc != 0 or not os.path.exists(out_mobi) or os.path.getsize(out_mobi) == 0:
                        _set_fmt_status(book_id, BookFileFormat.MOBI, "failed")
                        _log(book_id, f"mobi: convert failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                        _clear_progress(book.id, BookFileFormat.MOBI)
                        failed.append({"format": "MOBI", "error": f"convert failed (rc={rc})"})
                    else:
                        convert_elapsed = time.monotonic() - stage_started
                        mobi_key = _formats_key_from_pdf(pdf_key, "mobi")
                        try:
                            s3.upload_file(
                                out_mobi, S3_BUCKET, mobi_key,
                                ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for("mobi")}
                            )
                            size = os.path.getsize(out_mobi)
                            mobi_url = _safe_cdn_url(mobi_key)
                            db.add(BookFile(book_id=book.id, file_format=BookFileFormat.MOBI,
                                            s3_url=mobi_url, size_bytes=size))
                            db.commit()
                            _set_fmt_status(
                                book_id,
                                BookFileFormat.MOBI,
                                "success",
                                url=mobi_url,
                                size=size,
                                progress=100,
                            )
                            _update_job_progress_from_fmt(book_id, BookFileFormat.MOBI, 100)
                            _clear_progress(book.id, BookFileFormat.MOBI)
                            _log(
                                book_id,
                                f"mobi: uploaded → {mobi_url} ({size / (1024 * 1024):.2f} MiB, {convert_elapsed:.1f}s)",
                            )
                            created.append({"format": "MOBI", "url": mobi_url, "size": size})
                        except ClientError as e:
                            _set_fmt_status(book_id, BookFileFormat.MOBI, "failed")
                            _log(book_id, f"mobi: s3 upload failed: {e}")
                            _clear_progress(book.id, BookFileFormat.MOBI)
                            failed.append({"format": "MOBI", "error": "s3_upload_failed"})
                else:
                    _set_fmt_status(book_id, BookFileFormat.MOBI, "failed", progress=0)
                    _clear_progress(book.id, BookFileFormat.MOBI)
                    _log(book_id, "mobi: skipped (no local epub)")

            # ───────────── 3) AZW3 (EPUB → AZW3) ─────────────
            azw3_row = (
                db.query(BookFile)
                  .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.AZW3)
                  .first()
            )
            if azw3_row:
                _set_fmt_status(
                    book_id,
                    BookFileFormat.AZW3,
                    "skipped",
                    url=azw3_row.s3_url,
                    size=azw3_row.size_bytes or 0,
                    progress=100,
                )
                _update_job_progress_from_fmt(book_id, BookFileFormat.AZW3, 100)
                _clear_progress(book.id, BookFileFormat.AZW3)
                _log(book_id, "azw3: skipped (already in DB)")
            else:
                if have_epub_local:
                    _set_job_progress(book_id, 75, note="конвертация EPUB→AZW3")
                    _set_fmt_status(book_id, BookFileFormat.AZW3, "running", progress=0)
                    _update_job_progress_from_fmt(book_id, BookFileFormat.AZW3, 0)
                    out_azw3 = os.path.join(tmp, "out.azw3")
                    _log(book_id, "azw3: convert start (epub → azw3)")
                    stage_started = time.monotonic()
                    rc, out, err = _run(
                        _build_convert_args(base_epub_local, out_azw3, EPUB2AZW3_OPTS),
                        book_id=book.id,
                        fmt=BookFileFormat.AZW3,
                        phase="convert",
                    )
                    if rc != 0 or not os.path.exists(out_azw3) or os.path.getsize(out_azw3) == 0:
                        _set_fmt_status(book_id, BookFileFormat.AZW3, "failed")
                        _log(book_id, f"azw3: convert failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                        _clear_progress(book.id, BookFileFormat.AZW3)
                        failed.append({"format": "AZW3", "error": f"convert failed (rc={rc})"})
                    else:
                        convert_elapsed = time.monotonic() - stage_started
                        azw3_key = _formats_key_from_pdf(pdf_key, "azw3")
                        try:
                            s3.upload_file(
                                out_azw3, S3_BUCKET, azw3_key,
                                ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for("azw3")}
                            )
                            size = os.path.getsize(out_azw3)
                            azw3_url = _safe_cdn_url(azw3_key)
                            db.add(BookFile(book_id=book.id, file_format=BookFileFormat.AZW3,
                                            s3_url=azw3_url, size_bytes=size))
                            db.commit()
                            _set_fmt_status(
                                book_id,
                                BookFileFormat.AZW3,
                                "success",
                                url=azw3_url,
                                size=size,
                                progress=100,
                            )
                            _update_job_progress_from_fmt(book_id, BookFileFormat.AZW3, 100)
                            _clear_progress(book.id, BookFileFormat.AZW3)
                            _log(
                                book_id,
                                f"azw3: uploaded → {azw3_url} ({size / (1024 * 1024):.2f} MiB, {convert_elapsed:.1f}s)",
                            )
                            created.append({"format": "AZW3", "url": azw3_url, "size": size})
                        except ClientError as e:
                            _set_fmt_status(book_id, BookFileFormat.AZW3, "failed")
                            _log(book_id, f"azw3: s3 upload failed: {e}")
                            _clear_progress(book.id, BookFileFormat.AZW3)
                            failed.append({"format": "AZW3", "error": "s3_upload_failed"})
                else:
                    _set_fmt_status(book_id, BookFileFormat.AZW3, "failed", progress=0)
                    _clear_progress(book.id, BookFileFormat.AZW3)
                    _log(book_id, "azw3: skipped (no local epub)")

            # ───────────── 4) FB2 (EPUB → FB2) ─────────────
            fb2_row = (
                db.query(BookFile)
                  .filter(BookFile.book_id == book.id, BookFile.file_format == BookFileFormat.FB2)
                  .first()
            )
            if fb2_row:
                _set_fmt_status(
                    book_id,
                    BookFileFormat.FB2,
                    "skipped",
                    url=fb2_row.s3_url,
                    size=fb2_row.size_bytes or 0,
                    progress=100,
                )
                _update_job_progress_from_fmt(book_id, BookFileFormat.FB2, 100)
                _clear_progress(book.id, BookFileFormat.FB2)
                _log(book_id, "fb2: skipped (already in DB)")
            else:
                if have_epub_local:
                    _set_job_progress(book_id, 90, note="конвертация EPUB→FB2")
                    _set_fmt_status(book_id, BookFileFormat.FB2, "running", progress=0)
                    _update_job_progress_from_fmt(book_id, BookFileFormat.FB2, 0)
                    out_fb2 = os.path.join(tmp, "out.fb2")
                    _log(book_id, "fb2: convert start (epub → fb2)")
                    stage_started = time.monotonic()
                    rc, out, err = _run(
                        _build_convert_args(base_epub_local, out_fb2, EPUB2FB2_OPTS),
                        book_id=book.id,
                        fmt=BookFileFormat.FB2,
                        phase="convert",
                    )
                    if rc != 0 or not os.path.exists(out_fb2) or os.path.getsize(out_fb2) == 0:
                        _set_fmt_status(book_id, BookFileFormat.FB2, "failed")
                        _log(book_id, f"fb2: convert failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
                        _clear_progress(book.id, BookFileFormat.FB2)
                        failed.append({"format": "FB2", "error": f"convert failed (rc={rc})"})
                    else:
                        convert_elapsed = time.monotonic() - stage_started
                        fb2_key = _formats_key_from_pdf(pdf_key, "fb2")
                        try:
                            s3.upload_file(
                                out_fb2, S3_BUCKET, fb2_key,
                                ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for("fb2")}
                            )
                            size = os.path.getsize(out_fb2)
                            fb2_url = _safe_cdn_url(fb2_key)
                            db.add(BookFile(book_id=book.id, file_format=BookFileFormat.FB2,
                                            s3_url=fb2_url, size_bytes=size))
                            db.commit()
                            _set_fmt_status(
                                book_id,
                                BookFileFormat.FB2,
                                "success",
                                url=fb2_url,
                                size=size,
                                progress=100,
                            )
                            _update_job_progress_from_fmt(book_id, BookFileFormat.FB2, 100)
                            _clear_progress(book.id, BookFileFormat.FB2)
                            _log(
                                book_id,
                                f"fb2: uploaded → {fb2_url} ({size / (1024 * 1024):.2f} MiB, {convert_elapsed:.1f}s)",
                            )
                            created.append({"format": "FB2", "url": fb2_url, "size": size})
                        except ClientError as e:
                            _set_fmt_status(book_id, BookFileFormat.FB2, "failed")
                            _log(book_id, f"fb2: s3 upload failed: {e}")
                            _clear_progress(book.id, BookFileFormat.FB2)
                            failed.append({"format": "FB2", "error": "s3_upload_failed"})
                else:
                    _set_fmt_status(book_id, BookFileFormat.FB2, "failed", progress=0)
                    _clear_progress(book.id, BookFileFormat.FB2)
                    _log(book_id, "fb2: skipped (no local epub)")

        # Финальный статус
        status = "failed" if failed and not created else "success"
        _set_job_status(book_id, status)
        _set_job_times(book_id, finished=True)
        if status == "success":
            _set_job_progress(book_id, 100, note="готово")
        else:
            _set_job_progress(book_id, 100, note="завершено с ошибками")
        _log(book_id, f"done: created={len(created)} failed={len(failed)}")
        return {"ok": status == "success", "created": created, "failed": failed}

    except Exception as exc:
        logger.exception("[BOOK-FMT] unhandled")
        try:
            _set_job_status(book_id, "failed")
            _set_job_times(book_id, finished=True)
            _set_job_progress(book_id, 100, note="ошибка выполнения")
            _log(book_id, f"exception: {exc!r}")
        except Exception:
            pass
        return {"ok": False, "error": str(exc)}
    finally:
        for fmt in (BookFileFormat.EPUB, BookFileFormat.MOBI, BookFileFormat.AZW3, BookFileFormat.FB2):
            _clear_progress(book_id, fmt)
        db.close()
