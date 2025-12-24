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

from ..core.storage import S3_PUBLIC_HOST, public_url_for_key, s3_client
from ..db.database import SessionLocal
from ..models.models_v2 import LessonPreview, PreviewStatus

logger = logging.getLogger(__name__)

# S3 конфиг теперь централизован в core.storage
S3_BUCKET      = os.getenv("S3_BUCKET", "dent-s")  # оставляем для SQL/БД логики, но клиент берём из core.storage
REDIS_URL      = os.getenv("REDIS_URL", "redis://redis:6379/0")
S3_DIR         = "previews"
PLACEHOLDER_NAME = "placeholder.jpg"
PLACEHOLDER_URL  = public_url_for_key(f"{S3_DIR}/{PLACEHOLDER_NAME}", public_host=S3_PUBLIC_HOST)

# Для проверки CDN-источников (извлекаем хост из S3_PUBLIC_HOST)
from urllib.parse import urlparse as _urlparse
_CDN_HOST = _urlparse(S3_PUBLIC_HOST).hostname or "cloud.dent-s.com"
NEW_TASKS_WINDOW = 300
NEW_TASKS_LIMIT  = 30
SAFE_CHARS = "/()[]_,-."
FFMPEG_SEEKS    = ("00:00:58", "00:00:09")
FFMPEG_RETRIES  = 3

LOCK_TTL = 15 * 60
QUEUED_TTL = 45 * 60

REQUEST_TIMEOUT = 10

rds = redis.Redis.from_url(REDIS_URL, decode_responses=False)

s3 = s3_client(signature_version="s3v4")

def _key(prefix: str, video_link: str) -> str:
    h = hashlib.sha1(video_link.encode()).hexdigest()
    return f"{prefix}:{h}"

class Lock:
    def __init__(self, video_link: str):
        self.key = _key("preview:lock", video_link)
        self.acquired = False
    def __enter__(self):
        self.acquired = bool(rds.set(self.key, b"1", nx=True, ex=LOCK_TTL))
        return self.acquired
    def __exit__(self, exc_type, exc, tb):
        if self.acquired:
            rds.delete(self.key)

def clear_queued(video_link: str) -> None:
    rds.delete(_key("preview:queued", video_link))

def _set_preview_row(db: Session, video_link: str, url: str) -> None:
    """
    Обновляем/создаём запись с актуальным URL превью.
    Статус/attempts меняем отдельно в основной логике.
    """
    row = db.query(LessonPreview).filter_by(video_link=video_link).first()
    if row:
        row.preview_url  = url
        row.generated_at = datetime.utcnow()
        db.commit()
        return
    try:
        db.add(LessonPreview(
            video_link=video_link,
            preview_url=url,
            generated_at=datetime.utcnow()))
        db.commit()
    except DataError:
        db.rollback()
        short = video_link[:700]
        db.add(LessonPreview(
            video_link=short,
            preview_url=url,
            generated_at=datetime.utcnow()))
        db.commit()

def _sanitize_cdn_path(path: str) -> str:
    decoded = unquote(unquote(path))
    return quote(decoded, safe=SAFE_CHARS)

def _boomstream_html_poster(video_link: str) -> str | None:
    base_url = urlsplit(video_link)
    page_url = f"https://play.boomstream.com/{base_url.path.lstrip('/')}"
    try:
        r = requests.get(page_url, timeout=REQUEST_TIMEOUT)
        if r.status_code != 200:
            return None
        html = r.text
        m = re.search(r'<meta[^>]+property=[\'"]og:image[\'"][^>]+content=[\'"]([^\'"]+)[\'"]', html, flags=re.I)
        if m:
            return m.group(1)
        m = re.search(r'<link[^>]+rel=[\'"]image_src[\'"][^>]+href=[\'"]([^\'"]+)[\'"]', html, flags=re.I)
        if m:
            return m.group(1)
    except requests.RequestException:
        pass
    return None

def _boomstream_poster(vid: str) -> str | None:
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
    m = VIMEO_ID_RE.search(video_link)
    if not m:
        return None
    vid = m.group(1)
    try:
        oembed = f"https://vimeo.com/api/oembed.json?url=https://vimeo.com/{vid}"
        r = requests.get(oembed, timeout=REQUEST_TIMEOUT)
        if r.status_code == 200:
            j = r.json()
            url = j.get("thumbnail_url")
            if url:
                return re.sub(r"_[0-9x]+\.([a-z]+)$", r"_1280.\1", url)
    except Exception:
        pass
    try:
        url = f"https://player.vimeo.com/video/{vid}"
        r = requests.get(url, timeout=REQUEST_TIMEOUT, headers={"User-Agent": "Mozilla/5.0"})
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

def _may_enqueue_window_limit() -> bool:
    key = f"preview_enqueue:{int(time.time() // NEW_TASKS_WINDOW)}"
    val = rds.incr(key)
    if val == 1:
        rds.expire(key, NEW_TASKS_WINDOW)
    return val <= NEW_TASKS_LIMIT

def preview_url_for(video_link: str) -> tuple[str | None, bool]:
    if "play.boomstream.com" in video_link:
        poster = _boomstream_html_poster(video_link)
        if poster:
            return poster, False
        return None, False

    if "kinescope.io/embed/" in video_link:
        poster = _kinescope_poster(video_link)
        return (poster, False) if poster else (None, False)

    if "vimeo.com" in video_link:
        poster = _vimeo_poster(video_link)
        return (poster, False) if poster else (None, False)

    # Проверяем, что это наш CDN (используем hostname из S3_PUBLIC_HOST)
    if _CDN_HOST in video_link:
        p = urlsplit(video_link)
        safe_path  = _sanitize_cdn_path(p.path)
        safe_query = quote(unquote(p.query), safe="=&")
        safe_url   = urlunsplit((p.scheme, p.netloc, safe_path, safe_query, ""))
        return safe_url, True

    return None, False

