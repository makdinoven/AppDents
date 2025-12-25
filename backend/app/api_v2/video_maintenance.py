from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..dependencies.role_checker import require_roles
from ..db.database import get_db
from ..models.models_v2 import Course, Landing


router = APIRouter()


def _redis():
    import os
    import redis

    return redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)


def _active_task_id_for_lock(lock_key: str) -> Optional[str]:
    """
    Возвращает активный task_id, если он уже запущен и ещё не завершился.
    Если task завершился — чистим lock и возвращаем None.
    """
    rds = _redis()
    task_id = rds.get(lock_key)
    if not task_id:
        return None
    try:
        from celery.result import AsyncResult
        from ..celery_app import celery

        r = AsyncResult(task_id, app=celery)
        if r.ready():
            rds.delete(lock_key)
            return None
        return task_id
    except Exception:
        # если не смогли проверить — пусть будет “активным”, чтобы не плодить дубликаты
        return task_id


def _remember_lock(lock_key: str, task_id: str, *, ttl_sec: int = 6 * 3600) -> None:
    try:
        _redis().set(lock_key, task_id, ex=ttl_sec)
    except Exception:
        pass


def _lock_key_for_course(course_id: int) -> str:
    return f"video_maint:inflight:course:{int(course_id)}"


def _lock_key_for_landing(landing_id: int) -> str:
    return f"video_maint:inflight:landing:{int(landing_id)}"


def _lock_key_for_single_video(video_ref: str) -> str:
    """
    Lock per *normalized* key (hash), чтобы безопасно хранить в Redis.
    """
    import hashlib
    from urllib.parse import unquote
    from ..core.storage import key_from_public_or_endpoint_url

    key = unquote(key_from_public_or_endpoint_url(video_ref).lstrip("/"))
    h = hashlib.sha1(key.encode("utf-8", "ignore")).hexdigest()[:16]
    return f"video_maint:inflight:video:{h}"


class VideoMaintenanceRunPayload(BaseModel):
    videos: List[str] = Field(..., description="Список video_url или s3 key")
    dry_run: bool = Field(default=True, description="Если true — только отчёт, без изменений")
    delete_old_key: bool = Field(default=False, description="Если true — удаляет старый key после успешного rename")


class VideoMaintenanceRunForCoursePayload(BaseModel):
    course_id: int = Field(..., description="ID курса (courses.id)")
    dry_run: bool = Field(default=True, description="Если true — только отчёт, без изменений")
    delete_old_key: bool = Field(default=False, description="Если true — удаляет старый key после успешного rename")


class VideoMaintenanceRunForLandingPayload(BaseModel):
    landing_id: int = Field(..., description="ID лендинга (landings.id)")
    dry_run: bool = Field(default=True, description="Если true — только отчёт, без изменений")
    delete_old_key: bool = Field(default=False, description="Если true — удаляет старый key после успешного rename")


def _is_our_video_ref(v: str) -> bool:
    """
    Фильтр для ссылок из БД: пропускаем только то, что похоже на наши mp4/ключи.
    Сторонние хосты (boomstream/youtube/etc) игнорируем.
    """
    if not v:
        return False
    s = str(v).strip()
    if not s:
        return False

    # raw key
    if "://" not in s:
        return s.lower().endswith(".mp4")

    try:
        from urllib.parse import urlparse

        u = urlparse(s)
        host = (u.hostname or "").lower()
        path = (u.path or "").lower()
        if not path.endswith(".mp4"):
            return False
        if host.endswith(".r2.cloudflarestorage.com"):
            return True
        # допускаем оба домена, т.к. в БД может жить cdn.* или cloud.*
        if host.endswith(".dent-s.com") or host.endswith(".med-g.com"):
            return True
        return False
    except Exception:
        return False


