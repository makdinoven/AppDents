# app/services_v2/hls_validator.py
import io
import json
import os
import re
import tempfile
import subprocess
import urllib
import uuid
from dataclasses import dataclass, field
from enum import Enum, auto
from functools import lru_cache
from typing import Optional, List, Dict, Tuple

import boto3
from botocore.exceptions import ClientError
import requests

# =============== S3 / ENV =================

S3_BUCKET      = os.getenv("S3_BUCKET")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
)

# =============== Problem / Fix ============

class Problem(Enum):
    MISSING_MASTER = auto()         # master.m3u8 отсутствует или некорректный
    MISSING_VARIANT = auto()        # нет variant-плейлистов
    NO_AUDIO = auto()               # в сегментах нет аудио-дорожки
    UNDECODABLE_SEGMENT = auto()    # не смогли прочитать сегмент (битый/отсутствует)

class Fix(Enum):
    REBUILD_HLS = auto()            # пересобрать HLS
    FORCE_AUDIO_REENCODE = auto()   # пересобрать аудио (видео копируем)
    WRITE_ALIAS_MASTER = auto()     # создать/переписать алиас (legacy ↔ new)
    WRITE_STATUS = auto()           # только записать статус / “OK”

# =============== DTO ======================

@dataclass
class HLSPaths:
    legacy_pl_key: Optional[str] = None
    new_pl_key: Optional[str] = None
    legacy_pl_url: Optional[str] = None
    new_pl_url: Optional[str] = None

@dataclass
class CheckResult:
    problems: List[Problem] = field(default_factory=list)
    details: Dict[str, str] = field(default_factory=dict)

@dataclass
class FixPlan:
    to_apply: List[Fix] = field(default_factory=list)
    notes: Dict[str, str] = field(default_factory=dict)

# =============== Regex ====================

HLS_MASTER_RE   = re.compile(r'#EXTM3U', re.I)
HLS_VARIANT_RE  = re.compile(r'#EXT-X-STREAM-INF', re.I)

HLS_DIR_RE_LEGACY = re.compile(r"/\.hls/([^/]+)/playlist\.m3u8$", re.I)
HLS_DIR_RE_NEW    = re.compile(r"/\.hls/([^/]+-[0-9a-f]{8})/playlist\.m3u8$", re.I)

# =============== S3 helpers (с кэшем) =====

@lru_cache(maxsize=512)
def _s3_head_cached(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False

def s3_exists(key: str) -> bool:
    if not key:
        return False
    return _s3_head_cached(key)

def s3_get_text(key: str) -> Optional[str]:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return obj["Body"].read().decode("utf-8", errors="replace")
    except ClientError:
        return None

def s3_put_text(key: str, text: str, content_type: str = "application/vnd.apple.mpegurl") -> None:
    # Важно: после записи инвалидация кэша head()
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=text.encode("utf-8"), ContentType=content_type)
    try:
        _s3_head_cached.cache_clear()
    except Exception:
        pass

def url_from_key(key: str) -> str:
    # Ключи иногда содержат пробелы — CDN это переваривает.
    return f"{S3_PUBLIC_HOST}/{key}"

# =============== HLS parsing ==============

def parse_variant_paths(master_text: str) -> List[str]:
    """
    Из master.m3u8 достаём относительные пути к variant-плейлистам (по EXT-X-STREAM-INF).
    """
    lines = [l.strip() for l in (master_text or "").splitlines() if l.strip()]
    variants = []
    last_inf = False
    for l in lines:
        if l.startswith("#EXT-X-STREAM-INF"):
            last_inf = True
            continue
        if last_inf and not l.startswith("#"):
            variants.append(l)
            last_inf = False
    return variants

def join_hls_path(master_key: str, rel: str) -> str:
    # master_key: path/to/playlist.m3u8, rel: variant/720p.m3u8
    base = master_key.rsplit("/", 1)[0]
    return f"{base}/{rel}"

def pick_first_media_segment(variant_text: str) -> Optional[str]:
    """
    Находим первый медиа-сегмент (.ts или .m4s) из variant.m3u8.
    """
    for l in (variant_text or "").splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if l.endswith(".ts") or l.endswith(".m4s"):
            return l
    return None

# =============== ffprobe ==================

def ffprobe_json_bytes(data: bytes) -> Optional[dict]:
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        return ffprobe_json_path(tmp.name)

def ffprobe_json_path(path_or_url: str) -> Optional[dict]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path_or_url],
        capture_output=True, text=True
    )
    if proc.returncode != 0:
        return None
    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError:
        return None

