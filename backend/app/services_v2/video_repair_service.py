# app/services_v2/hls_validator.py
import io
import json
import os
import re
import tempfile
import subprocess
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


# ---------- Fixes (стабы с понятной реализацией) ----------

def fix_rebuild_hls(src_mp4_key: str, hls_dir_key: str) -> None:
    """
    Пересборка HLS «с нуля».
    Реальная реализация может вызывать твой существующий task конвейера.
    Здесь — пример локально через ffmpeg в tmp и заливка в S3.
    """
    # 1) скачать исходник
    obj = s3.get_object(Bucket=S3_BUCKET, Key=src_mp4_key)
    with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as tmp_in:
        tmp_in.write(obj["Body"].read())
        tmp_in.flush()
        in_path = tmp_in.name

    with tempfile.TemporaryDirectory() as tmpdir:
        master_path = os.path.join(tmpdir, "master.m3u8")
        # простой одно-рендитный HLS с AAC
        cmd = [
            "ffmpeg", "-y", "-i", in_path,
            "-c:v", "h264", "-c:a", "aac", "-b:a", "128k",
            "-start_number", "0",
            "-hls_time", "6", "-hls_list_size", "0",
            "-f", "hls", master_path
        ]
        proc = subprocess.run(cmd, capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"ffmpeg failed: {proc.stderr[:4000]}")

        # 3) залить всё содержимое каталога tmpdir в hls_dir_key
        for root, _, files in os.walk(tmpdir):
            for f in files:
                local = os.path.join(root, f)
                rel = os.path.relpath(local, tmpdir).replace("\\", "/")
                key = f"{hls_dir_key}/{rel}"
                content_type = "video/MP2T" if f.endswith(".ts") or f.endswith(".m4s") else "application/vnd.apple.mpegurl"
                with open(local, "rb") as fp:
                    s3.put_object(Bucket=S3_BUCKET, Key=key, Body=fp.read(), ContentType=content_type)

def fix_force_audio_reencode(src_mp4_key: str, hls_dir_key: str) -> None:
    """
    Принудительно гарантируем AAC-аудио в HLS (если исходник «тихий»/без аудио).
    """
    fix_rebuild_hls(src_mp4_key, hls_dir_key)

def write_status_json(hls_dir_key: str, data: dict) -> None:
    key = f"{hls_dir_key.rstrip('/')}/status.json"
    s3_put_object = s3.put_object  # кратко
    s3_put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(data, ensure_ascii=False, indent=2).encode("utf-8"),
        ContentType="application/json"
    )

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
