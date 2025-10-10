
import hashlib
import logging
import os
import re
import subprocess
import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote, quote

import boto3
import redis
import requests
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task

# ──────────────────────────── ENV / CONST ────────────────────────────────────
logger = logging.getLogger(__name__)

REDIS_URL           = os.getenv("REDIS_URL", "redis://redis:6379/0")
rds                  = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# Redis‑ключи
R_SET_READY         = "hls:ready"          # успешно обработанные mp4
R_SET_QUEUED        = "hls:queued"         # стоят в расписании / выполняются
R_TOTAL             = "hls:total_mp4"
R_LAST_RECOUNT_TS   = "hls:last_recount_ts"

S3_ENDPOINT         = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET           = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION           = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST      = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")
_NO_KEY = ("NoSuchKey", "404")

SPACING             = int(os.getenv("HLS_TASK_SPACING", 360))   # сек. между ETA
BATCH_LIMIT         = int(os.getenv("HLS_BATCH_LIMIT", 40))     # задач за один проход
RATE_LIMIT_HLS      = "15/m"                                     # Celery annotation

R_SET_BAD = "hls:bad"

# основной S3‑клиент (V2 signature)
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

_s3_copy = boto3.client(        # v4-подпись
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

# эксклюзивно для листинга (V4 signature)
def _s3_v4():
    return boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

# ───────────────────────────── HELPERS ───────────────────────────────────────
def _copy_with_metadata(key: str, meta: dict) -> None:
    """Copy the object onto itself, replacing metadata (UTF-8–safe)."""
    _s3_copy.copy_object(
        Bucket=S3_BUCKET,
        Key=key,
        CopySource={"Bucket": S3_BUCKET, "Key": quote(key, safe="")},
        Metadata=meta,
        MetadataDirective="REPLACE",
        ACL="public-read",
        ContentType="video/mp4",
    )

def _each_mp4_objects():
    """yield key for every .mp4 object (V4 list)."""
    paginator = _s3_v4().get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.lower().endswith(".mp4"):
                yield key

SLUG_MAX = 60

def legacy_slug(name: str) -> str:
    """Старый способ (для совместимости с фронтом): просто обрезать до 60."""
    stem = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii","ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+","-", ascii_name).strip("-").lower()
    if not base:
        return hashlib.sha1(stem.encode()).hexdigest()[:SLUG_MAX]
    return base[:SLUG_MAX]

def stable_slug(name: str) -> str:
    """Новый устойчивый слуг: truncate + короткий sha1-хвост (без коллизий)."""
    stem = Path(name).stem
    ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii","ignore").decode()
    base = re.sub(r"[^A-Za-z0-9]+","-", ascii_name).strip("-").lower()
    if not base:
        return hashlib.sha1(stem.encode()).hexdigest()[:SLUG_MAX]
    if len(base) <= SLUG_MAX:
        return base
    suffix = hashlib.sha1(stem.encode()).hexdigest()[:8]
    keep = SLUG_MAX - 1 - len(suffix)  # место под "-{suffix}"
    return f"{base[:keep]}-{suffix}"


def hls_prefixes_for(key: str) -> tuple[str, str]:
    base, fname = os.path.split(key)
    leg = f"{base}/.hls/{legacy_slug(fname)}/".lstrip("/")
    new = f"{base}/.hls/{stable_slug(fname)}/".lstrip("/")
    return leg, new

def put_alias_master(legacy_playlist_key: str, canonical_m3u8_url: str) -> None:
    """
    Кладём маленький master.m3u8 по legacy-пути, который указывает на канонический media-плейлист.
    """
    body = (
        "#EXTM3U\n"
        "#EXT-X-VERSION:3\n"
        "#EXT-X-INDEPENDENT-SEGMENTS\n"
        "#EXT-X-STREAM-INF:BANDWIDTH=2000000\n"
        f"{canonical_m3u8_url}\n"
    ).encode("utf-8")
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=legacy_playlist_key,
        Body=body,
        ACL="public-read",
        ContentType="application/vnd.apple.mpegurl",
        CacheControl="public, max-age=60",
    )


