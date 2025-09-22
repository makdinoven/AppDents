import sys

import assemblyai as aai

aai.settings.api_key = "65cbfa04b9634311a6523f1c9ee2745e"
audio_url = "https://cdn.dent-s.com/%D0%9E%D0%BD%D0%BB%D0%B0%D0%B9%D0%BD-%D0%BA%D1%83%D1%80%D1%81%20%D0%B8%D0%B7%205%20%D0%BC%D0%BE%D0%B4%D1%83%D0%BB%D0%B5%D0%B9.%20Restologia/%D0%9F%D1%80%D0%B5%D0%BF%D0%B0%D1%80%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%B8%20%D0%B8%D0%B7%D0%BE%D0%BB%D1%8F%D1%86%D0%B8%D1%8F.%20%D0%9B%D0%B5%D0%B1%D0%B5%D0%B4%D0%B5%D0%B2%D0%B0%20%D0%90%D0%BD%D0%BD%D0%B0/%D0%9F%D1%80%D0%B5%D0%BF%D0%B0%D1%80%D0%B8%D1%80%D0%BE%D0%B2%D0%B0%D0%BD%D0%B8%D0%B5%20%D0%B8%20%D0%B8%D0%B7%D0%BE%D0%BB%D1%8F%D1%86%D0%B8%D1%8F%2C%20%D1%87%D0%B0%D1%81%D1%82%D1%8C%201.%20%D0%9B%D0%B5%D0%B1%D0%B5%D0%B4%D0%B5%D0%B2%D0%B0%20%D0%90%D0%BD%D0%BD%D0%B0.mp4"

cfg = aai.TranscriptionConfig(language_detection=True)
tr = aai.Transcriber().transcribe(audio_url, config=cfg)
if tr.status == "error":
    raise RuntimeError(tr.error)

# 2) Саммари на русском через LeMUR (обязательно final_model)
res = tr.lemur.summarize(
    final_model="anthropic/claude-3-5-sonnet",  # ← укажи одну из поддерживаемых моделей
    context="Ты делаешь сжатые выдержки о том о чем видео по стоматологии.",
    answer_format=""
)
print(res.response)