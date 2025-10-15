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
from typing import Optional, List, Dict, Tuple

import boto3
from botocore.exceptions import ClientError
import requests

S3_BUCKET      = os.getenv("S3_BUCKET")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
)

class Problem(Enum):
    MISSING_MASTER = auto()
    MISSING_VARIANT = auto()
    NO_AUDIO = auto()
    UNDECODABLE_SEGMENT = auto()

class Fix(Enum):
    REBUILD_HLS = auto()
    FORCE_AUDIO_REENCODE = auto()
    WRITE_ALIAS_MASTER = auto()
    WRITE_STATUS = auto()

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

HLS_MASTER_RE = re.compile(r'#EXTM3U', re.I)
HLS_VARIANT_RE = re.compile(r'#EXT-X-STREAM-INF', re.I)


# ---------- S3 helpers ----------

def s3_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False

def s3_get_text(key: str) -> Optional[str]:
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return obj["Body"].read().decode("utf-8", errors="replace")
    except ClientError:
        return None

def s3_put_text(key: str, text: str, content_type: str = "application/vnd.apple.mpegurl") -> None:
    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=text.encode("utf-8"), ContentType=content_type)

def url_from_key(key: str) -> str:
    # Ключи у тебя встречаются с пробелами: не кодируем — CDN у тебя это переваривает.
    return f"{S3_PUBLIC_HOST}/{key}"


# ---------- HLS parsing ----------

def parse_variant_paths(master_text: str) -> List[str]:
    """
    Из master.m3u8 достаём относительные пути к variant-плейлистам.
    """
    lines = [l.strip() for l in master_text.splitlines() if l.strip()]
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
    # master_key: path/to/master.m3u8, rel: variant/720p.m3u8
    base = master_key.rsplit("/", 1)[0]
    return f"{base}/{rel}"

def pick_first_media_segment(variant_text: str) -> Optional[str]:
    """
    Находим первый медиа-сегмент из variant.m3u8 (обычно .ts или .m4s)
    """
    for l in variant_text.splitlines():
        l = l.strip()
        if not l or l.startswith("#"):
            continue
        if l.endswith(".ts") or l.endswith(".m4s"):
            return l
    return None


# ---------- ffprobe ----------

def ffprobe_json_bytes(data: bytes) -> Optional[dict]:
    with tempfile.NamedTemporaryFile(suffix=".bin", delete=True) as tmp:
        tmp.write(data)
        tmp.flush()
        return ffprobe_json_path(tmp.name)

