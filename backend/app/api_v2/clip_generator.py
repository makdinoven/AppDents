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


router = APIRouter()



class ClipIn(BaseModel):
    url: str

def _bucket_from_url(url: str) -> str:
    """Если ссылка вида *.s3.twcstorage.ru — берём поддомен, иначе используем S3_BUCKET."""
    host = urlparse(url).hostname or ""
    return host.split(".")[0] if host.endswith(".s3.twcstorage.ru") else S3_BUCKET


def _key_from_url(url: str) -> str:
    """
    Возвращаем **декодированный** ключ для S3‑операций.
    '%20' → пробел, '%E2%80%99' → ’ и т.д.
    """
    return unquote(urlparse(url).path.lstrip("/"))


def _unique_clip_name(original_key: str) -> str:
    parent = Path(original_key).parent
    stem   = Path(original_key).stem
    ext    = Path(original_key).suffix or ".mp4"
    return str(parent / "narezki" / f"{stem}_clip_{uuid.uuid4().hex}{ext}")


def _reencode_for_url(key: str) -> str:
    """
    Обратно кодируем спец‑символы для ссылки в ответе,
    сохраняя '/' нетронутым.
    """
    return quote(key, safe="/")


def _run_ffmpeg(src_path: str, dst_path: str) -> None:
    cmd = [
        "ffmpeg", "-loglevel", "error", "-y",
        "nice", "-n", "10",
        "-i", src_path,
        "-threads", "1",
        "-t", "300",  # 5 мин
        "-c", "copy",
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))


# -------------------------------------------------
# ROUTE
# -------------------------------------------------
@router.post("/clip")
async def create_clip(data: ClipIn):
    src_bucket = _bucket_from_url(data.url)
    src_key    = _key_from_url(data.url)          # 👈 декодированный

    with tempfile.TemporaryDirectory() as tmpdir:
        ext       = Path(src_key).suffix or ".mp4"
        src_path  = os.path.join(tmpdir, f"src{ext}")
        dst_path  = os.path.join(tmpdir, f"clip{ext}")

        # 1. Скачиваем оригинал
        try:
            s3.download_file(src_bucket, src_key, src_path)
        except Exception as e:
            raise HTTPException(400, f"S3 download error: {e}")

        # 2. Обрезаем 5 минут
        try:
            _run_ffmpeg(src_path, dst_path)
        except Exception as e:
            raise HTTPException(500, f"ffmpeg error: {e}")

        # 3. Загружаем клип
        clip_key = _unique_clip_name(src_key)     # тоже без %xx
        mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
        try:
            s3.upload_file(
                dst_path,
                S3_BUCKET,                         # ваш origin‑bucket
                clip_key,
                ExtraArgs={
                    "ContentType": mime,
                    "ContentDisposition": "inline",
                    # "ACL": "public-read",
                },
            )
        except Exception as e:
            raise HTTPException(500, f"S3 upload error: {e}")

    # 4. Формируем CDN‑ссылку с %‑кодировкой
    clip_url = f"{S3_PUBLIC_HOST}/{_reencode_for_url(clip_key)}"

    return {
        "source_url": data.url,   # без изменения
        "clip_url":   clip_url,   # открывается в браузере
        "length_sec": 300,
    }
