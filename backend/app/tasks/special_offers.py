import logging
from celery import shared_task
from ..db.database import SessionLocal
from ..services_v2.special_offer_service import (
    generate_offers_for_all_users, cleanup_expired_offers
)

logger = logging.getLogger(__name__)

@shared_task
def process_special_offers():
    """
    1. выдаёт новые офферы тем, кому пора;
    2. удаляет протухшие.
    Запускается Celery beat-ом.
    """
    db = SessionLocal()
    try:
        generate_offers_for_all_users(db)
        cleanup_expired_offers(db)
    finally:
        db.close()
