# app/api_v2/clip_generator.py
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from celery.result import AsyncResult

from ..celery_app import celery as celery_app            # ваш существующий Celery инстанс
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
from ..tasks.clip_tasks import clip_video      # таск из шага 1

router = APIRouter()

class ClipIn(BaseModel):
    url: str

@router.post("/clip", status_code=202)
async def submit_clip(data: ClipIn, current_admin: User = Depends(require_roles("admin"))):
    # отправляем задачу в выделенную очередь "clip"
    res = clip_video.apply_async(args=[data.url], queue="special")
    return {"job_id": res.id, "status": "queued"}

@router.get("/clip/{job_id}")
async def clip_status(job_id: str, current_admin: User = Depends(require_roles("admin"))):
    r = celery_app.AsyncResult(job_id)
    state = r.state
    meta = r.info if isinstance(r.info, dict) else {}

    if state == "PENDING":
        return {"status": "queued"}
    if state in ("STARTED", "RETRY", "PROGRESS"):
        return {"status": "processing", **meta}
    if state == "SUCCESS":
        return {"status": "done", **(r.get() or {})}
    if state == "FAILURE":
        return {"status": "error", "error": str(r.result)}
    return {"status": state.lower(), **meta}