def has_audio(meta: dict) -> bool:
    if not meta:
        return False
    return any(s.get("codec_type") == "audio" for s in meta.get("streams", []))

# =============== Smart checks =============

def _check_master_core(master_key: str) -> Tuple[CheckResult, List[str]]:
    """
    Базовая проверка master + сбор variant-путей (как относительных, так и абсолютных ключей).
    Возвращает (CheckResult, абсолютные variant-keys).
    """
    res = CheckResult()
    if not s3_exists(master_key):
        res.problems.append(Problem.MISSING_MASTER)
        res.details["missing_master"] = master_key
        return res, []

    master_text = s3_get_text(master_key) or ""
    if not HLS_MASTER_RE.search(master_text):
        res.problems.append(Problem.MISSING_MASTER)
        res.details["corrupt_master"] = "not an M3U8"
        return res, []

    variants_rel = parse_variant_paths(master_text)
    res.details["variants_total"] = str(len(variants_rel))

    if not variants_rel:
        res.problems.append(Problem.MISSING_VARIANT)
        res.details["no_variants"] = "master has no variants"
        return res, []

    # Абсолютные ключи variant-плейлистов
    variant_keys = [join_hls_path(master_key, rel) for rel in variants_rel]

    # Подсчёт реально существующих variant
    existing = sum(1 for vk in variant_keys if s3_exists(vk))
    res.details["variants_exist"] = str(existing)
    res.details["variants_missing"] = str(len(variant_keys) - existing)

    # Частичное отсутствие variant НЕ считается критичным для rebuild — это логируем
    if existing == 0:
        # вообще нет ни одного существующего variant → критика
        res.problems.append(Problem.MISSING_VARIANT)

    return res, variant_keys

def check_master_and_variants(master_key: str) -> CheckResult:
    res, _ = _check_master_core(master_key)
    return res

def _first_working_variant_key(variant_keys: List[str]) -> Tuple[Optional[str], Optional[str]]:
    """
    Возвращает tuple(variant_key, first_segment_key) для первого доступного variant.
    Если ни один variant не подходит — (None, None).
    """
    for vkey in variant_keys:
        text = s3_get_text(vkey)
        if not text:
            continue
        seg_rel = pick_first_media_segment(text)
        if not seg_rel:
            # variant без сегментов — пробуем следующий
            continue
        seg_key = join_hls_path(vkey, seg_rel)
        try:
            # Проверим существует ли сегмент — иначе ffprobe свалится
            s3.head_object(Bucket=S3_BUCKET, Key=seg_key)
            return vkey, seg_key
        except ClientError:
            # сегмент отсутствует — пробуем следующий variant
            continue
    return None, None

def check_audio_present(master_key: str) -> CheckResult:
    """
    Диагностика аудио:
      • перебираем variant-плейлисты до первого «рабочего» сегмента;
      • если удалось прочитать сегмент — ffprobe -> наличие аудио;
      • если ни один вариант не подошёл — UNDECODABLE_SEGMENT.
    """
    res = CheckResult()

    # Базовые вещи (существование master/variants)
    base, variant_keys = _check_master_core(master_key)
    res.problems.extend(base.problems)
    res.details.update(base.details)

    if Problem.MISSING_MASTER in base.problems:
        # дальше проверять нечего
        return res
    if Problem.MISSING_VARIANT in base.problems:
        # ни одного живого variant
        return res

    vkey, seg_key = _first_working_variant_key(variant_keys)
    if not vkey or not seg_key:
        res.problems.append(Problem.UNDECODABLE_SEGMENT)
        res.details["no_working_variant"] = "all variants missing or without segments"
        return res

    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=seg_key)
        seg_bytes = obj["Body"].read()
    except ClientError:
        res.problems.append(Problem.UNDECODABLE_SEGMENT)
        res.details["segment_missing"] = seg_key
        return res

    meta = ffprobe_json_bytes(seg_bytes)
    if not has_audio(meta):
        res.problems.append(Problem.NO_AUDIO)
        res.details["segment_key"] = seg_key
    return res

# =============== Fix helpers ==============

def fix_write_alias_master(from_master_key: str, alias_master_key: str) -> None:
    """
    «Алиас» на master: копируем плейлист (при необходимости можно переписать относительные пути).
    В нашей структуре каталогов обычно достаточно прямой копии.
    """
    text = s3_get_text(from_master_key) or ""
    s3_put_text(alias_master_key, text)