def ffprobe_json_path(path: str) -> Optional[dict]:
    proc = subprocess.run(
        ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", path],
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


# ---------- Core checks ----------

def check_master_and_variants(master_key: str) -> CheckResult:
    res = CheckResult()
    if not s3_exists(master_key):
        res.problems.append(Problem.MISSING_MASTER)
        res.details["missing_master"] = master_key
        return res

    master_text = s3_get_text(master_key) or ""
    if not HLS_MASTER_RE.search(master_text):
        res.problems.append(Problem.MISSING_MASTER)
        res.details["corrupt_master"] = "not an M3U8"
        return res

    variants = parse_variant_paths(master_text)
    if not variants:
        res.problems.append(Problem.MISSING_VARIANT)
        res.details["no_variants"] = "master has no variants"
        return res

    # Проверяем, что хотя бы один variant существует
    existing = 0
    for rel in variants:
        v_key = join_hls_path(master_key, rel)
        if s3_exists(v_key):
            existing += 1
    if existing == 0:
        res.problems.append(Problem.MISSING_VARIANT)
        res.details["variants_exist"] = "0"
    else:
        res.details["variants_exist"] = str(existing)

    return res

def check_audio_present(master_key: str) -> CheckResult:
    """
    Скачиваем первый variant и первый сегмент; ffprobe -> наличие аудио.
    """
    res = CheckResult()
    master_text = s3_get_text(master_key)
    if not master_text:
        res.problems.append(Problem.MISSING_MASTER)
        return res

    variants = parse_variant_paths(master_text)
    if not variants:
        res.problems.append(Problem.MISSING_VARIANT)
        return res

    # Возьмём первый существующий variant
    variant_key = None
    variant_text = None
    for rel in variants:
        v_key = join_hls_path(master_key, rel)
        text = s3_get_text(v_key)
        if text:
            variant_key = v_key
            variant_text = text
            break

    if not variant_key:
        res.problems.append(Problem.MISSING_VARIANT)
        return res

    seg_rel = pick_first_media_segment(variant_text or "")
    if not seg_rel:
        res.problems.append(Problem.UNDECODABLE_SEGMENT)
        res.details["no_segment"] = "no media segment in variant"
        return res

    seg_key = join_hls_path(variant_key, seg_rel)
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


def fix_write_alias_master(from_master_key: str, alias_master_key: str) -> None:
    """
    «Алиас» на master: копируем плейлист (и, при необходимости, правим относительные пути).
    В простом случае — просто копия (если структура каталогов совпадает).
    """
    text = s3_get_text(from_master_key) or ""
    # если alias лежит в другом каталоге — нужно переписать относительные пути
    # здесь минимально: предполагаем ту же структуру => просто копируем
    s3_put_text(alias_master_key, text)

def fix_mark_ready(db_session, video_id: int) -> None:
    """
    Пометить сущность в БД как готовую (пример).
    """
    # from ..models.models_v2 import Video
    # video = db_session.query(Video).get(video_id)
    # video.is_ready = True
    # db_session.commit()
    pass


# ---------- Planner ----------
HLS_DIR_RE_LEGACY = re.compile(r"/\.hls/([^/]+)/playlist\.m3u8$", re.I)
HLS_DIR_RE_NEW    = re.compile(r"/\.hls/([^/]+-[0-9a-f]{8})/playlist\.m3u8$", re.I)

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
        # если прислали прямой S3 endpoint URL — вырежем host и leading '/'
        parsed = urllib.parse.urlparse(url)
        key = parsed.path.lstrip("/")
    # Не декодируем пробелы намеренно (у тебя в ключах реальные пробелы).
    return key

def discover_hls_for_src(src_mp4_key: str) -> HLSPaths:
    """
    По ключу исходного MP4 ищем существующие HLS плейлисты.
    Логика:
      - Берём базовую папку: <dir of mp4>/.hls/
      - Ищем все playlist.m3u8 внутри.
      - Классифицируем: legacy (без суффикса -hash) и new (с суффиксом -[0-9a-f]{8})
      - Если ничего нет — предложим new-путь автоматически.
    """
    base_dir = src_mp4_key.rsplit("/", 1)[0] if "/" in src_mp4_key else ""
    hls_prefix = f"{base_dir}/.hls/"
    legacy_pl_key = None
    new_pl_key = None

    paginator = s3.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_prefix):
        for obj in page.get("Contents", []):
            key = obj["Key"]
            if key.endswith("playlist.m3u8"):
                if HLS_DIR_RE_NEW.search(key):
                    # выбираем самый «свежий» new (по времени последнего модификатора)
                    if not new_pl_key:
                        new_pl_key = key
                elif HLS_DIR_RE_LEGACY.search(key):
                    if not legacy_pl_key:
                        legacy_pl_key = key

    # Если не нашли new — предлагаем новый каталог с суффиксом
    if not new_pl_key:
        # slug делаем из имени родительской папки или имени mp4
        base_name = os.path.splitext(os.path.basename(src_mp4_key))[0]
        # лёгкий "slug"
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

def build_fix_plan(
    paths: HLSPaths,
    src_mp4_key: str,
    prefer_new: bool = True
) -> Tuple[FixPlan, Dict[str, CheckResult]]:
    """
    Проверяем new/legacy master, собираем общий список проблем и составляем план фиксов.
    """
    plan = FixPlan()
    checks: Dict[str, CheckResult] = {}

    chosen_master = paths.new_pl_key if prefer_new and paths.new_pl_key else paths.legacy_pl_key

    # 1) Проверка master+variants
    if chosen_master:
        c_master = check_master_and_variants(chosen_master)
        checks["master_variants"] = c_master
    else:
        c_master = CheckResult(problems=[Problem.MISSING_MASTER], details={"reason": "no chosen master"})
        checks["master_variants"] = c_master

    # 2) Проверка звука (если master есть)
    if Problem.MISSING_MASTER not in c_master.problems:
        c_audio = check_audio_present(chosen_master)
        checks["audio"] = c_audio
    else:
        checks["audio"] = CheckResult(problems=[Problem.MISSING_MASTER])

    # 3) Сбор проблем
    all_problems = set(checks["master_variants"].problems + checks["audio"].problems)

    # 4) План фиксов
    if Problem.MISSING_MASTER in all_problems or Problem.MISSING_VARIANT in all_problems or Problem.UNDECODABLE_SEGMENT in all_problems:
        plan.to_apply.append(Fix.REBUILD_HLS)

    if Problem.NO_AUDIO in all_problems:
        plan.to_apply.append(Fix.FORCE_AUDIO_REENCODE)

    # Если есть «красивый» путь и он не существует — пишем алиас
    if paths.legacy_pl_key and paths.new_pl_key and s3_exists(paths.new_pl_key) and not s3_exists(paths.legacy_pl_key):
        plan.to_apply.append(Fix.WRITE_ALIAS_MASTER)

    # Если проблем не осталось — можно пометить готовым
    if not all_problems:
        plan.to_apply.append(Fix.WRITE_STATUS)

    # Пояснения
    plan.notes["chosen_master"] = chosen_master or "none"
    plan.notes["problems"] = ", ".join(p.name for p in all_problems) or "none"

    return plan, checks

