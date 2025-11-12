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
import psutil
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
# PDF → EPUB - по умолчанию пробуем использовать внешний pdftohtml (быстрее и стабильнее)
PDF2EPUB_OPTS  = os.getenv("CALIBRE_PDF2EPUB_OPTS", "--use-auto-toc --pdf-engine=pdftohtml")
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
STALL_NO_OUTPUT_SECS   = int(os.getenv("CALIBRE_STALL_NO_OUTPUT_SECS", "150"))   
STALL_NO_PROGRESS_SECS = int(os.getenv("CALIBRE_STALL_NO_PROGRESS_SECS", "300")) 
MAX_STAGE_SECS         = int(os.getenv("CALIBRE_MAX_STAGE_SECS", "5400"))
MAX_CONVERT_RETRIES = int(os.getenv("CALIBRE_MAX_CONVERT_RETRIES", "3"))  # 3 попытки: обычная → нормализация → агрессивное упрощение
# Доп. опции на ретраях (более мягкие эвристики + внешний движок)
PDF2EPUB_RETRY_OPTS = os.getenv(
    "CALIBRE_PDF2EPUB_RETRY_OPTS",
    "--use-auto-toc --pdf-engine=pdftohtml --enable-heuristics --unwrap-factor 0.18"
)
MIN_EPUB_ABS_BYTES = int(os.getenv("CALIBRE_MIN_EPUB_ABS_BYTES", str(512 * 1024)))  # ≥ 512KB
MIN_EPUB_RATIO     = float(os.getenv("CALIBRE_MIN_EPUB_RATIO", "0.01"))             # ≥ 1% от размера PDF

# --- OCR (ocrmypdf) ---
OCR_ENABLE   = os.getenv("CALIBRE_ENABLE_OCR", "1").strip().lower() in {"1","true","yes","y"}
OCRMYPDF_BIN = os.getenv("OCRMYPDF_BIN", "ocrmypdf")
OCR_LANGS    = os.getenv("OCR_LANGS", "eng+rus")   # под себя
# разумные, не «тяжёлые» опции по умолчанию; можно переопределить через ENV
# --output-type pdf: не делать PDF/A (избегает проблем с цветовыми пространствами)
OCR_OPTS     = os.getenv(
    "OCR_OPTS",
    "--skip-text --output-type pdf"
)

# --- флаги для AZW3 (минимальные, чтобы избежать ошибок) ---
# Оставляем пустыми по умолчанию, чтобы не конфликтовать с версией Calibre
EPUB2AZW3_OPTS = os.getenv("EPUB2AZW3_OPTS", "")
# Стратегия нормализации PDF по шагам (через запятую): gs,mutool,qpdf
PDF_PREFLIGHT_STRATEGY = os.getenv("CALIBRE_PDF_PREFLIGHT_STRATEGY", "gs,mutool,qpdf")        # 90 мин на шаг

def _tail_lines(s: str, n: int = 120) -> str:
    if not s:
        return ""
    lines = s.splitlines()[-n:]
    return "\n".join(lines)

def _set_job_phase(book_id: int, phase: str) -> None:
    _set_job_status(book_id, rds.hget(_k_job(book_id), "status") or "running")
    rds.hset(_k_job(book_id), mapping={"phase": phase})

def _should_treat_epub_as_broken(pdf_path: str, epub_path: str) -> bool:
    """Эвристика «пустого» EPUB: слишком малый размер относительно исходного PDF."""
    try:
        pdf_size  = os.path.getsize(pdf_path)
        epub_size = os.path.getsize(epub_path)
    except Exception:
        return False
    min_reasonable = max(MIN_EPUB_ABS_BYTES, int(pdf_size * MIN_EPUB_RATIO))
    return epub_size < max(1, min_reasonable)


