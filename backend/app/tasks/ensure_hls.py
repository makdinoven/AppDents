
import hashlib
import json
import logging
import os
import re
import subprocess
import tempfile
import time
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from urllib.parse import unquote, quote, urlparse

import boto3
import redis
import requests
from botocore.config import Config
from botocore.exceptions import ClientError
from celery import shared_task
from sqlalchemy.orm import Session

from ..services_v2.video_repair_service import HLSPaths, build_fix_plan, fix_rebuild_hls, \
    fix_force_audio_reencode, s3_exists, fix_write_alias_master, url_from_key, write_status_json, key_from_url, \
    discover_hls_for_src

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
    """
    HLS c гарантированным аудио:
      A) быстрый путь: копируем видео, АУДИО -> AAC (стерео, 48кГц)
      B) фолбэк: полная перекодировка (x264 + AAC)
    """
    fast_cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-threads", "1",
        "-i", in_mp4,

        # включаем ровно 1 дорожку видео и 1 аудио (если есть)
        "-map", "0:v:0",
        "-map", "0:a:0?",

        # видео быстро копируем, аудио всегда в AAC
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "48000",

        # разумные флаги для HLS
        "-movflags", "+faststart",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", seg_pat,
        playlist,
    ]
    try:
        subprocess.run(fast_cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        logger.warning("[HLS] fast path (vcopy+aac) failed (%s) — fallback to full re-encode", e)

    full_cmd = [
        "ffmpeg", "-v", "error", "-y",
        "-threads", "1",
        "-i", in_mp4,

        "-map", "0:v:0",
        "-map", "0:a:0?",

        "-c:v", "libx264", "-preset", "veryfast", "-crf", "23",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "48000",

        "-movflags", "+faststart",
        "-max_muxing_queue_size", "1024",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", seg_pat,
        playlist,
    ]
    try:
        subprocess.run(full_cmd, check=True, timeout=3600)
        return True
    except subprocess.CalledProcessError as e:
        logger.error("[HLS] full re-encode failed: %s", e)
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

def _ffprobe_streams(path: str) -> dict:
    """Возвращает {'vcodec': 'h264'|'hevc'|..., 'acodec': 'aac'|'mp3'|...}."""
    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "v:0", "-show_entries", "stream=codec_name",
        "-of", "json", path
    ]
    out_v = subprocess.check_output(cmd).decode("utf-8", "ignore")
    vcodec = None
    try:
        data = json.loads(out_v)
        vcodec = (data.get("streams") or [{}])[0].get("codec_name")
    except Exception:
        pass

    cmd = [
        "ffprobe", "-v", "error",
        "-select_streams", "a:0", "-show_entries", "stream=codec_name",
        "-of", "json", path
    ]
    out_a = subprocess.check_output(cmd).decode("utf-8", "ignore")
    acodec = None
    try:
        data = json.loads(out_a)
        acodec = (data.get("streams") or [{}])[0].get("codec_name")
    except Exception:
        pass

    return {"vcodec": (vcodec or "").lower(), "acodec": (acodec or "").lower()}


def _is_h264(codec: str) -> bool:
    return codec in ("h264", "avc1")

def _is_aac(codec: str) -> bool:
    return codec in ("aac", "mp4a")


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


def _key_from_url(url: str) -> str:
    return unquote(urlparse(url).path.lstrip("/"))

def _delete_prefix(prefix: str) -> None:
    # prefix типа "path/.hls/slug/"
    s3v4 = _s3_v4()
    paginator = s3v4.get_paginator("list_objects_v2")
    to_delete = []
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix):
        for obj in page.get("Contents", []):
            to_delete.append({"Key": obj["Key"]})
            if len(to_delete) >= 1000:
                s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": to_delete})
                to_delete.clear()
    if to_delete:
        s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": to_delete})


from typing import Dict, Any
from urllib.parse import unquote, urlparse
import traceback as _tb
import time
import logging

logger = logging.getLogger(__name__)

def _normalize_src_key(video_url_or_key: str) -> str:
    """
    Приводим к «сырому» S3 key (без %XX).
    Если пришёл http(s) — берём path и unquote().
    Если пришёл «ключ» — тоже делаем unquote на случай закодированных сегментов.
    """
    try:
        p = urlparse(video_url_or_key)
        if p.scheme in ("http", "https"):
            return unquote(p.path.lstrip("/"))
        # «ключ» без схемы
        return unquote(video_url_or_key.lstrip("/"))
    except Exception:
        # последний шанс — вернуть как есть
        return video_url_or_key.lstrip("/")


def _master_dir_from(paths, plan) -> str | None:
    """
    Возвращает директорию, где должен лежать выбранный master.m3u8.
    Сначала пытаемся взять chosen_master из плана,
    иначе — new_pl_key, иначе — legacy_pl_key.
    """
    cm = (plan.notes.get("chosen_master") if getattr(plan, "notes", None) else None) or None
    if isinstance(cm, str) and "/" in cm:
        return cm.rsplit("/", 1)[0]

    for k in ("new_pl_key", "legacy_pl_key"):
        v = getattr(paths, k, None)
        if isinstance(v, str) and v and v.endswith("playlist.m3u8") and "/" in v:
            return v.rsplit("/", 1)[0]

    return None


