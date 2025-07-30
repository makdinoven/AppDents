# main.py
import os
import shutil
import subprocess
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlparse, unquote

import boto3
from botocore.config import Config
from fastapi import FastAPI, HTTPException, APIRouter
from pydantic import BaseModel

# ---------------- S3 / CDN CONFIG ----------------
S3_ENDPOINT       = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET         = os.getenv("S3_BUCKET", "cdn.dent-s.com")         # bucket‑name, без https://
S3_REGION         = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST    = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")  # для ответа

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# ---------------- FASTAPI APP ----------------
router = APIRouter()

class ClipIn(BaseModel):
    url: str


def _key_from_url(url: str) -> str:
    """
    Принимает:
        https://604b5d90‑....s3.twcstorage.ru/Style/1.mp4
        https://cdn.dent-s.com/Style/1.mp4
    Возвращает ключ внутри бакета:  Style/1.mp4
    """
    parsed = urlparse(url)
    # путь может содержать %20 – раскодируем
    return unquote(parsed.path.lstrip("/"))


def _unique_clip_name(original_key: str) -> str:
    """
    Style/1.mp4 -> Style/narezki/1_clip_<uuid>.mp4
    """
    parent = Path(original_key).parent
    stem   = Path(original_key).stem
    ext    = Path(original_key).suffix
    clip_fname = f"{stem}_clip_{uuid.uuid4().hex}{ext}"
    return str(parent / "narezki" / clip_fname)


def _run_ffmpeg(src_path: str, dst_path: str) -> None:
    """
    Берём первые 300 секунд (5 мин).
    Сохраняем аудио/видео без перекодирования если возможно (-c copy),
    иначе вы можете заменить на перекодирование (‑c:v libx264 ...).
    """
    cmd = [
        "ffmpeg",
        "-loglevel", "error",
        "-y",                       # overwrite
        "-i", src_path,
        "-t", "300",                # 5 минут
        "-c", "copy",               # без перекодирования
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))


@router.post("/clip")
async def create_clip(data: ClipIn):
    original_key = _key_from_url(data.url)

    # Скачаем исходник во временный файл
    with tempfile.TemporaryDirectory() as tmpdir:
        src_path = os.path.join(tmpdir, "src")
        dst_path = os.path.join(tmpdir, "clip")

        try:
            s3.download_file(S3_BUCKET, original_key, src_path)
        except Exception as e:
            raise HTTPException(400, f"S3 download error: {e}")

        # делаем обрезку
        try:
            _run_ffmpeg(src_path, dst_path)
        except Exception as e:
            raise HTTPException(500, f"ffmpeg error: {e}")

        # уникальное имя + каталог narezki
        clip_key = _unique_clip_name(original_key)

        # убедимся, что каталога narezki ещё нет/есть
        try:
            s3.upload_file(dst_path, S3_BUCKET, clip_key)
        except Exception as e:
            raise HTTPException(500, f"S3 upload error: {e}")

    # CDN‑ссылка
    clip_url = f"{S3_PUBLIC_HOST}/{clip_key}"

    return {
        "source_url": data.url,
        "clip_url": clip_url,
        "length_sec": 300,
    }
