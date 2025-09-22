#!/usr/bin/env python3
"""
Пересобирает «маленькие» клипы в бакете:
- ищет .../narezki/*.mp4 с Size < MIN_OK_BYTES,
- восстанавливает исходный ключ (убирает /narezki/ и суффикс _clip_<uuid>),
- шлёт Celery-задачу clip_video(src_url, dest_key=сломанный_ключ, force_download=True) в очередь REPAIR_QUEUE.

ENV:
  S3_ENDPOINT (https://s3.timeweb.com)
  S3_REGION   (ru-1)
  S3_BUCKET   (origin bucket)   [обязательно]
  AWS_ACCESS_KEY_ID / AWS_SECRET_ACCESS_KEY
  CLIP_MIN_OK_BYTES (байты, default 1_000_000)
  REPAIR_PREFIX      (ограничить область)
  REPAIR_QUEUE       (default: special)
  REPAIR_FORCE_LOCAL (true/false, default true)
  REPAIR_MAX_TASKS   (предел, default 1000000)
  REPAIR_DRY_RUN     (true/false, default false)
  CELERY_BROKER_URL / CELERY_RESULT_BACKEND
"""

import os
import re
from urllib.parse import quote

import boto3
from botocore.config import Config
from celery import Celery

S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION   = os.getenv("S3_REGION", "ru-1")
BUCKET      = os.getenv("S3_BUCKET")
if not BUCKET:
    raise SystemExit("S3_BUCKET is required")

MIN_OK_BYTES = int(os.getenv("CLIP_MIN_OK_BYTES", "1000000"))
PREFIX       = os.getenv("REPAIR_PREFIX", "")
QUEUE        = os.getenv("REPAIR_QUEUE", "default")
FORCE_LOCAL  = os.getenv("REPAIR_FORCE_LOCAL", "true").lower() == "true"
MAX_TASKS    = int(os.getenv("REPAIR_MAX_TASKS", "1000000"))
DRY_RUN      = os.getenv("REPAIR_DRY_RUN", "false").lower() == "true"

BROKER  = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")
celery = Celery("dent_backend", broker=BROKER, backend=BACKEND)

CLIP_TASK_NAME = "app.tasks.clip_tasks.clip_video"

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

RE_CLIP = re.compile(r"^(?P<base>.+)_clip_[0-9a-f]{32}$", re.IGNORECASE)

def derive_source_key(clip_key: str) -> str | None:
    """
    "Course/Folder/narezki/lesson1_clip_<uuid>.mp4" -> "Course/Folder/lesson1.mp4"
    """
    if "/narezki/" not in clip_key:
        return None
    parts = clip_key.split("/")
    try:
        i = parts.index("narezki")
    except ValueError:
        return None
    if i == 0 or i == len(parts) - 1:
        return None
    filename = parts[-1]
    stem, dot, ext = filename.rpartition(".")
    if not dot:
        return None
    m = RE_CLIP.match(stem)
    if not m:
        return None
    base_stem = m.group("base")
    src_filename = f"{base_stem}.{ext}"
    src_parts = parts[:i] + parts[i+1:-1] + [src_filename]
    return "/".join(src_parts)

def to_origin_url(bucket: str, key: str) -> str:
    return f"https://{bucket}.s3.twcstorage.ru/{quote(key, safe='/')}"

def main():
    paginator = s3.get_paginator("list_objects_v2")
    pages = paginator.paginate(Bucket=BUCKET, Prefix=PREFIX, PaginationConfig={"PageSize": 1000})

    queued = 0
    skipped = 0

    for page in pages:
        for obj in page.get("Contents", []):
            key  = obj["Key"]
            size = obj["Size"]
            if "/narezki/" not in key or not key.lower().endswith(".mp4"):
                continue
            if size >= MIN_OK_BYTES:
                continue

            src_key = derive_source_key(key)
            if not src_key:
                print(f"[skip] cannot derive source for: {key}")
                skipped += 1
                continue

            # убедимся, что исходник существует
            try:
                s3.head_object(Bucket=BUCKET, Key=src_key)
            except Exception as e:
                print(f"[skip] source missing: {src_key} (for clip {key}) err={e}")
                skipped += 1
                continue

            src_url = to_origin_url(BUCKET, src_key)
            kwargs = {"dest_key": key, "force_download": FORCE_LOCAL}

            if DRY_RUN:
                print(f"[DRY] would repair: clip={key} size={size} src={src_key} url={src_url} kwargs={kwargs}")
            else:
                res = celery.send_task(CLIP_TASK_NAME, args=[src_url], kwargs=kwargs, queue=QUEUE)
                print(f"[task] queued {res.id}: clip={key} size={size} src={src_key}")
                queued += 1
                if queued >= MAX_TASKS:
                    print(f"Reached REPAIR_MAX_TASKS={MAX_TASKS}, stopping.")
                    print(f"Queued={queued} Skipped={skipped}")
                    return

    print(f"Done. Queued={queued} Skipped={skipped}")

if __name__ == "__main__":
    main()
