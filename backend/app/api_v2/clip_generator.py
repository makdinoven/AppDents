# main.py
import mimetypes
import os
import subprocess
import tempfile
import uuid
from pathlib import Path
from urllib.parse import quote, unquote, urlparse

import boto3
from botocore.config import Config
from fastapi import APIRouter, FastAPI, HTTPException
from pydantic import BaseModel

# -------------------------------------------------
# ENV / CONSTS
# -------------------------------------------------
S3_BUCKET = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")  # origin‑bucket
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")  # CDN‑домен

session = boto3.session.Session()
s3 = session.client(
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

class ClipIn(BaseModel):
    url: str


# -------------------------------------------------
# helpers
# -------------------------------------------------
def _bucket_from_url(url: str) -> str:
    """
    Если хост заканчивается на .s3.twcstorage.ru → берём поддомен как bucket.
    Иначе используем S3_BUCKET из окружения.
    """
    host = urlparse(url).hostname or ""
    if host.endswith(".s3.twcstorage.ru"):
        return host.split(".")[0]  # то, что до первой точки
    return S3_BUCKET


def _key_from_url(url: str) -> str:
    """Возвращает ключ объекта в S3, декодируя %‑последовательности."""
    return unquote(urlparse(url).path.lstrip("/"))


def _unique_clip_name(original_key: str) -> str:
    parent = Path(original_key).parent
    stem = Path(original_key).stem
    ext = Path(original_key).suffix or ".mp4"
    return str(parent / "narezki" / f"{stem}_clip_{uuid.uuid4().hex}{ext}")


def _run_ffmpeg(src_path: str, dst_path: str) -> None:
    cmd = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        src_path,
        "-t",
        "300",  # 5 минут
        "-c",
        "copy",
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))


def _encode_for_url(key: str) -> str:
    """URL‑кодирует пробелы/не‑ASCII, оставляя '/' нетронутым."""
    return quote(key, safe="/")


# -------------------------------------------------
# ROUTE
# -------------------------------------------------
@router.post("/clip")
async def create_clip(data: ClipIn):
    src_bucket = _bucket_from_url(data.url)
    src_key = _key_from_url(data.url)

    with tempfile.TemporaryDirectory() as tmpdir:
        ext = Path(src_key).suffix or ".mp4"
        src_path = os.path.join(tmpdir, f"src{ext}")
        dst_path = os.path.join(tmpdir, f"clip{ext}")

        # 1) скачиваем из определённого бакета
        try:
            s3.download_file(src_bucket, src_key, src_path)
        except Exception as e:
            raise HTTPException(400, f"S3 download error: {e}")

        # 2) обрезаем
        try:
            _run_ffmpeg(src_path, dst_path)
        except Exception as e:
            raise HTTPException(500, f"ffmpeg error: {e}")

        # 3) загружаем клип обратно в origin‑bucket (S3_BUCKET)
        clip_key = _unique_clip_name(src_key)
        mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
        try:
            s3.upload_file(
                dst_path,
                S3_BUCKET,             # кладём в CDN‑origin
                clip_key,
                ExtraArgs={
                    "ContentType": mime,
                    "ContentDisposition": "inline",
                    # "ACL": "public-read",  # при необходимости
                },
            )
        except Exception as e:
            raise HTTPException(500, f"S3 upload error: {e}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"

    return {
        "source_url": data.url,  # без изменений
        "clip_url": clip_url,    # %‑кодировка сохранена
        "length_sec": 300,
    }
