import logging

import requests
from sqlalchemy.orm import Session
import datetime as _dt

from ..models.models_v2 import LessonPreview
from ..tasks.preview_tasks import generate_preview

logger = logging.getLogger(__name__)
PLACEHOLDER_URL = "https://cdn.dent-s.com/previews/placeholder.jpg"
CHECK_TTL = _dt.timedelta(hours=6)      # чаще нет смысла
HEAD_TIMEOUT = 4                        # сек

def _is_url_alive(url: str) -> bool:
    try:
        r = requests.head(url, timeout=HEAD_TIMEOUT, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False


def get_or_schedule_preview(db: Session, video_link: str) -> str:
    row = (
        db.query(LessonPreview)
        .filter_by(video_link=video_link)
        .first()
    )
    now = _dt.datetime.utcnow()

    # --- если строки ещё нет → ставим таску и выдаём плейсхолдер ---
    if not row:
        generate_preview.delay(video_link)
        return PLACEHOLDER_URL

    # --- если это плейсхолдер, но кадр ещё не сгенерирован ---
    if row.preview_url == PLACEHOLDER_URL:
        # «давно» ли в очереди?  (15 мин — абстрактный таймаут генерации)
        if (now - row.generated_at) > _dt.timedelta(minutes=15):
            generate_preview.delay(video_link)        # дублировать не страшно
        return PLACEHOLDER_URL

    # --- URL есть. Проверяем редко (раз в CHECK_TTL) ---
    if (
        row.checked_at is None or
        (now - row.checked_at) > CHECK_TTL
    ):
        row.checked_at = now
        db.commit()

        if not _is_url_alive(row.preview_url):
            # ссылка мертва → плейсхолдер + пере-генерация
            row.preview_url = PLACEHOLDER_URL
            row.generated_at = now
            db.commit()
            generate_preview.delay(video_link)
            return PLACEHOLDER_URL

    return row.preview_url
