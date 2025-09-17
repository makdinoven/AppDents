from typing import Literal, Optional, Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status, Request
from pydantic import BaseModel, AnyUrl, Field
from celery.result import AsyncResult
import os

from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User
# ВАЖНО: импортируйте именно вашу точку входа Celery
# Ниже предполагается, что Celery-инстанс находится в app.celery_app: celery
from ..celery_app import celery  # поправьте путь, если отличается

LangCode = Literal["auto", "ru", "en", "it", "es"]
OutLang = Literal["auto", "ru", "en", "it", "es"]

router = APIRouter()

DEFAULT_LEMUR_MODEL = os.getenv("AAI_LEMUR_MODEL", "anthropic/claude-3-5-sonnet")

class VideoSummaryRequest(BaseModel):
    video_url: AnyUrl
    language_code: LangCode = Field("auto", description="Язык контента: auto|ru|en|it|es")
    output_language: OutLang = Field("auto", description="Язык ответа: auto|ru|en|it|es")
    context: Optional[str] = Field(  # <-- было: дефолтная строка; стало: None
        None,
        description="Опционально: уточнение редактора (добавится к базовому промпту)",
    )
    answer_format: Optional[str] = Field(  # <-- тоже None
        None,
        description="Опционально: формат ответа; добавим наши ограничения стиля",
    )
    final_model: Optional[str] = Field(
        DEFAULT_LEMUR_MODEL, description="LeMUR final_model"
    )


class EnqueueResponse(BaseModel):
    task_id: str
    status_url: str

class JobStatusResponse(BaseModel):
    task_id: str
    state: str
    result: Optional[Dict[str, Any]] = None
    progress: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


@router.post("/video-summary", response_model=EnqueueResponse, status_code=status.HTTP_202_ACCEPTED)
def enqueue_video_summary(
    body: VideoSummaryRequest,
    request: Request,
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Ставит задачу в Celery и возвращает task_id + URL для опроса статуса.
    """
    try:
        async_result = celery.send_task(
            "app.tasks.video_summary.summarize_video_task",
            kwargs={
                "video_url": str(body.video_url),
                "language_code": body.language_code,
                "output_language": body.output_language,
                "context": body.context or "",  # None → ""
                "answer_format": body.answer_format or "",  # None → ""
                "final_model": body.final_model or DEFAULT_LEMUR_MODEL,
            },
            queue="special",
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Failed to enqueue task: {e}")

    # Сформируем URL статуса
    base = str(request.base_url).rstrip("/")
    status_url = f"{base}/admin/ai/video-summary/{async_result.id}"

    return EnqueueResponse(task_id=async_result.id, status_url=status_url)


@router.get("/video-summary/{task_id}", response_model=JobStatusResponse)
def get_video_summary_status(
    task_id: str,
    current_admin: User = Depends(require_roles("admin")),
):
    """
    Возвращает состояние задачи Celery и результат (когда готов).
    """
    result = AsyncResult(task_id, app=celery)

    state = result.state  # PENDING | STARTED | PROGRESS | SUCCESS | FAILURE | ...
    payload: Dict[str, Any] = {}

    if state == "PENDING":
        return JobStatusResponse(task_id=task_id, state=state)

    if state in ("STARTED", "PROGRESS"):
        meta = result.info if isinstance(result.info, dict) else {}
        return JobStatusResponse(task_id=task_id, state=state, progress=meta)

    if state == "SUCCESS":
        data = result.get(propagate=False)  # словарь из summarize_video_task (VideoSummaryResponse-совместимый)
        return JobStatusResponse(task_id=task_id, state=state, result=data)

    if state == "FAILURE":
        err = str(result.info) if result.info else "unknown error"
        return JobStatusResponse(task_id=task_id, state=state, error=err)

    # Прочие нестандартные статусы
    meta = result.info if isinstance(result.info, dict) else {}
    return JobStatusResponse(task_id=task_id, state=state, progress=meta)
