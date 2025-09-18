# app/tasks/video_summary.py
from typing import Optional, Dict, Any, Literal
import os
import re
import assemblyai as aai
from celery import shared_task

# ================== ENV / конфиг ==================
AAI_API_KEY = os.getenv("AAI_API_KEY")
DEFAULT_LEMUR_MODEL = os.getenv("AAI_LEMUR_MODEL", "anthropic/claude-3-5-sonnet")

if not AAI_API_KEY:
    raise RuntimeError("AAI_API_KEY is not set")

LangCode = Literal["auto", "ru", "en", "it", "es"]
OutLang = Literal["auto", "ru", "en", "it", "es"]

# ================== Базовый промпт (всегда используется) ==================
DEFAULT_MARKETING_PROMPT = """
Ты — ассистент, который делает краткие, маркетинговые выжимки по стоматологическим видеоурокам.
Цель — ясно и интересно показать СУТЬ содержания, чтобы заинтересовать просмотром, без раскрытия деталей.

Правила стиля:
• Не упоминай формат материала: никакого «вебинар», «видео», «урок», «лекция», «занятие», «в этом/данном вебинаре…» и т.п.
• Не указывай целевую аудиторию и пользу для кого-то (никаких «материал будет полезен…», «для стоматологов…», «подойдёт…», «ориентирован на…»).
• Не упоминай ведущего/лекторов/автора (никаких «Лектор рассказывает…»). Используй безличные формулировки: «рассматриваются», «обсуждаются», «показывается», «разбираются».
• Пиши одним абзацем из 2–6 предложений. Никаких списков, нумерации, буллетов, двоеточий с перечислениями.
• Обобщай темы вместо конкретных деталей.
• Не давай пошаговых инструкций, чисел/параметров, торговых марок, названий материалов и программ, конкретных углов/толщин/скоростей и протоколов.
• Без хайпа и оценочных эпитетов. Нейтрально и ёмко, с фокусом на ценности для обучающегося.

Формат ответа:
Единый абзац из 2–6 предложений, который поясняет, о чём содержание и чему помогает научиться, без конкретики.

Ответь на языке: {target_lang}.
""".strip()


# ================== Хелперы ==================
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

def _build_effective_prompt(target_lang: str, extra_context: Optional[str]) -> str:
    """Всегда берём базовый промпт; контекст админа добавляем как уточнение."""
    prompt = DEFAULT_MARKETING_PROMPT.format(target_lang=target_lang)
    extra = (extra_context or "").strip()
    if extra:
        prompt = f"{prompt}\n\nУточнение от редактора: {extra}"
    return prompt

def _combine_answer_format(answer_format: Optional[str], target_lang: str) -> str:
    """
    Даже если админ задал свой формат, добавляем наши жёсткие ограничения
    (без списков, без «Это видео…», без личных оборотов и пр.).
    """
    base_constraints = (
        "Единый абзац (2–5 предложений), без списков и нумерации; "
        "обобщённо, без деталей и конкретных параметров; "
        "без упоминания ведущего и формулировок вроде «в видео/вебинаре». "
        f"Ответ на языке: {target_lang}."
    )
    user_fmt = (answer_format or "").strip()
    return f"{user_fmt}\n\nТребования к стилю: {base_constraints}" if user_fmt else base_constraints

def _apply_style_guards(s: Optional[str]) -> Optional[str]:
    """
    Мягкая зачистка ответа: убираем буллеты/нумерацию, стартовые «Это видео…» и личные обороты.
    Держим один абзац.
    """
    if not s:
        return s
    import re

    # 1) Сносим буллеты/нумерацию построчно
    lines = []
    for ln in s.splitlines():
        ln = re.sub(r'^\s*[-•–—]\s*', '', ln)
        ln = re.sub(r'^\s*\d+[\.\)]\s*', '', ln)
        lines.append(ln)
    s = ' '.join(l.strip() for l in lines if l.strip())

    # 2) Удаляем вступления «Это видео…/В видео…/Вебинар…/Урок…» в самом начале
    s = re.sub(r'^(?:это\s+видео|в\s+видео|вебинар|урок)\s+[^.]*\.\s*', '', s, flags=re.IGNORECASE)

    # 3) Убираем предложения с «Лектор/Докладчик/Автор ...»
    s = re.sub(r'\b(?:лектор|докладчик|автор)\b[^.]*\.\s*', '', s, flags=re.IGNORECASE)

    # 4) Схлопываем пробелы
    s = re.sub(r'\s{2,}', ' ', s).strip()
    return s

# Совместимость с разными версиями SDK (input_text vs input)
def _lemur_task(lemur, *, model: str, prompt: str, text: str):
    try:
        return lemur.task(final_model=model, prompt=prompt, input_text=text)
    except TypeError as e:
        if "input_text" in str(e) or "unexpected keyword argument 'input_text'" in str(e):
            return lemur.task(final_model=model, prompt=prompt, input=text)
        raise

def _lemur_summarize(lemur, *, model: str, context: str, answer_format: str, text: str):
    try:
        return lemur.summarize(final_model=model, context=context, answer_format=answer_format, input_text=text)
    except TypeError as e:
        if "input_text" in str(e) or "unexpected keyword argument 'input_text'" in str(e):
            return lemur.summarize(final_model=model, context=context, answer_format=answer_format, input=text)
        raise

# ================== Celery task ==================
@shared_task(
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
    context: str = "Нужно сделать короткую выдержку о том, про что рассказывается в стоматологическом видео.",
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

    # 4) LeMUR: всегда базовый промпт + добавки админа
    self.update_state(state="PROGRESS", meta={"stage": "lemur_requested"})

    target_lang = _to_target_language(lang, language_code, output_language)
    model = final_model or DEFAULT_LEMUR_MODEL
    lemur = aai.Lemur()  # конструктор без final_model для совместимости

    eff_prompt = _build_effective_prompt(target_lang, context)  # база + уточнение редактора

    try:
        if (answer_format or "").strip():
            eff_answer_format = _combine_answer_format(answer_format, target_lang)
            res = _lemur_summarize(
                lemur,
                model=model,
                context=eff_prompt,
                answer_format=eff_answer_format,
                text=text,
            )
            summary = (res.response or "").strip()
        else:
            res = _lemur_task(
                lemur,
                model=model,
                prompt=eff_prompt,
                text=text,
            )
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
                    "Убедитесь, что AAI_API_KEY имеет доступ к LeMUR.",
                ],
            },
        }

    # 5) Пост-обработка формы (убрать списки/вступления/личные обороты)
    summary = _apply_style_guards(summary)

    # 6) Пустой ответ → фолбэк
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
                    "Уточните формулировки (context/answer_format).",
                    "Попробуйте другой final_model (например, anthropic/claude-3-5-haiku-20241022).",
                ],
            },
        }

    # 7) Успех
    self.update_state(state="PROGRESS", meta={"stage": "lemur_done"})
    return {
        "summary": summary,
        "language_code": lang,
        "language_confidence": conf,
        "status": "ok",
        "transcript_id": getattr(tr, "id", None),
        "diagnostics": None,
    }