# ─────────────────────── ffmpeg (copy→fallback) ──────────────────────────────

def _make_hls(in_mp4: str, playlist: str, seg_pat: str) -> bool:
    """True  → HLS готов; False → ffmpeg окончательно упал."""
    copy_cmd = [
        "ffmpeg", "-v", "error", "-y", "-threads", "1",
        "-i", in_mp4,
        "-c", "copy",
        "-bsf:v", "h264_mp4toannexb",
        "-movflags", "+faststart",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", seg_pat,
        playlist,
    ]
    try:
        subprocess.run(copy_cmd, check=True)
        return True                      # ← успешный fast‑remux
    except subprocess.CalledProcessError as e:
        logger.warning("[HLS] copy‑mux failed (%s) — fallback to re‑encode", e)

    # fallback: re‑encode
    encode_cmd = [
        "ffmpeg", "-v", "error", "-y", "-threads", "1",
        "-i", in_mp4,
        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "192k",
        "-movflags", "+faststart",
        "-max_muxing_queue_size", "1024",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", seg_pat,
        playlist,
    ]
    try:
        subprocess.run(encode_cmd, check=True, timeout=3600)
        return True                      # ← перекодирование прошло
    except subprocess.CalledProcessError as e:
        logger.error("[HLS] re‑encode failed: %s", e)
        return False

# ───────────────────────────── METADATA FIX ──────────────────────────────────
def _safe_head(key: str) -> dict | None:
    try:
        return s3.head_object(Bucket=S3_BUCKET, Key=key)
    except ClientError as e:
        if e.response["Error"]["Code"] in _NO_KEY:
            return None
        raise

def _mark_hls_ready(key: str) -> None:
    head = _safe_head(key)
    if head is None:                 # файла нет → очищаем Redis и уходим
        rds.srem(R_SET_READY, key)
        rds.srem(R_SET_QUEUED, key)
        logger.info("[HLS] skip, object disappeared: %s", key)
        return

    meta = head.get("Metadata", {})
    if meta.get("hls") == "true":
        return
    meta["hls"] = "true"

    try:
        _copy_with_metadata(key, meta)
    except ClientError as e:
        if e.response["Error"]["Code"] in _NO_KEY:
            # объект исчез между head и copy
            rds.srem(R_SET_READY, key)
            logger.info("[HLS] skip, object disappeared during copy: %s", key)
            return
        raise
    rds.sadd(R_SET_READY, key)


def _mark_hls_error(key: str, note: str) -> None:
    rds.sadd(R_SET_BAD, key)
    head = _safe_head(key)
    if head is None:
        logger.info("[HLS] cannot mark error, object gone: %s", key)
        return
    meta = head.get("Metadata", {})
    meta.update({"hls": "error", "hls_note": note[:60]})
    try:
        _copy_with_metadata(key, meta)
    except ClientError as e:
        if e.response["Error"]["Code"] not in _NO_KEY:
            raise



# ────────────────────────────── TASKS ────────────────────────────────────────

@shared_task(name="app.tasks.ensure_hls")
def ensure_hls() -> None:
    start_ts   = time.time()
    queued_now = 0

    for key in _each_mp4_objects():
        if "/.hls/" in key or key.endswith("_hls/"):
            continue
        if rds.sismember(R_SET_READY, key) or rds.sismember(R_SET_QUEUED, key) or rds.sismember(R_SET_BAD, key):
            continue

        legacy_prefix, new_prefix = hls_prefixes_for(key)
        legacy_pl = f"{legacy_prefix}playlist.m3u8"
        new_pl    = f"{new_prefix}playlist.m3u8"

        # 1) Канонический существует? → готово.
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=new_pl)
            _mark_hls_ready(key)
            continue
        except ClientError:
            pass

        # 2) Если в метадате уже hls=true — всё равно проверяем new_pl.
        #    Если его нет — надо мигрировать (ставим задачу), НЕ считаем готовым.
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=key)
            if head.get("Metadata", {}).get("hls") == "true":
                # не выходим — идём ставить задачу на миграцию
                pass
        except ClientError:
            continue

        # 3) Legacy найден, а canonical отсутствует → миграция требуется.
        #    (Если и legacy нет — это просто новая генерация.)
        #    В обоих случаях — ставим heavy-таску.
        eta = start_ts + queued_now * SPACING
        process_hls_video.apply_async((key,), queue="special_hls", eta=datetime.utcfromtimestamp(eta))
        rds.sadd(R_SET_QUEUED, key)
        logger.info("[HLS] queued #%02d  %s  eta=%s",
                    queued_now + 1, key,
                    datetime.utcfromtimestamp(eta).isoformat(timespec="seconds"))
        queued_now += 1
        if queued_now >= BATCH_LIMIT:
            break

    logger.info("[HLS] scan done, queued %d", queued_now)

