# app/api_v2/clip_generator.py
import os
from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from celery.result import AsyncResult

from ..celery_app import celery as celery_app
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
from ..tasks.clip_tasks import clip_video

router = APIRouter()

# Очередь можно задать через ENV, по умолчанию "default"
CLIP_QUEUE = os.getenv("CLIP_QUEUE", "default")

class ClipIn(BaseModel):
    # Не делаем строгий HttpUrl, чтобы не сломать presigned/CDN-ссылки с пробелами и пр.
    url: str

@router.post("/clip", status_code=202)
async def submit_clip(
    data: ClipIn,
    current_admin: User = Depends(require_roles("admin")),
):
    # Отправляем задачу в настраиваемую очередь (по умолчанию "default")
    res = clip_video.apply_async(args=[data.url], queue=CLIP_QUEUE)
    return {"job_id": res.id, "status": "queued"}

@router.get("/clip/{job_id}")
async def clip_status(
    job_id: str,
    current_admin: User = Depends(require_roles("admin")),
    debug: bool = Query(True, description="Вернуть расширенную отладочную информацию (не влияет на контракт по умолчанию)"),
):
    r: AsyncResult = celery_app.AsyncResult(job_id)
    state = r.state
    meta = r.info if isinstance(r.info, dict) else {}

    # Опциональная отладка — только если явно запросили ?debug=1
    if debug:
        dbg = {}
        try:
            dbg["raw_state"] = state
            dbg["ready"] = r.ready()
            dbg["successful"] = bool(r.successful()) if r.ready() else None
            # Некоторые бекенды дают date_done
            dbg["date_done"] = getattr(r, "date_done", None)

            # Сырые данные из бекенда Celery (если доступны)
            try:
                raw = r.backend.get_task_meta(job_id)  # может бросать, поэтому отдельно
                dbg["backend_state"] = raw.get("status")
                tb = (raw.get("traceback") or "") if isinstance(raw, dict) else ""
                if tb:
                    # последние строки трейсбэка, чтобы не раздувать ответ
                    dbg["traceback_tail"] = tb.splitlines()[-10:]
            except Exception:
                pass

        except Exception:
            # Отладка никогда не должна ронять эндпоинт
            pass

        # Встраиваем _debug внутрь meta, чтобы не менять верхнеуровневый контракт
        if isinstance(meta, dict):
            meta = {**meta, "_debug": dbg}
        else:
            meta = {"_debug": dbg}

    if state == "PENDING":
        return {"status": "queued"}
    if state in ("STARTED", "RETRY", "PROGRESS"):
        # Контракт: "status": "processing" + весь meta из update_state
        return {"status": "processing", **meta}
    if state == "SUCCESS":
        # Контракт: "status": "done" + результат таски
        return {"status": "done", **(r.get() or {})}
    if state == "FAILURE":
        # Контракт: "status": "error" + строка ошибки
        return {"status": "error", "error": str(r.result)}

    # На всякий — возвращаем состояние как есть (в нижнем регистре) и meta
    return {"status": state.lower(), **(meta if isinstance(meta, dict) else {})}
