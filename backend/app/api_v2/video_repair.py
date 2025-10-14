from fastapi import APIRouter, Query
from celery.result import AsyncResult
from ..tasks.ensure_hls import repair_hls_for_key

router = APIRouter()

@router.post("/repair")
def repair_hls(
    url: str = Query(..., description="Публичная ссылка на MP4 в CDN (или S3-key)"),
    force_rebuild: bool = Query(False, description="Пересобирать даже если canonical уже есть"),
    purge_legacy_trash: bool = Query(True, description="Удалить старые legacy-сегменты/плейлисты перед сборкой"),
    purge_cdn: bool = Query(True, description="Почистить кэш CDN для плейлистов"),
):
    task = repair_hls_for_key.apply_async(
        (url,),
        kwargs={
            "force_rebuild": force_rebuild,
            "purge_legacy_trash": purge_legacy_trash,
        },
        queue="special_hls",  # тот же heavy-воркер, что и конверсия
    )
    return {"task_id": task.id, "message": "Repair enqueued"}

@router.get("/repair/{task_id}")
def repair_status(task_id: str):
    ar = AsyncResult(task_id)
    return {
        "task_id": task_id,
        "state": ar.state,
        "result": ar.result if ar.ready() else None,
    }
