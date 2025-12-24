"""
Единая точка конфигурации и клиентов для S3-совместимого хранилища (Cloudflare R2).

Зачем:
- не дублировать S3_ENDPOINT/S3_BUCKET/S3_REGION/S3_PUBLIC_HOST по десяткам файлов
- гарантировать единые настройки boto3 (в т.ч. SigV4 для R2)
- централизовать построение публичных URL и извлечение key
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from typing import Optional
from urllib.parse import quote, unquote, urlparse, urlunparse

import boto3
from botocore.config import Config


@dataclass(frozen=True)
class StorageConfig:
    endpoint_url: str | None
    bucket: str
    region: str
    public_host: str

    @property
    def endpoint_host(self) -> str:
        return (urlparse(self.endpoint_url or "").netloc or "").lower()

    @property
    def public_hostname(self) -> str:
        return (urlparse(self.public_host).hostname or "").lower()


@lru_cache(maxsize=1)
def get_storage_config() -> StorageConfig:
    """
    Читаем конфиг из env один раз за процесс.
    """
    endpoint = os.getenv("S3_ENDPOINT")  # R2: https://<accountid>.r2.cloudflarestorage.com
    bucket = os.getenv("S3_BUCKET", "dent-s")
    region = os.getenv("S3_REGION", "auto")  # для R2 обычно "auto"
    public_host = os.getenv("S3_PUBLIC_HOST", "https://cloud.dent-s.com")
    return StorageConfig(endpoint_url=endpoint, bucket=bucket, region=region, public_host=public_host)


# Единые экспортируемые значения (подхватываются один раз при импорте процесса).
# Если нужно “горячее” обновление — используйте get_storage_config().
CFG = get_storage_config()
S3_ENDPOINT: str | None = CFG.endpoint_url
S3_BUCKET: str = CFG.bucket
S3_REGION: str = CFG.region
S3_PUBLIC_HOST: str = CFG.public_host


def _cfg() -> StorageConfig:
    # локальный шорткат для функций, чтобы не тащить CFG руками
    return CFG


def public_url_for_key(key: str, *, public_host: Optional[str] = None) -> str:
    """
    Стабильный публичный URL для object key.
    - кодируем path (пробелы -> %20 и т.п.)
    """
    base = (public_host or _cfg().public_host).rstrip("/")
    safe_key = quote(unquote(key).lstrip("/"), safe="/-._~()")
    return f"{base}/{safe_key}"


def encode_http_url(url: str) -> str:
    """
    Возвращает тот же http(s) URL, но с корректно percent-encoded path.
    """
    p = urlparse(url)
    encoded_path = quote(unquote(p.path), safe="/-._~()")
    return urlunparse((p.scheme, p.netloc, encoded_path, p.params, p.query, p.fragment))


def key_from_public_or_endpoint_url(url: str) -> str:
    """
    Извлекает object key из:
    - публичного URL (<S3_PUBLIC_HOST>/key)
    - endpoint URL (<S3_ENDPOINT>/<bucket>/<key>) (path-style)
    - любого другого URL: берём path как key
    """
    if not url:
        return url
    p = urlparse(url)
    host = (p.netloc or "").lower()
    path = unquote(p.path.lstrip("/"))

    cfg = _cfg()
    if cfg.public_hostname and host == cfg.public_hostname:
        return path

    if cfg.endpoint_host and host == cfg.endpoint_host:
        parts = path.split("/", 1)
        if len(parts) == 2:
            _bucket, key = parts
            return key
        return path

    return path


@lru_cache(maxsize=8)
def s3_client(
    *,
    signature_version: str = "s3v4",
    max_pool_connections: int | None = None,
):
    """
    Единый boto3 client. Для Cloudflare R2 должен быть SigV4.
    """
    cfg = _cfg()
    botocore_cfg = Config(
        signature_version=signature_version,
        s3={"addressing_style": "path"},
        **({"max_pool_connections": max_pool_connections} if max_pool_connections else {}),
    )
    return boto3.client(
        "s3",
        endpoint_url=cfg.endpoint_url,
        region_name=cfg.region,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=botocore_cfg,
    )