def _maybe_ocr_pdf(
    book_id: int,
    src_pdf: str,
    workdir: str,
    *,
    note: str = "ocr pass",
) -> tuple[bool, str | None]:
    """
    Если есть ocrmypdf и OCR включен — сделать OCR поверх src_pdf → вернуть путь к ocr.pdf.
    """
    if not OCR_ENABLE:
        _log(book_id, "ocr: disabled by CALIBRE_ENABLE_OCR")
        return False, None
    if not _which(OCRMYPDF_BIN):
        _log(book_id, f"ocr: '{OCRMYPDF_BIN if 'OCRMYPDF_BIN' in globals() else OCRMYPDF_BIN}' not found; skip")
        return False, None

    out_pdf = os.path.join(workdir, "in.ocr.pdf")
    args = [OCRMYPDF_BIN, *shlex.split(OCR_OPTS), "-l", OCR_LANGS, src_pdf, out_pdf]

    _log(book_id, f"ocr: start ({note}) → {' '.join(args)}")
    rc, _, _ = _run(args, book_id=book_id, fmt=BookFileFormat.EPUB, phase="ocr")
    if rc == 0 and os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 0:
        _log(book_id, f"ocr: ok → {out_pdf}")
        return True, out_pdf

    _log(book_id, f"ocr: failed rc={rc}")
    return False, None

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
def _simplify_pdf_via_ps(book_id: int, src_pdf: str, workdir: str) -> tuple[bool, str | None]:
    """
    Упрощение PDF через PostScript (pdf2ps → ps2pdf):
    - Сохраняет векторную графику и текст
    - "Перепечатывает" PDF, удаляя сложные структуры
    - Лучше качество, чем растеризация
    """
    if not _which("pdf2ps") or not _which("ps2pdf"):
        _log(book_id, "simplify-ps: pdf2ps/ps2pdf not found, skipping")
        return False, None
    
    ps_file = os.path.join(workdir, "temp.ps")
    out_pdf = os.path.join(workdir, "in.ps-simplified.pdf")
    
    _log(book_id, "simplify-ps: converting PDF → PS → PDF")
    
    # PDF → PostScript
    rc1, _, _ = _run(["pdf2ps", src_pdf, ps_file],
                     book_id=book_id, fmt=BookFileFormat.EPUB, phase="ps-simplify")
    if rc1 != 0 or not os.path.exists(ps_file):
        _log(book_id, f"simplify-ps: pdf2ps failed rc={rc1}")
        return False, None
    
    # PostScript → PDF
    rc2, _, _ = _run(["ps2pdf", ps_file, out_pdf],
                     book_id=book_id, fmt=BookFileFormat.EPUB, phase="ps-simplify")
    
    # Удаляем временный PS
    try:
        os.remove(ps_file)
    except Exception:
        pass
    
    if rc2 == 0 and os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 0:
        _log(book_id, f"simplify-ps: ok → {out_pdf}")
        return True, out_pdf
    
    _log(book_id, f"simplify-ps: ps2pdf failed rc={rc2}")
    return False, None


def _simplify_pdf_aggressive(book_id: int, src_pdf: str, workdir: str) -> tuple[bool, str | None]:
    """
    Агрессивное упрощение PDF через Ghostscript (качественная растеризация):
    - Конвертирует в изображения высокого разрешения
    - Сохраняет читаемость текста
    - Оптимизирует для конверсии
    """
    if not _which("gs"):
        return False, None
    
    out_pdf = os.path.join(workdir, "in.simplified.pdf")
    # 300 DPI - стандарт для качественного текста
    dpi = os.getenv("CALIBRE_SIMPLIFY_DPI", "300")
    
    _log(book_id, f"simplify: quality rasterization at {dpi} dpi (preserving text)")
    rc, _, _ = _run([
        "gs",
        "-dBATCH", "-dNOPAUSE", "-dSAFER",
        "-sDEVICE=pdfwrite",
        "-dPDFSETTINGS=/prepress",  # высокое качество вместо /ebook
        "-dColorImageResolution=" + dpi,
        "-dGrayImageResolution=" + dpi,
        "-dMonoImageResolution=" + dpi,
        "-dDownsampleColorImages=true",
        "-dDownsampleGrayImages=true",
        "-dDownsampleMonoImages=true",
        "-dColorImageDownsampleType=/Bicubic",
        "-dGrayImageDownsampleType=/Bicubic",
        "-dEmbedAllFonts=true",  # СОХРАНЯЕМ шрифты
        "-dSubsetFonts=true",
        "-dCompressFonts=true",
        "-dAutoFilterColorImages=false",  # без автофильтров
        "-dAutoFilterGrayImages=false",
        "-dColorImageFilter=/FlateEncode",  # качественное сжатие
        "-dGrayImageFilter=/FlateEncode",
        "-sOutputFile=" + out_pdf,
        src_pdf
    ], book_id=book_id, fmt=BookFileFormat.EPUB, phase="simplify")
    
    if rc == 0 and os.path.exists(out_pdf) and os.path.getsize(out_pdf) > 0:
        _log(book_id, f"simplify: ok → {out_pdf} ({os.path.getsize(out_pdf) / (1024*1024):.1f} MiB)")
        return True, out_pdf
    
    _log(book_id, f"simplify: failed rc={rc}")
    return False, None


