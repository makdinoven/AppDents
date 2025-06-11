import hashlib
import logging
import os
import subprocess
import tempfile
from datetime import datetime
from urllib.parse import urlunsplit, quote, urlsplit, unquote

import boto3
import requests
from sqlalchemy.orm import Session

from ..db.database import get_db, SessionLocal
from ..models.models_v2 import LessonPreview
from ..celery_app import celery  # ваш главный Celery-инстанс

logger = logging.getLogger(__name__)

S3_ENDPOINT     = os.getenv("S3_ENDPOINT",     "https://s3.timeweb.com")
S3_BUCKET       = os.getenv("S3_BUCKET",       "cdn.dent-s.com")
S3_PUBLIC_HOST  = os.getenv("S3_PUBLIC_HOST",  "https://cdn.dent-s.com")
S3_REGION       = os.getenv("S3_REGION",       "ru-1")
S3_PREVIEW_DIR  = "previews"

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
)
REQUEST_TIMEOUT = 10
def resolve_and_sanitize(url: str) -> str:
    # 0) выполняем GET/HEAD с редиректами (как сейчас)
    real = requests.get(url, allow_redirects=True, timeout=REQUEST_TIMEOUT).url

    # 1) разбираем URL
    parts = urlsplit(real)

    # 2) Снимаем прежнюю кодировку, затем кодируем заново
    decoded_path  = unquote(parts.path)          #  %XX → символ
    decoded_query = unquote(parts.query)

    safe_path  = quote(decoded_path,  safe="/")   # кодируем ТОЛЬКО 1 раз
    safe_query = quote(decoded_query, safe="=&")

    return urlunsplit((parts.scheme,
                       parts.netloc,
                       safe_path,
                       safe_query,
                       parts.fragment))


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_preview(self, video_link: str):
    db: Session = SessionLocal()
    tmp_path: str | None = None          # ← объявляем заранее

    try:
        if db.query(LessonPreview).filter_by(video_link=video_link).first():
            return

        # --- ffmpeg: сохраняем кадр во временный файл ---------------
        with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
            tmp_path = tmp.name

        safe_url = resolve_and_sanitize(video_link)
        cmd = [
            "ffmpeg", "-loglevel", "error",
            "-ss", "00:00:01", "-i", safe_url,
            "-frames:v", "1", "-q:v", "3", tmp_path,
        ]
        subprocess.check_call(cmd, timeout=30)
        logger.info("Frame extracted for %s", video_link)

        # --- S3 upload ----------------------------------------------
        sha1 = hashlib.sha1(video_link.encode()).hexdigest()
        s3_key = f"{S3_PREVIEW_DIR}/{sha1}.jpg"
        s3.upload_file(tmp_path, S3_BUCKET, s3_key,
                       ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"})
        preview_url = f"{S3_PUBLIC_HOST}/{s3_key}"

        db.add(LessonPreview(video_link=video_link,
                             preview_url=preview_url,
                             generated_at=datetime.utcnow()))
        db.commit()
        logger.info("Preview uploaded to %s", preview_url)

    except subprocess.CalledProcessError as exc:
        db.rollback()
        logger.warning("ffmpeg exit-1 for %s", video_link)
        placeholder = f"{S3_PUBLIC_HOST}/{S3_PREVIEW_DIR}/placeholder.jpg"

        db.add(LessonPreview(video_link=video_link,
                             preview_url=placeholder,
                             generated_at=datetime.utcnow()))
        db.commit()

    except Exception as exc:
        db.rollback()
        logger.exception("Generate preview failed for %s", video_link)
        raise self.retry(exc=exc)

    finally:
        db.close()
        if tmp_path and os.path.exists(tmp_path):     # ← проверяем, объявлен ли
            os.remove(tmp_path)

