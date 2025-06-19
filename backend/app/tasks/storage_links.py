import logging
from sqlalchemy import text
from celery import shared_task

from ..db.database import SessionLocal     # та же SessionLocal, что у вас уже есть

logger = logging.getLogger(__name__)


# NB: помещаем сразу в очередь «special»
@shared_task(name="app.tasks.storage_links.replace_storage_links",
             queue="special",
             bind=True,  # удобно, если захотите self.request.id и др.
             acks_late=True,  # на всякий случай, чтобы re-queue при падении
             max_retries=3,
             default_retry_delay=30)
def replace_storage_links(self):
    """
    Каждые 3 часа ищем в JSON-полях `landings.lessons_info`
    и `courses.sections` хосты вида

        <uuid>.selstorage.ru
        <uuid>.s3.twcstorage.ru

    и меняем их на `cdn.dent-s.com`.

    Работает исключительно через SQL — без выгрузки
    данных в Python, поэтому не бьём БД огромным числом UPDATE’ов.
    """
    db = SessionLocal()

    # ➊ Регулярка, которая ловит «любой UUID + точка + (selstorage|s3.twcstorage).ru»
    #    \p{XDigit} не поддерживается, поэтому старый добрый [0-9a-f].
    pattern = r'[0-9a-f\-]+\.(selstorage\.ru|s3\.twcstorage\.ru)'

    try:
        with db.begin():               # атомарно, auto-commit по выходу
            # landings
            db.execute(text(f"""
                UPDATE landings
                SET lessons_info = CAST(
                        REGEXP_REPLACE(
                            CAST(lessons_info AS CHAR CHARACTER SET utf8mb4),
                            '{pattern}',
                            'cdn.dent-s.com'
                        ) AS JSON
                    )
                WHERE lessons_info REGEXP '{pattern}';
            """))

            # courses
            db.execute(text(f"""
                UPDATE courses
                SET sections = CAST(
                        REGEXP_REPLACE(
                            CAST(sections AS CHAR CHARACTER SET utf8mb4),
                            '{pattern}',
                            'cdn.dent-s.com'
                        ) AS JSON
                    )
                WHERE sections REGEXP '{pattern}';
            """))

        logger.info("Storage links successfully replaced")
    except Exception as exc:           # базовая защита от сбоев
        logger.exception("Error while replacing storage links")
        # ретрайните задачу, если считаете нужным
        raise self.retry(exc=exc)
    finally:
        db.close()
