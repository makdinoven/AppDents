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
import signal, os
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
CONVERT_HEARTBEAT_SECONDS = int(os.getenv("CALIBRE_PROGRESS_HEARTBEAT", "60"))
CALIBRE_SUPPORTS_JOBS_OVERRIDE = os.getenv("CALIBRE_SUPPORTS_JOBS")
CALIBRE_SUPPORTS_LOG_LEVEL_OVERRIDE = os.getenv("CALIBRE_SUPPORTS_LOG_LEVEL")
# --- новые константы сторожа ---
STALL_NO_OUTPUT_SECS   = int(os.getenv("CALIBRE_STALL_NO_OUTPUT_SECS", "300"))   # 5 мин
STALL_NO_PROGRESS_SECS = int(os.getenv("CALIBRE_STALL_NO_PROGRESS_SECS", "600")) # 10 мин
MAX_STAGE_SECS         = int(os.getenv("CALIBRE_MAX_STAGE_SECS", "5400"))        # 90 мин на шаг

def _tail_lines(s: str, n: int = 120) -> str:
    if not s:
        return ""
    lines = s.splitlines()[-n:]
    return "\n".join(lines)

def _set_job_phase(book_id: int, phase: str) -> None:
    _set_job_status(book_id, rds.hget(_k_job(book_id), "status") or "running")
    rds.hset(_k_job(book_id), mapping={"phase": phase})


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

def _which(cmd: str) -> str | None:
    for p in os.getenv("PATH", "").split(os.pathsep):
        candidate = os.path.join(p, cmd)
        if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
            return candidate
    return None

def _preflight_pdf(src_pdf: str, workdir: str) -> str:
    """Возвращает путь к «очищенному» PDF, либо исходный, если править нечем."""
    cleaned = os.path.join(workdir, "in.cleaned.pdf")
    # 1) qpdf --check и по возможности --linearize/clean
    qpdf = _which("qpdf")
    if qpdf:
        rc, out, err = _run([qpdf, "--check", src_pdf], phase="preflight")
        _log(0, f"qpdf --check rc={rc}")  # book_id здесь не обязателен
        # попробуем перепаковать
        rc, _, _ = _run([qpdf, "--linearize", "--object-streams=generate", src_pdf, cleaned], phase="preflight")
        if rc == 0 and os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            return cleaned
    # 2) mutool clean (MuPDF)
    mutool = _which("mutool")
    if mutool:
        rc, _, _ = _run([mutool, "clean", "-gg", src_pdf, cleaned], phase="preflight")
        if rc == 0 and os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            return cleaned
    # 3) (опционально) Ghostscript — дорогая операция, но спасает
    gs = _which("gs")
    if gs:
        rc, _, _ = _run([
            gs, "-dBATCH", "-dNOPAUSE", "-dSAFER", "-sDEVICE=pdfwrite",
            "-dDetectDuplicateImages=true", "-dCompressFonts=true",
            "-sOutputFile=" + cleaned, src_pdf
        ], phase="preflight")
        if rc == 0 and os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            return cleaned
    return src_pdf

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
        progress = max(0, min(100, progress))
        current = rds.hget(_k_job(book_id), "progress")
        if current is not None:
            try:
                progress = max(progress, int(current))
            except ValueError:
                pass
        data["progress"] = str(progress)
    if note is not None:
        data["note"] = note
    if data:
        rds.hset(_k_job(book_id), mapping=data)


