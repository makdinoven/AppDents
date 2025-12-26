# backend/app/tasks/migrate_abandoned_to_leads.py
import logging
from datetime import timedelta

from celery.utils.log import get_task_logger
from sqlalchemy import text
from sqlalchemy.orm import Session

from ..celery_app import celery
from ..db.database import SessionLocal

logger = get_task_logger(__name__)

# По договорённости: переносим если send_count == MAX_SENDS (в коде сейчас 7)
MAX_SENDS = 7
STALE_AFTER = timedelta(days=2)


@celery.task(
    bind=True,
    name="app.tasks.migrate_abandoned_to_leads.migrate_abandoned_to_leads_daily",
    rate_limit="10/h",
)
def migrate_abandoned_to_leads_daily(self, batch_limit: int = 20000) -> dict:
    """
    Ежедневный перенос «зависших» лидов из abandoned_checkouts → leads.
    Условия:
      - send_count >= MAX_SENDS
      - last_sent_at <= utc_timestamp() - 2 days
      - нет пользователя с этим email
      - после вставки (или если lead уже есть) — удаляем строку из abandoned_checkouts
    """
    db: Session = SessionLocal()
    try:
        # 1) upsert в leads (только если leads ещё нет)
        insert_sql = text(
            """
            INSERT INTO `leads` (`email`, `language`, `tags`, `source`)
            SELECT
              LOWER(TRIM(ac.`email`)) AS `email`,
              UPPER(COALESCE(NULLIF(TRIM(ac.`region`), ''), 'EN')) AS `language`,
              JSON_ARRAY('abandoned_checkout') AS `tags`,
              'abandoned_checkout' AS `source`
            FROM `abandoned_checkouts` ac
            LEFT JOIN `users` u
              ON (LOWER(TRIM(u.`email`)) COLLATE utf8mb4_0900_ai_ci) = (LOWER(TRIM(ac.`email`)) COLLATE utf8mb4_0900_ai_ci)
            LEFT JOIN `leads` l
              ON (l.`email` COLLATE utf8mb4_0900_ai_ci) = (LOWER(TRIM(ac.`email`)) COLLATE utf8mb4_0900_ai_ci)
            WHERE
              ac.`send_count` >= :max_sends
              AND ac.`last_sent_at` IS NOT NULL
              AND ac.`last_sent_at` <= (utc_timestamp() - INTERVAL :stale_days DAY)
              AND u.`id` IS NULL
              AND l.`id` IS NULL
            LIMIT :limit_rows
            """
        )

        res_ins = db.execute(
            insert_sql,
            {
                "max_sends": MAX_SENDS,
                "stale_days": int(STALE_AFTER.total_seconds() // 86400),
                "limit_rows": batch_limit,
            },
        )
        inserted = int(getattr(res_ins, "rowcount", 0) or 0)

        # 2) чистим abandoned_checkouts: удаляем только те строки, у которых теперь есть lead (или lead уже был)
        delete_sql = text(
            """
            DELETE ac
            FROM `abandoned_checkouts` ac
            JOIN `leads` l
              ON (l.`email` COLLATE utf8mb4_0900_ai_ci) = (LOWER(TRIM(ac.`email`)) COLLATE utf8mb4_0900_ai_ci)
            LEFT JOIN `users` u
              ON (LOWER(TRIM(u.`email`)) COLLATE utf8mb4_0900_ai_ci) = (l.`email` COLLATE utf8mb4_0900_ai_ci)
            WHERE
              ac.`send_count` >= :max_sends
              AND ac.`last_sent_at` IS NOT NULL
              AND ac.`last_sent_at` <= (utc_timestamp() - INTERVAL :stale_days DAY)
              AND u.`id` IS NULL
            LIMIT :limit_rows
            """
        )
        res_del = db.execute(
            delete_sql,
            {
                "max_sends": MAX_SENDS,
                "stale_days": int(STALE_AFTER.total_seconds() // 86400),
                "limit_rows": batch_limit,
            },
        )
        deleted = int(getattr(res_del, "rowcount", 0) or 0)

        db.commit()
        logger.info("migrate_abandoned_to_leads_daily: inserted=%s deleted=%s", inserted, deleted)
        return {"inserted": inserted, "deleted": deleted}
    except Exception as e:
        db.rollback()
        logger.exception("migrate_abandoned_to_leads_daily failed: %s", e)
        raise
    finally:
        db.close()


