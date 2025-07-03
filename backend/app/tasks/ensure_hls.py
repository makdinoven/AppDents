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

# ---------------------------------------------------------------------------
# Environment / constants
# ---------------------------------------------------------------------------

S3_ENDPOINT: str = os.getenv("S3_ENDPOINT", "")
S3_BUCKET: str = os.getenv("S3_BUCKET", "")
S3_REGION: str = os.getenv("S3_REGION", "")
S3_PUBLIC_HOST: str = os.getenv("S3_PUBLIC_HOST", "")


NEW_TASKS_LIMIT: int = int(os.getenv("NEW_TASKS_LIMIT", 10))  # per scanner run
PRESIGN_EXPIRY: int = 3600                                     # seconds

logger = logging.getLogger(__name__)

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

def slug(name: str) -> str:
    """ASCII‑safe slug for directory names (max 60 chars)."""
    stem = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower()
    return (ascii_name or hashlib.sha1(stem.encode()).hexdigest())[:60]


def hls_prefix_for(key: str) -> str:
    base, fname = os.path.split(key)
    return f"{base}/.hls/{slug(fname)}/".lstrip("/")

@shared_task(name="app.tasks.ensure_hls")
def ensure_hls() -> None:
    """Scan the entire bucket for `.mp4` objects without `hls=true` metadata
    and queue conversion jobs (up to NEW_TASKS_LIMIT per invocation)."""
    paginator = s3.get_paginator("list_objects_v2")
    queued = 0

    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".mp4"):
                continue
            # skip files already inside .hls sub‑folders
            if "/.hls/" in key or key.endswith("_hls/"):
                continue
            try:
                head = s3.head_object(Bucket=S3_BUCKET, Key=key)
                if head.get("Metadata", {}).get("hls") == "true":
                    continue
            except ClientError as e:  # pragma: no cover — log and skip
                logger.warning("Head failed for %s: %s", key, e)
                continue

            process_hls_video.apply_async((key,), queue="special")
            queued += 1
            logger.info("[HLS] queued %s", key)
            if queued >= NEW_TASKS_LIMIT:
                logger.info("[HLS] limit %d reached", NEW_TASKS_LIMIT)
                return

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