def _update_job_progress_from_fmt(book_id: int, fmt: BookFileFormat, fmt_progress: int) -> None:
    if fmt_progress <= 0:
        return
    base, span = _JOB_PROGRESS_STEPS.get(fmt, (0, 0))
    fmt_progress = max(0, min(100, fmt_progress))
    job_progress = min(100, base + (fmt_progress * span) // 100)
    _set_job_progress(book_id, job_progress)


_progress_cache: dict[tuple[int, BookFileFormat], tuple[int, float]] = {}
PROGRESS_MIN_DELTA = int(os.getenv("CALIBRE_PROGRESS_MIN_DELTA", "1"))
PROGRESS_MIN_INTERVAL = float(os.getenv("CALIBRE_PROGRESS_MIN_INTERVAL", "5"))


def _fmt_label(fmt: BookFileFormat) -> str:
    return fmt.value.lower()


def _remember_progress(book_id: int, fmt: BookFileFormat, progress: int) -> bool:
    now = time.monotonic()
    key = (book_id, fmt)
    prev = _progress_cache.get(key)
    prev_val = prev[0] if prev else None
    prev_ts = prev[1] if prev else 0.0

    if prev is None or progress in (0, 100):
        _progress_cache[key] = (progress, now)
        return True

    if progress <= prev_val:
        _progress_cache[key] = (prev_val, now)
        return False

    delta = progress - prev_val
    if delta >= 5 or delta >= PROGRESS_MIN_DELTA and (now - prev_ts) >= PROGRESS_MIN_INTERVAL:
        _progress_cache[key] = (progress, now)
        return True

    _progress_cache[key] = (prev_val, now)
    return False


def _clear_progress(book_id: int, fmt: BookFileFormat) -> None:
    _progress_cache.pop((book_id, fmt), None)


def _handle_convert_output(book_id: int, fmt: BookFileFormat, line: str, *, stream: str) -> None:
    if not line:
        return

    for chunk in re.split(r"[\r\n]+", line):
        stripped = chunk.strip()
        if not stripped:
            continue

        match = _PROGRESS_RE.search(stripped)
        if match:
            progress = max(0, min(100, int(match.group(1))))
            if _remember_progress(book_id, fmt, progress):
                _set_fmt_status(book_id, fmt, "running", progress=progress)
                _update_job_progress_from_fmt(book_id, fmt, progress)
                _log(book_id, f"{_fmt_label(fmt)}: progress {progress}%")
            continue

        lowered = stripped.lower()
        if stream == "stderr":
            _log(book_id, f"{_fmt_label(fmt)} stderr: {stripped}")
        elif any(lowered.startswith(prefix) for prefix in ("input ", "output ", "parsed", "converting", "rendering", "creating", "processing", "splitting", "working")):
            _log(book_id, f"{_fmt_label(fmt)}: {stripped}")


def _build_convert_args(src_path: str, dst_path: str, extra_opts: str | None = None) -> list[str]:
    args = [EBOOK_CONVERT_BIN, src_path, dst_path]
    opts = shlex.split(extra_opts or "")

    if "--jobs" not in opts and _calibre_supports_jobs():
        jobs = _calibre_jobs()
        if jobs:
            args.extend(["--jobs", str(jobs)])

    if (
        "--log-level" not in opts
        and "--verbose" not in opts
        and _calibre_supports_log_level()
    ):
        args.extend(["--log-level", CALIBRE_LOG_LEVEL])

    args.extend(opts)
    return args


_CALIBRE_SUPPORTS_JOBS: bool | None = None
_CALIBRE_SUPPORTS_LOG_LEVEL: bool | None = None
_CALIBRE_HELP_CACHE: str | None = None


def _calibre_help_text() -> str:
    global _CALIBRE_HELP_CACHE
    if _CALIBRE_HELP_CACHE is not None:
        return _CALIBRE_HELP_CACHE
    try:
        proc = subprocess.run(
            [EBOOK_CONVERT_BIN, "--help"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            check=False,
            timeout=8,
        )
        _CALIBRE_HELP_CACHE = proc.stdout or ""
    except Exception as exc:
        logger.warning("Cannot probe ebook-convert capabilities: %s", exc)
        _CALIBRE_HELP_CACHE = ""
    return _CALIBRE_HELP_CACHE


def _calibre_supports_jobs() -> bool:
    global _CALIBRE_SUPPORTS_JOBS

    if _CALIBRE_SUPPORTS_JOBS is not None:
        return _CALIBRE_SUPPORTS_JOBS

    if CALIBRE_SUPPORTS_JOBS_OVERRIDE is not None:
        _CALIBRE_SUPPORTS_JOBS = CALIBRE_SUPPORTS_JOBS_OVERRIDE.strip().lower() in {"1", "true", "yes", "y"}
        return _CALIBRE_SUPPORTS_JOBS

    try:
        _CALIBRE_SUPPORTS_JOBS = "--jobs" in _calibre_help_text()
    except Exception:
        _CALIBRE_SUPPORTS_JOBS = False

    return _CALIBRE_SUPPORTS_JOBS


def _calibre_supports_log_level() -> bool:
    global _CALIBRE_SUPPORTS_LOG_LEVEL

    if _CALIBRE_SUPPORTS_LOG_LEVEL is not None:
        return _CALIBRE_SUPPORTS_LOG_LEVEL

    if CALIBRE_SUPPORTS_LOG_LEVEL_OVERRIDE is not None:
        _CALIBRE_SUPPORTS_LOG_LEVEL = CALIBRE_SUPPORTS_LOG_LEVEL_OVERRIDE.strip().lower() in {"1", "true", "yes", "y"}
        return _CALIBRE_SUPPORTS_LOG_LEVEL

    try:
        help_text = _calibre_help_text()
        _CALIBRE_SUPPORTS_LOG_LEVEL = "--log-level" in help_text
    except Exception:
        _CALIBRE_SUPPORTS_LOG_LEVEL = False

    return _CALIBRE_SUPPORTS_LOG_LEVEL

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

def _run(cmd, *, book_id: int | None = None, fmt: BookFileFormat | None = None, phase: str | None = None):
    args = shlex.split(cmd) if isinstance(cmd, str) else cmd
    # отдельная группа процессов, чтобы убивать детей одним сигналом
    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,
    )

    stdout_lines, stderr_lines = [], []
    start_time = time.monotonic()
    last_output = start_time
    last_heartbeat = start_time

    def _pg_kill(sig):
        try:
            os.killpg(proc.pid, sig)
        except Exception:
            pass

    if book_id is not None and fmt is not None and phase:
        _log(book_id, f"{_fmt_label(fmt)}:{phase} started: {' '.join(args)}")

    sel = selectors.DefaultSelector()
    if proc.stdout: sel.register(proc.stdout, selectors.EVENT_READ, ("stdout", proc.stdout))
    if proc.stderr: sel.register(proc.stderr, selectors.EVENT_READ, ("stderr", proc.stderr))

    while sel.get_map():
        events = sel.select(timeout=1.0)

        # --- нет событий: проверки таймаутов ---
        now = time.monotonic()
        if not events:
            # хартбит + подсказка «жив»
            if (book_id is not None and fmt is not None and
                CONVERT_HEARTBEAT_SECONDS > 0 and now - last_heartbeat >= CONVERT_HEARTBEAT_SECONDS):
                elapsed = now - start_time
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} still running ({elapsed:.0f}s elapsed)")
                last_heartbeat = now

            # сторож: нет вывода
            if STALL_NO_OUTPUT_SECS and (now - last_output) >= STALL_NO_OUTPUT_SECS:
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} stalled: no output for {int(now-last_output)}s → terminate")
                _pg_kill(signal.SIGTERM)

            # общий предел на этап
            if MAX_STAGE_SECS and (now - start_time) >= MAX_STAGE_SECS:
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} timeout after {int(now-start_time)}s → kill")
                _pg_kill(signal.SIGKILL)

            if proc.poll() is not None and not sel.get_map():
                break
            continue

        # --- читаем вывод ---
        for key, _ in events:
            stream_name, stream = key.data
            line = stream.readline()
            if line:
                last_output = time.monotonic()
                if stream_name == "stdout":
                    stdout_lines.append(line)
                else:
                    stderr_lines.append(line)
                if book_id is not None and fmt is not None:
                    _handle_convert_output(book_id, fmt, line, stream=stream_name)
            else:
                sel.unregister(stream)

        # повторная проверка хартбита/прогресса
        now = time.monotonic()
        if (book_id is not None and fmt is not None and
            CONVERT_HEARTBEAT_SECONDS > 0 and now - last_heartbeat >= CONVERT_HEARTBEAT_SECONDS):
            elapsed = now - start_time
            _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} still running ({elapsed:.0f}s elapsed)")
            last_heartbeat = now

        if proc.poll() is not None and not sel.get_map():
            break

    rc = proc.wait()

    if book_id is not None and fmt is not None and phase:
        _log(book_id, f"{_fmt_label(fmt)}:{phase} finished rc={rc}")
        # полезный хвост в Redis на случай падения/сталла
        rds.hset(_k_fmt(book_id, fmt.value), mapping={
            "rc": str(rc),
            "stdout_tail": _tail_lines("".join(stdout_lines), 120),
            "stderr_tail": _tail_lines("".join(stderr_lines), 120),
        })

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
        try:
            vrc, vout, verr = _run([EBOOK_CONVERT_BIN, "--version"], phase="probe")
            ver_line = (vout or verr or "").strip() or f"rc={vrc}"
            _log(book_id, f"calibre: {ver_line}")
        except Exception as e:
            _log(book_id, f"calibre: version probe failed: {e}")

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
                _set_job_phase(book_id, "preflight")
                src_pdf_clean = _preflight_pdf(src_pdf, tmp)

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
                        _build_convert_args(src_pdf_clean, base_epub_local, PDF2EPUB_OPTS),
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
