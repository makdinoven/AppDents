import logging
import os
from celery import shared_task
from sqlalchemy import text
from sqlalchemy import exc as sa_exc

from ..db.database import SessionLocal  # скорректируй путь

logger = logging.getLogger(__name__)

# паттерны
PAT_OLD = (
    r'https?://'
    r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
    r'\.(selstorage\.ru|s3\.twcstorage\.ru)'
    r'(?:/|\?|#|$)'
)
PAT_BAD = (
    r'https?://'
    r'[0-9A-Fa-f]{8}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{4}-[0-9A-Fa-f]{12}'
    r'-cdn\.dent-s\.com'
    r'(?:/|\?|#|$)'
)

# Используем S3_PUBLIC_HOST из окружения (с fallback для совместимости)
REPLACEMENT = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com").rstrip('/') + '/'
REGEXP_TIME_LIMIT_MS = 5000
USE_HINT = True  # выключи, если MariaDB или MySQL < 8.0.21


def _update_table(db, table: str, column: str):
    hint = f"/*+ SET_VAR(regexp_time_limit={REGEXP_TIME_LIMIT_MS}) */ " if USE_HINT else ""
    # два прохода: сначала старые домены, затем «uuid-cdn.dent-s.com»
    sql = f"""
        UPDATE {table}
           SET {column} = CAST(
                   REGEXP_REPLACE(
                       REGEXP_REPLACE(
                           CAST({column} AS CHAR CHARACTER SET utf8mb4),
                           :pat_old, :cdn, 1, 0  -- БЕЗ 'c'
                       ),
                       :pat_bad, :cdn, 1, 0    -- БЕЗ 'c'
                   ) AS JSON
               )
         WHERE {column} REGEXP :pat_old
            OR {column} REGEXP :pat_bad;
    """
    db.execute(
        text(sql),
        {"pat_old": PAT_OLD, "pat_bad": PAT_BAD, "cdn": REPLACEMENT}
    )


@shared_task(
    name="app.tasks.storage_links.replace_storage_links",
    queue="special",
    bind=True,
    autoretry_for=(sa_exc.OperationalError,),
    retry_kwargs={"max_retries": 5, "countdown": 60},
    acks_late=True,
    task_reject_on_worker_lost=True,
)
def replace_storage_links(self):
    """
    Заменяет:
      https://<uuid>.selstorage.ru/...  или  https://<uuid>.s3.twcstorage.ru/...
    и чинит:
      https://<uuid>-cdn.dent-s.com/...
    на:
      https://cdn.dent-s.com/...
    в landings.lessons_info и courses.sections
    """
    db = SessionLocal()
    try:
        with db.begin():
            # Не трогаем SESSION-переменную: у вас только GLOBAL.
            _update_table(db, "landings", "lessons_info")
            _update_table(db, "courses", "sections")

        logger.info("replace_storage_links: success")
    except Exception as exc:
        logger.exception("replace_storage_links: failure")
        raise self.retry(exc=exc)
    finally:
        db.close()
