from typing import Optional, Dict, Any

from fastapi import APIRouter, Query, Body
from celery.result import AsyncResult
from pydantic import BaseModel
from ..tasks.ensure_hls import validate_and_fix_hls

router = APIRouter()

class HLSValidateFixIn(BaseModel):
    src_mp4_key: str
    legacy_pl_key: Optional[str] = None
    new_pl_key: Optional[str] = None
    prefer_new: bool = True
    sync: bool = False

@router.post("/validate-fix")
def validate_fix_hls(data: HLSValidateFixIn = Body(...)) -> Dict[str, Any]:
    payload = data.model_dump()
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