@shared_task(bind=True, soft_time_limit=60 * 30)
def validate_and_fix_hls(self, payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    payload:
      {
        "video_url": "https://cdn.dent-s.com/Es Okeson full/...-original.mp4" | "Es Okeson full/...-original.mp4",
        "prefer_new": true
      }
    """
    started = time.time()
    video_url: str = payload["video_url"]
    prefer_new: bool = bool(payload.get("prefer_new", True))

    applied: list[str] = []
    errors: list[str] = []

    # 1) Нормализуем исходный ключ (без %20 и т.п.)
    src_mp4_key = _normalize_src_key(video_url)

    try:
        # 2) Автодискавер путей
        paths: HLSPaths = discover_hls_for_src(src_mp4_key)

        # 3) План и проверки
        plan, checks = build_fix_plan(paths, src_mp4_key, prefer_new=prefer_new)

        # директория, куда писать/проверять master.m3u8
        hls_dir_key = _master_dir_from(paths, plan)

        # ── Применение плана ────────────────────────────────────────────────
        # Порядок важен: сначала rebuild (если требуется), потом — форс-аудио.
        try:
            if hls_dir_key and any(f.name == "REBUILD_HLS" for f in plan.to_apply):
                fix_rebuild_hls(src_mp4_key, hls_dir_key)
                applied.append("REBUILD_HLS")

            if hls_dir_key and any(f.name == "FORCE_AUDIO_REENCODE" for f in plan.to_apply):
                # даже если делали rebuild, делаем форс-аудио, если он есть в плане
                fix_force_audio_reencode(src_mp4_key, hls_dir_key)
                applied.append("FORCE_AUDIO_REENCODE")

            # alias master (legacy → canonical), только если оба пути известны и canonical реально есть
            if paths.legacy_pl_key and paths.new_pl_key and any(f.name == "WRITE_ALIAS_MASTER" for f in plan.to_apply):
                if s3_exists(paths.new_pl_key):
                    fix_write_alias_master(paths.new_pl_key, paths.legacy_pl_key)
                    applied.append("WRITE_ALIAS_MASTER")

        except Exception as step_exc:
            # не прерываем таску — фиксируем, что упало, пойдём писать статус
            err_txt = f"{type(step_exc).__name__}: {step_exc}"
            logger.error("[HLS][FIX] step failed: %s\n%s", err_txt, _tb.format_exc())
            errors.append(err_txt)

        # ── Финальная быстрая верификация + status.json ─────────────────────
        # Соберём человекочитаемый объект checks для status.json
        checks_dict = {
            k: {
                "problems": [p.name for p in v.problems],
                "details": v.details
            } for k, v in checks.items()
        }

        # Статус и пути
        paths_dict = {
            "legacy_pl_key": paths.legacy_pl_key,
            "new_pl_key": paths.new_pl_key,
            "legacy_pl_url": paths.legacy_pl_url,
            "new_pl_url": paths.new_pl_url
        }

        # Пишем status.json рядом с выбранным master — даже если были ошибки выше.
        try:
            if hls_dir_key:
                status_payload = {
                    "problems": {k: checks_dict[k]["problems"] for k in checks_dict},
                    "details":  {k: checks_dict[k]["details"]  for k in checks_dict},
                    "plan":     [f.name for f in plan.to_apply],
                    "applied":  applied,
                    "paths":    paths_dict,
                    "src_mp4_key": src_mp4_key,
                }
                write_status_json(hls_dir_key, status_payload)
                applied.append("WRITE_STATUS")
        except Exception as status_exc:
            err_txt = f"{type(status_exc).__name__}: {status_exc}"
            logger.error("[HLS][FIX] write_status failed: %s\n%s", err_txt, _tb.format_exc())
            errors.append(err_txt)

        # Быстрая пост-проверка: существует ли теперь выбранный master?
        # (берём из плана notes.chosen_master или canonical/legacy)
        chosen_master = plan.notes.get("chosen_master") if getattr(plan, "notes", None) else None
        probe_keys = [k for k in (chosen_master, paths.new_pl_key, paths.legacy_pl_key) if k]
        master_ok = any(s3_exists(k) for k in probe_keys)

        return {
            "status": "ok" if not errors and master_ok else "error",
            "applied": applied,
            "errors": errors,
            "checks": checks_dict,
            "plan": {
                "to_apply": [f.name for f in plan.to_apply],
                "notes": plan.notes
            },
            "paths": paths_dict,
            "src_mp4_key": src_mp4_key,
            "duration_sec": int(time.time() - started),
            "master_exists": bool(master_ok),
        }

    except Exception as e:
        err_txt = f"{type(e).__name__}: {e}"
        logger.error("[HLS][FIX] unexpected: %s\n%s", err_txt, _tb.format_exc())
        return {
            "status": "error",
            "applied": applied,
            "errors": [err_txt],
            "checks": {},
            "plan": {"to_apply": [], "notes": {}},
            "paths": {},
            "src_mp4_key": src_mp4_key,
            "duration_sec": int(time.time() - started),
            "master_exists": False,
        }
