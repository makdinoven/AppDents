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
from urllib.parse import urlparse, urljoin

import boto3
from botocore.config import Config

logger = logging.getLogger(__name__)

# ──────── Параметры окружения ──────────────────────────────────────────────
S3_ENDPOINT     = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET       = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION       = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST  = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

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

# ──────── Публичная/подписанная ссылка ────────────────────────────────────
def generate_presigned_url(
    s3_url: str,
    expires: timedelta = timedelta(hours=6)
) -> str:
    """
    • Принимает строку вида `s3://bucket/key` или готовую https-ссылку.
    • Если объект лежит в «публичном» бакете `S3_BUCKET`, возвращает прямой
      URL `S3_PUBLIC_HOST/<key>` без подписи.
    • Иначе — подписанный (V2) URL на `expires` секунд.
    """
    if not s3_url:
        return s3_url

    parsed = urlparse(s3_url)

    # 1. Уже публичная https-ссылка на CDN → отдаём как есть
    if parsed.scheme in {"http", "https"} and \
       parsed.netloc == urlparse(S3_PUBLIC_HOST).netloc:
        return s3_url

    # 2. s3://bucket/key
    bucket = parsed.netloc or S3_BUCKET
    key    = parsed.path.lstrip("/")

    # Если это «наш» CDN-бакет — формируем прямой публичный URL
    if bucket == S3_BUCKET:
        public_url = urljoin(f"{S3_PUBLIC_HOST.rstrip('/')}/", key)
        logger.debug("Public URL for %s → %s", s3_url, public_url)
        return public_url

    # 3. Иначе — подписываем ссылку (V2)
    try:
        signed = _s3_v2.generate_presigned_url(
            ClientMethod="get_object",
            Params={"Bucket": bucket, "Key": key},
            ExpiresIn=int(expires.total_seconds()),
        )
        logger.debug("Signed URL for %s generated (TTL=%s)", s3_url, expires)
        return signed
    except Exception as exc:
        logger.error("Cannot sign %s: %s", s3_url, exc, exc_info=True)
        return s3_url  # fallback — возвращаем оригинал
