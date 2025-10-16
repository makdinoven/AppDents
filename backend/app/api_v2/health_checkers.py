# app/api_v2/health_checkers.py
import asyncio, json, logging
import time
from typing import Any, Dict, List, Optional

import aiohttp
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status
import os
import redis
from urllib.parse import urlparse, unquote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, HTTPException, Depends, Body

from ..db.database import get_async_db                   # ваша обёртка
from ..models.models_v2 import Course, Landing        # ваши модели
from ..celery_app import celery

router = APIRouter()

# --------------------------------------------------------------------------- #
#                                У т и л и т ы                                #
# --------------------------------------------------------------------------- #

OK_STATUSES = {*range(200, 400)}        # 2xx и 3xx считаем «живыми»
REDIS_URL     = os.getenv("REDIS_URL", "redis://redis:6379/0")
rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Ключи в Redis
R_SET_READY   = "hls:ready"          # Set of original mp4 keys
R_TOTAL       = "hls:total_mp4"      # Int count of all original mp4
R_LAST_RECOUNT_TS = "hls:last_recount_ts"

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

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

ALLOWED_ORIGIN_SUFFIXES = (
    ".s3.twcstorage.ru",
    ".s3.timeweb.com",          # на случай других endpoint'ов
)

CDN_HOSTS = (
    "cdn.dent-s.com",
)

def key_from_url(url_or_key: str) -> str:
    """
    Принимает:
      * полный CDN URL (https://cdn.dent-s.com/Path/Video.mp4)
      * origin URL (https://<bucket>.s3.twcstorage.ru/Каталог/Видео.mp4)
      * просто ключ / путь (percent-encoded или сырой)
    Возвращает unicode object key без ведущего '/'.
    """
    if "://" not in url_or_key:          # уже ключ
        return unquote(url_or_key.lstrip("/"))

    p = urlparse(url_or_key)
    host = p.netloc.lower()
    raw_path = unquote(p.path.lstrip("/"))

    if host in CDN_HOSTS:
        return raw_path

    if any(host.endswith(suf) for suf in ALLOWED_ORIGIN_SUFFIXES):
        # bucket находится в host; path — ключ
        return raw_path

    # Неизвестный домен — всё равно возвращаем path (можно усилить: raise 400)
    return raw_path

def mp4_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False

# ============================================================================
# Pydantic Models
# ============================================================================

class ProcessIn(BaseModel):
    url: str

class ProcessOut(BaseModel):
    status: str           # queued | already_ready | source_not_found
    key: str

class StatsOut(BaseModel):
    hls_ready: int
    pending: int
    total_mp4: int
    last_recount_ts: Optional[int] = None
    fresh: bool

# ============================================================================
# Celery (отложенный импорт чтобы не мешать тестам)
# ============================================================================

try:
    from ..celery_app import celery  # noqa
except Exception:  # pragma: no cover
    celery = None

# ============================================================================
# Router
# ============================================================================



@router.get("/hls_stats", response_model=StatsOut)
async def hls_stats():
    """
    Быстрый ответ из Redis:
      - hls_ready = |set|
      - total_mp4 = integer counter
      - pending = total - ready
    """
    ready = rds.scard(R_SET_READY)
    total = int(rds.get(R_TOTAL) or 0)
    pending = max(total - ready, 0)
    last_ts = rds.get(R_LAST_RECOUNT_TS)
    # свежесть: если пересчёт был не позже 24ч
    fresh = False
    if last_ts:
        fresh = (time.time() - int(last_ts)) < 86400
    return StatsOut(
        hls_ready=ready,
        pending=pending,
        total_mp4=total,
        last_recount_ts=int(last_ts) if last_ts else None,
        fresh=fresh,
    )

@router.post("/hls_process", response_model=ProcessOut)
async def hls_process(data: ProcessIn):
    """
    Проверить конкретное видео и, при необходимости, поставить задачу генерации HLS.
    """
    if celery is None:
        raise HTTPException(status_code=500, detail="Celery not configured")

    key = key_from_url(data.url)
    if not key.lower().endswith(".mp4"):
        raise HTTPException(status_code=400, detail="Provided object is not an .mp4 file")

    if not mp4_exists(key):
        return ProcessOut(status="source_not_found", key=key)

    if rds.sismember(R_SET_READY, key):
        return ProcessOut(status="already_ready", key=key)

    celery.send_task("app.tasks.process_hls_video", args=[key], queue="special")
    return ProcessOut(status="queued", key=key)

# ============================================================================
# OPTIONAL: ручной запуск полного пересчёта (инициирует Celery таску)
# ============================================================================

@router.post("/hls_recount", status_code=202)
async def trigger_recount():
    if celery is None:
        raise HTTPException(status_code=500, detail="Celery not configured")
    celery.send_task("app.tasks.ensure_hls.recount_hls_counters", queue="special")
    return {"status": "started"}