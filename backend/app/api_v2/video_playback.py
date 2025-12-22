import time
from typing import Any, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel

from ..dependencies.auth import get_current_user
from ..models.models_v2 import User

# Хелперы из admin video_diagnostics (уже умеют доставать key из URL и читать S3 metadata)
from .video_diagnostics import (
    key_from_url,
    check_s3_object,
    safe_cdn_url,
    check_moov_position,
)

# IP берём так же, как в users.py (аналог getclientip)
from ..services_v2.ban_service import get_client_ip

router = APIRouter()

# Простой анти-спам/дедуп на уровне процесса — как локальный кулдаун по s3_key
_RECENT_FASTSTART_REQUESTS: Dict[str, float] = {}
_FASTSTART_COOLDOWN_SEC = 10 * 60  # 10 минут


class RequestFaststartPayload(BaseModel):
    video_url: str
    reason: Optional[str] = None  # диагностическая причина (stalled/startup/etc)


class FaststartStatusResponse(BaseModel):
    video_url: str
    s3_key: str
    faststart: bool
    task_id: Optional[str] = None
    task_state: Optional[str] = None
    task_ready: Optional[bool] = None
    task_successful: Optional[bool] = None
    task_failed: Optional[bool] = None
    message: Optional[str] = None


@router.post("/request-faststart")
def request_faststart(
    payload: RequestFaststartPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Пользовательский endpoint: ставит задачу "faststart" (перенос moov atom в начало)
    в очередь, если видео ещё не помечено metadata faststart=true.

    Требует авторизацию (как и остальные пользовательские ручки).
    Локальный кулдаун по s3_key — чтобы не заспамить очередь.
    """
    client_ip = get_client_ip(request)  # пока только для логов/диагностики

    s3_key = key_from_url(payload.video_url)
    low = s3_key.lower()
    if not (low.endswith(".mp4") or low.endswith(".mov")):
        raise HTTPException(status_code=400, detail="Only mp4/mov supported")

    check = check_s3_object(s3_key)
    if check.status == "error":
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {check.message}",
        )

    if check.details.get("faststart") == "true":
        return {
            "status": "skipped",
            "message": "Already faststart",
            "s3_key": s3_key,
        }

    now = time.time()
    last = _RECENT_FASTSTART_REQUESTS.get(s3_key, 0.0)
    if now - last < _FASTSTART_COOLDOWN_SEC:
        return {
            "status": "cooldown",
            "message": "Faststart already requested recently",
            "s3_key": s3_key,
        }

    _RECENT_FASTSTART_REQUESTS[s3_key] = now

    from ..tasks.fast_start import process_faststart_video

    task = process_faststart_video.apply_async(args=[s3_key], queue="special")

    return {
        "status": "queued",
        "task_id": task.id,
        "s3_key": s3_key,
        "reason": payload.reason,
        "message": "Faststart task queued",
    }


@router.post("/ensure-faststart")
def ensure_faststart(
    payload: RequestFaststartPayload,
    request: Request,
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    """
    Более надёжный user-endpoint:

    - Проверяет S3 metadata faststart
    - Если faststart неизвестен/false — делает server-side check moov-position
    - Ставит задачу только если moov после mdat (faststart реально нужен)

    Требует авторизацию. Локальный кулдаун по s3_key.
    """
    client_ip = get_client_ip(request)

    s3_key = key_from_url(payload.video_url)
    low = s3_key.lower()
    if not (low.endswith(".mp4") or low.endswith(".mov")):
        raise HTTPException(status_code=400, detail="Only mp4/mov supported")

    check = check_s3_object(s3_key)
    if check.status == "error":
        raise HTTPException(
            status_code=404,
            detail=f"Video not found: {check.message}",
        )

    if check.details.get("faststart") == "true":
        return {
            "status": "skipped",
            "message": "Already faststart",
            "s3_key": s3_key,
        }

    now = time.time()
    last = _RECENT_FASTSTART_REQUESTS.get(s3_key, 0.0)
    if now - last < _FASTSTART_COOLDOWN_SEC:
        return {
            "status": "cooldown",
            "message": "Faststart already requested recently",
            "s3_key": s3_key,
        }

    # Server-side moov check
    cdn_url = safe_cdn_url(s3_key)
    moov = check_moov_position(cdn_url)
    details = moov.details or {}
    moov_pos = details.get("moov_position")
    mdat_pos = details.get("mdat_position")

    if isinstance(moov_pos, int) and isinstance(mdat_pos, int) and moov_pos < mdat_pos:
        return {
            "status": "skipped",
            "message": "faststart OK (moov before mdat)",
            "s3_key": s3_key,
        }

    # moov после mdat — faststart нужен, ставим задачу
    if isinstance(moov_pos, int) and isinstance(mdat_pos, int) and moov_pos > mdat_pos:
        _RECENT_FASTSTART_REQUESTS[s3_key] = now

        from ..tasks.fast_start import process_faststart_video

        task = process_faststart_video.apply_async(args=[s3_key], queue="special")

        return {
            "status": "queued",
            "task_id": task.id,
            "s3_key": s3_key,
            "reason": payload.reason,
            "message": "Faststart task queued (moov after mdat)",
        }

    # Не смогли надёжно определить — не создаём задач автоматически
    return {
        "status": "unknown",
        "message": moov.message,
        "s3_key": s3_key,
        "details": details,
    }


@router.get("/faststart-status", response_model=FaststartStatusResponse)
def faststart_status(
    video_url: str = Query(..., description="URL видео"),
    task_id: Optional[str] = Query(
        default=None,
        description="Celery task id (если есть)",
    ),
    current_user: User = Depends(get_current_user),
) -> FaststartStatusResponse:
    """
    Авторизованный polling статуса faststart по video_url и (опционально) task_id.
    """
    s3_key = key_from_url(video_url)
    check = check_s3_object(s3_key)
    faststart = check.details.get("faststart") == "true"

    # Если faststart уже появился в metadata — считаем готово независимо от task state
    if faststart:
        return FaststartStatusResponse(
            video_url=video_url,
            s3_key=s3_key,
            faststart=True,
            task_id=task_id,
            task_state="SUCCESS",
            task_ready=True,
            task_successful=True,
            task_failed=False,
            message="faststart metadata is true",
        )

    if not task_id:
        return FaststartStatusResponse(
            video_url=video_url,
            s3_key=s3_key,
            faststart=False,
            task_id=None,
            task_state=None,
            task_ready=None,
            task_successful=None,
            task_failed=None,
            message="faststart not applied yet",
        )

    from ..celery_app import celery as celery_app

    r = celery_app.AsyncResult(task_id)
    state = getattr(r, "state", None)
    ready = bool(r.ready())
    successful = bool(r.successful()) if ready else False
    failed = bool(r.failed()) if ready else False

    return FaststartStatusResponse(
        video_url=video_url,
        s3_key=s3_key,
        faststart=False,
        task_id=task_id,
        task_state=state,
        task_ready=ready,
        task_successful=successful if ready else None,
        task_failed=failed if ready else None,
        message=(
            "queued"
            if state in ("PENDING", "RECEIVED")
            else "running"
            if state in ("STARTED", "RETRY")
            else None
        ),
    )
