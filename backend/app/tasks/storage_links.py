import logging
import sqlalchemy
from sqlalchemy import text
from celery import shared_task

from ..db.database import SessionLocal

logger = logging.getLogger(__name__)

PATTERN = (
    r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'
    r'\.(selstorage\.ru|s3\.twcstorage\.ru)'
)
REGEXP_TIME_LIMIT_MS = 5000  # желаемое значение
USE_HINT = True              # попробуем хинтом, если ваша версия MySQL поддерживает


def _update_table(db, table, column):
    """Один UPDATE с REGEXP_REPLACE. Хинт добавляем при необходимости."""
    hint = f"/*+ SET_VAR(regexp_time_limit={REGEXP_TIME_LIMIT_MS}) */ " if USE_HINT else ""
    sql = f"""
        UPDATE {table}
        {hint}
        SET {column} = CAST(
                REGEXP_REPLACE(
                    CAST({column} AS CHAR CHARACTER SET utf8mb4),
                    '{PATTERN}',
                    'cdn.dent-s.com',
                    1, 0, 'c'
                ) AS JSON
            )
        WHERE {column} REGEXP '{PATTERN}';
    """
    db.execute(text(sql))


@shared_task(
    name="app.tasks.storage_links.replace_storage_links",
    queue="special",
    bind=True,
    autoretry_for=(sqlalchemy.exc.OperationalError,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
    acks_late=True,
)
def replace_storage_links(self):
    """
    Обновляет JSON-поля landings.lessons_info и courses.sections,
    заменяя <uuid>.selstorage.ru / <uuid>.s3.twcstorage.ru на cdn.dent-s.com.
    """
    db = SessionLocal()
    try:
        with db.begin():
            # Пытаемся поставить SESSION-переменную (если вдруг станет доступна).
            try:
                db.execute(text(f"SET SESSION regexp_time_limit = {REGEXP_TIME_LIMIT_MS}"))
            except sqlalchemy.exc.OperationalError as e:
                # код 1229 — только GLOBAL, игнорируем.
                if "1229" not in str(e.orig):
                    raise

            _update_table(db, "landings", "lessons_info")
            _update_table(db, "courses", "sections")

        logger.info("replace_storage_links: done")
    except Exception as exc:
        logger.exception("replace_storage_links: error")
        raise self.retry(exc=exc)
    finally:
        db.close()
