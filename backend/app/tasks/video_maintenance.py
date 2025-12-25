from __future__ import annotations

import hashlib
import logging
import os
import subprocess
import tempfile
import time
from datetime import timedelta
from dataclasses import asdict
from typing import Any, Dict, List, Optional
from urllib.parse import unquote

import redis
from botocore.exceptions import ClientError
from celery import shared_task

from ..core.storage import (
    S3_BUCKET,
    S3_PUBLIC_HOST,
    s3_client,
    key_from_public_or_endpoint_url,
    public_url_for_key,
)
from ..core.video_maintenance_config import VIDEO_MAINTENANCE
from ..db.database import SessionLocal
from ..utils.db_url_rewrite import rewrite_references_for_key
from ..utils.s3 import generate_presigned_url
from ..utils.video_key_normalizer import canonicalize_s3_key

# HLS helpers (переиспользуем существующую логику slug/canonical)
# ВАЖНО: НЕ используем ensure_aliases_to_canonical(), т.к. она переписывает ВСЕ legacy playlist.m3u8
# под base_dir/.hls/ и может «перекрестно» сломать другие видео в том же каталоге.
from .ensure_hls import hls_prefixes_for, put_alias_master  # noqa: E402
from ..services_v2.video_repair_service import (
    Problem,
    check_master_and_variants,
    check_audio_present,
    fix_rebuild_hls,
)

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)

s3 = s3_client(signature_version="s3v4")

# ───────────────────────────── ACL helpers ─────────────────────────────
def _acl_is_public_read(key: str) -> Optional[bool]:
    """
    Возвращает:
    - True/False если удалось проверить ACL
    - None если хранилище/права не позволяют читать ACL (тогда не считаем ошибкой)
    """
    try:
        resp = s3.get_object_acl(Bucket=S3_BUCKET, Key=key)
        grants = resp.get("Grants", []) or []
        for g in grants:
            gr = g.get("Grantee", {}) or {}
            if gr.get("URI") == "http://acs.amazonaws.com/groups/global/AllUsers":
                perm = (g.get("Permission") or "").upper()
                if perm in ("READ", "FULL_CONTROL"):
                    return True
        return False
    except Exception:
        return None


def _ensure_public_read_acl(keys: list[str], *, dry_run: bool) -> dict:
    """
    Делает public-read ACL для набора ключей (best-effort).
    """
    fixed: list[str] = []
    skipped_private_unknown: list[str] = []
    errors: list[str] = []

    for k in keys[: VIDEO_MAINTENANCE.hls_fix_acl_max_files]:
        st = _acl_is_public_read(k)
        if st is True:
            continue
        if st is None:
            skipped_private_unknown.append(k)
            continue
        # st is False -> приватный
        if dry_run:
            fixed.append(k)
            continue
        try:
            s3.put_object_acl(Bucket=S3_BUCKET, Key=k, ACL="public-read")
            fixed.append(k)
        except Exception as e:
            errors.append(f"{k}: {type(e).__name__}: {e}")

    return {"would_fix_or_fixed": fixed, "acl_check_unsupported": skipped_private_unknown[:10], "errors": errors[:10]}


def _copy_replace_metadata(key: str, meta: dict, *, content_type: str = "video/mp4") -> None:
    """
    Быстрый способ обновить metadata без перезаливки файла: copy_object на себя с REPLACE.
    """
    s3.copy_object(
        Bucket=S3_BUCKET,
        Key=key,
        CopySource={"Bucket": S3_BUCKET, "Key": key},
        Metadata=meta,
        MetadataDirective="REPLACE",
        ACL="public-read",
        ContentType=content_type,
    )