def _normalize_pdf_sequence(book_id: int, src_pdf: str, workdir: str, *, strategy: str) -> tuple[str, str]:
    """
    Прогоняет src_pdf через цепочку нормализаций (gs → mutool → qpdf),
    возвращает (путь_к_нормализованному, метка_чем_нормализовали).
    Если ничего не удалось — возвращает исходный файл и 'none'.
    """
    steps = [s.strip().lower() for s in strategy.split(",") if s.strip()]
    cur = src_pdf
    used = []
    for step in steps:
        out = os.path.join(workdir, f"in.norm.{len(used)+1}.pdf")
        if step == "gs" and _which("gs"):
            rc, _, _ = _run(["gs",
                                "-dBATCH","-dNOPAUSE","-dSAFER",
                                "-sDEVICE=pdfwrite",
                                "-dDownsampleColorImages=false",
                                "-dDownsampleGrayImages=false",
                                "-dDownsampleMonoImages=false",
                                "-dDetectDuplicateImages=true",
                                "-dCompressFonts=true",
                                "-dEmbedAllFonts=true","-dSubsetFonts=true",
                                "-sColorConversionStrategy=UseDeviceIndependentColor",
                                "-sOutputFile=" + out, cur]
            , book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
            if rc == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
                used.append("gs"); cur = out; continue

        if step == "mutool" and _which("mutool"):
            rc, _, _ = _run(["mutool", "clean", "-gg", cur, out],
                            book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
            if rc == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
                used.append("mutool"); cur = out; continue

        if step == "qpdf" and _which("qpdf"):
            rc, _, _ = _run(["qpdf", "--linearize", "--object-streams=generate", cur, out],
                            book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
            if rc == 0 and os.path.exists(out) and os.path.getsize(out) > 0:
                used.append("qpdf"); cur = out; continue
    return cur, ("+".join(used) if used else "none")


def _convert_pdf_to_epub_with_retries(
    book_id: int,
    src_pdf_initial: str,
    out_epub: str,
) -> tuple[bool, str | None]:
    """
    Пытается PDF→EPUB с авто-нормализацией, sanity-check и OCR-веткой.
    Возвращает (success, путь_к_epub_или_None).
    """
    attempt = 0
    src_pdf_current = src_pdf_initial
    tried_ocr = False

    while True:
        # ограничим число обычных ретраев
        if attempt > MAX_CONVERT_RETRIES:
            # если OCR ещё не пробовали — попробуем 1 раз
            if not tried_ocr:
                ok, ocr_pdf = _maybe_ocr_pdf(book_id, src_pdf_current, os.path.dirname(out_epub), note="on final fallback")
                if ok and ocr_pdf:
                    tried_ocr = True
                    src_pdf_current = ocr_pdf
                    attempt = 0  # дадим ещё проходов после OCR
                    continue
            _log(book_id, "epub: all attempts exhausted")
            return False, None

        attempt += 1
        extra_opts = PDF2EPUB_OPTS if attempt == 1 else (PDF2EPUB_OPTS + " " + PDF2EPUB_RETRY_OPTS)
        _set_job_progress(book_id, note=f"PDF→EPUB попытка {attempt}")
        _set_fmt_status(book_id, BookFileFormat.EPUB, "running", progress=0)

        rc, _, _ = _run(
            _build_convert_args(src_pdf_current, out_epub, extra_opts),
            book_id=book_id, fmt=BookFileFormat.EPUB, phase=f"convert#{attempt}",
        )

        # успех по коду возврата и наличию файла
        if rc == 0 and os.path.exists(out_epub) and os.path.getsize(out_epub) > 0:
            # sanity-check по размеру
            if _should_treat_epub_as_broken(src_pdf_current, out_epub):
                _log(book_id, "epub: sanity-check failed (file too small) → treat as failure")
                try:
                    os.remove(out_epub)
                except Exception:
                    pass
            else:
                return True, out_epub

        # сюда попадаем при неуспехе попытки (rc!=0) или провале sanity-check
        if attempt > MAX_CONVERT_RETRIES:
            # OCR как отдельный финальный шанс
            if not tried_ocr:
                ok, ocr_pdf = _maybe_ocr_pdf(book_id, src_pdf_current, os.path.dirname(out_epub), note="after normal retries")
                if ok and ocr_pdf:
                    tried_ocr = True
                    src_pdf_current = ocr_pdf
                    attempt = 0
                    continue
            _log(book_id, f"epub: all attempts failed (last rc={rc})")
            return False, None

        # ещё не исчерпали обычные ретраи → пробуем разные стратегии
        _log(book_id, f"epub: attempt {attempt} failed (rc={rc}), trying PDF normalize…")
        
        # Попытка 2: PostScript путь (быстрее и лучше качество)
        if attempt == 2:
            _log(book_id, "epub: trying PS-simplification (pdf→ps→pdf)")
            ok_ps, ps_pdf = _simplify_pdf_via_ps(book_id, src_pdf_current, os.path.dirname(out_epub))
            if ok_ps and ps_pdf:
                src_pdf_current = ps_pdf
                _log(book_id, "epub: PS-simplified → retry")
                continue
            # Если PS не сработал, пробуем обычную нормализацию
            _log(book_id, "epub: PS-simplification failed, trying standard normalize")
        
        # Попытка 3: Качественная растеризация (последний шанс перед OCR)
        if attempt == 3:
            _log(book_id, "epub: trying quality rasterization (300 dpi)")
            ok_simp, simp_pdf = _simplify_pdf_aggressive(book_id, src_pdf_current, os.path.dirname(out_epub))
            if ok_simp and simp_pdf:
                src_pdf_current = simp_pdf
                _log(book_id, "epub: rasterized PDF → retry")
                continue
        
        # Обычная нормализация (для попытки 1 и fallback)
        src_pdf_current, used = _normalize_pdf_sequence(
            book_id, src_pdf_current, os.path.dirname(out_epub),
            strategy=PDF_PREFLIGHT_STRATEGY
        )
        _log(book_id, f"epub: normalize done via [{used}] → retry")


def _preflight_pdf(book_id: int, src_pdf: str, workdir: str) -> str:
    cleaned = os.path.join(workdir, "in.cleaned.pdf")

    qpdf = _which("qpdf")
    if qpdf:
        rc, out, err = _run([qpdf, "--check", src_pdf],
                            book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
        _log(book_id, f"qpdf --check rc={rc}")
        rc, _, _ = _run([qpdf, "--linearize", "--object-streams=generate", src_pdf, cleaned],
                        book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
        if rc == 0 and os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            return cleaned

    mutool = _which("mutool")
    if mutool:
        rc, _, _ = _run([mutool, "clean", "-gg", src_pdf, cleaned],
                        book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
        if rc == 0 and os.path.exists(cleaned) and os.path.getsize(cleaned) > 0:
            return cleaned

    gs = _which("gs")
    if gs:
        rc, _, _ = _run([
            gs, "-dBATCH", "-dNOPAUSE", "-dSAFER", "-sDEVICE=pdfwrite",
            "-dDetectDuplicateImages=true", "-dCompressFonts=true",
            "-sOutputFile=" + cleaned, src_pdf
        ], book_id=book_id, fmt=BookFileFormat.EPUB, phase="preflight")
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


def _handle_convert_output(
    book_id: int,
    fmt: BookFileFormat,
    line: str,
    *,
    stream: str,
) -> bool:
    """
    Разбирает строку вывода calibre. Обновляет прогресс/лог/статусы.
    Возвращает True, если в этой строке был обнаружен НОВЫЙ прогресс (%).
    """
    if not line:
        return False

    progress_seen = False

    for chunk in re.split(r"[\r\n]+", line):
        stripped = chunk.strip()
        if not stripped:
            continue

        # 1) прогресс "NN%"
        m = _PROGRESS_RE.search(stripped)
        if m:
            prog = max(0, min(100, int(m.group(1))))
            if _remember_progress(book_id, fmt, prog):
                _set_fmt_status(book_id, fmt, "running", progress=prog)
                _update_job_progress_from_fmt(book_id, fmt, prog)
                try:
                    rds.hset(_k_fmt(book_id, fmt.value), mapping={
                        "last_progress_at": str(int(time.time()))
                    })
                except Exception:
                    pass
                _log(book_id, f"{_fmt_label(fmt)}: progress {prog}%")
                progress_seen = True
            continue

        # 2) диагностический вывод
        lowered = stripped.lower()
        if stream == "stderr":
            _log(book_id, f"{_fmt_label(fmt)} stderr: {stripped}")
        elif any(
            lowered.startswith(prefix) for prefix in (
                "input ", "output ", "parsed", "converting",
                "rendering", "creating", "processing",
                "splitting", "working"
            )
        ):
            _log(book_id, f"{_fmt_label(fmt)}: {stripped}")

    return progress_seen



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

from collections import deque

def _run(
    cmd,
    *,
    book_id: int | None = None,
    fmt: BookFileFormat | None = None,
    phase: str | None = None,
):
    """
    Запускает внешнюю команду, построчно читает stdout/stderr,
    шлёт хартбиты, следит за «тишиной», отсутствием прогресса
    и предельной длительностью этапа. При убийстве кладёт хвосты в Redis.
    Возвращает (rc, stdout_tail, stderr_tail).
    """
    args = shlex.split(cmd) if isinstance(cmd, str) else list(cmd)

    proc = subprocess.Popen(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        bufsize=1,
        preexec_fn=os.setsid,  # отдельная группа процессов
    )

    # буферы с ограничением по числу строк (без раздувания памяти)
    STD_TAIL_LINES = int(os.getenv("CALIBRE_STD_TAIL_LINES", "200"))
    stdout_tail_buf: deque[str] = deque(maxlen=STD_TAIL_LINES)
    stderr_tail_buf: deque[str] = deque(maxlen=STD_TAIL_LINES)

    # CPU «пульс» процесса
    try:
        proc_obj = psutil.Process(proc.pid) if psutil else None
    except Exception:
        proc_obj = None

    start_time = time.monotonic()
    last_progress_ts = start_time
    last_heartbeat_ts = start_time
    last_any_activity_ts = start_time  # output || new progress || cpu pulse

    last_cpu_check = start_time
    last_cpu_time = 0.0
    if proc_obj:
        try:
            c0 = proc_obj.cpu_times()
            last_cpu_time = float(getattr(c0, "user", 0.0)) + float(getattr(c0, "system", 0.0))
        except Exception:
            last_cpu_time = 0.0

    def _pg_kill(sig):
        try:
            os.killpg(proc.pid, sig)
        except Exception:
            pass

    if book_id is not None and fmt is not None and phase:
        _log(book_id, f"{_fmt_label(fmt)}:{phase} started: {' '.join(args)}")

    sel = selectors.DefaultSelector()
    if proc.stdout:
        sel.register(proc.stdout, selectors.EVENT_READ, ("stdout", proc.stdout))
    if proc.stderr:
        sel.register(proc.stderr, selectors.EVENT_READ, ("stderr", proc.stderr))

    while sel.get_map():
        events = sel.select(timeout=1.0)
        now = time.monotonic()

        # CPU-пульс (проверяем всегда, не только при отсутствии событий)
        if proc_obj and (now - last_cpu_check) >= 15.0:
            try:
                ct = proc_obj.cpu_times()
                cpu_time = float(getattr(ct, "user", 0.0)) + float(getattr(ct, "system", 0.0))
                if cpu_time - last_cpu_time >= 1.0:
                    last_any_activity_ts = now
                last_cpu_time = cpu_time
            except Exception:
                pass
            last_cpu_check = now

        # heartbeat (проверяем всегда)
        if (
            book_id is not None and fmt is not None and
            CONVERT_HEARTBEAT_SECONDS > 0 and
            (now - last_heartbeat_ts) >= CONVERT_HEARTBEAT_SECONDS
        ):
            elapsed = now - start_time
            _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} still running ({int(elapsed)}s elapsed)")
            last_heartbeat_ts = now

        # «нет прогресса» - критично проверять всегда, независимо от вывода!
        if STALL_NO_PROGRESS_SECS and (now - last_progress_ts) >= STALL_NO_PROGRESS_SECS:
            if book_id is not None and fmt is not None:
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} stalled: "
                              f"no progress for {int(now - last_progress_ts)}s → terminate")
                try:
                    rds.hset(_k_fmt(book_id, fmt.value), mapping={"stalled": "1", "stall_kind": "no_progress"})
                except Exception:
                    pass
            _pg_kill(signal.SIGTERM)
            break

        # «тишина» - только при отсутствии событий
        if not events and STALL_NO_OUTPUT_SECS and (now - last_any_activity_ts) >= STALL_NO_OUTPUT_SECS:
            if book_id is not None and fmt is not None:
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} stalled: "
                              f"no output/progress for {int(now - last_any_activity_ts)}s → terminate")
                try:
                    rds.hset(_k_fmt(book_id, fmt.value), mapping={"stalled": "1", "stall_kind": "no_output"})
                except Exception:
                    pass
            _pg_kill(signal.SIGTERM)
            break

        # общий таймаут (проверяем всегда)
        if MAX_STAGE_SECS and (now - start_time) >= MAX_STAGE_SECS:
            if book_id is not None and fmt is not None:
                _log(book_id, f"{_fmt_label(fmt)}:{phase or 'convert'} timeout after {int(now - start_time)}s → kill")
                try:
                    rds.hset(_k_fmt(book_id, fmt.value), mapping={"stalled": "1", "stall_kind": "max_stage"})
                except Exception:
                    pass
            _pg_kill(signal.SIGKILL)
            break

        if not events:
            if proc.poll() is not None and not sel.get_map():
                break
            continue

        # есть строки
        for key, _ in events:
            stream_name, stream = key.data
            line = stream.readline()
            if line:
                last_any_activity_ts = now
                if stream_name == "stdout":
                    stdout_tail_buf.append(line.rstrip("\n"))
                else:
                    stderr_tail_buf.append(line.rstrip("\n"))

                if book_id is not None and fmt is not None:
                    progressed = _handle_convert_output(book_id, fmt, line, stream=stream_name)
                    if progressed:
                        last_progress_ts = now
                        last_any_activity_ts = now
            else:
                sel.unregister(stream)

        if proc.poll() is not None and not sel.get_map():
            break

    rc = proc.wait()

    # хвосты для диагностики
    stdout_tail = "\n".join(list(stdout_tail_buf)[-120:])
    stderr_tail = "\n".join(list(stderr_tail_buf)[-120:])

    if book_id is not None and fmt is not None and phase:
        try:
            rds.hset(_k_fmt(book_id, fmt.value), mapping={
                "rc": str(rc),
                "stdout_tail": stdout_tail,
                "stderr_tail": stderr_tail,
            })
        except Exception:
            pass
        _log(book_id, f"{_fmt_label(fmt)}:{phase} finished rc={rc}")

    return rc, stdout_tail, stderr_tail


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
                src_pdf_clean = _preflight_pdf(book_id, src_pdf, tmp)

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
                ok_epub, local_epub_path = _convert_pdf_to_epub_with_retries(
                    book_id=book.id,
                    src_pdf_initial=src_pdf_clean,   # твой «предпрефлайченный» src_pdf_clean
                    out_epub=base_epub_local,
                )

                if not ok_epub:
                    _convert_pdf_direct_formats(
                        book_id=book.id,
                        src_pdf=src_pdf_clean,   # уже «очищенный» после _preflight_pdf
                        tmp_dir=tmp,
                        pdf_key=pdf_key,
                        db=db,
                        created=created,
                        failed=failed,
                    )
                else:
                    convert_elapsed = time.monotonic() - stage_started
                    epub_key = _formats_key_from_pdf(pdf_key, "epub")
                    try:
                        s3.upload_file(
                            local_epub_path, S3_BUCKET, epub_key,
                            ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for("epub")}
                        )
                        size = os.path.getsize(local_epub_path)
                        epub_url = _safe_cdn_url(epub_key)
                        db.add(BookFile(book_id=book.id, file_format=BookFileFormat.EPUB,
                                        s3_url=epub_url, size_bytes=size))
                        db.commit()
                        _set_fmt_status(book_id, BookFileFormat.EPUB, "success", url=epub_url, size=size, progress=100)
                        _update_job_progress_from_fmt(book_id, BookFileFormat.EPUB, 100)
                        _clear_progress(book.id, BookFileFormat.EPUB)
                        _log(book_id, f"epub: uploaded → {epub_url} ({size / (1024 * 1024):.2f} MiB, {convert_elapsed:.1f}s)")
                        created.append({"format": "EPUB", "url": epub_url, "size": size})
                    except ClientError as e:
                        _set_fmt_status(book_id, BookFileFormat.EPUB, "failed")
                        _clear_progress(book.id, BookFileFormat.EPUB)
                        _log(book_id, f"epub: s3 upload failed: {e}")
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

