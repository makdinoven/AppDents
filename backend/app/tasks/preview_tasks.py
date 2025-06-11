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
import re
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
from botocore.config import Config


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
SAFE_CHARS = "/()[]_,-."

rds = redis.Redis.from_url(REDIS_URL, decode_responses=False)

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(
        signature_version="s3v4",
        s3={"use_unsigned_payload": False},

    ),
)


REQUEST_TIMEOUT = 10   # сек для HEAD/GET Boomstream

def _sanitize_cdn_path(path: str) -> str:
    """
    Снимаем все старые %XX → кодируем один раз.
    ()[]_,-. остаются, пробел → %20, кириллица → %D0%....
    """
    decoded = unquote(unquote(path))          # str
    return quote(decoded, safe=SAFE_CHARS)    # str in → str out

def _boomstream_html_poster(video_link: str) -> str | None:
    """
    GET https://play.boomstream.com/<ID>
    Возвращает URL JPEG из og:image или link[rel=image_src].
    """
    # ⚑ убираем query (?title=0) — он не нужен для HTML-страницы
    base_url = urlsplit(video_link)
    page_url = f"https://play.boomstream.com/{base_url.path.lstrip('/')}"
    try:
        r = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None
        html = r.text

        # meta og:image  (любые кавычки и порядок атрибутов)
        m = re.search(
            r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]',
            html, flags=re.I)
        if m:
            return m.group(1)

        # link rel=image_src
        m = re.search(
            r'<link[^>]+rel=[\'"]image_src[\'"][^>]+href=[\'"]([^\'"]+)[\'"]',
            html, flags=re.I)
        if m:
            return m.group(1)
    except requests.RequestException:
        pass
    return None

def _boomstream_poster(vid: str) -> str | None:
    """
    Возвращает URL существующего JPEG-постера для Boomstream-ID
    или None, если найти не удалось.
    """
    candidates = [
        f"https://snapshot.boomstream.com/frames/{vid}_1.jpg",
        f"https://snapshot.boomstream.com/frames/{vid}_0.jpg",
        f"https://snapshot.boomstream.com/frames/{vid}_0001.jpg",
    ]
    for url in candidates:
        try:
            r = requests.head(url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            if r.status_code == 200:
                return url
        except requests.RequestException:
            pass
    return None

def _may_enqueue(video_link: str) -> bool:
    """
    Лукасный счётчик в Redis: key=preview_enqueue:<epoch>
    """
    key = f"preview_enqueue:{int(time.time() // NEW_TASKS_WINDOW)}"
    val = rds.incr(key)
    if val == 1:
        rds.expire(key, NEW_TASKS_WINDOW)
    return val <= NEW_TASKS_LIMIT


# ───────────  какой URL вернуть для данного video_link  ───────────
def preview_url_for(video_link: str) -> tuple[str | None, bool]:
    """
    Возвращает (url_or_none, use_ffmpeg)
      • Boom stream : (poster .jpg, False)  либо (None, False)
      • CDN mp4     : (sanitised .mp4, True)
      • Иное        : (None, False)
    """
    if "play.boomstream.com" in video_link:
        poster = _boomstream_html_poster(video_link)
        if poster:
            return poster, False          # готовый JPEG
        return None, False                # постера нет → плейсхолдер

    if "cdn.dent-s.com" in video_link:
        p = urlsplit(video_link)
        safe_path  = _sanitize_cdn_path(p.path)
        safe_query = quote(unquote(p.query), safe="=&")
        safe_url   = urlunsplit((p.scheme, p.netloc, safe_path, safe_query, ""))
        return safe_url, True             # нужен ffmpeg

    return None, False                    # неизвестный источник



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

        safe_url, need_ffmpeg = preview_url_for(video_link)

        # неизвестный источник → плейсхолдер
        if safe_url is None:
            logger.info("Unknown source for %s — placeholder", video_link)
            _save_preview_row(db, video_link, PLACEHOLDER_URL)
            return

        # Boomstream-JPEG (или другой прямой jpg) — ffmpeg не нужен
        if not need_ffmpeg:
            _save_preview_row(db, video_link, safe_url)
            return

        # ───── CDN-mp4: режем кадр ffmpeg-ом ─────
        # ───── CDN-mp4 или HLS: режем кадр ffmpeg-ом ─────
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        cmd = [
            "ffmpeg", "-y", "-loglevel", "error", "-threads", "1",
            "-ss", "00:00:01", "-i", safe_url,
            "-frames:v", "1", "-q:v", "4", tmp_path,
        ]

        logger.debug("ffmpeg cmd: %s", " ".join(cmd))
        subprocess.check_call(cmd, timeout=60)
        logger.info("Frame extracted for %s", video_link)

        # ---------- загрузка в S3 (один цельный Body) ----------
        sha1 = hashlib.sha1(video_link.encode()).hexdigest()
        s3_key = f"{S3_DIR}/{sha1}.jpg"

        with open(tmp_path, "rb") as fh:
            data = fh.read()  # читаем целиком

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=data,  # ← 1 цельный блок
            ACL="public-read",
            ContentType="image/jpeg",
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