# ──────────────────────────────────────────────────────────────────────────────

@shared_task(name="app.tasks.process_hls_video", rate_limit=RATE_LIMIT_HLS)
def process_hls_video(key: str) -> None:
    try:
        legacy_prefix, new_prefix = hls_prefixes_for(key)
        legacy_pl_key = f"{legacy_prefix}playlist.m3u8"
        new_pl_key    = f"{new_prefix}playlist.m3u8"
        new_pl_url    = f"{S3_PUBLIC_HOST}/{new_pl_key}"

        # Ранний выход — ТОЛЬКО если есть канонический
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=new_pl_key)
            _mark_hls_ready(key)
            logger.info("[HLS] already exists (canonical) for %s", key)
            return
        except ClientError:
            pass  # нет canonical → строим

        with tempfile.TemporaryDirectory() as tmp:
            in_mp4   = os.path.join(tmp, "in.mp4")
            seg_pat  = os.path.join(tmp, "segment_%03d.ts")
            playlist = os.path.join(tmp, "playlist.m3u8")

            s3.download_file(S3_BUCKET, key, in_mp4)

            ok = _make_hls(in_mp4, playlist, seg_pat)
            if not ok:
                _mark_hls_error(key, "ffmpeg_failed")
                logger.error("[HLS] ffmpeg failed for %s", key)
                return

            # выгружаем в КАНОНИЧЕСКИЙ префикс
            for fname in os.listdir(tmp):
                if fname == "in.mp4":
                    continue
                src = os.path.join(tmp, fname)
                dst = f"{new_prefix}{fname}"
                ct = "application/vnd.apple.mpegurl" if fname.endswith(".m3u8") else "video/MP2T"
                s3.upload_file(src, S3_BUCKET, dst, ExtraArgs={"ACL": "public-read", "ContentType": ct})

        _mark_hls_ready(key)

        # Перезаписываем legacy на alias-master → укажет на canonical
        if legacy_pl_key != new_pl_key:
            try:
                put_alias_master(legacy_pl_key, new_pl_url)
            except ClientError as e:
                logger.warning("[HLS] put alias failed for %s → %s: %s", key, legacy_pl_key, e)

        logger.info("[HLS] ready → %s", new_pl_url)

    finally:
        rds.srem(R_SET_QUEUED, key)


# Клиент только для листинга — V4
s3v4 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)

