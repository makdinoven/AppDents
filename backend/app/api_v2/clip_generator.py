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
# 👉 Укажите фактическое имя бакета (обычно UUID‑подобная строка)
S3_BUCKET = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION = os.getenv("S3_REGION", "ru-1")

# 👉 Домен вашего CDN — тот, что возвращаем клиенту
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

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
router = APIRouter(prefix="/api/clip_generator")
app = FastAPI(title="Dent‑S Clip Generator")
app.include_router(router)


class ClipIn(BaseModel):
    url: str


# -------------------------------------------------
# helpers
# -------------------------------------------------
def _key_from_url(url: str) -> str:
    """Возвращает ключ внутри бакета (раскодированный)."""
    return unquote(urlparse(url).path.lstrip("/"))


def _unique_clip_name(original_key: str) -> str:
    """
    Folder/1.mp4 → Folder/narezki/1_clip_<uuid>.mp4
    """
    parent = Path(original_key).parent
    stem = Path(original_key).stem
    ext = Path(original_key).suffix
    return str(parent / "narezki" / f"{stem}_clip_{uuid.uuid4().hex}{ext}")


def _run_ffmpeg(src_path: str, dst_path: str) -> None:
    """Обрезает первые 5 мин аудио/видео без перекодирования."""
    cmd = [
        "ffmpeg",
        "-loglevel",
        "error",
        "-y",
        "-i",
        src_path,
        "-t",
        "300",
        "-c",
        "copy",
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))


def _encode_for_url(key: str) -> str:
    """Обратно кодирует пробелы и не‑ASCII (оставляя '/' нетронутым)."""
    return quote(key, safe="/")


# -------------------------------------------------
# ROUTE
# -------------------------------------------------
@router.post("/clip")
async def create_clip(data: ClipIn):
    src_key = _key_from_url(data.url)           # путь к оригиналу

    with tempfile.TemporaryDirectory() as tmpdir:
        ext = Path(src_key).suffix or ".mp4"
        src_path = os.path.join(tmpdir, f"src{ext}")
        dst_path = os.path.join(tmpdir, f"clip{ext}")

        # 1) скачиваем из *одного и того же* бакета
        try:
            s3.download_file(S3_BUCKET, src_key, src_path)
        except Exception as e:
            raise HTTPException(400, f"S3 download error: {e}")

        # 2) обрезаем
        try:
            _run_ffmpeg(src_path, dst_path)
        except Exception as e:
            raise HTTPException(500, f"ffmpeg error: {e}")

        # 3) загружаем обратно
        clip_key = _unique_clip_name(src_key)
        mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
        try:
            s3.upload_file(
                dst_path,
                S3_BUCKET,
                clip_key,
                ExtraArgs={
                    "ContentType": mime,
                    "ContentDisposition": "inline",
                    # "ACL": "public-read",  # раскомментируйте при необходимости
                },
            )
        except Exception as e:
            raise HTTPException(500, f"S3 upload error: {e}")

    # 4) формируем ссылку через CDN
    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"

    return {
        "source_url": data.url,  # без изменений
        "clip_url": clip_url,    # все %‑последовательности сохранены
        "length_sec": 300,
    }
