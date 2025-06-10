import logging
from sqlalchemy.orm import Session

from ..models.models_v2 import LessonPreview
from ..tasks.preview_tasks import generate_preview

logger = logging.getLogger(__name__)
PLACEHOLDER = "https://cdn.dent-s.com/previews/placeholder.jpg"

def get_or_schedule_preview(db: Session, video_link: str) -> str:
    """
    Возвращает URL превью.  Если в БД его нет – ставит Celery-таск
    и отдаёт плейсхолдер.
    """
    row = db.query(LessonPreview).filter_by(video_link=video_link).first()
    if row:
        return row.preview_url

    # запускаем в фоне
    logger.debug("Schedule preview for %s", video_link)
    generate_preview.delay(video_link)
    return PLACEHOLDER
