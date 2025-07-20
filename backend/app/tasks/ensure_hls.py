import hashlib
import logging
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
import os, time, logging, boto3, redis
from celery import shared_task
from botocore.config import Config

logger = logging.getLogger(__name__)
REDIS_URL   = os.getenv("REDIS_URL", "redis://redis:6379/0")
R_SET_READY = "hls:ready"
R_TOTAL     = "hls:total_mp4"
R_LAST_RECOUNT_TS = "hls:last_recount_ts"
rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)
S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET: str = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION: str = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST: str = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

CF_ZONE_ID: str | None = os.getenv("CF_ZONE_ID")              # ← Cloudflare
CF_AUTH_EMAIL: str | None = os.getenv("CF_AUTH_EMAIL")        # credentials
CF_AUTH_KEY: str | None = os.getenv("CF_AUTH_KEY")

NEW_TASKS_LIMIT: int = int(os.getenv("NEW_TASKS_LIMIT", 10))  # per scanner run
PRESIGN_EXPIRY: int = 3600                                     # seconds


s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _each_mp4_objects():
    """ generator(key) по bucket, совместим с timeweb S3 """
    s3v4 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4"),      # ВАЖНО!
    )

    paginator = s3v4.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".mp4"):
                yield key

def slug(name: str) -> str:
    stem = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii","ignore").decode()
    ascii_name = re.sub(r"[^A-Za-z0-9]+","-", ascii_name).strip("-").lower()
    return (ascii_name or hashlib.sha1(stem.encode()).hexdigest())[:60]



def hls_prefix_for(key: str) -> str:
    base, fname = os.path.split(key)
    return f"{base}/.hls/{slug(fname)}/".lstrip("/")

# ---------------------------------------------------------------------------
# Celery tasks
# ---------------------------------------------------------------------------

@shared_task(name="app.tasks.ensure_hls")
def ensure_hls() -> None:
    """Scan S3 for .mp4 objects without `hls=true` and enqueue up to
    `NEW_TASKS_LIMIT` conversion jobs.  
    **Uses a temporary S3 client with V4‑signature _только_ для операции
    `ListObjectsV2`, чтобы обойти ограничения Timeweb‑S3.**"""

    queued = 0

    for key in _each_mp4_objects():  # V4‑подпись, безопасна для листинга
        # пропускаем сервисные каталоги
        if "/.hls/" in key or key.endswith("_hls/"):
            continue
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            if head.get("Metadata", {}).get("hls") == "true":
                continue  # уже обработано
        except ClientError as e:
            logger.warning("HeadObject failed for %s: %s", key, e)
            continue

        process_hls_video.apply_async((key,), queue="special")
        queued += 1
        logger.info("[HLS] queued %s", key)
        if queued >= NEW_TASKS_LIMIT:
            logger.info("[HLS] limit %d reached", NEW_TASKS_LIMIT)
            break

    logger.info("[HLS] scan done, queued %d", queued)


