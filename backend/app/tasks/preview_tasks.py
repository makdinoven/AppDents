"""
Генерируем превью-картинку для каждого video_link.

• Видео лежит на CDN  → вытягиваем кадр ffmpeg-ом (00:00:01)
• Видео лежит на Boomstream → берём готовый JPEG
• Если ничего не получилось (403/404 и т.п.) → сохраняем плейсхолдер
"""

from __future__ import annotations

import base64
import functools
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
from celery import shared_task
from sqlalchemy.exc import DataError
from sqlalchemy.orm import Session
from botocore.config import Config


from ..db.database import SessionLocal
from ..models.models_v2 import LessonPreview


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
FFMPEG_SEEKS    = ("00:00:58", "00:00:09")      # секунды для попыток  # ← NEW
FFMPEG_RETRIES  = 3

rds = redis.Redis.from_url(REDIS_URL, decode_responses=False)

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,           # https://s3.timeweb.com
    region_name=S3_REGION,             # ru-1
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(
        signature_version="s3",         # ← V2-подпись, без SHA-256
        s3={
            "addressing_style": "path", # путь /bucket/key
        },
    ),
)


REQUEST_TIMEOUT = 10   # сек для HEAD/GET Boomstream
def _set_preview_row(db: Session, video_link: str, url: str) -> None:            # ← NEW
    """
    Если запись уже есть — обновляем её.
    Иначе создаём новую (старое название _save_preview_row осталось нетронутым).
    """
    row = db.query(LessonPreview).filter_by(video_link=video_link).first()
    if row:
        row.preview_url  = url
        row.generated_at = datetime.utcnow()
        db.commit()
        return
    # если записи нет — вызываем старую функцию
    _save_preview_row(db, video_link, url)

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

def _kinescope_poster(embed_url: str) -> str | None:
    """
    Принимает URL вида  https://kinescope.io/embed/<ID>
    Возвращает thumbnailUrl из <script type="application/ld+json">,
    либо None, если не найден.
    """
    # убираем query (?title=0 и т. д.)
    base = urlsplit(embed_url)
    page = f"https://kinescope.io{base.path}"
    try:
        r = requests.get(page, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None
        m = re.search(r'"thumbnailUrl"\s*:\s*"([^"]+)"', r.text)
        if m:
            return m.group(1)
    except requests.RequestException:
        pass
    return None

VIMEO_ID_RE = re.compile(r"(?:player\.vimeo\.com\/video\/|vimeo\.com\/)(\d{6,12})")

@functools.lru_cache(maxsize=512)
def _vimeo_poster(video_link: str) -> str | None:
    """
    • Принимаем любые ссылки (player.vimeo.com/… или vimeo.com/…)
    • Сначала пробуем oEmbed (100 % работает без ключей)
    • Если не удалось — fallback к HTML-странице
    """
    m = VIMEO_ID_RE.search(video_link)
    if not m:
        return None
    vid = m.group(1)

    # ───── 1. oEmbed ─────
    try:
        oembed = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid}"
        r = requests.get(oembed, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            j = r.json()
            url = j.get("thumbnail_url")
            if url:
                # oEmbed даёт превью 640 px; заменим на 1280 px, если нужно
                return re.sub(r"_[0-9x]+\.([a-z]+)$", r"_1280.\1", url)
    except Exception:
        pass

    # ───── 2. fallback: HTML-страница ─────
    try:
        url = f"https://player.vimeo.com/video/{vid}"
        r = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "Mozilla/5.0"}  # без UA бывает 403
        )
        if r.status_code != 200:
            return None

        html = r.text
        for key in ("thumbnailUrl", "thumbnail_url"):
            m = re.search(fr'"{key}"\s*:\s*"([^"]+)"', html)
            if m:
                return m.group(1).replace("?mw=80", "?mw=1280")
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

    if "kinescope.io/embed/" in video_link:
        poster = _kinescope_poster(video_link)
        if poster:
            return poster, False  # jpeg, ffmpeg не нужен
        return None, False

    if "vimeo.com" in video_link:
        poster = _vimeo_poster(video_link)
        return (poster, False) if poster else (None, False)

    if "cdn.dent-s.com" in video_link:
        p = urlsplit(video_link)
        safe_path  = _sanitize_cdn_path(p.path)
        safe_query = quote(unquote(p.query), safe="=&")
        safe_url   = urlunsplit((p.scheme, p.netloc, safe_path, safe_query, ""))
        return safe_url, True             # нужен ffmpeg

    return None, False                    # неизвестный источник



