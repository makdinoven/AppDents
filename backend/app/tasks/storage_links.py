import logging
import sqlalchemy
from sqlalchemy import text
from celery import shared_task

from ...db.database import SessionLocal  # скорректируйте путь под вашу структуру

logger = logging.getLogger(__name__)

# Строгий UUID + нужные домены
PATTERN = (
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'\.(selstorage\.ru|s3\.twcstorage\.ru)'
)
REGEXP_TIME_LIMIT_MS = 5000  # можно 0 (без лимита), но 3-5 сек. обычно достаточно


@shared_task(
    name="app.tasks.special_offers.replace_storage_links",
    queue="special",
    bind=True,
    # автоматический ретрай на OperationalError (таймаут, сетевые глюки и т.д.)
    autoretry_for=(sqlalchemy.exc.OperationalError,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
    acks_late=True,
)
def replace_storage_links(self):
    """
    Каждые 3 часа заменяем в JSON-полях:
      - landings.lessons_info
      - courses.sections
    ссылки вида:
        <uuid>.selstorage.ru
        <uuid>.s3.twcstorage.ru
    на:   cdn.dent-s.com
    """
    db = SessionLocal()

    try:
        with db.begin():
            # повысим лимит только в этой сессии
            db.execute(text(f"SET SESSION regexp_time_limit = {REGEXP_TIME_LIMIT_MS}"))

            # 'c' = case-sensitive (быстрее)
            db.execute(text(f"""
                UPDATE landings
                   SET lessons_info = CAST(
                           REGEXP_REPLACE(
                               CAST(lessons_info AS CHAR CHARACTER SET utf8mb4),
                               '{PATTERN}',
                               'cdn.dent-s.com',
                               1, 0, 'c'
                           ) AS JSON
                       )
                 WHERE lessons_info REGEXP '{PATTERN}';
            """))

            db.execute(text(f"""
                UPDATE courses
                   SET sections = CAST(
                           REGEXP_REPLACE(
                               CAST(sections AS CHAR CHARACTER SET utf8mb4),
                               '{PATTERN}',
                               'cdn.dent-s.com',
                               1, 0, 'c'
                           ) AS JSON
                       )
                 WHERE sections REGEXP '{PATTERN}';
            """))

        logger.info("replace_storage_links: successfully replaced storage links")

    except Exception as exc:
        logger.exception("replace_storage_links: failed, will retry if allowed")
        raise self.retry(exc=exc)  # для не-OperationalError тоже ретраим
    finally:
        db.close()
