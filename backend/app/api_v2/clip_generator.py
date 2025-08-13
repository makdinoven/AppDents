# main.py  —  S3 ➜ ffmpeg ➜ S3 (streaming)
import asyncio
import logging
import mimetypes
import os
import subprocess
import uuid
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import boto3
from botocore.config import Config
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
S3_BUCKET      = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")  # origin bucket
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

# тайм-аут nginx / gunicorn надо поднять ≥ времени обрезки!
DEFAULT_TIMEOUT = int(os.getenv("CLIP_TIMEOUT", "600"))   # sec

# -------------------------------------------------
# LOG
# -------------------------------------------------
logging.basicConfig(level=logging.INFO)
log = logging.getLogger("clip")

# -------------------------------------------------
# AWS S3
# -------------------------------------------------
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# -------------------------------------------------
# FASTAPI
# -------------------------------------------------
router = APIRouter()
executor = ThreadPoolExecutor(max_workers=int(os.getenv("FFMPEG_WORKERS", 2)))


class ClipIn(BaseModel):
    url: str


# -------------------------------------------------
# helpers
# -------------------------------------------------
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


# -------------------------------------------------
# core: ffmpeg streaming
# -------------------------------------------------
def _run_ffmpeg_stream(in_url: str, out_pipe, length: int = 300):
    """
    in_url  – HTTPS presigned-URL из S3
    out_pipe – sys.stdout (pipe:1)
    """
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
        "-f", "mp4",           # обязательно указать контейнер, когда пишем в pipe
        "pipe:1",
    ]
    proc = subprocess.Popen(cmd, stdout=out_pipe)
    return proc


async def _clip_async(src_bucket: str, src_key: str, clip_key: str):
    """
    Стримим вход → ffmpeg → upload_fileobj
    """
    presigned_url = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": src_bucket, "Key": src_key},
        ExpiresIn=3600,
    )

    # запускаем ffmpeg в отдельном потоке чтоб не блокировать event-loop
    loop = asyncio.get_running_loop()

    def _worker():
        mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
        proc = _run_ffmpeg_stream(presigned_url, subprocess.PIPE)
        try:
            s3.upload_fileobj(
                proc.stdout,            # file-like stream
                S3_BUCKET,
                clip_key,
                ExtraArgs={
                    "ContentType": mime,
                    "ContentDisposition": "inline",
                },
            )
        finally:
            proc.stdout.close()
            ret = proc.wait()
            if ret != 0:
                raise RuntimeError(f"ffmpeg exited with code {ret}")

    await loop.run_in_executor(executor, _worker)


# -------------------------------------------------
# ROUTE
# -------------------------------------------------
@router.post("/clip")
async def create_clip(data: ClipIn):
    src_bucket = _bucket_from_url(data.url)
    src_key = _key_from_url(data.url)

    # ключ для нового клипа
    clip_key = _unique_clip_name(src_key)

    try:
        await asyncio.wait_for(
            _clip_async(src_bucket, src_key, clip_key),
            timeout=DEFAULT_TIMEOUT,
        )
    except asyncio.TimeoutError:
        log.error("ffmpeg clip timeout")
        raise HTTPException(504, "Clip generation timeout")
    except Exception as e:
        log.exception("clip generation failed")
        raise HTTPException(500, f"clip generation error: {e}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
    return {
        "source_url": data.url,
        "clip_url": clip_url,
        "length_sec": 300,
    }
