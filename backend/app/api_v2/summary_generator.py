from typing import Literal, Optional, Any, Dict
import os

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, AnyUrl, Field

import assemblyai as aai

from ..dependencies.role_checker import require_roles
from ..models.models_v2 import User

router = APIRouter()

# --- Конфигурация AssemblyAI ---
AAI_API_KEY = os.getenv("AAI_API_KEY")
DEFAULT_LEMUR_MODEL = os.getenv("AAI_LEMUR_MODEL", "anthropic/claude-3-5-sonnet")

if not AAI_API_KEY:
    raise RuntimeError("AAI_API_KEY is not set")

# --------- Pydantic схемы ----------
LangCode = Literal["auto", "ru", "en", "it", "es"]
OutLang = Literal["auto", "ru", "en", "it", "es"]

class VideoSummaryRequest(BaseModel):
    video_url: AnyUrl = Field(..., description="Публичный или presigned URL на видео/аудио")
    # если хотите форсировать язык, укажите один из: ru/en/it/es; иначе auto
    language_code: LangCode = Field("auto", description="Язык контента: auto|ru|en|it|es")
    # на каком языке вернуть выдержку: по умолчанию auto = как в исходнике
    output_language: OutLang = Field("auto", description="Язык ответа: auto|ru|en|it|es")
    context: Optional[str] = Field(
        "Нужно сделать короткую выдержку о том, про что рассказывается в стоматологическом видео.",
        description="Опциональный контекст для LeMUR"
    )
    answer_format: Optional[str] = Field(
        "",
        description="Опциональный формат ответа (например, '5–7 буллетов, без воды'). По умолчанию пусто."
    )
    # можно переопределить модель для LeMUR
    final_model: Optional[str] = Field(
        DEFAULT_LEMUR_MODEL,
        description="LeMUR final_model, напр. 'anthropic/claude-3-5-sonnet'"
    )

class VideoSummaryResponse(BaseModel):
    summary: Optional[str]
    language_code: Optional[str]
    language_confidence: Optional[float]
    status: str
    transcript_id: Optional[str]
    diagnostics: Optional[Dict[str, Any]] = None


def _to_target_language(detected: Optional[str], forced: LangCode, output: OutLang) -> str:
    """
    Возвращает код языка для итогового текста.
    - Если задан output_language != auto → он.
    - Иначе, если задан language_code != auto → он.
    - Иначе → detected (или 'ru' как разумный дефолт).
    """
    if output != "auto":
        return output
    if forced != "auto":
        return forced
    return (detected or "ru").split("_")[0]  # нормализуем 'en_us' → 'en'


@router.post("/video-summary", response_model=VideoSummaryResponse)
def summarize_video(
    body: VideoSummaryRequest,
    current_admin: User = Depends(require_roles("admin")),
):
    # 1) Настроим конфиг распознавания
    if body.language_code == "auto":
        config = aai.TranscriptionConfig(language_detection=True)
    else:
        # фиксируем язык распознавания
        config = aai.TranscriptionConfig(language_code=body.language_code)

    # 2) Транскрибируем синхронно
    try:
        tr = aai.Transcriber().transcribe(str(body.video_url), config=config)
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Transcription call failed: {e}")

    if tr.status == "error":
        # Ошибки часты при недоступности URL для загрузчика AAI
        return VideoSummaryResponse(
            summary=None,
            language_code=None,
            language_confidence=None,
            status="error",
            transcript_id=getattr(tr, "id", None),
            diagnostics={
                "error": tr.error,
                "hint": (
                    "Проверьте, что ссылка общедоступна без VPN/Referer/Auth. "
                    "Для S3 используйте presigned URL; для приватного контента можно прогнать через /upload."
                ),
            },
        )

    # 3) Язык и длина текста
    lang = getattr(tr, "language_code", None) or tr.json_response.get("language_code")
    conf = getattr(tr, "language_confidence", None) or tr.json_response.get("language_confidence")
    text = tr.text or ""
    text_len = len(text)

    if text_len == 0:
        return VideoSummaryResponse(
            summary=None,
            language_code=lang,
            language_confidence=conf,
            status="ok_but_empty_transcript",
            transcript_id=getattr(tr, "id", None),
            diagnostics={
                "reason": "Пустая транскрипция (тишина/музыка/неразборчивая речь).",
                "text_len": text_len,
                "suggestions": [
                    "Убедитесь, что в видео есть отчётливая речь.",
                    "Если звук очень тихий или с шумом — предварительно улучшите аудио.",
                ],
            },
        )

    # 4) Генерация выдержки через LeMUR на нужном языке
    target_lang = _to_target_language(lang, body.language_code, body.output_language)

    # Создадим LeMUR-клиент с выбранной моделью
    lemur = aai.Lemur(final_model=body.final_model or DEFAULT_LEMUR_MODEL)

    # Если пользователь явно задал answer_format — используем summarize(),
    # иначе используем task() с безопасным дефолтом на 5–7 пунктов.
    try:
        if body.answer_format:
            # В answer_format мы не будем «портить» формат явными инструкциями,
            # поэтому язык укажем через контекст.
            context = (body.context or "").strip()
            if target_lang:
                context += f"\nПожалуйста, ответь на языке: {target_lang}."
            res = lemur.summarize(
                context=context.strip(),
                answer_format=body.answer_format.strip(),
                input=text,
            )
            summary = (res.response or "").strip()
        else:
            # Дефолт: безопасный промпт с требованием языка и короткого формата
            prompt = (
                (body.context or "").strip() + "\n\n"
                f"Сделай краткую выдержку. Ответь на языке: {target_lang}.\n"
                "- Формат: 5–7 кратких пунктов, без воды."
            ).strip()
            res = lemur.task(prompt=prompt, input=text)
            summary = (res.response or "").strip()
    except Exception as e:
        # Если LeMUR не ответил — вернём диагностическую инфу и подсказки
        return VideoSummaryResponse(
            summary=None,
            language_code=lang,
            language_confidence=conf,
            status="lemur_error",
            transcript_id=getattr(tr, "id", None),
            diagnostics={
                "error": str(e),
                "suggestions": [
                    "Проверьте значение final_model (см. список поддерживаемых в ошибке).",
                    "Попробуйте более короткий формат ответа.",
                    "Убедитесь, что AAI_API_KEY имеет доступ к LeMUR.",
                ],
            },
        )

    # 5) Если выдержка пуста — вернём диагностику и подсказки
    if not summary:
        diags = {
            "reason": "LeMUR вернул пустой ответ.",
            "text_len": text_len,
            "language_detected": lang,
            "language_confidence": conf,
            "suggestions": [
                "Уточните answer_format (например: '5–7 буллетов, без воды').",
                "Попробуйте другой final_model (например, anthropic/claude-3-5-haiku-20241022 — быстрее и дешевле).",
                "Проверьте, что в тексте нет сплошного шума/повторов.",
            ],
        }
        # В качестве последнего резерва — отдадим первые 3–5 предложений как «черновой конспект»
        fallback = None
        try:
            import re
            sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
            if sentences:
                fallback = " ".join(sentences[:5])
        except Exception:
            pass

        return VideoSummaryResponse(
            summary=fallback,
            language_code=lang,
            language_confidence=conf,
            status="ok_but_summary_empty_fallback_used" if fallback else "ok_but_summary_empty",
            transcript_id=getattr(tr, "id", None),
            diagnostics=diags,
        )

    # 6) Успешный ответ
    return VideoSummaryResponse(
        summary=summary,
        language_code=lang,
        language_confidence=conf,
        status="ok",
        transcript_id=getattr(tr, "id", None),
        diagnostics=None,
    )
