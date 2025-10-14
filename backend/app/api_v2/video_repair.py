from typing import Optional, Dict, Any

from fastapi import APIRouter, Query, Body
from celery.result import AsyncResult
from pydantic import BaseModel, HttpUrl
from ..tasks.ensure_hls import validate_and_fix_hls

router = APIRouter()


class HLSValidateFixIn(BaseModel):
    video_url: HttpUrl
    prefer_new: bool = True
    sync: bool = False

def _model_to_dict(m: BaseModel) -> Dict[str, Any]:
    # совместимость Pydantic v1/v2
    if hasattr(m, "model_dump"):   # v2
        return m.model_dump()
    return m.dict()                # v1
@router.post("/validate-fix")
def validate_fix_hls(data: HLSValidateFixIn = Body(...)) -> Dict[str, Any]:
    payload = _model_to_dict(data)
    if data.sync:
        result = validate_and_fix_hls.apply(args=[payload]).get()
        return {"mode": "sync", "result": result}
    else:
        task = validate_and_fix_hls.apply_async(args=[payload], queue="special_hls")
        return {"mode": "async", "task_id": task.id}

@router.get("/repair/{task_id}")
def repair_status(task_id: str):
    ar = AsyncResult(task_id)
    payload = {
        "task_id": task_id,
        "state": ar.state,
        "result": None,
        "traceback": None,
    }
    # если уже готова — это твой финальный dict
    if ar.ready():
        payload["result"] = ar.result
    else:
        # промежуточная мета (если будет)
        payload["result"] = getattr(ar, "info", None)
    if ar.failed():
        payload["traceback"] = ar.traceback
    return payload
