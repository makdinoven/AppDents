import hashlib
import logging
import os
import re
import subprocess
import tempfile
import unicodedata
from pathlib import Path
from urllib.parse import unquote

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

NEW_TASKS_LIMIT: int = int(os.getenv("NEW_TASKS_LIMIT", 20))  # per scanner run
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
    Улучшенный пересчёт:
      - Определяем total_mp4.
      - Восстанавливаем готовые исходники без HeadObject.
      - Используем несколько методов сопоставления:
          * единственный mp4 в каталоге
          * точный slug
          * slug c percent-decode
          * fuzzy очистка (только буквы/цифры)
      - Логируем unmatched и collisions.
    """
    logger.info("[HLS][RECOUNT] start (improved)")

    s3v4 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    paginator = s3v4.get_paginator("list_objects_v2")

    mp4_by_dir = {}          # dir -> [ {key,size,stem,slug} ]
    playlists = []           # [{base_dir, slug_dir, full_key}]
    total_mp4 = 0

    def norm_slug(stem: str) -> str:
        ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii","ignore").decode()
        ascii_name = re.sub(r"[^A-Za-z0-9]+","-", ascii_name).strip("-").lower()
        return (ascii_name or hashlib.sha1(stem.encode()).hexdigest())[:60]

    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            low = key.lower()
            if "/.hls/" in key:
                # возможный playlist?
                if low.endswith("playlist.m3u8"):
                    parts = key.split("/")
                    try:
                        hls_index = parts.index(".hls")
                    except ValueError:
                        continue
                    if hls_index >= 1 and hls_index + 2 < len(parts):
                        base_dir = "/".join(parts[:hls_index])  # может быть "", если в корне
                        slug_dir = parts[hls_index + 1]
                        playlists.append({
                            "base_dir": base_dir,
                            "slug_dir": slug_dir,
                            "playlist_key": key,
                        })
                continue

            if low.endswith(".mp4"):
                total_mp4 += 1
                base_dir = os.path.dirname(key)
                stem = os.path.splitext(os.path.basename(key))[0]
                entry = {
                    "key": key,
                    "size": obj.get("Size", 0),
                    "stem": stem,
                    "slug": norm_slug(stem),
                }
                mp4_by_dir.setdefault(base_dir, []).append(entry)

    recovered = set()
    collisions = 0
    unmatched = 0

    def fuzzy(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", s.lower())

    for pl in playlists:
        base_dir = pl["base_dir"]
        slug_dir = pl["slug_dir"]

        candidates = mp4_by_dir.get(base_dir, [])
        if not candidates:
            # нет исходников в этом каталоге
            unmatched += 1
            continue

        if len(candidates) == 1:
            recovered.add(candidates[0]["key"])
            continue

        # 1) точный slug
        exact = [c for c in candidates if c["slug"] == slug_dir]
        if len(exact) == 1:
            recovered.add(exact[0]["key"])
            continue
        elif len(exact) > 1:
            # slug коллизия -> возьмём самый большой размером (или логируем)
            exact_sorted = sorted(exact, key=lambda x: x["size"], reverse=True)
            recovered.add(exact_sorted[0]["key"])
            collisions += 1
            continue

        # 2) percent-decode stem (если в stem есть '%')
        decoded_matches = []
        for c in candidates:
            if "%" in c["stem"]:
                dec = unquote(c["stem"])
                if norm_slug(dec) == slug_dir:
                    decoded_matches.append(c)
        if len(decoded_matches) == 1:
            recovered.add(decoded_matches[0]["key"])
            continue
        elif len(decoded_matches) > 1:
            decoded_matches.sort(key=lambda x: x["size"], reverse=True)
            recovered.add(decoded_matches[0]["key"])
            collisions += 1
            continue

        # 3) fuzzy
        fuzzy_matches = [c for c in candidates if fuzzy(c["stem"]) == fuzzy(slug_dir)]
        if len(fuzzy_matches) == 1:
            recovered.add(fuzzy_matches[0]["key"])
            continue
        elif len(fuzzy_matches) > 1:
            fuzzy_matches.sort(key=lambda x: x["size"], reverse=True)
            recovered.add(fuzzy_matches[0]["key"])
            collisions += 1
            continue

        # не нашли
        unmatched += 1

    # Обновляем Redis (объединяем, чтобы не потерять добавленные параллельно)
    pipe = rds.pipeline()
    if recovered:
        pipe.sadd(R_SET_READY, *recovered)
    pipe.set(R_TOTAL, total_mp4)
    pipe.set(R_LAST_RECOUNT_TS, int(time.time()))
    pipe.execute()

    logger.info(
        "[HLS][RECOUNT] total_mp4=%d playlists=%d recovered=%d collisions=%d unmatched_playlists=%d ready_now=%d",
        total_mp4, len(playlists), len(recovered), collisions, unmatched, rds.scard(R_SET_READY)
    )
