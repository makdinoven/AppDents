import logging
from celery import shared_task
from sqlalchemy.orm import Session

from ..db.database import SessionLocal
from ..services_v2.creative_service import generate_all_creatives

logger = logging.getLogger(__name__)


@shared_task(name="app.tasks.creatives.generate_all")
def generate_all(book_id: int, language: str) -> dict:
    db: Session = SessionLocal()
    try:
        items = generate_all_creatives(db, book_id, language)
        return {
            "items": [
                {"code": x.creative_code, "status": x.status, "s3_url": x.s3_url}
                for x in items
            ]
        }
    except Exception as e:
        logger.exception("creatives failed: %s", e)
        raise
    finally:
        db.close()


