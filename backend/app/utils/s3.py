"""
Обёртка над boto3 для работы с S3-совместимым хранилищем Timeweb.

• generate_presigned_url() — главный публичный метод.
  ─ s3://<bucket>/<key>  →  https://cdn.dent-s.com/<key>      (если bucket == S3_BUCKET)
  ─ https://cdn.dent-s.com/<key>                              (осталась как есть)
  ─ любой другой bucket      →  подписанный URL c TTL
"""

import os
import logging
from datetime import timedelta
from urllib.parse import urlparse, urljoin, quote, unquote, urlunparse

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

# ──────── Параметры окружения ──────────────────────────────────────────────
S3_ENDPOINT     = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET       = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION       = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST  = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

_S3_ENDPOINT_HOST = urlparse(S3_ENDPOINT).netloc.lower()
_S3_PUBLIC_HOST   = urlparse(S3_PUBLIC_HOST).netloc.lower()

# ──────── Клиенты ─────────────────────────────────────────────────────────
# V2-подпись — для download
_s3_v2 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# V4-подпись — для LIST, PUT и пр. (если потребуется)
def _s3_v4():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

def generate_presigned_url(s3_url: str, expires: timedelta = timedelta(hours=6)) -> str:
    """
    Принимает:
      • s3://bucket/key                → вернёт подписанный https URL (endpoint)
      • https://<S3_ENDPOINT>/<b>/<k>  → вернёт подписанный https URL
      • https://<CDN>/<key>            → вернёт публичный CDN-URL (с корректным encoding)
      • любые другие https://…         → вернёт как есть (с корректным encoding), без подписи.

    ВАЖНО: не пытаемся подписывать «чужие» домены (example.com и т.п.), только наш endpoint/CDN.
    """
    if not s3_url:
        return s3_url

    try:
        p = urlparse(s3_url)
        scheme = (p.scheme or "").lower()

        # s3://bucket/key
        if scheme == "s3":
            bucket = p.netloc or S3_BUCKET
            key    = p.path.lstrip("/")
            if not bucket or not key:
                return _encode_http_url(s3_url)
            signed = _s3_v2.generate_presigned_url(
                ClientMethod="get_object",
                Params={"Bucket": bucket, "Key": key},
                ExpiresIn=int(expires.total_seconds()),
            )
            return signed

        # http(s)://…
        if scheme in ("http", "https"):
            host = (p.netloc or "").lower()

            # Наш CDN — ссылка и так публичная: просто корректно кодируем path.
            if host == _S3_PUBLIC_HOST:
                return _encode_http_url(s3_url)

            # Наш endpoint вида https://s3.twcstorage.ru/<bucket>/<key>
            if host == _S3_ENDPOINT_HOST:
                parts = p.path.lstrip("/").split("/", 1)
                if len(parts) == 2:
                    bucket, key = parts
                    if bucket and key:
                        signed = _s3_v2.generate_presigned_url(
                            ClientMethod="get_object",
                            Params={"Bucket": bucket, "Key": key},
                            ExpiresIn=int(expires.total_seconds()),
                        )
                        return signed
                # не смогли разобрать — вернём публично (с корректным encoding)
                return _encode_http_url(s3_url)

            # Любой другой домен — не подписываем, просто чиним encoding
            return _encode_http_url(s3_url)

        # Неизвестная схема — возвращаем как есть
        return s3_url

    except Exception as exc:
        logger.error("Cannot sign %s: %s", s3_url, exc)
        # Фоллбек: хотя бы отдаём валидный http(s) URL, если это он
        try:
            return _encode_http_url(s3_url)
        except Exception:
            return s3_url



def _encode_http_url(url: str) -> str:
    """
    Возвращает тот же http(s) URL, но с корректно percent-encoded path.
    Пробелы → %20, нерегистрируемые символы кодируются, а '/', '-', '_', '.', '~', '()' оставляем.
    """
    try:
        p = urlparse(url)
        encoded_path = quote(unquote(p.path), safe="/-._~()")
        return urlunparse((p.scheme, p.netloc, encoded_path, p.params, p.query, p.fragment))
    except Exception as e:
        logger.warning("encode_url failed for %r: %s", url, e)
        return url