def _convert_pdf_direct_formats(
    book_id: int,
    src_pdf: str,
    tmp_dir: str,
    pdf_key: str,
    db: Session,
    created: list,
    failed: list,
):
    """Пытается собрать AZW3/MOBI/FB2 напрямую из PDF, если EPUB не вышел."""
    # Для прямой конверсии из PDF используем минимальные опции (пустые строки)
    direct_targets = [
        (BookFileFormat.AZW3, "azw3", ""),
        (BookFileFormat.MOBI, "mobi", ""),
        (BookFileFormat.FB2,  "fb2",  ""),
    ]

    for fmt, ext, opts in direct_targets:
        _set_fmt_status(book_id, fmt, "running", progress=0)
        _update_job_progress_from_fmt(book_id, fmt, 0)
        out_path = os.path.join(tmp_dir, f"out_direct.{ext}")
        _log(book_id, f"{ext}: direct convert start (pdf → {ext})")

        rc, out, err = _run(
            _build_convert_args(src_pdf, out_path, opts),
            book_id=book_id, fmt=fmt, phase="convert_direct",
        )

        if rc != 0 or not os.path.exists(out_path) or os.path.getsize(out_path) == 0:
            _set_fmt_status(book_id, fmt, "failed")
            _clear_progress(book_id, fmt)
            _log(book_id, f"{ext}: direct PDF→{ext} failed (rc={rc})\nSTDOUT:\n{out}\nSTDERR:\n{err}")
            failed.append({"format": fmt.value, "error": f"pdf→{ext} failed (rc={rc})"})
            continue

        key = _formats_key_from_pdf(pdf_key, ext)
        try:
            s3.upload_file(
                out_path, S3_BUCKET, key,
                ExtraArgs={"ACL": "public-read", "ContentType": _content_type_for(ext)}
            )
            size = os.path.getsize(out_path)
            url  = _safe_cdn_url(key)
            db.add(BookFile(book_id=book_id, file_format=fmt, s3_url=url, size_bytes=size))
            db.commit()
            _set_fmt_status(book_id, fmt, "success", url=url, size=size, progress=100)
            _update_job_progress_from_fmt(book_id, fmt, 100)
            _clear_progress(book_id, fmt)
            _log(book_id, f"{ext}: direct uploaded → {url} ({size/(1024*1024):.2f} MiB)")
            created.append({"format": fmt.value, "url": url, "size": size})
        except ClientError as e:
            _set_fmt_status(book_id, fmt, "failed")
            _clear_progress(book_id, fmt)
            _log(book_id, f"{ext}: direct s3 upload failed: {e}")
            failed.append({"format": fmt.value, "error": "s3_upload_failed"})
