# app/api_v2/clip_generator.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult

from ..celery_app import celery as celery_app            # ваш существующий Celery инстанс
from ..tasks.clip_tasks import clip_video      # таск из шага 1

router = APIRouter(prefix="/api/clip_generator")

class ClipIn(BaseModel):
    url: str

@router.post("/clip", status_code=202)
async def submit_clip(data: ClipIn):
    # отправляем задачу в выделенную очередь "clip"
    res = clip_video.apply_async(args=[data.url], queue="special")
    return {"job_id": res.id, "status": "queued"}

@router.get("/clip/{job_id}")
async def clip_status(job_id: str):
    r = AsyncResult(job_id, app=celery_app)
    state = r.state
    if state == "PENDING":
        return {"status": "queued"}
    if state in ("STARTED", "RETRY"):
        return {"status": "processing"}
    if state == "SUCCESS":
        result = r.get()  # {"clip_url": ..., "length_sec": 300}
        return {"status": "done", **result}
    if state == "FAILURE":
        # r.result — Exception, приведём к строке
        return {"status": "error", "error": str(r.result)}
    return {"status": state.lower()}
