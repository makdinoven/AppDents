# app/api_v2/video_repair.py (или где у тебя роут)
from typing import Dict, Any
from fastapi import APIRouter, Body
from pydantic import BaseModel
from celery.result import AsyncResult

from ..celery_app import celery as celery_app
from ..tasks.ensure_hls import validate_and_fix_hls

router = APIRouter()

class HLSValidateFixIn(BaseModel):
    video_url: str  # только строка; пробелы допустимы (как в ключах)

def _model_to_dict(m: BaseModel) -> Dict[str, Any]:
    return m.model_dump() if hasattr(m, "model_dump") else m.dict()

@router.post("/validate-fix")
def validate_fix_hls(data: HLSValidateFixIn = Body(...)) -> Dict[str, Any]:
    payload = _model_to_dict(data)
    # всегда асинхронно; очередь «hls»
    task = validate_and_fix_hls.apply_async(args=[payload], queue="special_hls")
    return {"mode": "async", "task_id": task.id}

@router.get("/repair/{task_id}")
def repair_status(task_id: str):
    ar = AsyncResult(task_id, app=celery_app)
    payload = {
        "task_id": task_id,
        "state": ar.state,
        "result": ar.result if ar.ready() else getattr(ar, "info", None),
        "traceback": ar.traceback if ar.failed() else None,
    }
    return payload
