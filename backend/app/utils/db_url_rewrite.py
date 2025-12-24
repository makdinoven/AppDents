from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable

from sqlalchemy import text

from ..core.config import settings
from ..core.storage import S3_PUBLIC_HOST, public_url_for_key

logger = logging.getLogger(__name__)


_CANDIDATE_COLS_CACHE: list["ColumnRef"] | None = None


@dataclass(frozen=True)
class ColumnRef:
    table_name: str
    column_name: str
    data_type: str


def _q_ident(name: str) -> str:
    # экранирование идентификатора для MySQL (backticks)
    return "`" + (name or "").replace("`", "``") + "`"


def _load_candidate_columns(db) -> list[ColumnRef]:
    """
    Ищем колонки, где *могут* лежать ссылки на CDN/S3 key.
    Делается один раз за процесс (кэшируется).
    """
    sql = text(
        """
        SELECT table_name, column_name, data_type
          FROM information_schema.columns
         WHERE table_schema = :schema
           AND data_type IN (
                'json',
                'varchar',
                'text',
                'longtext',
                'mediumtext',
                'tinytext'
           )
        """
    )
    rows = db.execute(sql, {"schema": settings.DB_NAME}).fetchall()
    cols = [ColumnRef(r[0], r[1], (r[2] or "").lower()) for r in rows]
    logger.info("[db_url_rewrite] discovered %d candidate columns", len(cols))
    return cols


def discover_candidate_columns(db) -> list[ColumnRef]:
    global _CANDIDATE_COLS_CACHE
    if _CANDIDATE_COLS_CACHE is None:
        _CANDIDATE_COLS_CACHE = _load_candidate_columns(db)
    return _CANDIDATE_COLS_CACHE


def rewrite_references_for_key(
    db,
    *,
    old_key: str,
    new_key: str,
    dry_run: bool = False,
) -> dict:
    """
    Точечная замена ссылок/ключей в БД для одного mp4:
    - меняем как полный URL, так и «сырой» key (если где-то хранится без хоста)
    - поддерживаем JSON колонки через CAST(... AS CHAR) -> REPLACE -> CAST(... AS JSON)
    """
    if not old_key or not new_key or old_key == new_key:
        return {"dry_run": dry_run, "updated": 0, "by_column": []}

    old_url = public_url_for_key(old_key, public_host=S3_PUBLIC_HOST)
    new_url = public_url_for_key(new_key, public_host=S3_PUBLIC_HOST)

    like_old_url = f"%{old_url}%"
    like_old_key = f"%{old_key}%"

    cols = discover_candidate_columns(db)
    updated_total = 0
    per_col: list[dict] = []

    for c in cols:
        table = _q_ident(c.table_name)
        col = _q_ident(c.column_name)

        where_sql = f"CAST({col} AS CHAR CHARACTER SET utf8mb4) LIKE :like_old_url OR CAST({col} AS CHAR CHARACTER SET utf8mb4) LIKE :like_old_key"

        if dry_run:
            count_sql = text(f"SELECT COUNT(*) FROM {table} WHERE {where_sql}")
            cnt = int(
                db.execute(
                    count_sql,
                    {"like_old_url": like_old_url, "like_old_key": like_old_key},
                ).scalar()
                or 0
            )
            if cnt:
                per_col.append({"table": c.table_name, "column": c.column_name, "would_touch": cnt})
            continue

        if c.data_type == "json":
            # Важно: предполагаем, что исходный JSON валиден. REPLACE не должен ломать структуру.
            update_sql = text(
                f"""
                UPDATE {table}
                   SET {col} = CAST(
                        REPLACE(
                          REPLACE(CAST({col} AS CHAR CHARACTER SET utf8mb4), :old_url, :new_url),
                          :old_key, :new_key
                        ) AS JSON
                      )
                 WHERE {where_sql}
                """
            )
        else:
            update_sql = text(
                f"""
                UPDATE {table}
                   SET {col} = REPLACE(
                        REPLACE({col}, :old_url, :new_url),
                        :old_key, :new_key
                      )
                 WHERE {where_sql}
                """
            )

        res = db.execute(
            update_sql,
            {
                "old_url": old_url,
                "new_url": new_url,
                "old_key": old_key,
                "new_key": new_key,
                "like_old_url": like_old_url,
                "like_old_key": like_old_key,
            },
        )
        try:
            rowcount = int(getattr(res, "rowcount", 0) or 0)
        except Exception:
            rowcount = 0

        if rowcount:
            updated_total += rowcount
            per_col.append({"table": c.table_name, "column": c.column_name, "updated_rows": rowcount})

    return {"dry_run": dry_run, "updated": updated_total, "by_column": per_col, "old_url": old_url, "new_url": new_url}


