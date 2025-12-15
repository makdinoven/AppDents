# app/api_v2/video_diagnostics.py
"""
Диагностика видео: проверка доступности MP4, HLS сегментов, URL encoding и т.д.
Помогает выявить причины ошибок 520 и остановки видео.
"""
import json
import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass, field, asdict
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse, unquote, quote

import boto3
import requests
from botocore.config import Config
from botocore.exceptions import ClientError
from fastapi import APIRouter, Query, Depends, HTTPException
from pydantic import BaseModel

from ..dependencies.auth import require_roles
from ..models.models_v2 import User

logger = logging.getLogger(__name__)

router = APIRouter()

# S3 Config
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
)


@dataclass
class DiagnosticResult:
    """Результат диагностики одного аспекта."""
    status: str  # ok, warning, error
    message: str
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class VideoHealth:
    """Полный отчёт о здоровье видео."""
    video_url: str
    s3_key: str
    overall_status: str  # healthy, degraded, broken
    checks: Dict[str, DiagnosticResult] = field(default_factory=dict)
    recommendations: List[str] = field(default_factory=list)


def key_from_url(url: str) -> str:
    """Извлекает S3 key из CDN URL."""
    prefix = S3_PUBLIC_HOST.rstrip("/") + "/"
    if url.startswith(prefix):
        key = url[len(prefix):]
    else:
        parsed = urlparse(url)
        key = parsed.path.lstrip("/")
    # Декодируем URL encoding
    return unquote(key)


def safe_cdn_url(key: str) -> str:
    """Создаёт безопасный CDN URL с правильным encoding."""
    # Разбиваем путь на части и кодируем каждую отдельно
    parts = key.split("/")
    encoded_parts = [quote(part, safe="") for part in parts]
    return f"{S3_PUBLIC_HOST}/{'/'.join(encoded_parts)}"


