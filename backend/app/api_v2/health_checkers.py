# app/api_v2/health_checkers.py
import asyncio, json, logging
from typing import Any, Dict, List

import aiohttp
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import os
import re
import unicodedata
import hashlib
from pathlib import Path
from urllib.parse import urlparse, unquote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, Body

from ..db.database import get_async_db                   # ваша обёртка
from ..models.models_v2 import Course, Landing        # ваши модели
from ..celery_app import celery

router = APIRouter(prefix="/videos", tags=["videos"])

# --------------------------------------------------------------------------- #
#                                У т и л и т ы                                #
# --------------------------------------------------------------------------- #

OK_STATUSES = {*range(200, 400)}        # 2xx и 3xx считаем «живыми»

async def probe_url(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> bool:
    """
    True → ссылка рабочая,  False → битая.
    HEAD-запрос + fallback на мини-GET, чтобы не качать мегабайты.
    """
    try:
        async with session.head(url, allow_redirects=True, timeout=timeout) as r:
            return r.status in OK_STATUSES
    except Exception:
        try:
            async with session.get(url, allow_redirects=True, timeout=timeout) as r:
                return r.status in OK_STATUSES
        except Exception:
            return False

# ---------- JSON-парсинг полей моделей ---------- #

def extract_videos_from_course(course: Course) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not course.sections:
        return out
    try:
        for sec in course.sections.values():
            sec_name = sec.get("section_name", "")
            for lesson in sec.get("lessons", []):
                out.append(
                    {
                        "source": "course",
                        "course_id": course.id,
                        "section": sec_name,
                        "lesson": lesson.get("lesson_name", ""),
                        "video_link": lesson.get("video_link", ""),
                    }
                )
    except Exception as e:
        logging.warning("Course %s JSON parse error: %s", course.id, e)
    return out


def extract_videos_from_landing(landing: Landing) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not landing.lessons_info:
        return out
    try:
        for item in landing.lessons_info:
            _, info = next(iter(item.items()))
            out.append(
                {
                    "source": "landing",
                    "landing_id": landing.id,
                    "lesson": info.get("name", ""),
                    "video_link": info.get("link", ""),
                }
            )
    except Exception as e:
        logging.warning("Landing %s JSON parse error: %s", landing.id, e)
    return out

# --------------------------------------------------------------------------- #
#                            С т р и м – г е н е р а т о р                    #
# --------------------------------------------------------------------------- #

async def broken_videos_stream(db: AsyncSession, concurrency: int = 30):
    """
    Асинхронный генератор, который:
      1. собирает все ссылки,
      2. проверяет их параллельно,
      3. сразу стримит «битые» как элементы JSON-массива.
    """
    # 1. достаём модели из БД
    courses  = (await db.scalars(select(Course))).all()
    landings = (await db.scalars(select(Landing))).all()

    videos: List[Dict[str, Any]] = [
        *(
            v for c in courses  for v in extract_videos_from_course(c)  if v["video_link"]
        ),
        *(
            v for l in landings for v in extract_videos_from_landing(l) if v["video_link"]
        ),
    ]

    # 2. конвейер проверки
    semaphore = asyncio.Semaphore(concurrency)

    async def check(v: Dict[str, Any]):
        async with semaphore, aiohttp.ClientSession() as session:
            ok = await probe_url(session, v["video_link"])
            return v if not ok else None

    # 3. начинаем ответ-поток
    yield '['                                 # открыли массив
    first = True

    # Одновременно создаём все задачи, но читаем результаты
    # по мере готовности (as_completed)
    tasks = [asyncio.create_task(check(v)) for v in videos]

    for coro in asyncio.as_completed(tasks):
        broken = await coro
        if not broken:
            continue
        if first:                      # первый элемент – без запятой
            first = False
        else:                          # остальные – ставим запятую
            yield ','
        # отправляем результат
        yield json.dumps(broken, ensure_ascii=False)
        # «\n» не нужен, но полезен людям, когда тестируете глазами
        yield '\n'

    # 4. если битых не было – сразу закрываем пустой массив
    if first:
        yield ']'
    else:
        yield ']'                      # закрыли массив


# --------------------------------------------------------------------------- #
#                                Р о у т                                      #
# --------------------------------------------------------------------------- #

@router.get(
    "/check/stream",
    summary="Проверить все видео и стримить список битых",
    response_class=StreamingResponse,
    status_code=status.HTTP_200_OK,

    # ↓↓↓ добавляем описание ответа 200
    responses={
        200: {
            "description": "Потоковый JSON-массив объектов с битым видео",
            "content": {
                "application/json": {
                    # для стрима хватит простейшей схемы «строка»,
                    # Swagger-UI больше не отметит ответ как Undocumented
                    "schema": {"type": "string", "example": '[{"source":"course",…}]'},
                }
            },
        }
    },
)
async def check_videos_stream(db: AsyncSession = Depends(get_async_db)):
    generator = broken_videos_stream(db)
    return StreamingResponse(generator, media_type="application/json")

# ---------------------------------------------------------------------------
# Configuration (env)
# ---------------------------------------------------------------------------
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET = os.getenv("S3_BUCKET", "")
S3_REGION = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

# Основной клиент (V2) для Head/Get/Put
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# Отдельный клиент с подписью V4 — только для листинга (ListObjectsV2)
s3_list = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

router = APIRouter(prefix="/admin/hls", tags=["hls-admin"])

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def slug(name: str) -> str:
    stem = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii", "ignore").decode()
    ascii_name = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower()
    return (ascii_name or hashlib.sha1(stem.encode()).hexdigest())[:60]

def hls_prefix_for(key: str) -> str:
    base, fname = os.path.split(key)
    return f"{base}/.hls/{slug(fname)}/".lstrip("/")

def key_from_url(url: str) -> str:
    parsed = urlparse(url)
    # Если передана уже только часть пути без протокола, тоже обработаем
    if not parsed.scheme:
        # считаем что это уже ключ (мог быть percent-encoded)
        return unquote(url.lstrip('/'))
    return unquote(parsed.path.lstrip('/'))

def mp4_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False

def hls_ready(key: str) -> bool:
    # 1) По метаданным исходника
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        if head.get("Metadata", {}).get("hls") == "true":
            return True
    except ClientError:
        return False  # исходник отсутствует
    # 2) По наличию плейлиста
    prefix = hls_prefix_for(key)
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=f"{prefix}playlist.m3u8")
        return True
    except ClientError:
        return False

# ---------------------------------------------------------------------------
# Routes
# ---------------------------------------------------------------------------

@router.get("/hls_stats")
async def hls_stats():
    """Return counts of MP4 objects that have / do not have HLS yet.
    O(N) list. Cache outside if needed."""
    paginator = s3_list.get_paginator("list_objects_v2")
    total = 0
    ready = 0
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.lower().endswith(".mp4"):
                continue
            if "/.hls/" in key:
                continue
            total += 1
            if hls_ready(key):
                ready += 1
    return {"hls_ready": ready, "pending": total - ready, "total_mp4": total}


class ProcessRequest(BaseException):  # placeholder removed later
    pass

from pydantic import BaseModel

class HLSProcessIn(BaseModel):
    url: str

@router.post("/hls_process")
async def hls_process(data: HLSProcessIn):
    key = key_from_url(data.url)
    if not key.lower().endswith('.mp4'):
        raise HTTPException(status_code=400, detail="Provided URL is not an .mp4")

    if not mp4_exists(key):
        return {"status": "source_not_found", "key": key}

    if hls_ready(key):
        return {"status": "already_ready", "key": key}

    celery.send_task("app.tasks.process_hls_video", args=[key], queue="special")
    return {"status": "queued", "key": key}
