import os
import time
import tempfile
import subprocess
import logging
import io

import redis
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task, current_app

# --- Configuration (from your environment) ---
S3_ENDPOINT     = os.getenv("S3_ENDPOINT",     "https://s3.timeweb.com")
S3_BUCKET       = os.getenv("S3_BUCKET",       "cdn.dent-s.com")
S3_PUBLIC_HOST  = os.getenv("S3_PUBLIC_HOST",  "https://cdn.dent-s.com")
S3_REGION       = os.getenv("S3_REGION",       "ru-1")
REDIS_URL       = os.getenv("REDIS_URL",       "redis://redis:6379/0")
NEW_TASKS_LIMIT = int(os.getenv("NEW_TASKS_LIMIT", 15))
FFMPEG_RETRIES  = int(os.getenv("FFMPEG_RETRIES", 3))
PRESIGN_EXPIRY  = 3600  # seconds

# --- Clients ---
logger = logging.getLogger(__name__)
rds    = redis.Redis.from_url(REDIS_URL, decode_responses=False)
s3     = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(
        signature_version="s3",
        s3={"addressing_style": "path"},
    ),
)

@shared_task(name="app.tasks.ensure_faststart")
def ensure_faststart():
    """
    Scan entire S3 bucket for .mp4 objects without faststart metadata and enqueue up to NEW_TASKS_LIMIT jobs.
    """
    paginator = s3.get_paginator("list_objects_v2")
    queued = 0

    # No specific prefix: check all objects
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            # only .mp4 files
            if not key.lower().endswith(".mp4"):
                continue

            # skip if already processed (metadata faststart=true)
            try:
                head = s3.head_object(Bucket=S3_BUCKET, Key=key)
                if head.get('Metadata', {}).get('faststart') == 'true':
                    continue
            except ClientError as e:
                logger.warning("HeadObject failed for %s: %s", key, e)
                continue

            # enqueue processing
            process_faststart_video.apply_async((key,), queue='special')
            queued += 1
            logger.info("Enqueued faststart for %s", key)

            if queued >= NEW_TASKS_LIMIT:
                logger.info("Reached limit of %d tasks", NEW_TASKS_LIMIT)
                return

    logger.info("Scan complete, enqueued %d tasks", queued)


@shared_task(name="app.tasks.process_faststart_video")
def process_faststart_video(key: str):
    def process_faststart_video_disk(key: str):
        """
        Надёжный вариант: скачиваем файл, добавляем +faststart на диске, заливаем обратно.
        Требует свободного пространства ≥ размера видео.
        """
        with tempfile.TemporaryDirectory() as tmp:
            in_mp4 = os.path.join(tmp, "in.mp4")
            out_mp4 = os.path.join(tmp, "out.mp4")

            # 1) Скачать
            s3.download_file(S3_BUCKET, key, in_mp4)

            # 2) Remux с faststart
            cmd = [
                "ffmpeg", "-y",
                "-i", in_mp4,
                "-c", "copy",
                "-movflags", "+faststart",
                out_mp4
            ]
            subprocess.run(cmd, check=True)

            # 3) Загрузить обратно
            s3.upload_file(
                out_mp4, S3_BUCKET, key,
                ExtraArgs={
                    "ACL": "public-read",
                    "ContentType": "video/mp4",
                    "Metadata": {"faststart": "true"}
                }
            )

        logger.info("Faststart applied (disk) → %s", key)