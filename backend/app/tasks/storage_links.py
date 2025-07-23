import logging
import sqlalchemy
from sqlalchemy import text
from celery import shared_task

from ..db.database import SessionLocal

logger = logging.getLogger(__name__)

# (scheme)://(uuid).(selstorage|s3.twcstorage).ru/
PATTERN = (
    r'https?://'
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'\.(selstorage\.ru|s3\.twcstorage\.ru)/'
)
REPLACEMENT = 'https://cdn.dent-s.com/'         # со слэшем на конце

REGEXP_TIME_LIMIT_MS = 5000
USE_HINT = True  # если MySQL >= 8.0.21 — оставь True, иначе False


def _update_table(db, table, column):
    hint = f"/*+ SET_VAR(regexp_time_limit={REGEXP_TIME_LIMIT_MS}) */ " if USE_HINT else ""
    sql = f"""
        UPDATE {table}
        {hint}
        SET {column} = CAST(
                REGEXP_REPLACE(
                    CAST({column} AS CHAR CHARACTER SET utf8mb4),
                    '{PATTERN}',
                    '{REPLACEMENT}',
                    1, 0, 'c'
                ) AS JSON
            )
        WHERE {column} REGEXP '{PATTERN}';
    """
    db.execute(text(sql))


@shared_task(
    name="app.tasks.special_offers.replace_storage_links",
    queue="special",
    bind=True,
    autoretry_for=(sqlalchemy.exc.OperationalError,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
    acks_late=True,
)
def replace_storage_links(self):
    """
    Заменяет ссылки вида:
        https://<uuid>.selstorage.ru/...
        https://<uuid>.s3.twcstorage.ru/...
    на:
        https://cdn.dent-s.com/...
    в landings.lessons_info и courses.sections
    """
    db = SessionLocal()
    try:
        with db.begin():
            # Попытка поставить SESSION-переменную — вдруг разрешили позже.
            try:
                db.execute(text(f"SET SESSION regexp_time_limit = {REGEXP_TIME_LIMIT_MS}"))
            except sqlalchemy.exc.OperationalError as e:
                if "1229" not in str(e.orig):
                    raise

            _update_table(db, "landings", "lessons_info")
            _update_table(db, "courses", "sections")

        logger.info("replace_storage_links: success")

    except Exception as exc:
        logger.exception("replace_storage_links: failure")
        raise self.retry(exc=exc)
    finally:
        db.close()