def _check_moov_position(url: str) -> dict:
    """
    Проверка faststart «по факту»: moov перед mdat = OK.
    Используем ffprobe -v trace и парсим позиции atom'ов.
    """
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "trace", "-show_format", "-i", url],
            capture_output=True,
            text=True,
            timeout=15,
        )
        stderr = proc.stderr or ""
        moov_pos = None
        mdat_pos = None
        for line in stderr.splitlines():
            if ("type:'moov'" in line or "type: moov" in line) and "pos:" in line:
                try:
                    moov_pos = int(line.split("pos:")[1].split()[0])
                except Exception:
                    pass
            if ("type:'mdat'" in line or "type: mdat" in line) and "pos:" in line:
                try:
                    mdat_pos = int(line.split("pos:")[1].split()[0])
                except Exception:
                    pass
            if moov_pos is not None and mdat_pos is not None:
                break

        ok = None
        if isinstance(moov_pos, int) and isinstance(mdat_pos, int):
            ok = moov_pos < mdat_pos

        return {
            "ok": ok,  # True/False/None
            "moov_position": moov_pos,
            "mdat_position": mdat_pos,
            "stderr_snip": stderr[:200] if proc.returncode != 0 else None,
        }
    except Exception as e:
        return {"ok": None, "error": f"{type(e).__name__}: {e}"}

# Redis keys
R_CURSOR = "video_maint:cursor_token"
R_LOCK_PREFIX = "video_maint:lock:"
R_AUDIT = "video_maint:audit"


def _lock(key: str, ttl_sec: int = 60 * 30) -> bool:
    return bool(rds.set(R_LOCK_PREFIX + key, "1", nx=True, ex=ttl_sec))


def _unlock(key: str) -> None:
    try:
        rds.delete(R_LOCK_PREFIX + key)
    except Exception:
        pass


def _s3_exists(key: str) -> bool:
    try:
        s3.head_object(Bucket=S3_BUCKET, Key=key)
        return True
    except ClientError:
        return False


def _audit(event: dict, keep_last: int = 200) -> None:
    """
    Лёгкий аудит последних прогонов (в Redis).
    Не является «истиной», но помогает дебажить, не копаясь в логах.
    """
    try:
        import json

        rds.lpush(R_AUDIT, json.dumps(event, ensure_ascii=False))
        rds.ltrim(R_AUDIT, 0, max(0, keep_last - 1))
    except Exception:
        pass


def _unique_key_if_exists(candidate_key: str, *, salt: str) -> str:
    """
    Если key уже существует — добавляем короткий hash перед расширением.
    """
    if not _s3_exists(candidate_key):
        return candidate_key

    h = hashlib.sha1(salt.encode("utf-8", "ignore")).hexdigest()[:8]
    if "." in candidate_key.rsplit("/", 1)[-1]:
        base, ext = candidate_key.rsplit(".", 1)
        return f"{base}-{h}.{ext}"
    return f"{candidate_key}-{h}"


def _ffprobe(path: str) -> dict:
    out = subprocess.check_output(
        ["ffprobe", "-v", "fatal", "-print_format", "json", "-show_streams", "-show_format", path]
    ).decode("utf-8", "ignore")
    import json

    return json.loads(out)


def _ffprobe_url(url: str) -> Optional[dict]:
    """
    Dry-run helper: ffprobe по HTTP(S) URL.
    Обычно ffprobe умеет читать заголовки/метаданные через range-requests,
    не скачивая файл целиком.
    """
    try:
        out = subprocess.check_output(
            ["ffprobe", "-v", "fatal", "-print_format", "json", "-show_streams", "-show_format", url],
        ).decode("utf-8", "ignore")
        import json

        return json.loads(out)
    except Exception:
        return None


def _ffprobe_url_debug(url: str) -> tuple[Optional[dict], Optional[str]]:
    """
    То же, что _ffprobe_url, но возвращает краткую причину ошибки (для dry-run отчёта).
    """
    try:
        proc = subprocess.run(
            ["ffprobe", "-v", "error", "-print_format", "json", "-show_streams", "-show_format", url],
            capture_output=True,
            text=True,
            timeout=30,
        )
        if proc.returncode != 0:
            err = (proc.stderr or proc.stdout or "").strip()
            return None, (err[:400] if err else f"ffprobe_exit={proc.returncode}")
        import json

        return json.loads(proc.stdout), None
    except Exception as e:
        return None, f"{type(e).__name__}: {e}"


