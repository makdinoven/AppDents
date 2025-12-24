from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from ..dependencies.role_checker import require_roles


router = APIRouter()


class VideoMaintenanceRunPayload(BaseModel):
    videos: List[str] = Field(..., description="Список video_url или s3 key")
    dry_run: bool = Field(default=True, description="Если true — только отчёт, без изменений")
    delete_old_key: bool = Field(default=False, description="Если true — удаляет старый key после успешного rename")


@router.post("/run", dependencies=[Depends(require_roles("admin"))])
def run_video_maintenance(payload: VideoMaintenanceRunPayload) -> Dict[str, Any]:
    """
    Ручной запуск пайплайна на 1–5 видео. Возвращает task_id Celery.
    """
    from ..tasks.video_maintenance import process_list

    # Pydantic v1/v2 compatibility
    if hasattr(payload, "model_dump"):
        data = payload.model_dump()  # type: ignore[attr-defined]
    else:
        data = payload.dict()  # pydantic v1

    task = process_list.apply_async(kwargs={"payload": data}, queue="special")
    return {"status": "queued", "task_id": task.id, "dry_run": payload.dry_run, "delete_old_key": payload.delete_old_key}


@router.get("/status", dependencies=[Depends(require_roles("admin"))])
def video_maintenance_status(task_id: str) -> Dict[str, Any]:
    """
    Polling статуса Celery таски (минимальный интерфейс).
    """
    from celery.result import AsyncResult
    from ..celery_app import celery

    r = AsyncResult(task_id, app=celery)
    return {
        "task_id": task_id,
        "state": r.state,
        "ready": r.ready(),
        "successful": r.successful() if r.ready() else None,
        "result": r.result if r.ready() else None,
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