def _save_preview_row(db, video_link: str, url: str) -> None:
    try:
        db.add(LessonPreview(
            video_link=video_link,
            preview_url=url,
            generated_at=datetime.utcnow()))
        db.commit()
    except DataError:
        db.rollback()                 # сбросили failed-transaction
        # отрезаем до 1024, чтобы точно влезло
        short = video_link[:700]
        db.add(LessonPreview(
            video_link=short,
            preview_url=url,
            generated_at=datetime.utcnow()))
        db.commit()


# ─────────────────────────  MAIN TASK  ──────────────────────────
@shared_task(
    name="app.tasks.preview_tasks.generate_preview",
    bind=True,
    max_retries=0     # 1 попытка
)
def generate_preview(self, video_link: str) -> None:
    """
    Алгоритм:

      1. Если в базе уже есть НЕ плейсхолдер — выходим.
         Если есть плейсхолдер — пробуем сгенерировать заново.
      2. Определяем способ получения превью.
      3. Для CDN-видео:
         • пробуем FFMPEG_RETRIES раз извлечь кадр в FFMPEG_SEEKS[0]
         • при неудаче — столько же попыток со временем FFMPEG_SEEKS[1]
      4. При успехе грузим jpeg в S3, сохраняем / обновляем строку.
      5. При всех неудачах — записываем плейсхолдер.
    """
    db: Session = SessionLocal()
    tmp_path: str | None = None

    try:
        existing = (
            db.query(LessonPreview)
              .filter_by(video_link=video_link)
              .first()
        )                                                                      # ← CHANGED

        if existing and existing.preview_url != PLACEHOLDER_URL:               # ← CHANGED
            # Уже есть «живое» превью — делать ничего не нужно
            return

        safe_url, need_ffmpeg = preview_url_for(video_link)

        # неизвестный источник → плейсхолдер
        if safe_url is None:
            logger.info("Unknown source for %s — placeholder", video_link)
            _set_preview_row(db, video_link, PLACEHOLDER_URL)                  # ← CHANGED
            return

        # готовый JPEG (Boomstream и т. п.) — ffmpeg не нужен
        if not need_ffmpeg:
            _set_preview_row(db, video_link, safe_url)                         # ← CHANGED
            return

        # ───────────  CDN-mp4: пытаемся вырезать кадр  ───────────
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        success = False                                                        # ← NEW
        for ts in FFMPEG_SEEKS:                                                # ← NEW
            for attempt in range(1, FFMPEG_RETRIES + 1):                       # ← NEW
                cmd = [
                    "ffmpeg", "-y", "-loglevel", "error", "-threads", "1",
                    "-ss", ts, "-i", safe_url,
                    "-frames:v", "1", "-q:v", "4", tmp_path,
                ]
                try:
                    logger.debug("ffmpeg %s (attempt %d/%d)", ts, attempt,
                                 FFMPEG_RETRIES)
                    subprocess.check_call(cmd, timeout=60)
                    success = True
                    break
                except subprocess.CalledProcessError as exc:
                    logger.warning("ffmpeg failed (%s, attempt %d): %s",
                                   ts, attempt, exc)
                    continue
            if success:
                break

        if not success:                                                        # ← NEW
            raise subprocess.CalledProcessError(1, "ffmpeg")                   # ← NEW

        logger.info("Frame extracted for %s (ts=%s)", video_link, ts)          # ← CHANGED

        # ---------- загрузка в S3 ----------
        sha1 = hashlib.sha1(video_link.encode()).hexdigest()
        s3_key = f"{S3_DIR}/{sha1}.jpg"

        with open(tmp_path, "rb") as fh:
            data = fh.read()

        md5_b64 = base64.b64encode(hashlib.md5(data).digest()).decode()

        s3.put_object(
            Bucket=S3_BUCKET,
            Key=s3_key,
            Body=data,
            ACL="public-read",
            ContentType="image/jpeg",
            ContentLength=len(data),
            ContentMD5=md5_b64,
        )
        public_url = f"{S3_PUBLIC_HOST}/{s3_key}"
        _set_preview_row(db, video_link, public_url)                           # ← CHANGED
        logger.info("Preview uploaded → %s", public_url)

    except subprocess.CalledProcessError:
        logger.warning("All ffmpeg attempts failed for %s", video_link)        # ← CHANGED
        _set_preview_row(db, video_link, PLACEHOLDER_URL)                      # ← CHANGED

    except Exception:
        logger.exception("Unhandled error for %s", video_link)
        _set_preview_row(db, video_link, PLACEHOLDER_URL)                      # ← CHANGED

    finally:
        db.close()
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink(missing_ok=True)