def _pick_stream(meta: dict, codec_type: str) -> Optional[dict]:
    for s in meta.get("streams", []) or []:
        if s.get("codec_type") == codec_type:
            return s
    return None


def _needs_full_transcode(v: dict | None) -> bool:
    if not v:
        return False
    codec = (v.get("codec_name") or "").lower()
    pix = (v.get("pix_fmt") or "").lower()
    if codec not in ("h264", "avc1"):
        return True
    # 10-bit / 4:4:4 и т.п. часто ломают аппаратный декодер на части устройств
    if pix != VIDEO_MAINTENANCE.target_pixel_format:
        return True
    return False


def _needs_audio_reencode(a: dict | None) -> bool:
    if not a:
        return False
    codec = (a.get("codec_name") or "").lower()
    return codec not in ("aac", "mp4a")


def _fix_mp4_to_compatible(
    *,
    src_key: str,
    dry_run: bool,
) -> dict:
    """
    Делает MP4 максимально совместимым:
    - гарантирует faststart (+faststart)
    - если нужно — перекодирует аудио в AAC
    - если нужно — full transcode в H.264 + yuv420p
    """
    if dry_run:
        meta_faststart = None
        try:
            head = s3.head_object(Bucket=S3_BUCKET, Key=src_key)
            meta_faststart = (head.get("Metadata", {}) or {}).get("faststart")
        except Exception:
            pass

        cdn_url = public_url_for_key(src_key, public_host=S3_PUBLIC_HOST)
        presigned_url = generate_presigned_url(f"s3://{S3_BUCKET}/{src_key}", expires=timedelta(minutes=10))

        # faststart по факту: пробуем presigned (обычно стабильнее)
        moov = _check_moov_position(presigned_url) if presigned_url else {"ok": None}

        m = None
        probe_error = None
        used_url = None

        # Сначала пробуем CDN (дешевле), потом presigned endpoint (обычно надёжнее для ffprobe)
        for u in (cdn_url, presigned_url):
            m, probe_error = _ffprobe_url_debug(u)
            if m:
                used_url = u
                break

        if not m:
            # Не смогли определить кодеки по URL (например, URL недоступен или ключ не существует).
            # В таком случае не делаем выводов про transcode/audio, только показываем faststart по метадате.
            # если moov известно и ok=True, faststart ремакс не нужен
            if moov.get("ok") is True:
                would_faststart = False
            elif moov.get("ok") is False:
                would_faststart = True
            else:
                would_faststart = (meta_faststart != "true")
            return {
                "status": "dry_run",
                "action": "probe_failed",
                "faststart_metadata": meta_faststart,
                "would_faststart_remux": bool(would_faststart),
                "would_full_transcode": None,
                "would_audio_reencode": None,
                "detected": {"vcodec": None, "pix_fmt": None, "acodec": None},
                "target": {"vcodec": "h264", "pix_fmt": VIDEO_MAINTENANCE.target_pixel_format, "acodec": "aac"},
                "probe_url": cdn_url,
                "probe_url_presigned": presigned_url,
                "probe_error": probe_error,
                "faststart_fact": moov,
            }
        v = _pick_stream(m, "video")
        a = _pick_stream(m, "audio")

        full = _needs_full_transcode(v)
        audio_re = _needs_audio_reencode(a)
        if moov.get("ok") is True:
            would_faststart = False
        elif moov.get("ok") is False:
            would_faststart = True
        else:
            would_faststart = (meta_faststart != "true")

        if full:
            action = "would_full_transcode_h264_aac_faststart"
        elif audio_re:
            action = "would_remux_vcopy_audio_aac_faststart"
        elif would_faststart:
            action = "would_remux_copy_faststart"
        else:
            action = "would_skip_already_compatible"

        return {
            "status": "dry_run",
            "action": action,
            "faststart_metadata": meta_faststart,
            "would_faststart_remux": bool(would_faststart),
            "would_full_transcode": bool(full),
            "would_audio_reencode": bool(audio_re),
            "detected": {
                "vcodec": (v or {}).get("codec_name"),
                "pix_fmt": (v or {}).get("pix_fmt"),
                "acodec": (a or {}).get("codec_name"),
            },
            "target": {
                "vcodec": "h264",
                "pix_fmt": VIDEO_MAINTENANCE.target_pixel_format,
                "acodec": "aac",
            },
            "probe_url": used_url or cdn_url,
            "probe_url_presigned": presigned_url,
            "faststart_fact": moov,
        }

    head = s3.head_object(Bucket=S3_BUCKET, Key=src_key)
    meta = dict(head.get("Metadata", {}) or {})
    ct = head.get("ContentType") or "video/mp4"

    # Проверяем faststart «по факту» до тяжёлых операций (по URL, без скачивания)
    presigned_url = generate_presigned_url(f"s3://{S3_BUCKET}/{src_key}", expires=timedelta(minutes=10))
    moov = _check_moov_position(presigned_url) if presigned_url else {"ok": None}

    with tempfile.TemporaryDirectory() as tmp:
        in_mp4 = os.path.join(tmp, "in.mp4")
        out_mp4 = os.path.join(tmp, "out.mp4")

        s3.download_file(S3_BUCKET, src_key, in_mp4)
        m = _ffprobe(in_mp4)
        v = _pick_stream(m, "video")
        a = _pick_stream(m, "audio")

        full = _needs_full_transcode(v)
        audio_re = _needs_audio_reencode(a)
        need_faststart = (moov.get("ok") is False)

        # Если всё уже совместимо и faststart ok — только проставим метадату (если её нет), без перезаливки
        if (not full) and (not audio_re) and (need_faststart is False):
            if meta.get("faststart") != "true":
                meta["faststart"] = "true"
                _copy_replace_metadata(src_key, meta, content_type=ct)
                return {"status": "ok", "action": "mark_faststart_metadata", "faststart_fact": moov}
            return {"status": "ok", "action": "skip_already_ok", "faststart_fact": moov}

        if full:
            cmd = [
                "ffmpeg",
                "-v",
                "fatal",
                "-nostdin",
                "-y",
                "-i",
                in_mp4,
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-c:v",
                VIDEO_MAINTENANCE.target_video_codec,
                "-preset",
                VIDEO_MAINTENANCE.video_preset,
                "-crf",
                str(VIDEO_MAINTENANCE.video_crf),
                "-pix_fmt",
                VIDEO_MAINTENANCE.target_pixel_format,
                "-profile:v",
                VIDEO_MAINTENANCE.h264_profile,
                "-level",
                VIDEO_MAINTENANCE.h264_level,
                "-c:a",
                VIDEO_MAINTENANCE.target_audio_codec,
                "-b:a",
                VIDEO_MAINTENANCE.audio_bitrate,
                "-ac",
                str(VIDEO_MAINTENANCE.audio_channels),
                "-ar",
                str(VIDEO_MAINTENANCE.audio_rate_hz),
                "-movflags",
                "+faststart",
                out_mp4,
            ]
            action = "full_transcode_h264_aac"
        else:
            # быстрый путь: видео копируем; аудио по необходимости -> AAC; контейнер переписываем с faststart
            cmd = [
                "ffmpeg",
                "-v",
                "fatal",
                "-nostdin",
                "-y",
                "-i",
                in_mp4,
                "-map",
                "0:v:0",
                "-map",
                "0:a:0?",
                "-c:v",
                "copy",
            ]
            if audio_re:
                cmd += [
                    "-c:a",
                    VIDEO_MAINTENANCE.target_audio_codec,
                    "-b:a",
                    VIDEO_MAINTENANCE.audio_bitrate,
                    "-ac",
                    str(VIDEO_MAINTENANCE.audio_channels),
                    "-ar",
                    str(VIDEO_MAINTENANCE.audio_rate_hz),
                ]
                action = "remux_vcopy_audio_aac_faststart"
            else:
                cmd += ["-c:a", "copy"]
                action = "remux_copy_faststart"
            cmd += ["-movflags", "+faststart", out_mp4]

        subprocess.run(cmd, check=True, timeout=VIDEO_MAINTENANCE.ffmpeg_timeout_sec)

        # помечаем, что faststart применён (в метадате)
        meta["faststart"] = "true"
        # hls метадату не трогаем — за неё отвечает HLS шаг
        s3.upload_file(
            out_mp4,
            S3_BUCKET,
            src_key,
            ExtraArgs={
                "ACL": "public-read",
                "ContentType": ct,
                "Metadata": meta,
            },
        )

    return {"status": "ok", "action": action, "full_transcode": full, "audio_reencode": audio_re, "faststart_fact": moov}


