
from typing import Optional, Dict, Any, Literal
import os
import re
import time
import assemblyai as aai
from celery import shared_task
import requests

from ..core.config import settings

# ================== ENV / конфиг ==================
AAI_API_KEY = os.getenv("AAI_API_KEY")

if not AAI_API_KEY:
    raise RuntimeError("AAI_API_KEY is not set")

LangCode = Literal["auto", "ru", "en", "it", "es"]
OutLang = Literal["auto", "ru", "en", "it", "es"]


# ================== Хелперы ==================
def _to_target_language(detected: Optional[str], forced: LangCode, output: OutLang) -> str:
    if output != "auto":
        return output
    if forced != "auto":
        return forced
    return (detected or "ru").split("_")[0]  # 'en_us' → 'en'

def _bookai_full_url(path_or_url: str) -> str:
    """
    Склеиваем URL для BookAI.
    settings.BOOKAI_BASE_URL может уже содержать '/api'.
    path_or_url может быть абсолютным URL или относительным путём.
    """
    raw = (path_or_url or "").strip()
    if raw.startswith("http://") or raw.startswith("https://"):
        return raw
    base = settings.BOOKAI_BASE_URL.rstrip("/")
    # Если base уже с '/api', а путь тоже начинается с '/api/...', не дублируем.
    if base.endswith("/api") and raw.startswith("/api/"):
        raw = raw[len("/api"):]  # оставляем ведущий '/'
    if raw.startswith("/"):
        return f"{base}{raw}"
    return f"{base}/{raw}"


def _bookai_enqueue(*, language: str, text: str) -> Dict[str, Any]:
    url = _bookai_full_url("/api/v1/video-summary")
    resp = requests.post(url, json={"language": language, "text": text}, timeout=30)
    resp.raise_for_status()
    data = resp.json() if resp.content else {}
    task_id = data.get("task_id")
    if not task_id:
        raise RuntimeError(f"BookAI enqueue: no task_id in response: {data}")
    status_url = data.get("status_url") or f"/api/v1/video-summary/{task_id}"
    return {"task_id": task_id, "status_url": status_url}


def _bookai_poll(*, status_url: str, max_wait_s: int, poll_interval_s: float, on_progress):
    """
    Ожидаем SUCCESS/FAILURE от BookAI, прокидывая прогресс наружу.
    on_progress: callable(meta: dict) -> None
    """
    started = time.time()
    last_state = None
    while True:
        elapsed = int(time.time() - started)
        if elapsed > max_wait_s:
            raise TimeoutError(f"BookAI poll timeout after {elapsed}s")

        url = _bookai_full_url(status_url)
        resp = requests.get(url, timeout=30)
        resp.raise_for_status()
        data = resp.json() if resp.content else {}

        state = (data.get("state") or "").upper().strip()
        if state:
            last_state = state

        if last_state == "SUCCESS":
            summary = (data.get("summary") or "").strip()
            if not summary:
                raise RuntimeError("BookAI returned SUCCESS but summary is empty")
            return summary

        if last_state == "FAILURE":
            raise RuntimeError(data.get("error") or "BookAI failure")

        progress = data.get("progress") if isinstance(data.get("progress"), dict) else {}
        on_progress({
            "stage": "bookai_polling",
            "bookai_state": last_state or "UNKNOWN",
            "progress": progress,
            "elapsed_s": elapsed,
        })
        time.sleep(poll_interval_s)