def fix_mark_ready(db_session, video_id: int) -> None:
    """
    Пример пометки сущности как готовой.
    """
    # from ..models.models_v2 import Video
    # video = db_session.query(Video).get(video_id)
    # video.is_ready = True
    # db_session.commit()
    pass

# =============== Discovery =================

def key_from_url(url: str) -> str:
    """
    Превращаем публичный URL CDN в S3 key.
    Пример:
      https://cdn.dent-s.com/Es Okeson full/dir/file.mp4
      -> Es Okeson full/dir/file.mp4
    """
    prefix = S3_PUBLIC_HOST.rstrip("/") + "/"
    if url.startswith(prefix):
        key = url[len(prefix):]
    else:
        parsed = urllib.parse.urlparse(url)
        key = parsed.path.lstrip("/")
    return key

def discover_hls_for_src(src_mp4_key: str) -> HLSPaths:
    """
    По ключу исходного MP4 ищем существующие HLS плейлисты.
    Логика:
      - базовая папка: <dir of mp4>/.hls/
      - ищем все playlist.m3u8 внутри;
      - классифицируем: legacy (без -hash) и new (с -[0-9a-f]{8});
      - если new нет — сгенерируем «красивый» путь под него.
    """
    base_dir = src_mp4_key.rsplit("/", 1)[0] if "/" in src_mp4_key else ""
    hls_prefix = f"{base_dir}/.hls/"
    legacy_pl_key = None
    new_pl_key = None

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if not key.endswith("playlist.m3u8"):
                continue
            if HLS_DIR_RE_NEW.search(key):
                # Выбираем первый найденный new (для упрощения; можно добрать «самый новый» по LastModified)
                if not new_pl_key:
                    new_pl_key = key
            elif HLS_DIR_RE_LEGACY.search(key):
                if not legacy_pl_key:
                    legacy_pl_key = key

    # Если не нашли new — предложим новый каталог с суффиксом
    if not new_pl_key:
        base_name = os.path.splitext(os.path.basename(src_mp4_key))[0]
        slug = re.sub(r"[^a-z0-9\-]+", "-", base_name.lower().replace(" ", "-")).strip("-")
        suffix = uuid.uuid4().hex[:8]
        new_dir = f"{hls_prefix}{slug}-{suffix}"
        new_pl_key = f"{new_dir}/playlist.m3u8"

    return HLSPaths(
        legacy_pl_key=legacy_pl_key,
        new_pl_key=new_pl_key,
        legacy_pl_url=url_from_key(legacy_pl_key) if legacy_pl_key else None,
        new_pl_url=url_from_key(new_pl_key) if new_pl_key else None,
    )

# =============== Планировщик фиксов =======

