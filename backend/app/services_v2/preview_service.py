import logging
from sqlalchemy.orm import Session

from ..models.models_v2 import LessonPreview
from ..tasks.preview_tasks import generate_preview

logger = logging.getLogger(__name__)
PLACEHOLDER = ""

# services_v2/preview_service.py
def get_or_schedule_preview(db: Session, video_link: str) -> str:
    row = db.query(LessonPreview).filter_by(video_link=video_link).first()
    if row:
        return row.preview_url

    logger.info("⏳ scheduling preview for  %s", video_link)  # ← ДОБАВЬТЕ
    try:
        generate_preview.delay(video_link)
    except Exception as exc:
        logger.exception("Celery .delay() failed: %s", exc)
    return PLACEHOLDER

