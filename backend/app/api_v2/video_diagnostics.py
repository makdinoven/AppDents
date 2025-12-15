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

from ..dependencies.role_checker import require_roles
from ..models.models import User

logger = logging.getLogger(__name__)

router = APIRouter()

# S3 Config
S3_ENDPOINT = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_BUCKET = os.getenv("S3_BUCKET", "cdn.dent-s.com")
S3_REGION = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

# S3 клиенты: v2 для чтения/записи объектов, v4 для листинга
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

s3_v4 = boto3.client(
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
    """Проверяет HLS playlist и считает сегменты. Следует по alias'ам."""
    try:
        # Сначала пробуем прочитать плейлист напрямую
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
            content = obj["Body"].read().decode("utf-8", errors="replace")
            resolved_key = key
            is_alias = False
        except ClientError as e:
            # Если не найден - логируем и возвращаем ошибку
            code = e.response["Error"]["Code"]
            if code in ("NoSuchKey", "404"):
                return DiagnosticResult(
                    status="error",
                    message=f"Playlist not found in S3",
                    details={"s3_key": key, "error_code": code, "bucket": S3_BUCKET}
                )
            raise
        
        # Проверяем, является ли это alias'ом (указывает на другой m3u8)
        m3u8_target = None
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and line.endswith(".m3u8"):
                m3u8_target = line
                break
        
        if m3u8_target:
            # Это alias - резолвим целевой плейлист
            # ВАЖНО: S3 может хранить ключи с %20 или с пробелами - пробуем оба варианта
            if m3u8_target.startswith("http://") or m3u8_target.startswith("https://"):
                target_key_decoded = key_from_url(m3u8_target)  # с пробелами
                # Также пробуем URL path напрямую (с %20)
                parsed = urlparse(m3u8_target)
                target_key_encoded = parsed.path.lstrip("/")
            else:
                base_dir = key.rsplit("/", 1)[0] if "/" in key else ""
                target_key_decoded = f"{base_dir}/{m3u8_target}" if base_dir else m3u8_target
                target_key_encoded = target_key_decoded  # для относительных путей - то же самое
            
            # Пробуем прочитать целевой плейлист - сначала decoded, потом encoded
            target_key = None
            for try_key in [target_key_decoded, target_key_encoded]:
                if not try_key:
                    continue
                try:
                    obj = s3.get_object(Bucket=S3_BUCKET, Key=try_key)
                    content = obj["Body"].read().decode("utf-8", errors="replace")
                    resolved_key = try_key
                    target_key = try_key
                    is_alias = True
                    break
                except ClientError:
                    continue
            
            if not target_key:
                # Целевой плейлист не найден ни с каким ключом - ЭТО ОШИБКА!
                return DiagnosticResult(
                    status="error",
                    message=f"Alias → target playlist MISSING in S3",
                    details={
                        "is_alias": True,
                        "alias_key": key,
                        "target": m3u8_target,
                        "tried_keys": [target_key_decoded, target_key_encoded],
                        "note": "Alias exists but target playlist missing - HLS BROKEN, needs Full Repair"
                    }
                )
        
        if not content.strip().startswith("#EXTM3U"):
            return DiagnosticResult(
                status="error",
                message="Invalid HLS playlist (no #EXTM3U header)",
                details={"first_100_chars": content[:100]}
            )
        
        # Считаем реальные сегменты (.ts, .m4s)
        segments = []
        m3u8_refs = []
        lines = content.strip().split("\n")
        for line in lines:
            line = line.strip()
            if line and not line.startswith("#"):
                if line.endswith(".ts") or line.endswith(".m4s"):
                    segments.append(line)
                elif line.endswith(".m3u8"):
                    m3u8_refs.append(line)
        
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
        
        # Если это alias (указывает на другой m3u8)
        if m3u8_refs and not segments:
            return DiagnosticResult(
                status="ok",
                message=f"Alias playlist → {m3u8_refs[0][:60]}...",
                details={
                    "is_alias": True,
                    "target": m3u8_refs[0],
                    "resolved_key": resolved_key,
                    "original_key": key if is_alias else None,
                }
            )
        
        return DiagnosticResult(
            status="ok" if segments else "warning",
            message=f"Found {len(segments)} segments, {total_duration:.1f}s total" + (" (via alias)" if is_alias else ""),
            details={
                "segment_count": len(segments),
                "total_duration_sec": total_duration,
                "has_endlist": has_endlist,
                "is_alias": is_alias,
                "resolved_key": resolved_key if is_alias else None,
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
    """Проверяет доступность нескольких HLS сегментов. Следует по alias'ам."""
    try:
        # Пробуем прочитать плейлист
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=playlist_key)
            content = obj["Body"].read().decode("utf-8", errors="replace")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            return DiagnosticResult(
                status="error",
                message=f"Segment check failed: {code}",
                details={"playlist_key": playlist_key, "error_code": code}
            )
        
        resolved_key = playlist_key
        is_alias = False
        
        # Проверяем, является ли это alias'ом (указывает на другой m3u8)
        m3u8_target = None
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and line.endswith(".m3u8"):
                m3u8_target = line
                break
        
        if m3u8_target:
            # Это alias - резолвим целевой плейлист
            # ВАЖНО: S3 может хранить ключи с %20 или с пробелами - пробуем оба варианта
            if m3u8_target.startswith("http://") or m3u8_target.startswith("https://"):
                target_key_decoded = key_from_url(m3u8_target)
                parsed = urlparse(m3u8_target)
                target_key_encoded = parsed.path.lstrip("/")
            else:
                base_dir = playlist_key.rsplit("/", 1)[0] if "/" in playlist_key else ""
                target_key_decoded = f"{base_dir}/{m3u8_target}" if base_dir else m3u8_target
                target_key_encoded = target_key_decoded
            
            # Пробуем прочитать целевой плейлист - сначала decoded, потом encoded
            target_key = None
            for try_key in [target_key_decoded, target_key_encoded]:
                if not try_key:
                    continue
                try:
                    obj = s3.get_object(Bucket=S3_BUCKET, Key=try_key)
                    content = obj["Body"].read().decode("utf-8", errors="replace")
                    resolved_key = try_key
                    target_key = try_key
                    is_alias = True
                    break
                except ClientError:
                    continue
            
            if not target_key:
                # Целевой плейлист не найден - ОШИБКА!
                return DiagnosticResult(
                    status="error",
                    message=f"Alias → target segments MISSING",
                    details={
                        "is_alias": True, 
                        "target": m3u8_target, 
                        "tried_keys": [target_key_decoded, target_key_encoded],
                        "note": "Target playlist missing - no segments available"
                    }
                )
        
        segments = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and (line.endswith(".ts") or line.endswith(".m4s")):
                segments.append(line)
        
        if not segments:
            # Проверим, не alias ли это на другой плейлист (вложенный)
            m3u8_refs = [l.strip() for l in content.split("\n") 
                        if l.strip() and not l.strip().startswith("#") and l.strip().endswith(".m3u8")]
            if m3u8_refs:
                return DiagnosticResult(
                    status="ok",
                    message=f"Nested alias playlist → {m3u8_refs[0][:50]}...",
                    details={"is_alias": True, "target": m3u8_refs[0], "resolved_key": resolved_key}
                )
            
            return DiagnosticResult(
                status="error",
                message="No segments found in playlist",
                details={"resolved_key": resolved_key, "is_alias": is_alias}
            )
        
        # Берём первый, средний и последний сегмент
        sample_indices = [0]
        if len(segments) > 1:
            sample_indices.append(len(segments) // 2)
        if len(segments) > 2:
            sample_indices.append(len(segments) - 1)
        
        base_dir = resolved_key.rsplit("/", 1)[0] if "/" in resolved_key else ""
        
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
                details={"sampled": results, "total_segments": len(segments), "resolved_key": resolved_key}
            )
        
        return DiagnosticResult(
            status="ok",
            message=f"All {len(sample_indices)} sampled segments accessible" + (" (via alias)" if is_alias else ""),
            details={"sampled": results, "total_segments": len(segments), "resolved_key": resolved_key, "is_alias": is_alias}
        )
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"Segment check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_hls_segments_cdn(playlist_key: str, sample_count: int = 5, timeout: int = 20) -> DiagnosticResult:
    """
    Проверяет доступность HLS сегментов через CDN с реальным GET запросом.
    Делает "стресс-тест": несколько запросов подряд для выявления rate limiting.
    """
    import time
    import concurrent.futures
    
    try:
        # Читаем плейлист из S3
        try:
            obj = s3.get_object(Bucket=S3_BUCKET, Key=playlist_key)
            content = obj["Body"].read().decode("utf-8", errors="replace")
        except ClientError as e:
            code = e.response["Error"]["Code"]
            return DiagnosticResult(
                status="error",
                message=f"Cannot read playlist: {code}",
                details={"playlist_key": playlist_key}
            )
        
        resolved_key = playlist_key
        
        # Проверяем, является ли это alias'ом
        m3u8_target = None
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and line.endswith(".m3u8"):
                m3u8_target = line
                break
        
        if m3u8_target:
            # Резолвим alias
            if m3u8_target.startswith("http://") or m3u8_target.startswith("https://"):
                target_key = key_from_url(m3u8_target)
            else:
                base_dir = playlist_key.rsplit("/", 1)[0] if "/" in playlist_key else ""
                target_key = f"{base_dir}/{m3u8_target}" if base_dir else m3u8_target
            
            try:
                obj = s3.get_object(Bucket=S3_BUCKET, Key=target_key)
                content = obj["Body"].read().decode("utf-8", errors="replace")
                resolved_key = target_key
            except ClientError:
                return DiagnosticResult(
                    status="error",
                    message="Alias target not found",
                    details={"alias": playlist_key, "target": m3u8_target}
                )
        
        # Собираем сегменты
        segments = []
        for line in content.strip().split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and (line.endswith(".ts") or line.endswith(".m4s")):
                segments.append(line)
        
        if not segments:
            return DiagnosticResult(
                status="warning",
                message="No segments to check via CDN",
                details={"resolved_key": resolved_key}
            )
        
        # Берём первые 5-7 сегментов подряд - это имитирует начало воспроизведения
        # Проблемы часто возникают после первого сегмента при rate limiting
        sample_indices = list(range(min(sample_count, len(segments))))
        
        base_dir = resolved_key.rsplit("/", 1)[0] if "/" in resolved_key else ""
        
        def check_segment(idx: int) -> dict:
            """Проверяет один сегмент через CDN."""
            seg_name = segments[idx]
            seg_key = f"{base_dir}/{seg_name}" if base_dir else seg_name
            seg_cdn_url = safe_cdn_url(seg_key)
            
            try:
                # Делаем полный GET запрос (не Range) чтобы лучше имитировать браузер
                # Но читаем только первые 256KB чтобы не качать всё
                start_time = time.time()
                resp = requests.get(seg_cdn_url, timeout=timeout, stream=True)
                
                if resp.status_code in (200, 206):
                    # Читаем 256KB данных - это больше чем Range request
                    # и лучше показывает реальное поведение
                    bytes_read = 0
                    try:
                        for chunk in resp.iter_content(chunk_size=65536):
                            bytes_read += len(chunk)
                            if bytes_read >= 262144:  # 256KB
                                break
                    finally:
                        resp.close()
                    
                    elapsed = time.time() - start_time
                    return {
                        "index": idx,
                        "name": seg_name,
                        "status": "ok",
                        "http_status": resp.status_code,
                        "content_length": resp.headers.get("Content-Length"),
                        "bytes_read": bytes_read,
                        "time_sec": round(elapsed, 2),
                    }
                else:
                    resp.close()
                    return {
                        "index": idx,
                        "name": seg_name,
                        "status": "error",
                        "http_status": resp.status_code,
                        "error": f"HTTP {resp.status_code}"
                    }
                    
            except requests.Timeout:
                return {
                    "index": idx,
                    "name": seg_name,
                    "status": "timeout",
                    "error": f"Timeout after {timeout}s"
                }
            except requests.RequestException as e:
                error_type = type(e).__name__
                return {
                    "index": idx,
                    "name": seg_name,
                    "status": "error",
                    "error": f"{error_type}: {str(e)[:100]}"
                }
        
        # Сначала делаем последовательные запросы (как при воспроизведении)
        results = []
        errors = []
        
        for idx in sample_indices:
            result = check_segment(idx)
            results.append(result)
            if result["status"] != "ok":
                errors.append(result["name"])
            # Небольшая пауза между запросами - как при реальном воспроизведении
            time.sleep(0.1)
        
        # Теперь делаем параллельный тест (3 запроса одновременно)
        # Это имитирует поведение браузера с prefetch
        parallel_results = []
        parallel_errors = []
        
        if len(segments) > sample_count + 3:
            parallel_indices = [sample_count, sample_count + 1, sample_count + 2]
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                futures = {executor.submit(check_segment, idx): idx for idx in parallel_indices}
                for future in concurrent.futures.as_completed(futures, timeout=timeout + 5):
                    try:
                        result = future.result()
                        parallel_results.append(result)
                        if result["status"] != "ok":
                            parallel_errors.append(result["name"])
                    except Exception as e:
                        parallel_results.append({
                            "index": futures[future],
                            "status": "error",
                            "error": f"Future error: {str(e)[:50]}"
                        })
                        parallel_errors.append(f"segment_{futures[future]}")
        
        all_errors = errors + parallel_errors
        
        if all_errors:
            return DiagnosticResult(
                status="error",
                message=f"{len(all_errors)} segments FAILED via CDN (sequential: {len(errors)}, parallel: {len(parallel_errors)})",
                details={
                    "sequential_results": results,
                    "parallel_results": parallel_results,
                    "total_segments": len(segments),
                    "resolved_key": resolved_key,
                    "failed_segments": all_errors,
                    "note": "Segments fail to load via CDN. May indicate rate limiting or HTTP/2 issues."
                }
            )
        
        # Проверяем время ответа - если слишком долго, это тоже проблема
        slow_segments = [r for r in results if r.get("time_sec", 0) > 5]
        if slow_segments:
            return DiagnosticResult(
                status="warning",
                message=f"Segments load but {len(slow_segments)} are slow (>5s)",
                details={
                    "sequential_results": results,
                    "parallel_results": parallel_results,
                    "total_segments": len(segments),
                    "slow_segments": slow_segments,
                    "note": "Some segments take too long to load. May cause playback issues."
                }
            )
        
        return DiagnosticResult(
            status="ok",
            message=f"All {len(results) + len(parallel_results)} segments load OK via CDN",
            details={
                "sequential_results": results,
                "parallel_results": parallel_results,
                "total_segments": len(segments)
            }
        )
        
    except Exception as e:
        return DiagnosticResult(
            status="error",
            message=f"CDN segment check failed: {type(e).__name__}",
            details={"error": str(e)}
        )


def check_hls_acl(playlist_keys: List[str], sample_count: int = 3) -> DiagnosticResult:
    """
    Проверяет ACL нескольких HLS файлов.
    Возвращает ошибку если файлы не публичные.
    """
    if not playlist_keys:
        return DiagnosticResult(
            status="warning",
            message="No HLS playlists to check ACL",
            details={}
        )
    
    checked = []
    private_files = []
    errors = []
    
    for pl_key in playlist_keys[:sample_count]:
        try:
            # Получаем ACL файла
            acl_response = s3.get_object_acl(Bucket=S3_BUCKET, Key=pl_key)
            grants = acl_response.get("Grants", [])
            
            # Проверяем есть ли public-read grant
            is_public = False
            for grant in grants:
                grantee = grant.get("Grantee", {})
                permission = grant.get("Permission", "")
                # AllUsers URI означает публичный доступ
                if grantee.get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers":
                    if permission in ("READ", "FULL_CONTROL"):
                        is_public = True
                        break
            
            checked.append({
                "key": pl_key,
                "is_public": is_public,
                "grants_count": len(grants)
            })
            
            if not is_public:
                private_files.append(pl_key)
                
        except ClientError as e:
            code = e.response["Error"]["Code"]
            errors.append({"key": pl_key, "error": code})
        except Exception as e:
            errors.append({"key": pl_key, "error": str(e)})
    
    if private_files:
        return DiagnosticResult(
            status="error",
            message=f"{len(private_files)} of {len(checked)} HLS files are PRIVATE",
            details={
                "private_files": private_files[:5],
                "checked": checked,
                "errors": errors,
                "recommendation": "Use 'Fix ACL' button to make HLS files public"
            }
        )
    
    if errors:
        return DiagnosticResult(
            status="warning",
            message=f"ACL check had {len(errors)} errors",
            details={"errors": errors, "checked": checked}
        )
    
    return DiagnosticResult(
        status="ok",
        message=f"All {len(checked)} checked HLS files are public",
        details={"checked": checked}
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


def _compute_slugs_for_mp4(mp4_key: str) -> List[str]:
    """Вычисляет возможные слуги для MP4 файла (как на бэке)."""
    import hashlib
    import unicodedata
    import re
    from pathlib import Path
    
    fname = mp4_key.rsplit("/", 1)[-1] if "/" in mp4_key else mp4_key
    stem = Path(fname).stem
    
    SLUG_MAX = 60
    
    def legacy_slug(name: str) -> str:
        ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        base = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower()
        if not base:
            return hashlib.sha1(name.encode()).hexdigest()[:SLUG_MAX]
        return base[:SLUG_MAX]
    
    def stable_slug(name: str) -> str:
        ascii_name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
        base = re.sub(r"[^A-Za-z0-9]+", "-", ascii_name).strip("-").lower()
        if not base:
            return hashlib.sha1(name.encode()).hexdigest()[:SLUG_MAX]
        if len(base) <= SLUG_MAX:
            return base
        suffix = hashlib.sha1(name.encode()).hexdigest()[:8]
        keep = SLUG_MAX - 1 - len(suffix)
        return f"{base[:keep]}-{suffix}"
    
    slugs = []
    slugs.append(legacy_slug(stem))
    stable = stable_slug(stem)
    if stable not in slugs:
        slugs.append(stable)
    
    return slugs


def find_hls_playlists(mp4_key: str, only_matching: bool = True) -> List[str]:
    """
    Находит HLS плейлисты для данного MP4.
    
    Args:
        mp4_key: S3 ключ MP4 файла
        only_matching: Если True, возвращает только плейлисты, соответствующие slug'у видео
    """
    base_dir = mp4_key.rsplit("/", 1)[0] if "/" in mp4_key else ""
    hls_prefix = f"{base_dir}/.hls/" if base_dir else ".hls/"
    
    playlists = []
    try:
        # Используем s3_v4 для листинга (требуется для корректной работы с пробелами)
        paginator = s3_v4.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_prefix):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                if key.endswith("playlist.m3u8"):
                    playlists.append(key)
    except Exception as e:
        logger.warning(f"Failed to list HLS playlists: {e}")
    
    if not only_matching:
        return playlists
    
    # Фильтруем по slug'ам, соответствующим этому MP4
    expected_slugs = _compute_slugs_for_mp4(mp4_key)
    
    matching = []
    for pl in playlists:
        # Извлекаем slug из пути: base/.hls/{slug}/playlist.m3u8
        parts = pl.split("/")
        if len(parts) >= 2 and parts[-1] == "playlist.m3u8":
            slug_dir = parts[-2]
            # Проверяем, начинается ли slug_dir с одного из ожидаемых слугов
            for expected in expected_slugs:
                if slug_dir.startswith(expected) or expected.startswith(slug_dir.rstrip("-0123456789abcdef")[:20]):
                    matching.append(pl)
                    break
    
    return matching if matching else playlists[:5]  # Fallback: первые 5 если ничего не нашли


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
            
            # Проверяем доступность сегментов через CDN (выявляет HTTP/2 ошибки и rate limiting)
            health.checks[f"hls_segments_cdn_{pl_name}"] = check_hls_segments_cdn(pl_key)
        
        # 4.1. Проверка ACL HLS файлов
        health.checks["hls_acl"] = check_hls_acl(hls_playlists)
    else:
        health.checks["hls_found"] = DiagnosticResult(
            status="warning",
            message="No HLS playlists found",
            details={"searched_prefix": f"{s3_key.rsplit('/', 1)[0]}/.hls/"}
        )
    
    # 5. Проверка кодеков (через CDN URL)
    health.checks["codecs"] = check_video_codecs(cdn_url)
    
    # Определяем общий статус и рекомендации
    # НЕ считаем ошибкой: alias плейлисты, таймауты ffprobe, S3 ошибки когда CDN работает
    
    def is_real_error(key: str, check: DiagnosticResult) -> bool:
        if check.status != "error":
            return False
        
        # КРИТИЧЕСКИЕ ошибки - всегда считаются реальными
        if "MISSING" in check.message:
            return True  # Target playlist/segments отсутствуют
        if "target playlist missing" in check.details.get("note", "").lower():
            return True
        
        # Приватные HLS файлы - критическая ошибка
        if key == "hls_acl" and "PRIVATE" in check.message:
            return True
        
        # Сегменты недоступны через CDN - критическая ошибка
        if "segments_cdn" in key and "FAILED via CDN" in check.message:
            return True
        
        # Alias плейлисты которые работают - не ошибка
        if check.details.get("is_alias") and "MISSING" not in check.message:
            return False
        # Если сегменты показывают работающий alias - это OK
        if "segments" in key and "Alias playlist" in check.message and "MISSING" not in check.message:
            return False
        
        # Если HLS playlist не найден в S3, но CDN работает - это может быть кэш
        # НО только если это не alias с отсутствующим target
        if "playlist" in key and "not found" in check.message.lower() and "MISSING" not in check.message:
            cdn_key = key.replace("playlist", "cdn")
            if cdn_key in health.checks and health.checks[cdn_key].status == "ok":
                return False  # CDN работает - значит HLS функционирует
        
        return True
    
    def is_real_warning(key: str, check: DiagnosticResult) -> bool:
        if check.status != "warning":
            return False
        # ffprobe timeout для больших файлов - не критично
        if "codecs" in key and "timed out" in check.message:
            return False
        return True
    
    errors = sum(1 for k, c in health.checks.items() if is_real_error(k, c))
    warnings = sum(1 for k, c in health.checks.items() if is_real_warning(k, c))
    
    # Дополнительно: если CDN для MP4 и HLS работает - видео функционирует
    mp4_cdn_ok = health.checks.get("cdn_mp4", DiagnosticResult("error", "")).status == "ok"
    hls_cdn_ok = any(
        c.status == "ok" 
        for k, c in health.checks.items() 
        if k.startswith("hls_cdn_")
    )
    
    if errors > 0:
        # Но если всё работает через CDN - это "degraded", не "broken"
        if mp4_cdn_ok and hls_cdn_ok:
            health.overall_status = "degraded"
        else:
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
        if details.get("faststart") != "true" and details.get("faststart") != "unknown":
            health.recommendations.append("Видео не имеет faststart метаданных. Рекомендуется перезалить с -movflags +faststart.")
        if details.get("hls") != "true":
            health.recommendations.append("HLS не помечен как готовый. Используйте Magic Button для генерации.")
    
    if health.checks.get("hls_found", DiagnosticResult("error", "")).status == "warning":
        health.recommendations.append("HLS плейлисты не найдены. Используйте Magic Button для генерации.")
    
    # Проверяем критические ошибки HLS: alias с отсутствующим target
    for key, check in health.checks.items():
        if check.status == "error" and "MISSING" in check.message:
            health.recommendations.append(
                "HLS alias указывает на отсутствующий плейлист. Требуется Full Repair для пересборки HLS."
            )
            break
    
    # Проверяем только реальные ошибки сегментов
    for key, check in health.checks.items():
        if "segments" in key and check.status == "error":
            # Если уже добавили рекомендацию про MISSING - пропускаем
            if "MISSING" in check.message:
                continue
            # Пропускаем если это работающий alias
            if check.details.get("is_alias") and "MISSING" not in check.message:
                continue
            health.recommendations.append(f"Некоторые HLS сегменты отсутствуют. Требуется пересборка через Full Repair.")
            break
    
    if health.checks.get("codecs"):
        details = health.checks["codecs"].details
        if details.get("issues"):
            for issue in details["issues"]:
                health.recommendations.append(f"Проблема с кодеками: {issue}")
    
    # Проверяем ACL HLS файлов
    if health.checks.get("hls_acl"):
        acl_check = health.checks["hls_acl"]
        if acl_check.status == "error" and "PRIVATE" in acl_check.message:
            health.recommendations.append(
                "HLS файлы приватные и недоступны через CDN. Нажмите 'Fix ACL' для исправления."
            )
    
    # Проверяем доступность сегментов через CDN
    for key, check in health.checks.items():
        if "segments_cdn" in key and check.status == "error":
            failed_segments = check.details.get("failed_segments", [])
            health.recommendations.append(
                f"Сегменты HLS недоступны через CDN ({len(failed_segments)} ошибок). "
                "Возможные причины: HTTP/2 ошибки, rate limiting, проблемы с CDN. "
                "Попробуйте 'Force Rebuild' для пересоздания HLS."
            )
            break
        elif "segments_cdn" in key and check.status == "warning":
            slow_count = len(check.details.get("slow_segments", []))
            health.recommendations.append(
                f"Сегменты HLS загружаются слишком медленно ({slow_count} сегментов >5s). "
                "Это может вызывать остановки при воспроизведении. "
                "Возможные причины: rate limiting, перегрузка S3/CDN."
            )
            break
    
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
    4. Исправляет ACL на public-read
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
    
    # 3. Fix ACL для существующих HLS файлов (синхронно, быстро)
    acl_result = _fix_hls_acl_for_video(req.video_url, dry_run=False)
    acl_fixed = acl_result.get("summary", {}).get("fixed", 0)
    
    return {
        "status": "queued",
        "s3_key": s3_key,
        "tasks": tasks,
        "acl_fixed": acl_fixed,
        "message": f"Full repair started. ACL fixed for {acl_fixed} existing files. HLS rebuild may take several minutes."
    }


@router.post("/force-rebuild-hls")
def force_rebuild_hls_endpoint(
    req: DiagnoseRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Принудительная пересборка HLS:
    1. Удаляет ВСЕ HLS файлы для видео (включая с %20 в именах)
    2. Запускает свежую генерацию HLS
    
    Используйте когда HLS файлы повреждены или имеют проблемы с кодировкой путей.
    Всё выполняется асинхронно через Celery.
    """
    from ..tasks.ensure_hls import force_rebuild_hls_task
    
    s3_key = key_from_url(req.video_url)
    
    # Проверяем существование MP4
    check = check_s3_object(s3_key)
    if check.status == "error":
        raise HTTPException(status_code=404, detail=f"Video not found: {check.message}")
    
    # Запускаем асинхронную задачу
    task = force_rebuild_hls_task.apply_async(
        args=[req.video_url],
        queue="special_hls"
    )
    
    return {
        "status": "queued",
        "s3_key": s3_key,
        "task_id": task.id,
        "message": "Force rebuild task queued. Old HLS will be deleted and new one generated."
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


def _is_broken_playlist(playlist_key: str) -> tuple[bool, str]:
    """
    Проверяет, является ли HLS плейлист битым/неполным.
    Возвращает (is_broken, reason).
    """
    try:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=playlist_key)
        content = obj["Body"].read().decode("utf-8", errors="replace")
        
        if not content.strip().startswith("#EXTM3U"):
            return True, "Invalid playlist (no #EXTM3U)"
        
        # Считаем сегменты
        segments = []
        total_duration = 0.0
        for line in content.strip().split("\n"):
            line = line.strip()
            if line.startswith("#EXTINF:"):
                try:
                    dur = float(line.split(":")[1].split(",")[0])
                    total_duration += dur
                except:
                    pass
            elif line and not line.startswith("#"):
                if line.endswith(".ts") or line.endswith(".m4s"):
                    segments.append(line)
        
        # Проверяем, это master playlist (указывает на другой плейлист)
        is_master = any(
            l.strip().endswith(".m3u8") or "playlist.m3u8" in l
            for l in content.split("\n") 
            if l.strip() and not l.strip().startswith("#")
        )
        
        if is_master:
            return False, "Master/alias playlist"
        
        if len(segments) == 0:
            return True, "No segments"
        
        if total_duration < 1.0:
            return True, f"Too short ({total_duration:.1f}s)"
        
        # Проверяем доступность первого сегмента
        base_dir = playlist_key.rsplit("/", 1)[0] if "/" in playlist_key else ""
        first_seg_key = f"{base_dir}/{segments[0]}" if base_dir else segments[0]
        
        try:
            s3.head_object(Bucket=S3_BUCKET, Key=first_seg_key)
        except ClientError:
            return True, f"First segment missing: {segments[0]}"
        
        return False, f"OK ({len(segments)} segments, {total_duration:.1f}s)"
        
    except ClientError as e:
        return True, f"Cannot read: {e.response['Error']['Code']}"
    except Exception as e:
        return True, f"Error: {type(e).__name__}"


class CleanupHlsRequest(BaseModel):
    video_url: str
    dry_run: bool = True  # По умолчанию только показываем, что будет удалено


@router.post("/cleanup-hls")
def cleanup_hls_endpoint(
    req: CleanupHlsRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Находит и удаляет битые/пустые HLS плейлисты для видео.
    
    dry_run=True (по умолчанию): только показывает, что будет удалено
    dry_run=False: реально удаляет
    """
    s3_key = key_from_url(req.video_url)
    
    # Находим все плейлисты (не только matching)
    all_playlists = find_hls_playlists(s3_key, only_matching=False)
    matching_playlists = find_hls_playlists(s3_key, only_matching=True)
    
    results = {
        "video_url": req.video_url,
        "s3_key": s3_key,
        "dry_run": req.dry_run,
        "total_playlists_in_folder": len(all_playlists),
        "matching_this_video": len(matching_playlists),
        "playlists": [],
        "to_delete": [],
        "deleted": [],
        "kept": [],
    }
    
    # Анализируем каждый matching плейлист
    for pl_key in matching_playlists:
        is_broken, reason = _is_broken_playlist(pl_key)
        slug = pl_key.split("/")[-2] if "/" in pl_key else "unknown"
        
        info = {
            "key": pl_key,
            "slug": slug,
            "is_broken": is_broken,
            "reason": reason,
        }
        results["playlists"].append(info)
        
        if is_broken and "Master/alias" not in reason:
            results["to_delete"].append(pl_key)
            
            if not req.dry_run:
                # Удаляем плейлист и его сегменты
                try:
                    # Удаляем все файлы в папке slug
                    hls_dir = pl_key.rsplit("/", 1)[0] + "/"
                    paginator = s3.get_paginator("list_objects_v2")
                    objects_to_delete = []
                    
                    for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_dir):
                        for obj in page.get("Contents", []):
                            objects_to_delete.append({"Key": obj["Key"]})
                    
                    if objects_to_delete:
                        # Удаляем батчами по 1000
                        for i in range(0, len(objects_to_delete), 1000):
                            batch = objects_to_delete[i:i+1000]
                            s3.delete_objects(Bucket=S3_BUCKET, Delete={"Objects": batch})
                        
                        results["deleted"].append({
                            "key": pl_key,
                            "deleted_objects": len(objects_to_delete)
                        })
                except Exception as e:
                    logger.error(f"Failed to delete {pl_key}: {e}")
                    results["deleted"].append({
                        "key": pl_key,
                        "error": str(e)
                    })
        else:
            results["kept"].append(pl_key)
    
    return results


@router.get("/list-all-hls")
def list_all_hls_endpoint(
    video_url: str = Query(..., description="URL видео"),
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Показывает все HLS плейлисты в папке видео с их статусом.
    """
    s3_key = key_from_url(video_url)
    expected_slugs = _compute_slugs_for_mp4(s3_key)
    
    # Все плейлисты в папке
    all_playlists = find_hls_playlists(s3_key, only_matching=False)
    
    results = {
        "video_url": video_url,
        "s3_key": s3_key,
        "expected_slugs": expected_slugs,
        "total_playlists": len(all_playlists),
        "playlists": [],
    }
    
    for pl_key in all_playlists:
        slug = pl_key.split("/")[-2] if "/" in pl_key else "unknown"
        is_matching = any(
            slug.startswith(exp) or exp.startswith(slug.rstrip("-0123456789abcdef")[:20])
            for exp in expected_slugs
        )
        is_broken, reason = _is_broken_playlist(pl_key)
        
        results["playlists"].append({
            "key": pl_key,
            "slug": slug,
            "matches_video": is_matching,
            "is_broken": is_broken,
            "status": reason,
        })
    
    return results


# ============= МАССОВАЯ МИГРАЦИЯ %20 → пробелы =============

@router.post("/fix-encoded-paths")
def fix_encoded_paths_endpoint(
    dry_run: bool = True,
    folder_prefix: str = "",
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Находит все HLS файлы с %20 в именах и копирует их с правильными именами (с пробелами).
    
    Это исправляет проблему когда файлы были созданы с URL-encoded именами.
    
    Args:
        dry_run: True - только показать что будет сделано, False - реально копировать
        folder_prefix: Ограничить поиск определённой папкой (например "Spark MasterCoip")
    
    Returns:
        Список файлов которые были/будут скопированы
    """
    results = {
        "dry_run": dry_run,
        "folder_prefix": folder_prefix,
        "files_with_encoded_names": [],
        "files_to_copy": [],
        "copied": [],
        "errors": [],
        "already_exists": [],
    }
    
    # Ищем все файлы с %20 в именах
    prefix = folder_prefix if folder_prefix else ""
    
    try:
        paginator = s3_v4.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=1000):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                
                # Проверяем есть ли %20 или другие encoded символы в ключе
                if "%20" in key or "%2F" in key or "%25" in key:
                    decoded_key = unquote(key)
                    
                    # Пропускаем если decoded == encoded (нет реальных encoded символов)
                    if decoded_key == key:
                        continue
                    
                    results["files_with_encoded_names"].append({
                        "encoded": key,
                        "decoded": decoded_key,
                        "size": obj.get("Size", 0),
                    })
                    
                    # Проверяем существует ли файл с правильным именем
                    try:
                        s3.head_object(Bucket=S3_BUCKET, Key=decoded_key)
                        results["already_exists"].append(decoded_key)
                    except ClientError:
                        # Файла с правильным именем нет - нужно скопировать
                        results["files_to_copy"].append({
                            "from": key,
                            "to": decoded_key,
                        })
                        
                        if not dry_run:
                            try:
                                # Копируем файл
                                s3.copy_object(
                                    Bucket=S3_BUCKET,
                                    CopySource={"Bucket": S3_BUCKET, "Key": key},
                                    Key=decoded_key,
                                    MetadataDirective="COPY"
                                )
                                results["copied"].append(decoded_key)
                            except Exception as e:
                                results["errors"].append({
                                    "key": key,
                                    "error": str(e)
                                })
    except Exception as e:
        results["errors"].append({"error": f"Listing failed: {e}"})
    
    results["summary"] = {
        "total_encoded_files": len(results["files_with_encoded_names"]),
        "to_copy": len(results["files_to_copy"]),
        "already_fixed": len(results["already_exists"]),
        "copied": len(results["copied"]),
        "errors": len(results["errors"]),
    }
    
    return results


@router.post("/fix-hls-master-playlists")
def fix_hls_master_playlists_endpoint(
    dry_run: bool = True,
    folder_prefix: str = "",
    use_double_encoding: bool = True,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Находит все master playlists и исправляет URL внутри них.
    
    Args:
        dry_run: True - только показать что будет сделано
        folder_prefix: Ограничить поиск папкой
        use_double_encoding: True - заменить %20 на %2520 (CDN декодирует в %20)
                            False - заменить %20 на пробелы
    """
    results = {
        "dry_run": dry_run,
        "folder_prefix": folder_prefix,
        "playlists_checked": 0,
        "playlists_with_encoded_urls": [],
        "fixed": [],
        "errors": [],
    }
    
    prefix = f"{folder_prefix}/.hls/" if folder_prefix else ".hls/"
    # Также ищем с encoded prefix
    encoded_prefix = prefix.replace(" ", "%20") if " " in prefix else None
    
    prefixes_to_check = [prefix]
    if encoded_prefix and encoded_prefix != prefix:
        prefixes_to_check.append(encoded_prefix)
    
    for search_prefix in prefixes_to_check:
        try:
            paginator = s3_v4.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=search_prefix, MaxKeys=1000):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    
                    if not key.endswith("playlist.m3u8"):
                        continue
                    
                    results["playlists_checked"] += 1
                    
                    try:
                        # Читаем плейлист
                        resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
                        content = resp["Body"].read().decode("utf-8", errors="replace")
                        
                        # Проверяем есть ли %20 в URL внутри плейлиста (но не %2520)
                        if "%20" not in content or "%2520" in content:
                            continue
                        
                        # Это master/alias playlist с encoded URL
                        if use_double_encoding:
                            # Двойное кодирование: %20 → %2520
                            # CDN декодирует %25 → %, получается %20, S3 найдёт файл
                            new_content = content.replace("%20", "%2520")
                        else:
                            # Обычная замена на пробелы
                            new_content = content.replace("%20", " ")
                        
                        results["playlists_with_encoded_urls"].append({
                            "key": key,
                            "original_snippet": content[:200],
                            "fixed_snippet": new_content[:200],
                        })
                        
                        if not dry_run:
                            try:
                                s3.put_object(
                                    Bucket=S3_BUCKET,
                                    Key=key,
                                    Body=new_content.encode("utf-8"),
                                    ContentType="application/vnd.apple.mpegurl",
                                    CacheControl="public, max-age=60"
                                )
                                results["fixed"].append(key)
                            except Exception as e:
                                results["errors"].append({
                                    "key": key,
                                    "error": str(e)
                                })
                    except Exception as e:
                        results["errors"].append({
                            "key": key,
                            "error": f"Read error: {e}"
                        })
        except Exception as e:
            results["errors"].append({"prefix": search_prefix, "error": str(e)})
    
    results["summary"] = {
        "playlists_checked": results["playlists_checked"],
        "need_fixing": len(results["playlists_with_encoded_urls"]),
        "fixed": len(results["fixed"]),
        "errors": len(results["errors"]),
    }
    
    return results


@router.post("/fix-all-hls-aliases")
def fix_all_hls_aliases_endpoint(
    dry_run: bool = True,
    use_double_encoding: bool = True,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Исправляет ВСЕ HLS alias плейлисты во всём бакете.
    
    Находит все playlist.m3u8 которые содержат %20 в URL и:
    - use_double_encoding=True: заменяет %20 на %2520 (CDN декодирует обратно в %20)
    - use_double_encoding=False: заменяет %20 на пробелы
    
    Это СИСТЕМНОЕ исправление - запустить один раз.
    """
    results = {
        "dry_run": dry_run,
        "use_double_encoding": use_double_encoding,
        "total_playlists": 0,
        "aliases_with_encoded_urls": 0,
        "fixed": [],
        "errors": [],
        "skipped": [],
    }
    
    try:
        # Листим ВСЕ .hls/ папки в бакете
        paginator = s3_v4.get_paginator("list_objects_v2")
        
        for page in paginator.paginate(Bucket=S3_BUCKET, MaxKeys=1000):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                
                # Только playlist.m3u8 файлы
                if not key.endswith("playlist.m3u8"):
                    continue
                if "/.hls/" not in key:
                    continue
                    
                results["total_playlists"] += 1
                
                try:
                    # Читаем плейлист
                    resp = s3.get_object(Bucket=S3_BUCKET, Key=key)
                    content = resp["Body"].read().decode("utf-8", errors="replace")
                    
                    # Проверяем - это alias? (содержит URL, а не сегменты)
                    lines = [l.strip() for l in content.split("\n") if l.strip() and not l.strip().startswith("#")]
                    
                    # Alias содержит URL (http) а не имена сегментов (.ts)
                    is_alias = any(l.startswith("http") for l in lines)
                    if not is_alias:
                        continue
                    
                    # Проверяем есть ли %20 (но не %2520 - уже исправлено)
                    if "%20" not in content:
                        continue
                    if "%2520" in content:
                        results["skipped"].append({"key": key, "reason": "already fixed"})
                        continue
                    
                    results["aliases_with_encoded_urls"] += 1
                    
                    # Исправляем
                    if use_double_encoding:
                        new_content = content.replace("%20", "%2520")
                    else:
                        new_content = content.replace("%20", " ")
                    
                    if not dry_run:
                        s3.put_object(
                            Bucket=S3_BUCKET,
                            Key=key,
                            Body=new_content.encode("utf-8"),
                            ContentType="application/vnd.apple.mpegurl",
                            CacheControl="public, max-age=60"
                        )
                        results["fixed"].append(key)
                    else:
                        results["fixed"].append({"key": key, "would_fix": True})
                        
                except Exception as e:
                    results["errors"].append({"key": key, "error": str(e)})
                    
    except Exception as e:
        results["errors"].append({"error": f"Listing failed: {e}"})
    
    results["summary"] = {
        "total_playlists": results["total_playlists"],
        "aliases_needing_fix": results["aliases_with_encoded_urls"],
        "fixed": len(results["fixed"]),
        "skipped": len(results["skipped"]),
        "errors": len(results["errors"]),
    }
    
    return results


@router.post("/fix-hls-permissions")
def fix_hls_permissions_endpoint(
    folder_prefix: str = "",
    dry_run: bool = True,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Исправляет права доступа для HLS файлов - делает их публичными.
    
    Находит все файлы в .hls/ папках и устанавливает public-read ACL.
    """
    results = {
        "dry_run": dry_run,
        "folder_prefix": folder_prefix,
        "files_found": 0,
        "files_fixed": [],
        "errors": [],
    }
    
    # Формируем prefix для поиска
    if folder_prefix:
        # Пробуем оба варианта - с пробелами и с %20
        prefixes = [f"{folder_prefix}/.hls/"]
        if " " in folder_prefix:
            prefixes.append(f"{folder_prefix.replace(' ', '%20')}/.hls/")
    else:
        prefixes = [".hls/"]
    
    processed_keys = set()
    
    for prefix in prefixes:
        try:
            paginator = s3_v4.get_paginator("list_objects_v2")
            for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=prefix, MaxKeys=1000):
                for obj in page.get("Contents", []):
                    key = obj["Key"]
                    
                    if key in processed_keys:
                        continue
                    processed_keys.add(key)
                    
                    results["files_found"] += 1
                    
                    if not dry_run:
                        try:
                            # Устанавливаем public-read ACL
                            s3.put_object_acl(
                                Bucket=S3_BUCKET,
                                Key=key,
                                ACL='public-read'
                            )
                            results["files_fixed"].append(key)
                        except Exception as e:
                            results["errors"].append({
                                "key": key,
                                "error": str(e)
                            })
                    else:
                        results["files_fixed"].append({"key": key, "would_fix": True})
                        
        except Exception as e:
            results["errors"].append({"prefix": prefix, "error": str(e)})
    
    results["summary"] = {
        "files_found": results["files_found"],
        "fixed": len(results["files_fixed"]),
        "errors": len(results["errors"]),
    }
    
    return results


class FixVideoAclRequest(BaseModel):
    video_url: str
    dry_run: bool = False  # По умолчанию сразу исправляем


def _fix_hls_acl_for_video(video_url: str, dry_run: bool = False) -> Dict[str, Any]:
    """
    Исправляет ACL для всех HLS файлов конкретного видео.
    Возвращает словарь с результатами.
    """
    s3_key = key_from_url(video_url)
    base_dir = s3_key.rsplit("/", 1)[0] if "/" in s3_key else ""
    hls_prefix = f"{base_dir}/.hls/" if base_dir else ".hls/"
    
    results = {
        "video_url": video_url,
        "s3_key": s3_key,
        "hls_prefix": hls_prefix,
        "dry_run": dry_run,
        "files_found": 0,
        "files_fixed": [],
        "already_public": [],
        "errors": [],
    }
    
    # Собираем все HLS файлы для этого видео
    # Используем slug'и для фильтрации
    expected_slugs = _compute_slugs_for_mp4(s3_key)
    
    try:
        paginator = s3_v4.get_paginator("list_objects_v2")
        for page in paginator.paginate(Bucket=S3_BUCKET, Prefix=hls_prefix, MaxKeys=1000):
            for obj in page.get("Contents", []):
                key = obj["Key"]
                
                # Проверяем соответствует ли этот файл нашему видео
                # Извлекаем slug из пути: base/.hls/{slug}/...
                parts = key.replace(hls_prefix, "").split("/")
                if not parts:
                    continue
                slug_dir = parts[0]
                
                # Проверяем соответствие slug
                is_matching = any(
                    slug_dir.startswith(exp) or exp.startswith(slug_dir.rstrip("-0123456789abcdef")[:20])
                    for exp in expected_slugs
                )
                
                if not is_matching:
                    continue
                
                results["files_found"] += 1
                
                # Проверяем текущий ACL
                try:
                    acl_response = s3.get_object_acl(Bucket=S3_BUCKET, Key=key)
                    grants = acl_response.get("Grants", [])
                    
                    is_public = any(
                        grant.get("Grantee", {}).get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers"
                        and grant.get("Permission") in ("READ", "FULL_CONTROL")
                        for grant in grants
                    )
                    
                    if is_public:
                        results["already_public"].append(key)
                        continue
                    
                    # Нужно исправить ACL
                    if not dry_run:
                        s3.put_object_acl(
                            Bucket=S3_BUCKET,
                            Key=key,
                            ACL='public-read'
                        )
                        results["files_fixed"].append(key)
                    else:
                        results["files_fixed"].append({"key": key, "would_fix": True})
                        
                except Exception as e:
                    results["errors"].append({"key": key, "error": str(e)})
                    
    except Exception as e:
        results["errors"].append({"error": f"Listing failed: {e}"})
    
    results["summary"] = {
        "files_found": results["files_found"],
        "already_public": len(results["already_public"]),
        "fixed": len(results["files_fixed"]),
        "errors": len(results["errors"]),
    }
    
    return results


@router.post("/fix-video-acl")
def fix_video_acl_endpoint(
    req: FixVideoAclRequest,
    current_admin: User = Depends(require_roles("admin"))
) -> Dict[str, Any]:
    """
    Исправляет ACL (делает public-read) для всех HLS файлов конкретного видео.
    
    Args:
        video_url: URL видео
        dry_run: True - только показать что будет исправлено, False - реально исправить
    
    Returns:
        Информация о найденных и исправленных файлах
    """
    return _fix_hls_acl_for_video(req.video_url, req.dry_run)