def _normalize_ref_to_input(v: str) -> str:
    """
    Приводим вход к виду, который гарантированно понимает video_maintenance:
    - для R2 endpoint отдаём key (без bucket), чтобы не зависеть от точного endpoint_host
    - иначе отдаём исходную строку (url/key)
    """
    s = str(v).strip()
    if "://" not in s:
        return s
    try:
        from urllib.parse import unquote, urlparse

        u = urlparse(s)
        host = (u.hostname or "").lower()
        if not host.endswith(".r2.cloudflarestorage.com"):
            return s
        # ожидаемый path-style: /<bucket>/<key>
        path = unquote((u.path or "").lstrip("/"))
        from ..core.storage import S3_BUCKET

        if path.lower().startswith(f"{S3_BUCKET.lower()}/"):
            return path[len(S3_BUCKET) + 1 :]
        return path
    except Exception:
        return s


def _extract_course_video_refs(course: Course) -> list[str]:
    refs: list[str] = []
    sections = getattr(course, "sections", None) or {}

    # Ожидаем dict вида {"1": {"lessons": [...]}, ...}
    if isinstance(sections, dict):
        section_objs = list(sections.values())
    elif isinstance(sections, list):
        section_objs = sections
    else:
        section_objs = []

    for sec in section_objs:
        if not isinstance(sec, dict):
            continue
        lessons = sec.get("lessons") or []
        if not isinstance(lessons, list):
            continue
        for lesson in lessons:
            if not isinstance(lesson, dict):
                continue
            v = lesson.get("video_link")
            if isinstance(v, str) and v.strip():
                refs.append(v.strip())
    return refs


def _extract_landing_video_refs(landing: Landing) -> list[str]:
    refs: list[str] = []
    lessons_info = getattr(landing, "lessons_info", None) or []
    if not isinstance(lessons_info, list):
        return refs
    for item in lessons_info:
        if not isinstance(item, dict):
            continue
        # Ожидаем {"lesson1": {"link": "...", ...}}
        for _, payload in item.items():
            if not isinstance(payload, dict):
                continue
            v = payload.get("link")
            if isinstance(v, str) and v.strip():
                refs.append(v.strip())
    return refs


@router.post("/run", dependencies=[Depends(require_roles("admin"))])
def run_video_maintenance(payload: VideoMaintenanceRunPayload) -> Dict[str, Any]:
    """
    Ручной запуск пайплайна на 1–5 видео. Возвращает task_id Celery.
    """
    from ..tasks.video_maintenance import process_list

    # Дедупликация: если запускают фикс одного и того же видео вручную, возвращаем уже запущенную таску.
    if payload.videos and len(payload.videos) == 1:
        lock_key = _lock_key_for_single_video(payload.videos[0])
        active = _active_task_id_for_lock(lock_key)
        if active:
            return {
                "status": "already_running",
                "task_id": active,
                "dry_run": payload.dry_run,
                "delete_old_key": payload.delete_old_key,
            }

    # Pydantic v1/v2 compatibility
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()  # type: ignore[attr-defined]
    else:
        data = payload.dict()  # pydantic v1

    task = process_list.apply_async(kwargs={"payload": data}, queue="special_priority")
    if payload.videos and len(payload.videos) == 1:
        _remember_lock(_lock_key_for_single_video(payload.videos[0]), task.id)
    return {"status": "queued", "task_id": task.id, "dry_run": payload.dry_run, "delete_old_key": payload.delete_old_key}


