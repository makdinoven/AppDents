import hashlib
import logging
import os
import subprocess
import tempfile
from datetime import datetime

import boto3
from sqlalchemy.orm import Session

from ..db.database import get_db
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


@celery.task(bind=True, max_retries=3, default_retry_delay=60)
def generate_preview(self, video_link: str):
    """
    Вырезаем кадр на первой секунде, заливаем в S3,
    путь вида  /previews/<sha1>.jpg
    """
    db: Session = next(get_db())

    # защита от гонок
    if db.query(LessonPreview).filter_by(video_link=video_link).first():
        logger.debug("Preview already exists for %s", video_link)
        return

    # tmp.jpg → ffmpeg
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as tmp:
        tmp_path = tmp.name

    try:
        cmd = [
            "ffmpeg", "-loglevel", "error",
            "-ss", "00:00:01",
            "-i", video_link,
            "-frames:v", "1",
            "-q:v", "3",
            tmp_path,
        ]
        subprocess.check_call(cmd, timeout=30)
        logger.info("Frame extracted for %s", video_link)

        sha1 = hashlib.sha1(video_link.encode()).hexdigest()
        s3_key = f"{S3_PREVIEW_DIR}/{sha1}.jpg"
        s3.upload_file(
            tmp_path, S3_BUCKET, s3_key,
            ExtraArgs={"ACL": "public-read", "ContentType": "image/jpeg"},
        )
        preview_url = f"{S3_PUBLIC_HOST}/{s3_key}"

        db.add(LessonPreview(video_link=video_link, preview_url=preview_url,
                             generated_at=datetime.utcnow()))
        db.commit()
        logger.info("Preview uploaded to %s", preview_url)

    except subprocess.CalledProcessError as exc:
        logger.warning("ffmpeg error %s for %s", exc, video_link)
        self.retry(exc=exc)
    except Exception as exc:
        logger.exception("Generate preview failed for %s", video_link)
        self.retry(exc=exc)
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)