@shared_task(
    name="app.tasks.preview_tasks.check_preview_url",
    bind=True,
    max_retries=0
)
def check_preview_url(self, video_link: str) -> None:
    """
    Проверяет, жив ли URL превью. Если мёртв — ставит на перегенерацию.
    Вызывается асинхронно при запросе /by-page для URL, которые давно не проверялись.
    """
    db: Session = SessionLocal()
    try:
        row = db.query(LessonPreview).filter_by(video_link=video_link).first()
        if not row or row.status != PreviewStatus.SUCCESS:
            return
        
        # Проверяем URL
        try:
            r = requests.head(row.preview_url, timeout=REQUEST_TIMEOUT, allow_redirects=True)
            is_alive = r.status_code == 200
        except requests.RequestException:
            is_alive = False
        
        now = datetime.utcnow()
        row.checked_at = now
        
        if not is_alive:
            logger.warning("[check_preview_url] dead url %s → reschedule", row.preview_url)
            row.status = PreviewStatus.FAILED
            row.updated_at = now
            db.commit()
            # Ставим на перегенерацию
            generate_preview.apply_async(
                (video_link,),
                task_id=hashlib.sha1(video_link.encode()).hexdigest(),
                queue="default"
            )
        else:
            db.commit()
    finally:
        db.close()


@shared_task(
    name="app.tasks.preview_tasks.generate_preview",
    bind=True,
    max_retries=0
)
def generate_preview(self, video_link: str) -> None:
    db: Session = SessionLocal()
    tmp_path: str | None = None

    try:
        # Процессный замок: одна активная генерация на video_link
        with Lock(video_link) as ok:
            if not ok:
                return

            row = db.query(LessonPreview).filter_by(video_link=video_link).first()
            if row and row.preview_url and row.preview_url != PLACEHOLDER_URL and row.status == PreviewStatus.SUCCESS:
                return

            # отметим, что мы реально стартовали
            if row:
                row.status = PreviewStatus.RUNNING
                row.updated_at = datetime.utcnow()
                db.commit()

            if not _may_enqueue_window_limit():
                logger.warning("rate limited window for %s", video_link)

            safe_url, need_ffmpeg = preview_url_for(video_link)

            if safe_url is None:
                logger.info("Unknown source for %s — placeholder", video_link)
                _set_preview_row(db, video_link, PLACEHOLDER_URL)
                row = db.query(LessonPreview).filter_by(video_link=video_link).first()
                if row:
                    row.status = PreviewStatus.FAILED
                    row.attempts = (row.attempts or 0) + 1
                    row.updated_at = datetime.utcnow()
                    db.commit()
                return

            if not need_ffmpeg:
                _set_preview_row(db, video_link, safe_url)
                row = db.query(LessonPreview).filter_by(video_link=video_link).first()
                if row:
                    row.status = PreviewStatus.SUCCESS
                    row.attempts = (row.attempts or 0) + 1
                    row.updated_at = datetime.utcnow()
                    db.commit()
                return

            # CDN mp4 → пробуем вытащить кадр
            with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
                tmp_path = tmp.name

            success = False
            used_ts = None
            for ts in FFMPEG_SEEKS:
                for attempt in range(1, FFMPEG_RETRIES + 1):
                    cmd = [
                        "ffmpeg", "-y", "-loglevel", "fatal", "-threads", "1",
                        "-ss", ts, "-i", safe_url,
                        "-frames:v", "1", "-q:v", "4", tmp_path,
                    ]
                    try:
                        logger.debug("ffmpeg %s (attempt %d/%d)", ts, attempt, FFMPEG_RETRIES)
                        subprocess.check_call(cmd, timeout=60)
                        success = True
                        used_ts = ts
                        break
                    except subprocess.CalledProcessError as exc:
                        logger.warning("ffmpeg failed (%s, attempt %d): %s", ts, attempt, exc)
                        continue
                if success:
                    break

            if not success:
                raise subprocess.CalledProcessError(1, "ffmpeg")

            logger.info("Frame extracted for %s (ts=%s)", video_link, used_ts or "n/a")

            # Загрузка в S3
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
            _set_preview_row(db, video_link, public_url)

            row = db.query(LessonPreview).filter_by(video_link=video_link).first()
            if row:
                row.status = PreviewStatus.SUCCESS
                row.attempts = (row.attempts or 0) + 1
                row.updated_at = datetime.utcnow()
                db.commit()

    except subprocess.CalledProcessError as e:
        logger.warning("All ffmpeg attempts failed for %s", video_link)
        _set_preview_row(db, video_link, PLACEHOLDER_URL)
        row = db.query(LessonPreview).filter_by(video_link=video_link).first()
        if row:
            row.status = PreviewStatus.FAILED
            row.last_error = str(e)[:500]
            row.attempts = (row.attempts or 0) + 1
            row.updated_at = datetime.utcnow()
            db.commit()

    except Exception as e:
        logger.exception("Unhandled error for %s", video_link)
        _set_preview_row(db, video_link, PLACEHOLDER_URL)
        row = db.query(LessonPreview).filter_by(video_link=video_link).first()
        if row:
            row.status = PreviewStatus.FAILED
            row.last_error = str(e)[:500]
            row.attempts = (row.attempts or 0) + 1
            row.updated_at = datetime.utcnow()
            db.commit()

    finally:
        try:
            clear_queued(video_link)
        except Exception:
            pass
        db.close()
        if tmp_path and Path(tmp_path).exists():
            Path(tmp_path).unlink(missing_ok=True)