@router.post("/run-course", dependencies=[Depends(require_roles("admin"))])
def run_video_maintenance_for_course(
    payload: VideoMaintenanceRunForCoursePayload,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Запускает maintenance для ВСЕХ видео, привязанных к одному курсу (courses.sections).
    Берём ссылки ИЗ БД (несохранённые правки в UI сюда не попадут — сперва сохраните курс).
    """
    from ..tasks.video_maintenance import process_list

    lock_key = _lock_key_for_course(payload.course_id)
    active = _active_task_id_for_lock(lock_key)
    if active:
        return {
            "status": "already_running",
            "task_id": active,
            "entity": "course",
            "entity_id": payload.course_id,
            "dry_run": payload.dry_run,
            "delete_old_key": payload.delete_old_key,
        }

    course = db.query(Course).filter(Course.id == payload.course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="Course not found")

    raw_refs = _extract_course_video_refs(course)
    vids = [_normalize_ref_to_input(v) for v in raw_refs if _is_our_video_ref(v)]
    uniq: list[str] = list(dict.fromkeys(vids))  # дедуп с сохранением порядка

    data = {"videos": uniq, "dry_run": payload.dry_run, "delete_old_key": payload.delete_old_key}
    task = process_list.apply_async(kwargs={"payload": data}, queue="special_priority")
    _remember_lock(lock_key, task.id)
    return {
        "status": "queued",
        "task_id": task.id,
        "entity": "course",
        "entity_id": payload.course_id,
        "dry_run": payload.dry_run,
        "delete_old_key": payload.delete_old_key,
        "videos_total_in_entity": len(raw_refs),
        "videos_selected": len(uniq),
        "videos_sample": uniq[:20],
    }


@router.post("/run-landing", dependencies=[Depends(require_roles("admin"))])
def run_video_maintenance_for_landing(
    payload: VideoMaintenanceRunForLandingPayload,
    db: Session = Depends(get_db),
) -> Dict[str, Any]:
    """
    Запускает maintenance для ВСЕХ видео, привязанных к одному лендингу (landings.lessons_info).
    Берём ссылки ИЗ БД (несохранённые правки в UI сюда не попадут — сперва сохраните лендинг).
    """
    from ..tasks.video_maintenance import process_list

    lock_key = _lock_key_for_landing(payload.landing_id)
    active = _active_task_id_for_lock(lock_key)
    if active:
        return {
            "status": "already_running",
            "task_id": active,
            "entity": "landing",
            "entity_id": payload.landing_id,
            "dry_run": payload.dry_run,
            "delete_old_key": payload.delete_old_key,
        }

    landing = db.query(Landing).filter(Landing.id == payload.landing_id).first()
    if not landing:
        raise HTTPException(status_code=404, detail="Landing not found")

    raw_refs = _extract_landing_video_refs(landing)
    vids = [_normalize_ref_to_input(v) for v in raw_refs if _is_our_video_ref(v)]
    uniq: list[str] = list(dict.fromkeys(vids))

    data = {"videos": uniq, "dry_run": payload.dry_run, "delete_old_key": payload.delete_old_key}
    task = process_list.apply_async(kwargs={"payload": data}, queue="special_priority")
    _remember_lock(lock_key, task.id)
    return {
        "status": "queued",
        "task_id": task.id,
        "entity": "landing",
        "entity_id": payload.landing_id,
        "dry_run": payload.dry_run,
        "delete_old_key": payload.delete_old_key,
        "videos_total_in_entity": len(raw_refs),
        "videos_selected": len(uniq),
        "videos_sample": uniq[:20],
    }


@router.get("/status", dependencies=[Depends(require_roles("admin"))])
def video_maintenance_status(task_id: str) -> Dict[str, Any]:
    """
    Polling статуса Celery таски (минимальный интерфейс).
    """
    from celery.result import AsyncResult
    from ..celery_app import celery

    r = AsyncResult(task_id, app=celery)
    meta = None
    if not r.ready():
        # Celery кладёт сюда то, что мы передаём в update_state(meta=...)
        try:
            meta = r.info
        except Exception:
            meta = None
    return {
        "task_id": task_id,
        "state": r.state,
        "ready": r.ready(),
        "successful": r.successful() if r.ready() else None,
        "result": r.result if r.ready() else None,
        "meta": meta,
    }


@router.get("/audit", dependencies=[Depends(require_roles("admin"))])
def video_maintenance_audit(limit: int = 50) -> Dict[str, Any]:
    """
    Возвращает последние записи аудита из Redis (для быстрой диагностики).
    """
    import json
    import os

    import redis

    rds = redis.Redis.from_url(os.getenv("REDIS_URL", "redis://redis:6379/0"), decode_responses=True)
    raw = rds.lrange("video_maint:audit", 0, max(0, min(limit, 200) - 1))
    items = []
    for s in raw:
        try:
            items.append(json.loads(s))
        except Exception:
            items.append({"raw": s})
    return {"count": len(items), "items": items}