def _validate_and_fix_hls_for(src_key: str, *, dry_run: bool) -> dict:
    legacy_prefix, new_prefix = hls_prefixes_for(src_key)
    legacy_pl_key = f"{legacy_prefix}playlist.m3u8"
    new_pl_key = f"{new_prefix}playlist.m3u8"

    # Выбираем canonical (new) всегда — он устойчивый
    master_key = new_pl_key

    if dry_run:
        exists = _s3_exists(master_key)
        return {"status": "dry_run", "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key, "master_exists": exists}

    def _ensure_legacy_alias_only() -> None:
        """
        Создаём/перезаписываем legacy playlist.m3u8 ТОЛЬКО для текущего видео,
        чтобы он указывал на canonical new_pl_key.
        Это предотвращает ситуацию «ссылка на видео ведёт на другое видео» из‑за коллизий.
        """
        if legacy_pl_key == new_pl_key:
            return
        canonical_url = public_url_for_key(new_pl_key, public_host=S3_PUBLIC_HOST)
        put_alias_master(legacy_pl_key, canonical_url)

    def _parse_variant_paths(master_text: str) -> list[str]:
        lines = [l.strip() for l in (master_text or "").splitlines() if l.strip()]
        out: list[str] = []
        last_inf = False
        for l in lines:
            if l.startswith("#EXT-X-STREAM-INF"):
                last_inf = True
                continue
            if last_inf and not l.startswith("#"):
                out.append(l)
                last_inf = False
        return out

    def _read_text(key: str) -> str:
        obj = s3.get_object(Bucket=S3_BUCKET, Key=key)
        return obj["Body"].read().decode("utf-8", errors="replace")

    def _join(base_key: str, rel: str) -> str:
        # rel может быть URL; в таком случае это уже key_from_url, но нам хватит path.
        if rel.startswith("http://") or rel.startswith("https://"):
            return key_from_public_or_endpoint_url(rel)
        base = base_key.rsplit("/", 1)[0] if "/" in base_key else ""
        return f"{base}/{rel}" if base else rel

    def _segments_ok(master_k: str) -> tuple[bool, dict]:
        """
        Проверяем, что плейлист имеет варианты и что первые N сегментов реально существуют.
        Это дешёвый sanity-check, который ловит «битые/дырявые» HLS.
        """
        details: dict = {}
        try:
            master_text = _read_text(master_k)
        except Exception as e:
            return False, {"error": f"read_master: {type(e).__name__}: {e}"}

        variants = _parse_variant_paths(master_text)
        if not variants:
            return False, {"error": "no_variants"}
        # берём первый variant
        variant_key = _join(master_k, variants[0])
        details["variant_key"] = variant_key
        try:
            variant_text = _read_text(variant_key)
        except Exception as e:
            return False, {"error": f"read_variant: {type(e).__name__}: {e}", "variant_key": variant_key}

        segs = []
        for l in variant_text.splitlines():
            l = l.strip()
            if not l or l.startswith("#"):
                continue
            if l.endswith(".ts") or l.endswith(".m4s"):
                segs.append(l)
            if len(segs) >= VIDEO_MAINTENANCE.hls_segment_head_limit:
                break
        if not segs:
            return False, {"error": "no_segments", "variant_key": variant_key}

        missing = 0
        too_small = 0
        checked = 0
        for seg_rel in segs:
            seg_key = _join(variant_key, seg_rel)
            try:
                h = s3.head_object(Bucket=S3_BUCKET, Key=seg_key)
                checked += 1
                size = int(h.get("ContentLength") or 0)
                if size < VIDEO_MAINTENANCE.hls_min_segment_size_bytes:
                    too_small += 1
            except ClientError:
                missing += 1
        # сохраним список сегментов (первые N) — пригодится для ACL fix
        details["segment_keys"] = [_join(variant_key, s) for s in segs[:10]]
        details.update({"segments_checked": checked, "segments_missing": missing, "segments_too_small": too_small})
        ok = (missing == 0) and (too_small == 0)
        return ok, details

    # 1) если мастера нет — rebuild
    if not _s3_exists(master_key):
        fix_rebuild_hls(src_mp4_key=src_key, hls_dir_key=new_prefix.rstrip("/"), ffmpeg_timeout=VIDEO_MAINTENANCE.ffmpeg_timeout_sec)
        # гарантируем legacy alias (только для этого видео)
        try:
            _ensure_legacy_alias_only()
        except Exception:
            logger.exception("[video_maintenance] legacy alias write failed for %s", src_key)
        return {"status": "rebuilt", "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key}

    # 2) проверяем master/variants + аудио
    c1 = check_master_and_variants(master_key)
    c2 = check_audio_present(master_key)
    problems = set(c1.problems + c2.problems)

    if problems & {Problem.MISSING_MASTER, Problem.MISSING_VARIANT, Problem.UNDECODABLE_SEGMENT}:
        fix_rebuild_hls(src_mp4_key=src_key, hls_dir_key=new_prefix.rstrip("/"), ffmpeg_timeout=VIDEO_MAINTENANCE.ffmpeg_timeout_sec)
        try:
            _ensure_legacy_alias_only()
        except Exception:
            logger.exception("[video_maintenance] legacy alias write failed for %s", src_key)
        return {"status": "rebuilt", "reason": [p.name for p in problems], "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key}

    # NO_AUDIO: считаем некритичным для некоторых видео, но по вашим требованиям лучше чинить
    if Problem.NO_AUDIO in problems:
        fix_rebuild_hls(
            src_mp4_key=src_key,
            hls_dir_key=new_prefix.rstrip("/"),
            ffmpeg_timeout=VIDEO_MAINTENANCE.ffmpeg_timeout_sec,
        )
        try:
            _ensure_legacy_alias_only()
        except Exception:
            logger.exception("[video_maintenance] legacy alias write failed for %s", src_key)
        return {"status": "rebuilt_audio", "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key}

    # 2.5) проверка «первые сегменты существуют»
    ok, seg_details = _segments_ok(master_key)
    if not ok:
        fix_rebuild_hls(src_mp4_key=src_key, hls_dir_key=new_prefix.rstrip("/"), ffmpeg_timeout=VIDEO_MAINTENANCE.ffmpeg_timeout_sec)
        try:
            _ensure_legacy_alias_only()
        except Exception:
            logger.exception("[video_maintenance] legacy alias write failed for %s", src_key)
        return {"status": "rebuilt_segments", "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key, "segments": seg_details}

    # 2.6) ACL (public-read) — важная проверка из video_diagnostics:
    # если файлы приватные, S3 head_object работает, но браузер не сможет скачать через CDN.
    acl_report = None
    if VIDEO_MAINTENANCE.hls_fix_acl_public_read:
        keys_to_fix = [master_key, seg_details.get("variant_key")]
        keys_to_fix += list(seg_details.get("segment_keys") or [])
        keys_to_fix = [k for k in keys_to_fix if isinstance(k, str) and k]
        acl_report = _ensure_public_read_acl(keys_to_fix, dry_run=False)

    # 3) всё ок, но alias всё равно поддерживаем
    try:
        _ensure_legacy_alias_only()
    except Exception:
        logger.exception("[video_maintenance] legacy alias write failed for %s", src_key)

    out = {"status": "ok", "new_pl_key": new_pl_key, "legacy_pl_key": legacy_pl_key, "segments": seg_details}
    if acl_report:
        out["acl"] = acl_report
    return out


def _rename_key_if_needed(
    *,
    old_key: str,
    dry_run: bool,
) -> dict:
    canonical = canonicalize_s3_key(old_key)
    if not canonical or canonical == old_key:
        return {"status": "skipped", "old_key": old_key, "new_key": old_key}

    new_key = _unique_key_if_exists(canonical, salt=old_key)

    if dry_run:
        return {"status": "dry_run", "old_key": old_key, "new_key": new_key}

    # copy_object: key должен быть «сырым», без URL encoding
    head = s3.head_object(Bucket=S3_BUCKET, Key=old_key)
    meta = dict(head.get("Metadata", {}) or {})
    ct = head.get("ContentType") or "video/mp4"

    s3.copy_object(
        Bucket=S3_BUCKET,
        Key=new_key,
        CopySource={"Bucket": S3_BUCKET, "Key": old_key},
        Metadata=meta,
        MetadataDirective="REPLACE",
        ACL="public-read",
        ContentType=ct,
    )
    return {"status": "renamed", "old_key": old_key, "new_key": new_key}


def _delete_old_key(*, old_key: str, dry_run: bool) -> None:
    if dry_run:
        return
    try:
        s3.delete_object(Bucket=S3_BUCKET, Key=old_key)
    except Exception:
        logger.exception("[video_maintenance] failed to delete old key %s", old_key)


def _normalize_incoming_video_ref(video_url_or_key: str) -> str:
    # поддерживаем url и key; снимаем %xx если пришло
    k = key_from_public_or_endpoint_url(video_url_or_key)
    return unquote(k.lstrip("/"))


def _process_one(
    *,
    old_key: str,
    dry_run: bool,
    delete_old_key: bool,
) -> dict:
    """
    Обработка одного mp4.
    Важно: если key меняется — mp4 фиксируем и HLS строим уже на НОВОМ key.
    """
    if "/.hls/" in old_key or old_key.endswith("_hls/"):
        return {"status": "skipped", "reason": "hls_path", "old_key": old_key}
    if not old_key.lower().endswith(".mp4"):
        return {"status": "skipped", "reason": "not_mp4", "old_key": old_key}

    if not _lock(old_key):
        return {"status": "skipped", "reason": "locked", "old_key": old_key}

    try:
        # 1) rename key
        rename = _rename_key_if_needed(old_key=old_key, dry_run=dry_run)
        new_key = rename.get("new_key") or old_key

        # 2) mp4 fix (faststart + codecs)
        # В dry-run новый ключ ещё не создан, поэтому кодеки нужно определять по реальному (старому) объекту.
        probe_key = old_key if dry_run else new_key
        mp4_fix = _fix_mp4_to_compatible(src_key=probe_key, dry_run=dry_run)
        if dry_run and probe_key != new_key:
            mp4_fix = dict(mp4_fix)
            mp4_fix["probe_key"] = probe_key
            mp4_fix["would_apply_to_key"] = new_key

        # 3) HLS validate/repair + alias
        hls = _validate_and_fix_hls_for(new_key, dry_run=dry_run)

        # 4) DB rewrite old->new (только если rename был)
        db_report = None
        if new_key != old_key:
            db = SessionLocal()
            try:
                with db.begin():
                    db_report = rewrite_references_for_key(db, old_key=old_key, new_key=new_key, dry_run=dry_run)
            finally:
                db.close()

        # 5) delete old
        if (new_key != old_key) and delete_old_key:
            _delete_old_key(old_key=old_key, dry_run=dry_run)

        result = {
            "status": "ok",
            "old_key": old_key,
            "new_key": new_key,
            "rename": rename,
            "mp4": mp4_fix,
            "hls": hls,
            "db": db_report,
            "delete_old_key": bool(delete_old_key and (new_key != old_key)),
            "public_old": public_url_for_key(old_key, public_host=S3_PUBLIC_HOST),
            "public_new": public_url_for_key(new_key, public_host=S3_PUBLIC_HOST),
        }
        _audit({"ts": int(time.time()), "result": result})
        return result
    finally:
        _unlock(old_key)


@shared_task(name="app.tasks.video_maintenance.tick")
def tick() -> dict:
    """
    Периодическая таска: берёт батч mp4 из бакета (по continuation token) и чинит их.
    Расписание включаем после ручного теста.
    """
    t0 = time.time()
    token = rds.get(R_CURSOR) or None
    processed: list[dict] = []

    # 1) листим одну страницу, чтобы продвинуться по бакету
    kwargs: Dict[str, Any] = {"Bucket": S3_BUCKET, "MaxKeys": VIDEO_MAINTENANCE.list_page_size}
    if token:
        kwargs["ContinuationToken"] = token

    resp = s3.list_objects_v2(**kwargs)
    contents = resp.get("Contents", []) or []

    # курсор для следующего тика
    next_token = resp.get("NextContinuationToken")
    if resp.get("IsTruncated"):
        if next_token:
            rds.set(R_CURSOR, next_token)
    else:
        # дошли до конца — начинаем сначала
        rds.delete(R_CURSOR)

    # 2) выбираем до batch_size mp4
    candidates: list[str] = []
    for obj in contents:
        k = obj.get("Key")
        if not k:
            continue
        if "/.hls/" in k or k.endswith("_hls/"):
            continue
        if not k.lower().endswith(".mp4"):
            continue
        candidates.append(k)
        if len(candidates) >= VIDEO_MAINTENANCE.batch_size:
            break

    for k in candidates:
        try:
            processed.append(
                _process_one(old_key=k, dry_run=False, delete_old_key=VIDEO_MAINTENANCE.delete_old_key_by_default)
            )
        except Exception as e:
            logger.exception("[video_maintenance] failed for %s: %s", k, e)
            processed.append({"status": "error", "old_key": k, "error": f"{type(e).__name__}: {e}"})

    return {
        "status": "ok",
        "batch_size": VIDEO_MAINTENANCE.batch_size,
        "cursor_present": bool(token),
        "processed_count": len(processed),
        "processed": processed,
        "duration_sec": int(time.time() - t0),
        "config": asdict(VIDEO_MAINTENANCE),
    }


@shared_task(name="app.tasks.video_maintenance.process_list", bind=True)
def process_list(
    self,
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Ручной запуск (через API): payload = {\"videos\": [<url|key>...], \"dry_run\": bool, \"delete_old_key\": bool}
    """
    t0 = time.time()
    videos = payload.get("videos") or []
    dry_run = bool(payload.get("dry_run", False))
    delete_old_key = bool(payload.get("delete_old_key", False))

    results: list[dict] = []
    for v in videos:
        key = _normalize_incoming_video_ref(str(v))
        try:
            self.update_state(state="PROGRESS", meta={"current": key, "done": len(results), "total": len(videos)})
            results.append(_process_one(old_key=key, dry_run=dry_run, delete_old_key=delete_old_key))
        except Exception as e:
            logger.exception("[video_maintenance] manual failed for %s: %s", key, e)
            results.append({"status": "error", "old_key": key, "error": f"{type(e).__name__}: {e}"})

    return {"status": "ok", "dry_run": dry_run, "delete_old_key": delete_old_key, "results": results, "duration_sec": int(time.time() - t0)}


