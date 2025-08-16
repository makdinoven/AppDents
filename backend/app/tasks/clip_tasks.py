# app/tasks/clip_tasks.py
import mimetypes
import os
import subprocess
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse, quote

import boto3
from botocore.config import Config
from celery import shared_task

# --- S3/ENV ---
S3_BUCKET      = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

def _bucket_from_url(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.split(".")[0] if host.endswith(".s3.twcstorage.ru") else S3_BUCKET

def _key_from_url(url: str) -> str:
    return unquote(urlparse(url).path.lstrip("/"))

def _unique_clip_name(original_key: str) -> str:
    p = Path(original_key)
    return str(p.parent / "narezki" / f"{p.stem}_clip_{uuid.uuid4().hex}{p.suffix or '.mp4'}")

def _encode_for_url(key: str) -> str:
    return quote(key, safe="/")

def _run_ffmpeg_stream(in_url: str, out_pipe, length: int = 300):
    # фрагментированный MP4, поддержка ADTS→ASC
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-loglevel", "error",
        "-threads", "1",
        "-y",
        "-ss", "0",
        "-i", in_url,
        "-t", str(length),
        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-movflags", "frag_keyframe+empty_moov",
        "-f", "mp4",
        "pipe:1",
    ]
    return subprocess.Popen(cmd, stdout=out_pipe)

@shared_task(bind=True, autoretry_for=(), retry_backoff=False, track_started=True, name="clip_video")
def clip_video(self, src_url: str) -> dict:
    """
    Фоновая обрезка: S3 presigned (HTTPS) → ffmpeg (stdout) → S3 upload_fileobj
    Возвращает {"clip_url": ..., "length_sec": 300}
    """
    self.update_state(state="STARTED")

    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)
    clip_key   = _unique_clip_name(src_key)

    presigned = s3.generate_presigned_url(
        "get_object", Params={"Bucket": src_bucket, "Key": src_key}, ExpiresIn=3600
    )

    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
    proc = _run_ffmpeg_stream(presigned, subprocess.PIPE)

    try:
        s3.upload_fileobj(
            proc.stdout,
            S3_BUCKET,
            clip_key,
            ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
        )
    finally:
        proc.stdout.close()
        ret = proc.wait()
        if ret != 0:
            raise RuntimeError(f"ffmpeg exited with {ret}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
    return {"clip_url": clip_url, "length_sec": 300}
