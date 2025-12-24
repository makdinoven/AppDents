"""
Обёртка над boto3 для работы с S3-совместимым хранилищем (Cloudflare R2 / S3-compatible).

• generate_presigned_url() — главный публичный метод.
  ─ s3://<bucket>/<key>  →  подписанный https URL (endpoint)   (для скачивания/контроля заголовков)
  ─ https://<S3_PUBLIC_HOST>/<key>                             (осталась как есть)
  ─ любой другой bucket      →  подписанный URL c TTL
"""

import logging
from datetime import timedelta
from urllib.parse import urlparse, unquote

from ..core.storage import (
    S3_BUCKET,
    S3_PUBLIC_HOST,
    get_storage_config,
    s3_client,
    public_url_for_key,
    encode_http_url,
)

logger = logging.getLogger(__name__)

# ──────── Хосты для распознавания “наших” URL ─────────────────────────────
_CFG = get_storage_config()
_S3_ENDPOINT_HOST = (_CFG.endpoint_host or "").lower()
_S3_PUBLIC_HOST = (_CFG.public_hostname or "").lower()

def generate_presigned_url(
    s3_url: str, 
    expires: timedelta = timedelta(hours=6),
    response_content_disposition: str | None = None
) -> str:
    """
    Принимает:
      • s3://bucket/key                → вернёт подписанный https URL (endpoint)
      • https://<S3_ENDPOINT>/<b>/<k>  → вернёт подписанный https URL
      • https://<CDN>/<key>            → вернёт публичный CDN-URL (с корректным encoding)
      • любые другие https://…         → вернёт как есть (с корректным encoding), без подписи.

    ВАЖНО: не пытаемся подписывать «чужие» домены (example.com и т.п.), только наш endpoint/CDN.
    
    response_content_disposition: Добавляет заголовок Content-Disposition к ответу S3
      (работает только для подписанных URL, игнорируется для публичных CDN URL)
    """
    if not s3_url:
        return s3_url

    try:
        p = urlparse(s3_url)
        scheme = (p.scheme or "").lower()
        s3 = s3_client(signature_version="s3v4")

        # s3://bucket/key
        if scheme == "s3":
            bucket = p.netloc or S3_BUCKET
            key    = p.path.lstrip("/")
            if not bucket or not key:
                return encode_http_url(s3_url)
            
            params = {"Bucket": bucket, "Key": key}
            if response_content_disposition:
                params["ResponseContentDisposition"] = response_content_disposition
            
            signed = s3.generate_presigned_url(
                ClientMethod="get_object",
                Params=params,
                ExpiresIn=int(expires.total_seconds()),
            )
            return signed

        # http(s)://…
        if scheme in ("http", "https"):
            host = (p.netloc or "").lower()

            # Наш публичный домен — ссылка и так публичная
            if _S3_PUBLIC_HOST and host == _S3_PUBLIC_HOST:
                # Если нужно переопределить Content-Disposition, создаём presigned URL
                if response_content_disposition:
                    # Извлекаем key из публичного URL: <S3_PUBLIC_HOST>/books/8/file.pdf → books/8/file.pdf
                    key = unquote(p.path.lstrip("/"))
                    if key:
                        params = {"Bucket": S3_BUCKET, "Key": key}
                        params["ResponseContentDisposition"] = response_content_disposition
                        
                        signed = s3.generate_presigned_url(
                            ClientMethod="get_object",
                            Params=params,
                            ExpiresIn=int(expires.total_seconds()),
                        )
                        return signed
                # Иначе просто возвращаем публичный URL
                return encode_http_url(s3_url)

            # Наш endpoint вида https://<S3_ENDPOINT>/<bucket>/<key>
            if _S3_ENDPOINT_HOST and host == _S3_ENDPOINT_HOST:
                parts = p.path.lstrip("/").split("/", 1)
                if len(parts) == 2:
                    bucket, key = parts
                    if bucket and key:
                        params = {"Bucket": bucket, "Key": key}
                        if response_content_disposition:
                            params["ResponseContentDisposition"] = response_content_disposition
                        
                        signed = s3.generate_presigned_url(
                            ClientMethod="get_object",
                            Params=params,
                            ExpiresIn=int(expires.total_seconds()),
                        )
                        return signed
                # не смогли разобрать — вернём публично (с корректным encoding)
                return encode_http_url(s3_url)

            # Любой другой домен — не подписываем, просто чиним encoding
            return encode_http_url(s3_url)

        # Неизвестная схема — возвращаем как есть
        return s3_url

    except Exception as exc:
        logger.error("Cannot sign %s: %s", s3_url, exc)
        # Фоллбек: хотя бы отдаём валидный http(s) URL, если это он
        try:
            return encode_http_url(s3_url)
        except Exception:
            return s3_url
