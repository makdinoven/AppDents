# app/tasks/ensure_faststart.py (или там же, где у тебя сейчас)

import os, tempfile, subprocess, logging, time, json
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
import requests
from urllib.parse import quote

# ----- ENV -----
S3_ENDPOINT     = os.getenv("S3_ENDPOINT",     "https://s3.timeweb.com")
S3_BUCKET       = os.getenv("S3_BUCKET",       "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")  # <- УКАЖИ ИМЕННО origin-bucket, не CDN-домен
S3_PUBLIC_HOST  = os.getenv("S3_PUBLIC_HOST",  "https://cdn.dent-s.com")
S3_REGION       = os.getenv("S3_REGION",       "ru-1")
NEW_TASKS_LIMIT = int(os.getenv("NEW_TASKS_LIMIT", "200"))  # подними лимит
FFMPEG_RETRIES  = int(os.getenv("FFMPEG_RETRIES", "2"))

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

def _ffprobe_duration(path_or_url: str) -> float | None:
    try:
        p = subprocess.run(
            ["ffprobe","-v","error","-show_entries","format=duration","-of","json", path_or_url],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=30
        )
        if p.returncode != 0:
            return None
        return float(json.loads(p.stdout.decode("utf-8"))["format"]["duration"])
    except Exception:
        return None

@shared_task(name="app.tasks.ensure_faststart")
def ensure_faststart():
    """
    Идём по бакету и ставим в очередь до NEW_TASKS_LIMIT объектов .mp4 без метадаты faststart=true.
    """
    paginator = s3.get_paginator("list_objects_v2")
    queued = 0

    # при желании можно ограничить префиксом: Prefix="narezki/" или наоборот исключить narezki
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".mp4"):
                continue
            try:
                head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            except ClientError as e:
                logger.warning("HeadObject failed for %s: %s", key, e)
                continue

            # пропускаем уже обработанные
            if head.get("Metadata", {}).get("faststart") == "true":
                continue

            process_faststart_video.apply_async((key,), queue="special")
            queued += 1
            logger.info("Enqueued faststart for %s", key)

            if queued >= NEW_TASKS_LIMIT:
                logger.info("Reached limit of %d tasks", NEW_TASKS_LIMIT)
                return

    logger.info("Scan complete, enqueued %d tasks", queued)

@shared_task(name="app.tasks.process_faststart_video", bind=True, autoretry_for=(), retry_backoff=False)
def process_faststart_video(self, key: str):
    """
    Надёжно: скачать → ffmpeg -c copy -movflags +faststart → перезалить → метадата faststart=true → PURGE CDN.
    """
    with tempfile.TemporaryDirectory() as tmp:
        in_mp4  = os.path.join(tmp, "in.mp4")
        out_mp4 = os.path.join(tmp, "out.mp4")

        # 1) скачиваем
        s3.download_file(S3_BUCKET, key, in_mp4)

        # 2) ремукс с faststart (+ несколько попыток)
        last_err = None
        for attempt in range(1, FFMPEG_RETRIES + 1):
            try:
                subprocess.run(
                    ["ffmpeg","-hide_banner","-nostdin","-loglevel","error",
                     "-y","-i", in_mp4, "-c","copy", "-movflags","+faststart", out_mp4],
                    check=True
                )
                break
            except subprocess.CalledProcessError as e:
                last_err = e
                logger.warning("ffmpeg faststart failed (%s/%s) for %s: %s", attempt, FFMPEG_RETRIES, key, e)
                time.sleep(2)
        else:
            raise RuntimeError(f"ffmpeg faststart failed for {key}: {last_err}")

        # 3) лёгкая валидация: есть длительность (> 1 сек)
        dur = _ffprobe_duration(out_mp4)
        if dur is None or dur < 1:
            raise RuntimeError(f"ffprobe duration invalid for {key}: {dur}")

        # 4) перезаливаем (inline + отметка faststart)
        s3.upload_file(
            out_mp4,
            S3_BUCKET,
            key,
            ExtraArgs={
                "ContentType": "video/mp4",
                "ContentDisposition": "inline",
                "Metadata": {"faststart": "true", "ver": str(int(time.time()))},
            },
        )

    logger.info("Faststart applied → %s (dur≈%.1fs)", key, dur or -1)
    return {"key": key, "duration": dur}