def build_fix_plan(
    paths: HLSPaths,
    src_mp4_key: str,
    prefer_new: bool = True
) -> Tuple[FixPlan, Dict[str, CheckResult]]:
    """
    Улучшенная диагностика HLS:
      • различаем проблемы master/variant/audio;
      • НЕ делаем rebuild, если достаточно алиаса либо аудио-пересборки.
    Приоритеты (согласовано):
      1) есть только legacy → WRITE_ALIAS_MASTER;
      2) есть new, а legacy отсутствует/битый → WRITE_ALIAS_MASTER;
      3) master есть, но нет аудио → FORCE_AUDIO_REENCODE;
      4) варианты частично битые → WRITE_STATUS (без rebuild);
      5) rebuild только если master полностью отсутствует/бит.
    """
    plan = FixPlan()
    checks: Dict[str, CheckResult] = {}

    legacy_key = paths.legacy_pl_key
    new_key    = paths.new_pl_key

    legacy_exists = bool(legacy_key and s3_exists(legacy_key))
    new_exists    = bool(new_key and s3_exists(new_key))

    # Выбираем master: если prefer_new и new существует → он, иначе legacy
    chosen_master = new_key if (prefer_new and new_exists) else (legacy_key if legacy_exists else None)
    checks["paths"] = CheckResult(details={
        "legacy_key": str(legacy_key),
        "legacy_exists": str(legacy_exists),
        "new_key": str(new_key),
        "new_exists": str(new_exists),
        "chosen_master": chosen_master or "none",
    })

    # --- 1) Если нет НИ одного мастера — без вариантов: rebuild
    if not chosen_master:
        plan.to_apply.append(Fix.REBUILD_HLS)
        plan.notes["reason"] = "no master (new/legacy) found"
        plan.notes["prefer_new"] = str(prefer_new)
        return plan, checks

    # --- 2) Проверка master/variants
    c_master = check_master_and_variants(chosen_master)
    checks["master_variants"] = c_master

    # --- 3) Проверка аудио
    c_audio = check_audio_present(chosen_master)
    checks["audio"] = c_audio

    # Собираем финальные проблемы
    problems = set(c_master.problems + c_audio.problems)

    # ====== Решения (в порядке приоритета) ======
    # a) Алиас, если есть только legacy ИЛИ если new ok, а legacy отсутствует/битый
    if new_exists and not legacy_exists:
        plan.to_apply.append(Fix.WRITE_ALIAS_MASTER)
        plan.notes["alias"] = "legacy missing, new exists"

    # b) master отсутствует/битый → rebuild
    if Problem.MISSING_MASTER in problems:
        plan.to_apply.append(Fix.REBUILD_HLS)
        plan.notes["reason"] = "missing/corrupt master"
        return plan, checks

    # c) нет ни одного живого variant → выбираем: если второй мастер есть — алиас, иначе rebuild
    if Problem.MISSING_VARIANT in problems:
        if new_exists and not legacy_exists:
            # уже добавили алиас выше; этого достаточно
            plan.notes["reason"] = "variants missing, alias will expose valid new"
            plan.to_apply.append(Fix.WRITE_STATUS)
            return plan, checks
        # альтернатив нет → rebuild
        plan.to_apply.append(Fix.REBUILD_HLS)
        plan.notes["reason"] = "no variants at all"
        return plan, checks

    # d) сегменты не читаются на выбранном variant → пробовали все; если альтернативный master есть — алиас; если нет — rebuild
    if Problem.UNDECODABLE_SEGMENT in problems:
        if new_exists and not legacy_exists:
            plan.to_apply.append(Fix.WRITE_ALIAS_MASTER)
            plan.notes["reason"] = "segments undecodable in legacy, new exists"
            plan.to_apply.append(Fix.WRITE_STATUS)
            return plan, checks
        plan.to_apply.append(Fix.REBUILD_HLS)
        plan.notes["reason"] = "undecodable segments"
        return plan, checks

    # e) нет аудио, при этом master/variants валидны → только аудио-пересборка
    if Problem.NO_AUDIO in problems:
        plan.to_apply.append(Fix.FORCE_AUDIO_REENCODE)
        plan.notes["reason"] = "no audio detected"
        return plan, checks

    # f) Частично отсутствуют variant-плейлисты (не критично) → просто статус
    # (мы это различаем по details["variants_missing"] > 0, но без MISSING_VARIANT)
    try:
        missing = int(c_master.details.get("variants_missing", "0") or "0")
        if missing > 0:
            plan.notes["warn"] = f"{missing} variant(s) missing but others exist"
    except Exception:
        pass

    # g) Всё ок
    plan.to_apply.append(Fix.WRITE_STATUS)
    plan.notes["reason"] = "ok"
    return plan, checks

# =============== ffmpeg runners ===========

def _lower_prio():
    try:
        os.nice(10)
    except Exception:
        pass

def _run_ffmpeg(cmd: list[str], timeout: int) -> None:
    proc = subprocess.run(
        cmd,
        check=True,
        timeout=timeout,
        capture_output=True,
        text=True,
        preexec_fn=_lower_prio,
    )
    if proc.stderr:
        # у ffmpeg большая часть лога в stderr — это не обязательно ошибка
        print(proc.stderr[:4000])

def _make_hls_copy_aac(in_url: str, out_dir: str, timeout: int) -> None:
    """
    Быстрый HLS: видео копируем, аудио → AAC; гарантируем сегментацию.
    """
    master = os.path.join(out_dir, "playlist.m3u8")
    segpat = os.path.join(out_dir, "segment_%05d.ts")

    cmd = [
        "ffmpeg", "-v", "error", "-nostdin", "-y",
        "-threads", "1",
        "-i", in_url,
        "-map", "0:v:0",
        "-map", "0:a:0?",
        "-c:v", "copy",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "48000",
        "-movflags", "+faststart",
        "-fflags", "+genpts",
        "-max_muxing_queue_size", "2048",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", segpat,
        master,
    ]
    _run_ffmpeg(cmd, timeout)

