from typing import Optional, Dict, Any, Literal
import os
import re
import assemblyai as aai
from celery import shared_task

# ENV
AAI_API_KEY = os.getenv("AAI_API_KEY")
DEFAULT_LEMUR_MODEL = os.getenv("AAI_LEMUR_MODEL", "anthropic/claude-3-5-sonnet")

if not AAI_API_KEY:
    raise RuntimeError("AAI_API_KEY is not set")

LangCode = Literal["auto", "ru", "en", "it", "es"]
OutLang = Literal["auto", "ru", "en", "it", "es"]

DEFAULT_MARKETING_PROMPT = """
Ты — ассистент, который делает краткие, маркетинговые выжимки по стоматологическим видеоурокам.
Твоя цель — внятно и интересно показать СУТЬ курса, не раскрывая деталей.

Правила:
• Не давай пошаговых инструкций, цифр, марок инструментов, названий материалов, конкретных углов/толщин/скоростей и т.п.
• Избегай «жёстких» клинических рекомендаций; держись уровня тем и результатов обучения.
• Пиши живо, но без хайпа и громких эпитетов.

Формат ответа:
- Короткое описание: 2–5 предложений, чему научится зритель и о чем вообще этот курс.

Ответь на языке: {target_lang}.
""".strip()


def _to_target_language(detected: Optional[str], forced: LangCode, output: OutLang) -> str:
    if output != "auto":
        return output
    if forced != "auto":
        return forced
    return (detected or "ru").split("_")[0]  # 'en_us' → 'en'

def _fallback_summary(text: str) -> Optional[str]:
    try:
        sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", text) if s.strip()]
        return " ".join(sentences[:5]) if sentences else None
    except Exception:
        return None

@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=30 * 60,  # мягкий таймаут 30 мин
    time_limit=45 * 60,       # жёсткий таймаут 45 мин
    autoretry_for=(),         # без автоповторов по умолчанию
    default_retry_delay=30,
    max_retries=0,
    queue="special",          # отправляем в вашу "special" очередь
)
def summarize_video_task(
    self,
    *,
    video_url: str,
    language_code: LangCode = "auto",
    output_language: OutLang = "auto",
    context: str = "Нужно сделать короткую выдержку о том, про что рассказывается в стоматологическом видео.",
    answer_format: str = "",
    final_model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Результат: словарь, совместимый с VideoSummaryResponse (из API-роута)
    """
    # Настроим SDK (в воркере — на всякий случай каждый раз)
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

    # 3) LeMUR-саммари
    self.update_state(state="PROGRESS", meta={"stage": "lemur_requested"})

    target_lang = _to_target_language(lang, language_code, output_language)
    model = final_model or DEFAULT_LEMUR_MODEL
    lemur = aai.Lemur()

    try:
        if answer_format.strip():
            ctx = (context or "").strip()
            if target_lang:
                ctx += f"\nПожалуйста, ответь на языке: {target_lang}."
            res = lemur.summarize(
                final_model=model,
                context=ctx.strip(),
                answer_format=answer_format.strip(),
                input_text=text,
            )
            summary = (res.response or "").strip()
        else:
            prompt = (context or DEFAULT_MARKETING_PROMPT).format(target_lang=target_lang)
            res = lemur.task(final_model=model,prompt=prompt, input_text=text)
            summary = (res.response or "").strip()
    except Exception as e:
        return {
            "summary": None,
            "language_code": lang,
            "language_confidence": conf,
            "status": "lemur_error",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "error": str(e),
                "suggestions": [
                    "Проверьте final_model (см. список в сообщении ошибки).",
                    "Попробуйте более простой формат ответа.",
                    "Убедитесь, что ключ имеет доступ к LeMUR.",
                ],
            },
        }

    # 4) Пустой ответ от LLM → фолбэк
    if not summary:
        fb = _fallback_summary(text)
        self.update_state(state="PROGRESS", meta={"stage": "fallback_used", "fallback": bool(fb)})
        return {
            "summary": fb,
            "language_code": lang,
            "language_confidence": conf,
            "status": "ok_but_summary_empty_fallback_used" if fb else "ok_but_summary_empty",
            "transcript_id": getattr(tr, "id", None),
            "diagnostics": {
                "reason": "LeMUR вернул пустой ответ.",
                "text_len": text_len,
                "language_detected": lang,
                "language_confidence": conf,
                "suggestions": [
                    "Уточните answer_format (например: '5–7 буллетов, без воды').",
                    "Попробуйте другой final_model (напр., anthropic/claude-3-5-haiku-20241022).",
                ],
            },
        }

    self.update_state(state="PROGRESS", meta={"stage": "lemur_done"})
    return {
        "summary": summary,
        "language_code": lang,
        "language_confidence": conf,
        "status": "ok",
        "transcript_id": getattr(tr, "id", None),
        "diagnostics": None,
    }
