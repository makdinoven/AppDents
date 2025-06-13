
import asyncio, json, logging
from typing import List, Dict, Any, TypedDict

import aiohttp
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.database import get_async_db                     #  ваша обёртка  :contentReference[oaicite:0]{index=0}
from ..models.models_v2 import Course, Landing          #  модели         :contentReference[oaicite:1]{index=1}

router = APIRouter()

# ---------- типы для читаемого результата ---------- #

class BadCourseVideo(TypedDict):
    course_id: int
    section: str
    lesson: str
    video_link: str

class BadLandingVideo(TypedDict):
    landing_id: int
    lesson: str
    video_link: str

class VideosCheckReport(TypedDict):
    broken_from_courses: List[BadCourseVideo]
    broken_from_landings: List[BadLandingVideo]

# ---------- утилиты ---------- #

OK_STATUSES = {*range(200, 400)}          # 2xx + большинство 3xx

async def probe_url(session: aiohttp.ClientSession, url: str, timeout: int = 10) -> bool:
    """
    HEAD-запрос; True = ссылка доступна.
    •  HEAD → GET fallback для хостов, которые не поддерживают HEAD;
    •  любые исключения => False.
    """
    try:
        async with session.head(url, allow_redirects=True, timeout=timeout) as resp:
            return resp.status in OK_STATUSES
    except (aiohttp.ClientResponseError,
            aiohttp.ClientConnectorError,
            aiohttp.ServerTimeoutError,
            asyncio.TimeoutError):
        # fallback: попробуем GET мелким куском (0 байт)
        try:
            async with session.get(url, allow_redirects=True, timeout=timeout) as resp:
                return resp.status in OK_STATUSES
        except Exception:
            return False
    except Exception:
        return False

# ---------- разбор JSON-полей ---------- #

def extract_from_course(course: Course) -> List[BadCourseVideo]:
    """
    Вернёт плоский список:
       {'course_id': 1, 'section': 'Module 1', 'lesson': 'Lesson 1', 'video_link': '…'}
    """
    result: List[BadCourseVideo] = []
    if not course.sections:
        return result
    try:
        sections: Dict[str, Any] = course.sections
        for sec in sections.values():
            section_name = sec.get("section_name", "<unknown>")
            for lesson in sec.get("lessons", []):
                result.append(
                    {
                        "course_id": course.id,
                        "section":   section_name,
                        "lesson":    lesson.get("lesson_name", ""),
                        "video_link": lesson.get("video_link", ""),
                    }
                )
    except Exception as e:
        logging.warning("Failed to parse course %s sections: %s", course.id, e)
    return result

def extract_from_landing(landing: Landing) -> List[BadLandingVideo]:
    """
    lessons_info = [
         {"lesson1": {"link": "url", "name": "Lesson 1", …}},
         …
    ]
    """
    result: List[BadLandingVideo] = []
    if not landing.lessons_info:
        return result
    try:
        for item in landing.lessons_info:
            # каждый объект содержит ровно один ключ (lesson1, lesson2 …)
            _, info = next(iter(item.items()))
            result.append(
                {
                    "landing_id": landing.id,
                    "lesson": info.get("name", ""),
                    "video_link": info.get("link", ""),
                }
            )
    except Exception as e:
        logging.warning("Failed to parse landing %s lessons_info: %s", landing.id, e)
    return result

# ---------- сам роут ---------- #

@router.get("/video", response_model=VideosCheckReport)
async def check_all_videos(db: AsyncSession = Depends(get_async_db)):
    # 1. достаём JSON-поля одним ходом
    courses: list[Course] = (
        await db.scalars(select(Course))  # теперь приходит полноценный Course
    ).all()

    # landings аналогично
    landings: list[Landing] = (
        await db.scalars(select(Landing))
    ).all()

    # 2. «расплющиваем»
    course_videos   = [*(
        vid for course in courses for vid in extract_from_course(course)
        if vid["video_link"]
    )]
    landing_videos  = [*(
        vid for landing in landings for vid in extract_from_landing(landing)
        if vid["video_link"]
    )]

    # 3. проверяем все ссылки асинхронно
    #    ограничим одновременные запросы до 30 –- достаточный компромисс
    semaphore = asyncio.Semaphore(30)

    async with aiohttp.ClientSession() as session:

        async def guarded_probe(v):
            async with semaphore:
                ok = await probe_url(session, v["video_link"])
                return v, ok

        checks = await asyncio.gather(
            *[guarded_probe(v) for v in course_videos + landing_videos]
        )

    # 4. собираем только плохие
    broken_from_courses  : List[BadCourseVideo]  = [
        v for (v, ok) in checks if not ok and "course_id"  in v
    ]
    broken_from_landings : List[BadLandingVideo] = [
        v for (v, ok) in checks if not ok and "landing_id" in v
    ]

    return {
        "broken_from_courses":  broken_from_courses,
        "broken_from_landings": broken_from_landings,
    }
