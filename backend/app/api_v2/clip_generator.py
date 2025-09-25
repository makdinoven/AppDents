# app/api_v2/clip_generator.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult

from ..celery_app import celery as celery_app
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
from ..tasks.clip_tasks import clip_video

router = APIRouter()

class ClipIn(BaseModel):
    url: str

# --- NEW: контроль того, что всегда возвращаем debug-поля
ALWAYS_INCLUDE_DEBUG = True

# --- NEW: какие поля считаем “базовыми” (контракт совместим)
BASE_META_KEYS = {
    "stage", "uploaded_bytes", "elapsed_sec", "speed_bytes_per_sec",
    "clip_url", "length_sec", "path", "validated",
    "source_bytes", "downloaded_bytes", "download_bps", "faststart",
    "attempt",
    # можешь добавлять сюда поля, на которые опирается UI
}

def _split_meta(meta: dict):
    """Разделяем мету на базовую и отладочную."""
    base = {k: v for k, v in meta.items() if k in BASE_META_KEYS}
    debug = {k: v for k, v in meta.items() if k not in BASE_META_KEYS}
    return base, debug

@router.post("/clip", status_code=202)
async def submit_clip(data: ClipIn, current_admin: User = Depends(require_roles("admin"))):
    res = clip_video.apply_async(args=[data.url], queue="default")
    return {"job_id": res.id, "status": "queued"}

@router.get("/clip/{job_id}")
async def clip_status(job_id: str, current_admin: User = Depends(require_roles("admin"))):
    r = celery_app.AsyncResult(job_id)
    state = r.state
    meta = r.info if isinstance(r.info, dict) else {}
    base_meta, debug_meta = _split_meta(meta)

    if state == "PENDING":
        resp = {"status": "queued"}
    elif state in ("STARTED", "RETRY", "PROGRESS"):
        resp = {"status": "processing", **base_meta}
        if ALWAYS_INCLUDE_DEBUG and debug_meta:
            resp["debug"] = debug_meta
    elif state == "SUCCESS":
        # Итоговый результат как раньше (контракт не меняем)
        payload = (r.get() or {})
        resp = {"status": "done", **payload}
        # Опционально: можно вернуть финальный debug, если остался
        if ALWAYS_INCLUDE_DEBUG and debug_meta:
            resp.setdefault("debug", debug_meta)
    elif state == "FAILURE":
        resp = {"status": "error", "error": str(r.result)}
    else:
        resp = {"status": state.lower(), **base_meta}
        if ALWAYS_INCLUDE_DEBUG and debug_meta:
            resp["debug"] = debug_meta

    return resp
