"""
Генерируем превью-картинку для каждого video_link.

• Видео лежит на CDN  → вытягиваем кадр ffmpeg-ом (00:00:01)
• Видео лежит на Boomstream → берём готовый JPEG
• Если ничего не получилось (403/404 и т.п.) → сохраняем плейсхолдер
"""

from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import tempfile
import time
import redis
from datetime import datetime
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit, quote, unquote

import boto3
import requests
from celery import Celery
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..models.models_v2 import LessonPreview
from ..celery_app import celery

logger = logging.getLogger(__name__)

# ─────────────────────────  S3 CONFIG  ──────────────────────────
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET      = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
S3_DIR         = "previews"
PLACEHOLDER_NAME = "placeholder.jpg"
PLACEHOLDER_URL  = f"{S3_PUBLIC_HOST}/{S3_DIR}/{PLACEHOLDER_NAME}"
NEW_TASKS_WINDOW = 30
NEW_TASKS_LIMIT  = 10

rds = redis.Redis.from_url(REDIS_URL, decode_responses=False)

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)

REQUEST_TIMEOUT = 10   # сек для HEAD/GET Boomstream

def _may_enqueue(video_link: str) -> bool:
    """
    Лукасный счётчик в Redis: key=preview_enqueue:<epoch>
    """
    key = f"preview_enqueue:{int(time.time() // NEW_TASKS_WINDOW)}"
    val = rds.incr(key)
    if val == 1:
        rds.expire(key, NEW_TASKS_WINDOW)
    return val <= NEW_TASKS_LIMIT

# ─────────────────────────  HELPERS  ────────────────────────────
def _sanitize_cdn_path(path: str) -> str:
    """Снимаем все старые %XX и кодируем заново один раз."""
    decoded = unquote(unquote(path))
    return quote(decoded, safe="/")


# ───────────  какой URL вернуть для данного video_link  ───────────
def preview_url_for(video_link: str) -> str | None:
    """
    Возвращает:
      • direct JPEG  – если это Boomstream (моментально, без ffmpeg),
      • sanitised mp4 – если наш CDN,
      • None         – всё прочее (дам плейсхолдер).
    """
    if "play.boomstream.com" in video_link:
        # формат https://play.boomstream.com/<ID>[?title=0...]
        vid = urlsplit(video_link).path.lstrip("/")
        # вариант 1: их стандартный постер 640×360
        return f"https://play.boomstream.com/{vid}.jpg"
        #  или, если нужен кадр №1:
        # return f"https://snapshot.boomstream.com/frames/{vid}_1.jpg"

    if "cdn.dent-s.com" in video_link:
        parts = urlsplit(video_link)
        safe_path  = quote(unquote(unquote(parts.path)), safe="/")
        safe_query = quote(unquote(parts.query), safe="=&")
        return urlunsplit((parts.scheme, parts.netloc, safe_path, safe_query, ""))

    return None          # неизвестный протокол → плейсхолдер



def _save_preview_row(db: Session, video_link: str, url: str) -> None:
    db.add(LessonPreview(video_link=video_link,
                         preview_url=url,
                         generated_at=datetime.utcnow()))
    db.commit()


# ─────────────────────────  MAIN TASK  ──────────────────────────
@celery.task(bind=True, max_retries=0)  # 0 ретраев: 1 попытка и плейсхолдер
def generate_preview(self, video_link: str) -> None:
    db: Session = SessionLocal()
    tmp_path: str | None = None

    try:
        # уже есть?
        if db.query(LessonPreview).filter_by(video_link=video_link).first():
            return

        safe_url = preview_url_for(video_link)

        # неизвестный источник → сразу плейсхолдер
        if safe_url is None:
            logger.info("Unknown source for %s — placeholder", video_link)
            _save_preview_row(db, video_link, PLACEHOLDER_URL)
            return

        # Boomstream JPEG
        if safe_url.endswith(".jpg"):
            logger.debug("Use Boomstream poster for %s", video_link)
            _save_preview_row(db, video_link, safe_url)
            return

        # ───── CDN-mp4: режем кадр ffmpeg-ом ─────
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [
            "ffmpeg", "-loglevel", "error",
            "-ss", "00:00:01",
            "-i", safe_url,
            "-frames:v", "1",
            "-q:v", "3",
            tmp_path,
        ]

        logger.debug("ffmpeg cmd: %s", " ".join(cmd))
        subprocess.check_call(cmd, timeout=60)
        logger.info("Frame extracted for %s", video_link)

        sha1 = hashlib.sha1(video_link.encode()).hexdigest()
        s3_key = f"{S3_DIR}/{sha1}.jpg"
        s3.upload_file(
            tmp_path,
            S3_BUCKET,
            s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"},
        )
        public_url = f"{S3_PUBLIC_HOST}/{s3_key}"
        _save_preview_row(db, video_link, public_url)
        logger.info("Preview uploaded → %s", public_url)

    except subprocess.CalledProcessError as exc:
        logger.warning("ffmpeg failed for %s (%s)", video_link, exc)
        # фиксируем плейсхолдер
        _save_preview_row(db, video_link, PLACEHOLDER_URL)

    except Exception as exc:
        # любая неучтённая ошибка → плейсхолдер, но логируем стек
        logger.exception("Unhandled error for %s", video_link)
        _save_preview_row(db, video_link, PLACEHOLDER_URL)

    finally:
        db.close()
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink(missing_ok=True)
