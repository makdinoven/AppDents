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
# S3 / CDN CONFIG
# -------------------------------------------------
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")          # имя бакета (без https://)
S3_REGION = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")  # что отдаем клиенту

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# -------------------------------------------------
# FastAPI
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
    """
    https://604b5d90...s3.twcstorage.ru/Folder/1.mp4  ->
        Folder/1.mp4
    https://cdn.dent-s.com/Folder/1.mp4 ->
        Folder/1.mp4
    """
    parsed = urlparse(url)
    return unquote(parsed.path.lstrip("/"))  # снимаем %xx чтобы корректно работать с S3


def _unique_clip_name(original_key: str) -> str:
    """
    Folder/1.mp4  ->  Folder/narezki/1_clip_<uuid>.mp4
    """
    parent = Path(original_key).parent
    stem = Path(original_key).stem
    ext = Path(original_key).suffix
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
        "300",  # 5 минут
        "-c",
        "copy",
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(completed.stderr.decode("utf-8"))


def _encode_key_for_url(key: str) -> str:
    """
    Превращает 'Folder/file name.mp4' -> 'Folder/file%20name.mp4'
    (оставляя '/' нетронутым)
    """
    return quote(key, safe="/")


# -------------------------------------------------
# route
# -------------------------------------------------
@router.post("/clip")
async def create_clip(data: ClipIn):
    original_key = _key_from_url(data.url)

    with tempfile.TemporaryDirectory() as tmpdir:
        ext = Path(original_key).suffix or ".mp4"
        src_path = os.path.join(tmpdir, f"src{ext}")
        dst_path = os.path.join(tmpdir, f"clip{ext}")

        # 1. скачиваем исходник
        try:
            s3.download_file(S3_BUCKET, original_key, src_path)
        except Exception as e:
            raise HTTPException(400, f"S3 download error: {e}")

        # 2. обрезаем ffmpeg‑ом
        try:
            _run_ffmpeg(src_path, dst_path)
        except Exception as e:
            raise HTTPException(500, f"ffmpeg error: {e}")

        # 3. формируем ключ и MIME
        clip_key = _unique_clip_name(original_key)
        mime, _ = mimetypes.guess_type(clip_key)
        if not mime:
            mime = "video/mp4"

        # 4. загружаем с правильными заголовками
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

    # 5. собираем ссылку с сохранёнными %‑кодами
    clip_url = f"{S3_PUBLIC_HOST}/{_encode_key_for_url(clip_key)}"

    return {
        "source_url": data.url,  # здесь оставляем как есть
        "clip_url": clip_url,    # всё %xx осталось нетронутым
        "length_sec": 300,
    }
