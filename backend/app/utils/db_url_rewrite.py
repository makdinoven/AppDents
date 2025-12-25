from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable
from urllib.parse import quote, unquote, urlparse

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

    # Учитываем, что в БД ссылки могут быть:
    # - на разных доменах (cloud vs cdn)
    # - с key в сыром виде (пробелы/юникод) или percent-encoded
    def _encoded_key_variants(k: str) -> list[str]:
        """
        В проекте встречаются разные варианты percent-encoding для URL:
        - иногда `(` и `)` остаются как есть
        - иногда они кодируются как %28/%29 (например, когда URL копируют из браузера)
        Поэтому делаем несколько вариантов encoding, чтобы надёжно матчить старые записи.
        """
        raw = unquote((k or "").lstrip("/"))
        variants = [
            quote(raw, safe="/-._~()"),  # "мягкий" (скобки как есть)
            quote(raw, safe="/-._~"),    # "строгий" (скобки тоже кодируются)
        ]
        # уникализируем, сохраняя порядок
        return list(dict.fromkeys([v for v in variants if v]))

    old_key_raw = unquote(old_key.lstrip("/"))
    new_key_raw = unquote(new_key.lstrip("/"))
    old_key_enc_variants = _encoded_key_variants(old_key)
    new_key_enc_variants = _encoded_key_variants(new_key)

    def _host_variants(base: str) -> list[str]:
        base = (base or "").rstrip("/")
        out = {base}
        try:
            p = urlparse(base)
            if p.scheme and p.netloc:
                host = p.netloc
                # cloud.<x> <-> cdn.<x> (частый кейс в проекте)
                if host.startswith("cloud."):
                    out.add(base.replace(host, "cdn." + host[len("cloud."):], 1))
                if host.startswith("cdn."):
                    out.add(base.replace(host, "cloud." + host[len("cdn."):], 1))
        except Exception:
            pass
        return [u for u in out if u]

    hosts = _host_variants(S3_PUBLIC_HOST)

    # URL варианты: encoded и “сырой” (иногда в БД хранится без %20)
    old_urls: list[str] = []
    new_urls: list[str] = []
    for h in hosts:
        for ok in old_key_enc_variants:
            old_urls.append(f"{h}/{ok}")
        for nk in new_key_enc_variants:
            new_urls.append(f"{h}/{nk}")
        old_urls.append(f"{h}/{old_key_raw}")
        new_urls.append(f"{h}/{new_key_raw}")
    # выравниваем длины old/new (для zip ниже) — берём попарно только общие варианты
    pair_count = min(len(old_urls), len(new_urls))
    old_urls = old_urls[:pair_count]
    new_urls = new_urls[:pair_count]

    # В JSON-колонках слеши часто экранируются как '\/' (пример: https:\/\/cdn.dent-s.com\/...)
    old_urls_json = [u.replace("/", r"\/") for u in old_urls]
    new_urls_json = [u.replace("/", r"\/") for u in new_urls]

    # Для отчёта: основной (канонический) URL
    old_url = public_url_for_key(old_key, public_host=S3_PUBLIC_HOST)
    new_url = public_url_for_key(new_key, public_host=S3_PUBLIC_HOST)

    # Паттерны для LIKE (важен порядок: сначала наиболее вероятные)
    like_patterns: list[str] = []
    for u in old_urls:
        like_patterns.append(f"%{u}%")
    for u in old_urls_json:
        like_patterns.append(f"%{u}%")
    # также пробуем key как raw и encoded (если где-то хранится без хоста)
    for ok in old_key_enc_variants:
        like_patterns.append(f"%{ok}%")
    like_patterns.append(f"%{old_key_raw}%")

    cols = discover_candidate_columns(db)
    updated_total = 0
    per_col: list[dict] = []

    for c in cols:
        table = _q_ident(c.table_name)
        col = _q_ident(c.column_name)

        # Собираем OR по всем паттернам (ограниченно, чтобы не раздувать запрос)
        where_parts = []
        params = {}
        for i, pat in enumerate(like_patterns[:14]):  # чуть шире, чтобы хватало и JSON-escaped вариантов
            pname = f"like_{i}"
            where_parts.append(f"CAST({col} AS CHAR CHARACTER SET utf8mb4) LIKE :{pname}")
            params[pname] = pat
        where_sql = " OR ".join(where_parts) if where_parts else "1=0"

        if dry_run:
            count_sql = text(f"SELECT COUNT(*) FROM {table} WHERE {where_sql}")
            cnt = int(
                db.execute(
                    count_sql,
                    params,
                ).scalar()
                or 0
            )
            if cnt:
                per_col.append({"table": c.table_name, "column": c.column_name, "would_touch": cnt})
            continue

        # Готовим цепочку REPLACE: сначала URL варианты (обычные и JSON-escaped), потом key варианты.
        # Важно: используем детерминированные имена параметров (без hash()).
        def _chain_replace(expr: str) -> str:
            out = expr
            for i in range(len(old_urls)):
                out = f"REPLACE({out}, :old_url_{i}, :new_url_{i})"
            for i in range(len(old_urls_json)):
                out = f"REPLACE({out}, :old_url_json_{i}, :new_url_json_{i})"
            out = f"REPLACE({out}, :old_key_raw, :new_key_raw)"
            out = f"REPLACE({out}, :old_key_enc, :new_key_enc)"
            return out

        # Параметры для REPLACE
        repl_params = dict(params)
        for i, (ou, nu) in enumerate(zip(old_urls, new_urls)):
            repl_params[f"old_url_{i}"] = ou
            repl_params[f"new_url_{i}"] = nu
        for i, (ou, nu) in enumerate(zip(old_urls_json, new_urls_json)):
            repl_params[f"old_url_json_{i}"] = ou
            repl_params[f"new_url_json_{i}"] = nu
        repl_params.update(
            {
                "old_key_raw": old_key_raw,
                "new_key_raw": new_key_raw,
                # Берём первый вариант в качестве "основного" для replace raw key.
                # (остальные варианты закрываются URL-заменами выше)
                "old_key_enc": old_key_enc_variants[0] if old_key_enc_variants else old_key_raw,
                "new_key_enc": new_key_enc_variants[0] if new_key_enc_variants else new_key_raw,
            }
        )

        if c.data_type == "json":
            # Важно: предполагаем, что исходный JSON валиден. REPLACE не должен ломать структуру.
            update_sql = text(
                f"""
                UPDATE {table}
                   SET {col} = CAST({_chain_replace(f"CAST({col} AS CHAR CHARACTER SET utf8mb4)")} AS JSON)
                 WHERE {where_sql}
                """
            )
        else:
            update_sql = text(
                f"""
                UPDATE {table}
                   SET {col} = {_chain_replace(col)}
                 WHERE {where_sql}
                """
            )

        res = db.execute(
            update_sql,
            repl_params,
        )
        try:
            rowcount = int(getattr(res, "rowcount", 0) or 0)
        except Exception:
            rowcount = 0

        if rowcount:
            updated_total += rowcount
            per_col.append({"table": c.table_name, "column": c.column_name, "updated_rows": rowcount})

    return {
        "dry_run": dry_run,
        "updated": updated_total,
        "by_column": per_col,
        "old_url": old_url,
        "new_url": new_url,
        "old_urls_considered": old_urls[:8],
    }


