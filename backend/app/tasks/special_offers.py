import logging
from celery import shared_task
from ..db.database import SessionLocal
from ..services_v2.special_offer_service import (
    generate_offers_for_all_users, deactivate_expired_offers,
)

logger = logging.getLogger(__name__)

@shared_task(name="app.tasks.special_offers.process_special_offers")
def process_special_offers():
    """
    Запускается Celery beat-ом.
    """
    db = SessionLocal()
    try:
        # 0) сначала гасим протухшие записи
        deactivated = deactivate_expired_offers(db)
        logger.info("Deactivated %s expired offers", deactivated)

        # 1) выдаём новые
        generate_offers_for_all_users(db)
    finally:
        db.close()
