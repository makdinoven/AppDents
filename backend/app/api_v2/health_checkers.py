# app/api_v2/health_checkers.py
import asyncio, json, logging
from typing import Any, Dict, List

import aiohttp
from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import status

from ..db.database import get_async_db                   # ваша обёртка
from ..models.models_v2 import Course, Landing        # ваши модели

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