# ================== Celery task ==================
@shared_task(
    name="app.tasks.video_summary.summarize_video_task",
    bind=True,
    track_started=True,
    soft_time_limit=30 * 60,
    time_limit=45 * 60,
    autoretry_for=(),
    default_retry_delay=30,
    max_retries=0,
    queue="default",
)
def summarize_video_task(
    self,
    *,
    video_url: str,
    language_code: LangCode = "auto",
    output_language: OutLang = "auto",
    context: str = "Нужно сделать короткую выдержку о том, про что рассказывается в видео.",
    answer_format: str = "",
    final_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Результат: словарь, совместимый с VideoSummaryResponse (из API-роута)
    """
    # Настройка SDK
    aai.settings.api_key = AAI_API_KEY

    self.update_state(state="STARTED", meta={"stage": "transcription_requested"})

    # 1) Конфиг распознавания
    if language_code == "auto":
        cfg = aai.TranscriptionConfig(language_detection=True)
    else:
        cfg = aai.TranscriptionConfig(language_code=language_code)

    # 2) Транскрибация
    try:
        tr = aai.Transcriber().transcribe(video_url, config=cfg)
    except Exception as e:
        return {
            "summary": None,
            "language_code": None,
            "language_confidence": None,
            "status": "error",
            "transcript_id": None,
            "diagnostics": {
                "error": f"Transcription call failed: {e}",
                "hint": "Проверьте доступность URL (без VPN/Referer/Auth). Для S3 используйте presigned URL или загрузку через /upload.",
            },
        }

    if tr.status == "error":
        return {
            "summary": None,
            "language_code": None,
            "language_confidence": None,
            "status": "error",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "error": tr.error,
                "hint": "Проверьте, что ссылка общедоступна (или используйте presigned URL / /upload).",
            },
        }

    # 3) Язык и текст
    lang = getattr(tr, "language_code", None) or tr.json_response.get("language_code")
    conf = getattr(tr, "language_confidence", None) or tr.json_response.get("language_confidence")
    text = tr.text or ""
    text_len = len(text)

    self.update_state(state="PROGRESS", meta={
        "stage": "transcription_done",
        "language_code": lang,
        "language_confidence": conf,
        "text_len": text_len,
    })

    if text_len == 0:
        return {
            "summary": None,
            "language_code": lang,
            "language_confidence": conf,
            "status": "ok_but_empty_transcript",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "reason": "Пустая транскрипция (тишина/музыка/неразборчивая речь).",
                "text_len": text_len,
                "suggestions": [
                    "Убедитесь в наличии отчётливой речи.",
                    "Если звук тихий/шумный — улучшите аудио.",
                ],
            },
        }

    # 4) BookAI (LLM-саммари): отправляем язык+текст и ждём готовности, прокидывая прогресс.
    self.update_state(state="PROGRESS", meta={"stage": "bookai_enqueue"})

    target_lang = _to_target_language(lang, language_code, output_language)

    try:
        enq = _bookai_enqueue(language=target_lang, text=text)
        bookai_task_id = enq["task_id"]
        status_url = enq["status_url"]
    except Exception as e:
        return {
            "summary": None,
            "language_code": lang,
            "language_confidence": conf,
            "status": "bookai_error",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "error": f"BookAI enqueue failed: {e}",
                "bookai_base_url": settings.BOOKAI_BASE_URL,
            },
        }

    self.update_state(state="PROGRESS", meta={
        "stage": "bookai_queued",
        "bookai_task_id": bookai_task_id,
    })

    def _progress(meta: Dict[str, Any]):
        # meta включает progress от bookai (stage/percent/message)
        self.update_state(state="PROGRESS", meta={
            "stage": meta.get("stage") or "bookai_polling",
            "bookai_task_id": bookai_task_id,
            "bookai_state": meta.get("bookai_state"),
            "bookai_progress": meta.get("progress"),
            "elapsed_s": meta.get("elapsed_s"),
        })

    try:
        summary = _bookai_poll(
            status_url=status_url,
            max_wait_s=25 * 60,      # 25 минут (внутри time_limit=45 мин)
            poll_interval_s=2.0,     # частый polling внутри воркера
            on_progress=_progress,
        )
    except Exception as e:
        return {
            "summary": None,
            "language_code": lang,
            "language_confidence": conf,
            "status": "bookai_error",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "error": f"BookAI polling failed: {e}",
                "bookai_task_id": bookai_task_id,
            },
        }

    self.update_state(state="PROGRESS", meta={"stage": "bookai_done", "bookai_task_id": bookai_task_id})
    return {
        "summary": summary,
        "language_code": lang,
        "language_confidence": conf,
        "status": "ok",
        "transcript_id": getattr(tr, "id", None),
        "diagnostics": None,
    }