@shared_task(name="app.tasks.ensure_hls.recount_hls_counters")
def recount_hls_counters():
    """
    Улучшенный пересчёт:
      - Определяем total_mp4.
      - Восстанавливаем готовые исходники без HeadObject.
      - Используем несколько методов сопоставления:
          * единственный mp4 в каталоге
          * точный slug
          * slug c percent-decode
          * fuzzy очистка (только буквы/цифры)
      - Логируем unmatched и collisions.
    """
    logger.info("[HLS][RECOUNT] start (improved)")

    s3v4 = boto3.client(
        "s3",
        endpoint_url=S3_ENDPOINT,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
    )

    paginator = s3v4.get_paginator("list_objects_v2")

    mp4_by_dir = {}          # dir -> [ {key,size,stem,slug} ]
    playlists = []           # [{base_dir, slug_dir, full_key}]
    total_mp4 = 0

    def norm_slug(stem: str) -> str:
        ascii_name = unicodedata.normalize("NFKD", stem).encode("ascii","ignore").decode()
        ascii_name = re.sub(r"[^A-Za-z0-9]+","-", ascii_name).strip("-").lower()
        return (ascii_name or hashlib.sha1(stem.encode()).hexdigest())[:60]

    for page in paginator.paginate(Bucket=S3_BUCKET):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            low = key.lower()
            if "/.hls/" in key:
                # возможный playlist?
                if low.endswith("playlist.m3u8"):
                    parts = key.split("/")
                    try:
                        hls_index = parts.index(".hls")
                    except ValueError:
                        continue
                    if hls_index >= 1 and hls_index + 2 < len(parts):
                        base_dir = "/".join(parts[:hls_index])  # может быть "", если в корне
                        slug_dir = parts[hls_index + 1]
                        playlists.append({
                            "base_dir": base_dir,
                            "slug_dir": slug_dir,
                            "playlist_key": key,
                        })
                continue

            if low.endswith(".mp4"):
                total_mp4 += 1
                base_dir = os.path.dirname(key)
                stem = os.path.splitext(os.path.basename(key))[0]
                entry = {
                    "key": key,
                    "size": obj.get("Size", 0),
                    "stem": stem,
                    "slug": norm_slug(stem),
                }
                mp4_by_dir.setdefault(base_dir, []).append(entry)

    recovered = set()
    collisions = 0
    unmatched = 0

    def fuzzy(s: str) -> str:
        return re.sub(r"[^a-z0-9]+", "", s.lower())

    for pl in playlists:
        base_dir = pl["base_dir"]
        slug_dir = pl["slug_dir"]

        candidates = mp4_by_dir.get(base_dir, [])
        if not candidates:
            # нет исходников в этом каталоге
            unmatched += 1
            continue

        if len(candidates) == 1:
            recovered.add(candidates[0]["key"])
            continue

        # 1) точный slug
        exact = [c for c in candidates if c["slug"] == slug_dir]
        if len(exact) == 1:
            recovered.add(exact[0]["key"])
            continue
        elif len(exact) > 1:
            # slug коллизия -> возьмём самый большой размером (или логируем)
            exact_sorted = sorted(exact, key=lambda x: x["size"], reverse=True)
            recovered.add(exact_sorted[0]["key"])
            collisions += 1
            continue

        # 2) percent-decode stem (если в stem есть '%')
        decoded_matches = []
        for c in candidates:
            if "%" in c["stem"]:
                dec = unquote(c["stem"])
                if norm_slug(dec) == slug_dir:
                    decoded_matches.append(c)
        if len(decoded_matches) == 1:
            recovered.add(decoded_matches[0]["key"])
            continue
        elif len(decoded_matches) > 1:
            decoded_matches.sort(key=lambda x: x["size"], reverse=True)
            recovered.add(decoded_matches[0]["key"])
            collisions += 1
            continue

        # 3) fuzzy
        fuzzy_matches = [c for c in candidates if fuzzy(c["stem"]) == fuzzy(slug_dir)]
        if len(fuzzy_matches) == 1:
            recovered.add(fuzzy_matches[0]["key"])
            continue
        elif len(fuzzy_matches) > 1:
            fuzzy_matches.sort(key=lambda x: x["size"], reverse=True)
            recovered.add(fuzzy_matches[0]["key"])
            collisions += 1
            continue

        # не нашли
        unmatched += 1

    # Обновляем Redis (объединяем, чтобы не потерять добавленные параллельно)
    pipe = rds.pipeline()
    if recovered:
        pipe.sadd(R_SET_READY, *recovered)
    pipe.set(R_TOTAL, total_mp4)
    pipe.set(R_LAST_RECOUNT_TS, int(time.time()))
    pipe.execute()

    logger.info(
        "[HLS][RECOUNT] total_mp4=%d playlists=%d recovered=%d collisions=%d unmatched_playlists=%d ready_now=%d",
        total_mp4, len(playlists), len(recovered), collisions, unmatched, rds.scard(R_SET_READY)
    )