def _make_hls_full_reencode(in_url: str, out_dir: str, timeout: int) -> None:
    """
    Крайняя мера: полная перекодировка (ultrafast + CRF 25) если исходник проблемный.
    """
    master = os.path.join(out_dir, "playlist.m3u8")
    segpat = os.path.join(out_dir, "segment_%05d.ts")

    cmd = [
        "ffmpeg", "-v", "error", "-nostdin", "-y",
        "-threads", "1",
        "-i", in_url,
        "-map", "0:v:0",
        "-map", "0:a:0?",
        "-c:v", "libx264", "-preset", "ultrafast", "-crf", "25",
        "-c:a", "aac", "-b:a", "160k", "-ac", "2", "-ar", "48000",
        "-movflags", "+faststart",
        "-max_muxing_queue_size", "4096",
        "-hls_time", "8", "-hls_list_size", "0",
        "-hls_flags", "independent_segments",
        "-hls_segment_filename", segpat,
        master,
    ]
    _run_ffmpeg(cmd, timeout)

def _upload_dir_to_s3(local_dir: str, s3_dir_key: str) -> None:
    for root, _, files in os.walk(local_dir):
        for f in files:
            if f == ".DS_Store":
                continue
            local = os.path.join(root, f)
            rel   = os.path.relpath(local, local_dir).replace("\\", "/")
            key   = f"{s3_dir_key.rstrip('/')}/{rel}"
            ct    = "application/vnd.apple.mpegurl" if f.endswith(".m3u8") else "video/MP2T"
            with open(local, "rb") as fp:
                s3.put_object(Bucket=S3_BUCKET, Key=key, Body=fp.read(), ContentType=ct)
    try:
        _s3_head_cached.cache_clear()
    except Exception:
        pass

# =============== «умные» фиксы (rebuild/audio) ===

def _probe_codecs_from_url(in_url: str) -> tuple[str | None, str | None]:
    """
    Быстрая проверка кодеков исходного MP4 по URL: (vcodec, acodec) в нижнем регистре.
    """
    meta = ffprobe_json_path(in_url)
    vcodec = None
    acodec = None
    if meta and "streams" in meta:
        for s in meta["streams"]:
            if s.get("codec_type") == "video" and not vcodec:
                vcodec = (s.get("codec_name") or "").lower()
            if s.get("codec_type") == "audio" and not acodec:
                acodec = (s.get("codec_name") or "").lower()
    return vcodec, acodec

def fix_rebuild_hls(
    src_mp4_key: str,
    hls_dir_key: str,
    ffmpeg_timeout: int = 1800,
    prefer_in_url: bool = True,
    forbid_full_reencode: bool = True,
) -> None:
    """
    Пересборка HLS из исходного MP4.
      • читаем источник по CDN-URL;
      • по умолчанию НЕ делаем полный ре-энкод видео (copy), аудио → AAC;
      • если видео не h264/avc1 и forbid_full_reencode=False — делаем «лёгкий» полный ре-энкод.
    """
    in_url = url_from_key(src_mp4_key) if prefer_in_url else url_from_key(src_mp4_key)

    # Если исходник уже h264 — стараемся избежать полной перекодировки
    vcodec, _acodec = _probe_codecs_from_url(in_url)
    allow_full = (vcodec not in ("h264", "avc1")) and (not forbid_full_reencode)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            _make_hls_copy_aac(in_url, tmpdir, ffmpeg_timeout)
        except Exception as fast_err:
            if allow_full:
                _make_hls_full_reencode(in_url, tmpdir, ffmpeg_timeout)
            else:
                raise fast_err
        _upload_dir_to_s3(tmpdir, hls_dir_key)

def fix_force_audio_reencode(
    src_mp4_key: str,
    hls_dir_key: str,
    ffmpeg_timeout: int = 1800,
    prefer_in_url: bool = True,
    forbid_full_reencode: bool = True,
) -> None:
    """
    Принудительно гарантируем корректное AAC-аудио.
    Реализовано тем же путём, что и rebuild (видео copy + аудио AAC).
    """
    fix_rebuild_hls(
        src_mp4_key=src_mp4_key,
        hls_dir_key=hls_dir_key,
        ffmpeg_timeout=ffmpeg_timeout,
        prefer_in_url=prefer_in_url,
        forbid_full_reencode=forbid_full_reencode,
    )

# =============== Status ===================

def write_status_json(hls_dir_key: str, data: dict) -> None:
    key = f"{hls_dir_key.rstrip('/')}/status.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
        CacheControl="public, max-age=60",
    )
    try:
        _s3_head_cached.cache_clear()
    except Exception:
        pass