@shared_task(name="app.tasks.process_hls_video", rate_limit="6/m")
def process_hls_video(key: str) -> None:
    """Download MP4 → fragment → upload HLS set → mark object → purge CDN."""
    hls_prefix = hls_prefix_for(key)  # e.g. path/.hls/slug/
    playlist_url = f"{S3_PUBLIC_HOST}/{hls_prefix}playlist.m3u8"

    # Shortcut: if playlist already exists, skip heavy work
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=f"{hls_prefix}playlist.m3u8")
        logger.info("[HLS] already exists for %s", key)
        return
    except ClientError:
        pass  # really create

    with tempfile.TemporaryDirectory() as tmp:
        in_mp4 = os.path.join(tmp, "in.mp4")
        s3.download_file(S3_BUCKET, key, in_mp4)

        seg_pat = os.path.join(tmp, "segment_%03d.ts")
        playlist = os.path.join(tmp, "playlist.m3u8")

        cmd = [
            "ffmpeg", "-v", "error", "-y", "-i", in_mp4,
            "-c", "copy", "-movflags", "+faststart",
            "-hls_time", "8", "-hls_list_size", "0",
            "-hls_flags", "independent_segments",
            "-hls_segment_filename", seg_pat,
            playlist,
        ]
        subprocess.run(cmd, check=True)

        # Upload playlist + segments
        for fname in os.listdir(tmp):
            if fname == "in.mp4":
                continue
            src = os.path.join(tmp, fname)
            dst = f"{hls_prefix}{fname}"
            ct = "application/vnd.apple.mpegurl" if fname.endswith(".m3u8") else "video/MP2T"
            s3.upload_file(src, S3_BUCKET, dst,
                           ExtraArgs={"ACL": "public-read", "ContentType": ct})

    # Mark source MP4
    head = s3.head_object(Bucket=S3_BUCKET, Key=key)
    meta = head.get("Metadata", {})
    meta["hls"] = "true"
    s3.copy_object(Bucket=S3_BUCKET, Key=key,
                   CopySource={"Bucket": S3_BUCKET, "Key": key},
                   Metadata=meta, MetadataDirective="REPLACE",
                   ContentType=head["ContentType"], ACL="public-read")
    logger.info("[HLS] ready → %s", playlist_url)
    rds.sadd("hls:ready", key)

# Клиент только для листинга — V4
s3v4 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

@shared_task(name="app.tasks.ensure_hls.recount_hls_counters")
def recount_hls_counters():
    """
    Полный скан:
      - собираем все исходные mp4 (не внутри /.hls/)
      - собираем все playlist.m3u8
      - восстанавливаем slug -> оригинальный mp4 через поиск
      - наполняем Redis:
           hls:total_mp4
           hls:ready (union со старыми, чтобы не потерять то, что пришло параллельно)
           hls:last_recount_ts
    """
    logger.info("[HLS][RECOUNT] start")
    s3v4 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    paginator = s3v4.get_paginator("list_objects_v2")

    mp4_keys = []
    playlists = []  # (original_base_path, slug)
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            low = key.lower()
            if low.endswith(".mp4") and "/.hls/" not in low:
                mp4_keys.append(key)
            elif low.endswith("playlist.m3u8") and "/.hls/" in key:
                # структура: <base>/.hls/<slug>/playlist.m3u8
                # возьмём base и slug
                parts = key.split("/")
                try:
                    hls_index = parts.index(".hls")
                except ValueError:
                    # иногда .hls может быть частью имени? пропустим
                    continue
                if hls_index >= 1 and hls_index + 2 < len(parts):
                    base_parts = parts[:hls_index]  # каталог(и) исходника
                    slug_dir = parts[hls_index + 1]
                    playlists.append(("/".join(base_parts), slug_dir))

    # Построим map: slug -> кандидаты исходных файлов (basename без расширения slug-нутый)
    from collections import defaultdict
    slug_candidates = defaultdict(list)
    for key in mp4_keys:
        basename = os.path.basename(key)
        stem = os.path.splitext(basename)[0]
        slugified = slug(stem)
        slug_candidates[slugified].append(key)

    recovered = set()
    collisions = 0
    for base, slug_dir in playlists:
        cand_list = slug_candidates.get(slug_dir)
        if not cand_list:
            continue
        if len(cand_list) == 1:
            recovered.add(cand_list[0])
        else:
            # Несколько одинаковых slug — уточняем по каталогу base
            filtered = [k for k in cand_list if os.path.dirname(k) == base]
            if len(filtered) == 1:
                recovered.add(filtered[0])
            else:
                collisions += 1  # невозможно однозначно
    # Объединяем с уже существующим set (чтобы не потерять новые мгновенно добавленные)
    pipe = rds.pipeline()
    if recovered:
        pipe.sadd(R_SET_READY, *recovered)
    pipe.set(R_TOTAL, len(mp4_keys))
    pipe.set(R_LAST_RECOUNT_TS, int(time.time()))
    pipe.execute()

    logger.info("[HLS][RECOUNT] total_mp4=%d recovered_ready=%d collisions=%d existing_ready=%d",
                len(mp4_keys), len(recovered), collisions, rds.scard(R_SET_READY))