def check_s3_object(key: str) -> DiagnosticResult:
    """Проверяет существование и доступность объекта в S3."""
    try:
        head = s3.head_object(Bucket=S3_BUCKET, Key=key)
        size = head.get("ContentLength", 0)
        content_type = head.get("ContentType", "unknown")
        metadata = head.get("Metadata", {})
        
        return DiagnosticResult(
            status="ok",
            message=f"Object exists ({size / 1024 / 1024:.2f} MB)",
            details={
                "size_bytes": size,
                "content_type": content_type,
                "metadata": metadata,
                "faststart": metadata.get("faststart", "unknown"),
                "hls": metadata.get("hls", "unknown"),
            }
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("NoSuchKey", "404"):
            return DiagnosticResult(
                status="error",
                message="Object not found in S3",
                details={"error_code": code}
            )
        return DiagnosticResult(
            status="error",
            message=f"S3 error: {code}",
            details={"error": str(e)}
        )
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"Unexpected error: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_cdn_access(url: str, timeout: int = 10) -> DiagnosticResult:
    """Проверяет доступность через CDN (HEAD запрос)."""
    try:
        resp = requests.head(url, timeout=timeout, allow_redirects=True)
        if resp.status_code == 200:
            return DiagnosticResult(
                status="ok",
                message="CDN accessible",
                details={
                    "status_code": resp.status_code,
                    "content_length": resp.headers.get("Content-Length"),
                    "content_type": resp.headers.get("Content-Type"),
                    "cache_control": resp.headers.get("Cache-Control"),
                }
            )
        elif resp.status_code == 520:
            return DiagnosticResult(
                status="error",
                message="CDN Error 520 - Origin server returned unknown error",
                details={
                    "status_code": 520,
                    "likely_cause": "Timeweb S3 timeout or rate limit",
                    "recommendation": "Try magic button or wait and retry"
                }
            )
        else:
            return DiagnosticResult(
                status="error" if resp.status_code >= 400 else "warning",
                message=f"CDN returned status {resp.status_code}",
                details={"status_code": resp.status_code}
            )
    except requests.Timeout:
        return DiagnosticResult(
            status="error",
            message="CDN request timed out",
            details={"timeout_seconds": timeout}
        )
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"CDN check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_hls_playlist(key: str) -> DiagnosticResult:
    """Проверяет HLS playlist и считает сегменты."""
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        content = obj["Body"].read().decode("utf-8", errors="replace")
        
        if not content.strip().startswith("#EXTM3U"):
            return DiagnosticResult(
                status="error",
                message="Invalid HLS playlist (no #EXTM3U header)",
                details={"first_100_chars": content[:100]}
            )
        
        # Считаем сегменты
        segments = []
        lines = content.strip().split("\n")
        for i, line in enumerate(lines):
            line = line.strip()
            if line and not line.startswith("#"):
                segments.append(line)
        
        # Проверяем наличие #EXT-X-ENDLIST
        has_endlist = "#EXT-X-ENDLIST" in content
        
        # Парсим длительность
        total_duration = 0.0
        for line in lines:
            if line.startswith("#EXTINF:"):
                try:
                    dur = float(line.split(":")[1].split(",")[0])
                    total_duration += dur
                except:
                    pass
        
        return DiagnosticResult(
            status="ok" if segments else "warning",
            message=f"Found {len(segments)} segments, {total_duration:.1f}s total",
            details={
                "segment_count": len(segments),
                "total_duration_sec": total_duration,
                "has_endlist": has_endlist,
                "segments": segments[:10] if len(segments) <= 10 else segments[:5] + ["..."] + segments[-5:],
            }
        )
    except ClientError as e:
        code = e.response["Error"]["Code"]
        return DiagnosticResult(
            status="error",
            message=f"Playlist not found: {code}",
            details={"s3_key": key}
        )
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"Playlist check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_hls_segments(playlist_key: str, sample_count: int = 3) -> DiagnosticResult:
    """Проверяет доступность нескольких HLS сегментов."""
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=playlist_key)
        content = obj["Body"].read().decode("utf-8", errors="replace")
        
        segments = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and (line.endswith(".ts") or line.endswith(".m4s")):
                segments.append(line)
        
        if not segments:
            return DiagnosticResult(
                status="error",
                message="No segments found in playlist",
                details={}
            )
        
        # Берём первый, средний и последний сегмент
        sample_indices = [0]
        if len(segments) > 1:
            sample_indices.append(len(segments) // 2)
        if len(segments) > 2:
            sample_indices.append(len(segments) - 1)
        
        base_dir = playlist_key.rsplit("/", 1)[0] if "/" in playlist_key else ""
        
        results = []
        errors = []
        for idx in sample_indices[:sample_count]:
            seg_name = segments[idx]
            seg_key = f"{base_dir}/{seg_name}" if base_dir else seg_name
            
            try:
                head = s3.head_object(Bucket=S3_BUCKET, Key=seg_key)
                size = head.get("ContentLength", 0)
                results.append({
                    "index": idx,
                    "name": seg_name,
                    "status": "ok",
                    "size_bytes": size
                })
            except ClientError:
                errors.append(seg_name)
                results.append({
                    "index": idx,
                    "name": seg_name,
                    "status": "missing"
                })
        
        if errors:
            return DiagnosticResult(
                status="error",
                message=f"{len(errors)} of {len(sample_indices)} sampled segments missing",
                details={"sampled": results, "total_segments": len(segments)}
            )
        
        return DiagnosticResult(
            status="ok",
            message=f"All {len(sample_indices)} sampled segments accessible",
            details={"sampled": results, "total_segments": len(segments)}
        )
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"Segment check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_video_codecs(url: str) -> DiagnosticResult:
    """Проверяет кодеки видео через ffprobe (если доступен)."""
    try:
        cmd = [
            "ffprobe", "-v", "quiet",
            "-print_format", "json",
            "-show_streams", "-show_format",
            "-analyzeduration", "5000000",  # 5 секунд
            "-probesize", "5000000",
            url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        
        if result.returncode != 0:
            return DiagnosticResult(
                status="warning",
                message="ffprobe failed to analyze video",
                details={"stderr": result.stderr[:500] if result.stderr else ""}
            )
        
        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        format_info = data.get("format", {})
        
        video_codec = None
        audio_codec = None
        for s in streams:
            if s.get("codec_type") == "video" and not video_codec:
                video_codec = s.get("codec_name")
            if s.get("codec_type") == "audio" and not audio_codec:
                audio_codec = s.get("codec_name")
        
        # Проверяем moov atom (faststart)
        # Если format_name содержит "mov,mp4" и tags.encoder существует - скорее всего faststart ok
        
        issues = []
        if video_codec and video_codec not in ("h264", "avc1", "hevc", "h265"):
            issues.append(f"Non-standard video codec: {video_codec}")
        if audio_codec and audio_codec not in ("aac", "mp3", "opus"):
            issues.append(f"Non-standard audio codec: {audio_codec}")
        if not audio_codec:
            issues.append("No audio track detected")
        
        return DiagnosticResult(
            status="warning" if issues else "ok",
            message=f"Video: {video_codec or 'none'}, Audio: {audio_codec or 'none'}",
            details={
                "video_codec": video_codec,
                "audio_codec": audio_codec,
                "duration": format_info.get("duration"),
                "bitrate": format_info.get("bit_rate"),
                "issues": issues,
            }
        )
    except subprocess.TimeoutExpired:
        return DiagnosticResult(
            status="warning",
            message="ffprobe timed out (video may be slow to load)",
            details={"timeout": 30}
        )
    except FileNotFoundError:
        return DiagnosticResult(
            status="warning",
            message="ffprobe not available",
            details={}
        )
    except Exception as e:
        return DiagnosticResult(
            status="warning",
            message=f"Codec check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def find_hls_playlists(mp4_key: str) -> List[str]:
    """Находит все HLS плейлисты для данного MP4."""
    base_dir = mp4_key.rsplit("/", 1)[0] if "/" in mp4_key else ""
    hls_prefix = f"{base_dir}/.hls/" if base_dir else ".hls/"
    
    playlists = []
    try:
        paginator = s3.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("playlist.m3u8"):
                    playlists.append(key)
    except Exception as e:
        logger.warning(f"Failed to list HLS playlists: {e}")
    
    return playlists


def diagnose_video(video_url: str) -> VideoHealth:
    """Выполняет полную диагностику видео."""
    s3_key = key_from_url(video_url)
    health = VideoHealth(
        video_url=video_url,
        s3_key=s3_key,
        overall_status="unknown"
    )
    
    # 1. Проверка исходного MP4 в S3
    health.checks["s3_mp4"] = check_s3_object(s3_key)
    
    # 2. Проверка доступности через CDN
    cdn_url = safe_cdn_url(s3_key)
    health.checks["cdn_mp4"] = check_cdn_access(cdn_url)
    
    # 3. Проверка оригинального URL (если отличается)
    if video_url != cdn_url:
        health.checks["original_url"] = check_cdn_access(video_url)
    
    # 4. Поиск и проверка HLS плейлистов
    hls_playlists = find_hls_playlists(s3_key)
    if hls_playlists:
        health.checks["hls_found"] = DiagnosticResult(
            status="ok",
            message=f"Found {len(hls_playlists)} HLS playlist(s)",
            details={"playlists": hls_playlists}
        )
        
        # Проверяем первый (обычно canonical) плейлист
        for pl_key in hls_playlists[:2]:  # Проверяем максимум 2
            pl_name = pl_key.split("/")[-2] if "/" in pl_key else "playlist"
            health.checks[f"hls_playlist_{pl_name}"] = check_hls_playlist(pl_key)
            health.checks[f"hls_segments_{pl_name}"] = check_hls_segments(pl_key)
            
            # Проверяем доступность через CDN
            pl_cdn_url = safe_cdn_url(pl_key)
            health.checks[f"hls_cdn_{pl_name}"] = check_cdn_access(pl_cdn_url)
    else:
        health.checks["hls_found"] = DiagnosticResult(
            status="warning",
            message="No HLS playlists found",
            details={"searched_prefix": f"{s3_key.rsplit('/', 1)[0]}/.hls/"}
        )
    
    # 5. Проверка кодеков (через CDN URL)
    health.checks["codecs"] = check_video_codecs(cdn_url)
    
    # Определяем общий статус и рекомендации
    errors = sum(1 for c in health.checks.values() if c.status == "error")
    warnings = sum(1 for c in health.checks.values() if c.status == "warning")
    
    if errors > 0:
        health.overall_status = "broken"
    elif warnings > 0:
        health.overall_status = "degraded"
    else:
        health.overall_status = "healthy"
    
    # Рекомендации
    if health.checks.get("cdn_mp4", DiagnosticResult("error", "")).status == "error":
        if "520" in health.checks.get("cdn_mp4", DiagnosticResult("", "")).message:
            health.recommendations.append("Ошибка 520 указывает на проблемы с origin сервером (Timeweb S3). Попробуйте Magic Button или подождите.")
    
    if health.checks.get("s3_mp4"):
        details = health.checks["s3_mp4"].details
        if details.get("faststart") != "true":
            health.recommendations.append("Видео не имеет faststart метаданных. Рекомендуется перезалить с -movflags +faststart.")
        if details.get("hls") != "true":
            health.recommendations.append("HLS не помечен как готовый. Используйте Magic Button для генерации.")
    
    if health.checks.get("hls_found", DiagnosticResult("error", "")).status == "warning":
        health.recommendations.append("HLS плейлисты не найдены. Используйте Magic Button для генерации.")
    
    for key, check in health.checks.items():
        if "segments" in key and check.status == "error":
            health.recommendations.append(f"Некоторые HLS сегменты отсутствуют. Требуется пересборка через Magic Button.")
            break
    
    if health.checks.get("codecs"):
        details = health.checks["codecs"].details
        if details.get("issues"):
            for issue in details["issues"]:
                health.recommendations.append(f"Проблема с кодеками: {issue}")
    
    return health


class DiagnoseRequest(BaseModel):
    video_url: str


@router.post("/diagnose")
def diagnose_video_endpoint(
    req: DiagnoseRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Диагностика видео: проверяет MP4, CDN доступность, HLS сегменты, кодеки.
    Помогает выявить причины ошибок 520 и остановки видео.
    """
    health = diagnose_video(req.video_url)
    
    # Конвертируем в dict
    result = {
        "video_url": health.video_url,
        "s3_key": health.s3_key,
        "overall_status": health.overall_status,
        "checks": {k: asdict(v) for k, v in health.checks.items()},
        "recommendations": health.recommendations,
    }
    
    return result


@router.get("/diagnose")
def diagnose_video_get(
    video_url: str = Query(..., description="URL видео для диагностики"),
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """GET версия диагностики для удобства."""
    health = diagnose_video(video_url)
    
    return {
        "video_url": health.video_url,
        "s3_key": health.s3_key,
        "overall_status": health.overall_status,
        "checks": {k: asdict(v) for k, v in health.checks.items()},
        "recommendations": health.recommendations,
    }


@router.get("/quick-check")
def quick_check(
    video_url: str = Query(..., description="URL видео"),
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Быстрая проверка доступности видео (только HEAD запросы).
    """
    s3_key = key_from_url(video_url)
    cdn_url = safe_cdn_url(s3_key)
    
    results = {
        "video_url": video_url,
        "s3_key": s3_key,
        "cdn_url": cdn_url,
    }
    
    # S3 check
    results["s3_status"] = check_s3_object(s3_key).status
    
    # CDN check
    cdn_result = check_cdn_access(cdn_url, timeout=5)
    results["cdn_status"] = cdn_result.status
    results["cdn_message"] = cdn_result.message
    
    # HLS check
    hls_playlists = find_hls_playlists(s3_key)
    results["hls_count"] = len(hls_playlists)
    if hls_playlists:
        pl_cdn_url = safe_cdn_url(hls_playlists[0])
        results["hls_url"] = pl_cdn_url
        hls_cdn = check_cdn_access(pl_cdn_url, timeout=5)
        results["hls_cdn_status"] = hls_cdn.status
    
    return results


def check_moov_position(url: str) -> DiagnosticResult:
    """
    Проверяет позицию moov atom в MP4 файле.
    moov в начале = faststart, moov в конце = медленная загрузка.
    """
    try:
        # Используем ffprobe с show_format для проверки
        cmd = [
            "ffprobe", "-v", "trace",
            "-show_format",
            "-i", url
        ]
        result = subprocess.run(
            cmd, 
            capture_output=True, 
            text=True, 
            timeout=15
        )
        
        stderr = result.stderr or ""
        
        # Ищем позицию moov atom в выводе trace
        moov_pos = None
        mdat_pos = None
        
        for line in stderr.split("\n"):
            if "type:'moov'" in line or "type: moov" in line:
                # Пытаемся извлечь позицию
                if "pos:" in line:
                    try:
                        pos_str = line.split("pos:")[1].split()[0]
                        moov_pos = int(pos_str)
                    except:
                        pass
            if "type:'mdat'" in line or "type: mdat" in line:
                if "pos:" in line:
                    try:
                        pos_str = line.split("pos:")[1].split()[0]
                        mdat_pos = int(pos_str)
                    except:
                        pass
        
        if moov_pos is not None and mdat_pos is not None:
            if moov_pos < mdat_pos:
                return DiagnosticResult(
                    status="ok",
                    message="faststart OK (moov before mdat)",
                    details={"moov_position": moov_pos, "mdat_position": mdat_pos}
                )
            else:
                return DiagnosticResult(
                    status="warning",
                    message="NO faststart (moov after mdat) - видео будет долго загружаться",
                    details={
                        "moov_position": moov_pos, 
                        "mdat_position": mdat_pos,
                        "recommendation": "Используйте ffmpeg -movflags +faststart"
                    }
                )
        
        return DiagnosticResult(
            status="warning",
            message="Could not determine moov position",
            details={}
        )
        
    except subprocess.TimeoutExpired:
        return DiagnosticResult(
            status="warning",
            message="moov check timed out",
            details={}
        )
    except Exception as e:
        return DiagnosticResult(
            status="warning",
            message=f"moov check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


class ApplyFaststartRequest(BaseModel):
    video_url: str
    force: bool = False  # Принудительно применить даже если метаданные уже есть


@router.post("/apply-faststart")
def apply_faststart_endpoint(
    req: ApplyFaststartRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Запускает задачу применения faststart к видео.
    Это перемещает moov atom в начало файла, что ускоряет начало воспроизведения.
    """
    from ..tasks.fast_start import process_faststart_video
    from ..celery_app import celery as celery_app
    
    s3_key = key_from_url(req.video_url)
    
    # Проверяем существование файла
    check = check_s3_object(s3_key)
    if check.status == "error":
        raise HTTPException(status_code=404, detail=f"Video not found: {check.message}")
    
    # Проверяем метаданные faststart
    if not req.force and check.details.get("faststart") == "true":
        return {
            "status": "skipped",
            "message": "Video already has faststart metadata",
            "s3_key": s3_key
        }
    
    # Запускаем задачу
    task = process_faststart_video.apply_async(args=[s3_key], queue="special")
    
    return {
        "status": "queued",
        "task_id": task.id,
        "s3_key": s3_key,
        "message": "Faststart task queued. Video will be re-uploaded with moov atom at start."
    }


@router.post("/full-repair")
def full_repair_endpoint(
    req: DiagnoseRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Полный ремонт видео:
    1. Применяет faststart (если нужно)
    2. Пересобирает HLS
    3. Создаёт alias'ы
    """
    from ..tasks.ensure_hls import validate_and_fix_hls
    from ..tasks.fast_start import process_faststart_video
    
    s3_key = key_from_url(req.video_url)
    
    # Проверяем существование
    check = check_s3_object(s3_key)
    if check.status == "error":
        raise HTTPException(status_code=404, detail=f"Video not found: {check.message}")
    
    tasks = []
    
    # 1. Faststart (если нужно)
    if check.details.get("faststart") != "true":
        fs_task = process_faststart_video.apply_async(args=[s3_key], queue="special")
        tasks.append({"type": "faststart", "task_id": fs_task.id})
    
    # 2. HLS repair
    hls_task = validate_and_fix_hls.apply_async(
        args=[{"video_url": req.video_url}],
        queue="special_hls"
    )
    tasks.append({"type": "hls_repair", "task_id": hls_task.id})
    
    return {
        "status": "queued",
        "s3_key": s3_key,
        "tasks": tasks,
        "message": "Full repair started. This may take several minutes."
    }


@router.get("/check-moov")
def check_moov_endpoint(
    video_url: str = Query(..., description="URL видео"),
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Проверяет позицию moov atom (faststart).
    """
    cdn_url = safe_cdn_url(key_from_url(video_url))
    result = check_moov_position(cdn_url)
    
    return {
        "video_url": video_url,
        "cdn_url": cdn_url,
        **asdict(result)
    }