def _lower_prio():
    """Снижаем приоритет процесса (Linux)."""
    try:
        os.nice(10)
    except Exception:
        pass

def _run_ffmpeg(cmd: list[str], timeout: int) -> None:
    """
    Запускаем ffmpeg «бережно»: без чтения stdin, с 1 потоком, с таймаутом.
    Логируем stderr для диагностики.
    """
    proc = subprocess.run(
        cmd,
        check=True,
        timeout=timeout,
        capture_output=True,
        text=True,
        preexec_fn=_lower_prio,   # снижает CPU приоритет
    )
    if proc.stderr:
        # не «error» — у ffmpeg многое в stderr как обычный лог
        print(proc.stderr[:4000])


def _make_hls_copy_aac(in_url: str, out_dir: str, timeout: int) -> None:
    """
    Быстрый HLS: видео копируем как есть, аудио → AAC (если есть),
    гарантируем сегментацию и совместимость.
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
    Крайняя мера (если видео не h264 или источник «битый»):
    используем ultrafast + CRF 25, чтобы не грузить CPU.
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


# ───────────── «умные» фиксы ─────────────

def _probe_codecs_from_url(in_url: str) -> tuple[str | None, str | None]:
    """
    Быстрый пробник кодеков по исходному MP4 (без скачивания):
    возвращает (vcodec, acodec) в нижнем регистре.
    """
    with tempfile.NamedTemporaryFile(suffix=".url.txt", delete=False) as tmp:
        # ffprobe умеет читать по http(s), так что путь — это просто URL
        tmp.flush()
    try:
        meta = ffprobe_json_path(in_url)
    finally:
        try: os.unlink(tmp.name)
        except: pass

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
    - Читаем источник напрямую по URL (если prefer_in_url=True).
    - По умолчанию НЕ делаем полный ре-энкод видео (copy), аудио → AAC.
    - Если видео не h264/avc1 и forbid_full_reencode=False — сделаем «лёгкий» полный ре-энкод.
    """
    in_url = url_from_key(src_mp4_key) if prefer_in_url else None
    if not in_url:
        in_url = url_from_key(src_mp4_key)

    # Быстрый «интеллект»: если видео уже h264 — полного ре-энкода не требуется.
    vcodec, _acodec = _probe_codecs_from_url(in_url)
    allow_full = (vcodec not in ("h264", "avc1")) and (not forbid_full_reencode)

    with tempfile.TemporaryDirectory() as tmpdir:
        try:
            _make_hls_copy_aac(in_url, tmpdir, ffmpeg_timeout)
        except Exception as fast_err:
            if allow_full:
                # Последняя надежда — лёгкий полный ре-энкод
                _make_hls_full_reencode(in_url, tmpdir, ffmpeg_timeout)
            else:
                # Отдаём ошибку «как есть»
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
    Реализовано тем же путём, что и rebuild (copy видео + AAC аудио).
    """
    fix_rebuild_hls(
        src_mp4_key=src_mp4_key,
        hls_dir_key=hls_dir_key,
        ffmpeg_timeout=ffmpeg_timeout,
        prefer_in_url=prefer_in_url,
        forbid_full_reencode=forbid_full_reencode,
    )


def write_status_json(hls_dir_key: str, data: dict) -> None:
    key = f"{hls_dir_key.rstrip('/')}/status.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json",
        CacheControl="public, max-age=60",
    )