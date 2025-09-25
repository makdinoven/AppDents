# app/tasks/clip_tasks.py
import json
import mimetypes
import os
import subprocess
import time
import uuid
import tempfile
from pathlib import Path
from urllib.parse import unquote, urlparse, quote
from threading import Thread, Event
from collections import deque
import signal
from typing import Callable, Optional, Tuple

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# =========================
# S3 / ENV
# =========================
S3_BUCKET      = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

# =========================
# Жёстко вшитые настройки (без ENV)
# =========================
# таймауты стрима
START_TIMEOUT       = 180   # сек до первых байт
NOPROGRESS_TIMEOUT  = 60    # сек без прогресса → перезапуск/фолбэк
# критерии валидности
MIN_OK_BYTES        = 1_000_000     # не публикуем пустышки
MIN_OK_DURATION_SEC = 2.0
# Multipart размеры
MIN_PART            = 5 * 1024 * 1024
DEFAULT_PART        = 8 * 1024 * 1024
# Аудио-стратегия
TRANSCODE_NON_AAC   = True          # не-AAC → перекодировать в AAC
AUDIO_BR            = "128k"        # битрейт при перекодировании
# Поведение
ALLOW_DOWNLOAD_FALLBACK = True      # разрешить локальный фолбэк (надёжно, но использует диск)

# Celery лимиты — увеличены, чтобы не падать по софт-таймауту на медленных сетях
CELERY_SOFT_LIMIT = 2400   # 40 минут
CELERY_HARD_LIMIT = 3600   # 60 минут

# =========================
# S3 clients
# =========================
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

TRANSFER_CFG = TransferConfig(
    multipart_threshold=DEFAULT_PART,
    multipart_chunksize=DEFAULT_PART,
    max_concurrency=2,
    use_threads=True,
)

# =========================
# helpers
# =========================
def _bucket_from_url(url: str) -> str:
    host = urlparse(url).hostname or ""
    return host.split(".")[0] if host.endswith(".s3.twcstorage.ru") else S3_BUCKET

def _key_from_url(url: str) -> str:
    return unquote(urlparse(url).path.lstrip("/"))

def _unique_clip_name(original_key: str) -> str:
    p = Path(original_key)
    return str(p.parent / "narezki" / f"{p.stem}_clip_{uuid.uuid4().hex}{p.suffix or '.mp4'}")

def _encode_for_url(key: str) -> str:
    return quote(key, safe="/")

def _fmt_ret(ret: int) -> str:
    if ret is None:
        return "None"
    if ret < 0:
        sig = -ret
        try:
            name = signal.Signals(sig).name
        except Exception:
            name = f"SIG{sig}"
        return f"{ret} ({name})"
    return str(ret)

def _stderr_collector(proc):
    tail = deque(maxlen=200)
    stop = Event()
    def _reader():
        try:
            while not stop.is_set():
                line = proc.stderr.readline()
                if not line:
                    break
                text = line.decode("utf-8", "ignore").strip()
                if text:
                    tail.append(text)
        finally:
            stop.set()
    Thread(target=_reader, daemon=True).start()
    return tail, stop

def _make_presigned(bucket: str, key: str, ttl: int = 3600) -> str:
    return s3_v4.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=ttl
    )

# ----- ffprobe -----
def _ffprobe_duration_url(url: str, timeout: int = 25) -> Tuple[Optional[float], Optional[str]]:
    try:
        cp = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-of", "json", url],
            capture_output=True, timeout=timeout
        )
        if cp.returncode != 0:
            return None, None
        data = json.loads(cp.stdout.decode("utf-8", "ignore"))
        dur = data.get("format", {}).get("duration")
        return (float(dur) if dur is not None else None), cp.stdout.decode("utf-8", "ignore")
    except Exception:
        return None, None

def _ffprobe_duration_file(path: str, timeout: int = 25) -> Optional[float]:
    try:
        cp = subprocess.run(
            ["ffprobe", "-v", "error", "-show_format", "-of", "json", path],
            capture_output=True, timeout=timeout
        )
        if cp.returncode != 0:
            return None
        data = json.loads(cp.stdout.decode("utf-8", "ignore"))
        dur = data.get("format", {}).get("duration")
        return float(dur) if dur is not None else None
    except Exception:
        return None

def _ffprobe_codecs(url_or_path: str, timeout: int = 20) -> Tuple[Optional[str], Optional[str]]:
    """Возвращает (audio_codec, video_codec)."""
    a = v = None
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=codec_name", "-of", "json", url_or_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        if p.returncode == 0:
            obj = json.loads(p.stdout.decode("utf-8","ignore") or "{}")
            arr = obj.get("streams") or []
            if arr:
                a = (arr[0].get("codec_name") or "").lower() or None
    except Exception:
        pass
    try:
        p2 = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=codec_name", "-of", "json", url_or_path],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        if p2.returncode == 0:
            obj2 = json.loads(p2.stdout.decode("utf-8","ignore") or "{}")
            arr2 = obj2.get("streams") or []
            if arr2:
                v = (arr2[0].get("codec_name") or "").lower() or None
    except Exception:
        pass
    return a, v

def _validate_clip_s3(bucket: str, key: str) -> Tuple[bool, str]:
    """Проверяем загруженный клип: размер и (по возможности) длительность."""
    try:
        head = s3.head_object(Bucket=bucket, Key=key)
    except Exception as e:
        return False, f"head failed: {e}"
    size = head.get("ContentLength", 0)
    if size < MIN_OK_BYTES:
        return False, f"too small: {size} < {MIN_OK_BYTES}"

    url = _make_presigned(bucket, key, ttl=300)
    dur, _ = _ffprobe_duration_url(url, timeout=25)
    if dur is None:
        return True, f"ok_by_size_only:{size}"
    if dur < MIN_OK_DURATION_SEC:
        return False, f"too short: {dur:.3f}s < {MIN_OK_DURATION_SEC}s"
    return True, f"ok:{size}bytes,{dur:.3f}s"

# =========================
# Multipart upload из pipe (ручной)
# =========================
def multipart_upload_from_pipe(
    pipe,
    *,
    bucket: str,
    key: str,
    content_type: str = "video/mp4",
    content_disposition: str = "inline",
    part_size: int = DEFAULT_PART,
    progress_cb: Optional[Callable[[int], None]] = None,
    min_ok_bytes: int = MIN_OK_BYTES,
) -> int:
    mpu = s3.create_multipart_upload(
        Bucket=bucket,
        Key=key,
        ContentType=content_type,
        ContentDisposition=content_disposition,
    )
    upload_id = mpu["UploadId"]
    parts = []
    part_no = 1
    sent_total = 0
    buf = bytearray()

    try:
        READ_CHUNK = 1024 * 1024
        while True:
            chunk = pipe.read(READ_CHUNK)
            if not chunk:
                break
            buf += chunk
            if progress_cb:
                progress_cb(len(chunk))

            while len(buf) >= part_size:
                payload = bytes(buf[:part_size])
                del buf[:part_size]
                resp = s3.upload_part(
                    Bucket=bucket,
                    Key=key,
                    PartNumber=part_no,
                    UploadId=upload_id,
                    Body=payload,
                )
                parts.append({"ETag": resp["ETag"], "PartNumber": part_no})
                sent_total += len(payload)
                part_no += 1

        if buf:
            resp = s3.upload_part(
                Bucket=bucket,
                Key=key,
                PartNumber=part_no,
                UploadId=upload_id,
                Body=bytes(buf),
            )
            parts.append({"ETag": resp["ETag"], "PartNumber": part_no})
            sent_total += len(buf)

        if sent_total < max(min_ok_bytes, 1):
            s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
            raise RuntimeError(f"too few bytes streamed ({sent_total} < {min_ok_bytes})")

        s3.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return sent_total

    except Exception:
        try:
            s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
        except Exception:
            pass
        raise

# =========================
# FFmpeg запуск (HTTP → stdout)
# =========================
def _spawn_ffmpeg_http(in_url: str, length_sec: int, audio_codec: Optional[str]) -> subprocess.Popen:
    """
    Вход HTTPS (seekable), выход в fMP4 на stdout.
    - AAC: копируем аудио + aac_adtstoasc.
    - НЕ AAC: либо копируем (если TRANSCODE_NON_AAC=False), либо транскодируем в AAC.
    """
    copy_audio = (audio_codec == "aac") or (audio_codec is None and not TRANSCODE_NON_AAC)

    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-hide_banner", "-nostdin", "-loglevel", "error",
        "-threads", "1",

        # сетевые страховки
        "-rw_timeout", "30000000",         # 30s (μs)
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "3",
        "-reconnect_on_network_error", "1",

        "-ss", "0", "-i", in_url,
        "-t", str(length_sec),

        "-c:v", "copy",
    ]

    if copy_audio:
        cmd += ["-c:a", "copy"]
        if audio_codec == "aac":
            cmd += ["-bsf:a", "aac_adtstoasc"]
    else:
        cmd += ["-c:a", "aac", "-b:a", AUDIO_BR]

    cmd += [
        "-movflags", "frag_keyframe+empty_moov",
        "-muxpreload", "0",
        "-muxdelay", "0",
        "-flush_packets", "1",
        "-f", "mp4",
        "pipe:1",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

def _run_stream_pipeline(self, task_id: str, in_url: str, clip_key: str, mime: str, t0: float):
    """
    HTTPS → ffmpeg(stdout) → S3 (ручной MPU), прогресс и watchdog.
    Возвращает (uploaded_bytes, ffmpeg_ret, stderr_tail).
    """
    # определим кодеки входа и подготовим ffmpeg
    a_codec, _ = _ffprobe_codecs(in_url, timeout=20)
    proc = _spawn_ffmpeg_http(in_url, length_sec=300, audio_codec=a_codec)
    if not proc.stdout:
        return 0, -1, "ffmpeg stdout is not available"

    stderr_tail, stop_stderr = _stderr_collector(proc)
    uploaded = 0
    first_byte_ts = None
    last_progress = time.time()
    upload_err = {"exc": None}

    def _cb(nbytes: int):
        nonlocal uploaded, last_progress, first_byte_ts
        uploaded += nbytes
        now = time.time()
        last_progress = now
        if first_byte_ts is None and uploaded > 0:
            first_byte_ts = now
        if uploaded and (now - t0) >= 2:
            speed = uploaded / max(1.0, now - t0)
            self.update_state(
                task_id=task_id,
                state="PROGRESS",
                meta={
                    "stage": "uploading",
                    "uploaded_bytes": uploaded,
                    "elapsed_sec": int(now - t0),
                    "speed_bytes_per_sec": int(speed),
                },
            )

    def _uploader():
        try:
            multipart_upload_from_pipe(
                proc.stdout,
                bucket=S3_BUCKET,
                key=clip_key,
                content_type=mime,
                content_disposition="inline",
                part_size=DEFAULT_PART,
                progress_cb=_cb,
                min_ok_bytes=MIN_OK_BYTES,
            )
        except Exception as e:
            upload_err["exc"] = e

    th = Thread(target=_uploader, daemon=True)
    th.start()

    try:
        while th.is_alive():
            time.sleep(0.5)
            if first_byte_ts is None and (time.time() - t0) > START_TIMEOUT:
                try: proc.terminate()
                except Exception: pass
                break
            if first_byte_ts is not None and (time.time() - last_progress) > NOPROGRESS_TIMEOUT:
                try: proc.terminate()
                except Exception: pass
                break
    except SoftTimeLimitExceeded:
        try: proc.terminate()
        finally:
            try: proc.wait(timeout=5)
            except Exception: pass
        raise
    finally:
        th.join(timeout=15)
        stop_stderr.set()
        try:
            if proc.stdout: proc.stdout.close()
        except Exception:
            pass
        try:
            ret = proc.wait(timeout=5)
        except Exception:
            ret = 0

    tail = "\n".join(list(stderr_tail)[-30:])
    if upload_err["exc"] is not None:
        raise RuntimeError(f"S3 upload failed: {upload_err['exc']}; ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}")

    return uploaded, ret, tail

# =========================
# Локальный fallback
# =========================
def _ffmpeg_local_clip(src_path: str, dst_path: str):
    a_codec, _ = _ffprobe_codecs(src_path, timeout=15)
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
        "-threads", "2",
        "-i", src_path,
        "-t", "300",
        "-c:v", "copy",
    ]
    if a_codec == "aac":
        cmd += ["-c:a", "copy"]
    else:
        if TRANSCODE_NON_AAC:
            cmd += ["-c:a", "aac", "-b:a", AUDIO_BR]
        else:
            cmd += ["-c:a", "copy"]

    cmd += ["-movflags", "+faststart", "-y", dst_path]

    cp = subprocess.run(cmd, capture_output=True)
    if cp.returncode != 0:
        raise RuntimeError(f"local ffmpeg failed: {cp.stderr.decode('utf-8','ignore')[:2000]}")

# =========================
# TASK
# =========================
@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=CELERY_SOFT_LIMIT,
    time_limit=CELERY_HARD_LIMIT,
    name="app.tasks.clip_tasks.clip_video",
)
def clip_video(self, src_url: str, dest_key: Optional[str] = None, force_download: bool = False) -> dict:
    """
    A: origin presigned → ffmpeg → S3 (стрим, MPU) + валидация.
    B: (если A не дал результата и был stderr) тот же presigned повторно (редко нужно).
    C: локальный фолбэк (при разрешении): S3→диск→ffmpeg→S3 + валидация ДО аплоада.
    Всегда работаем с origin (presigned), вне зависимости от того, пришла CDN-или прямая ссылка.
    """
    t0 = time.time()
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "preparing"})

    # Нормализуем источник (bucket/key) из любой ссылки
    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)

    # HEAD на исходник
    try:
        head = s3.head_object(Bucket=src_bucket, Key=src_key)
    except ClientError as e:
        raise RuntimeError(f"source head failed: {e}")
    size = head.get("ContentLength", 0)
    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "source_ok", "source_bytes": size})

    clip_key = dest_key if dest_key else _unique_clip_name(src_key)
    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"

    # Если принудительно — сразу надёжный локальный путь
    if force_download or not ALLOW_DOWNLOAD_FALLBACK:
        with tempfile.TemporaryDirectory() as tmp:
            src_path  = os.path.join(tmp, "src.bin")
            dst_path  = os.path.join(tmp, "clip.mp4")
            # Скачиваем целиком (из origin)
            s3.download_file(src_bucket, src_key, src_path, Config=TRANSFER_CFG)
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "local_cut"})
            _ffmpeg_local_clip(src_path, dst_path)
            dur = _ffprobe_duration_file(dst_path) or 0.0
            if dur < MIN_OK_DURATION_SEC:
                raise RuntimeError(f"local result too short: {dur:.3f}s < {MIN_OK_DURATION_SEC}s")
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "uploading_result"})
            s3.upload_file(
                dst_path, S3_BUCKET, clip_key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG,
            )
            uploaded3 = os.path.getsize(dst_path)
        if uploaded3 >= MIN_OK_BYTES:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded3,
                    "elapsed_sec": int(time.time() - t0), "path": "download",
                    "validated": f"local:{uploaded3}b,{dur:.3f}s"}
        else:
            try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception: pass
            raise RuntimeError(f"clip too small after local fallback: {uploaded3} bytes (< {MIN_OK_BYTES})")

    # A: всегда используем origin presigned URL для ffmpeg (стабильнее, чем CDN)
    presigned = _make_presigned(src_bucket, src_key)
    uploaded, ret, tail = _run_stream_pipeline(self, task_id, presigned, clip_key, mime, t0)
    if uploaded > 0 and ret == 0:
        ok, why = _validate_clip_s3(S3_BUCKET, clip_key)
        if ok:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded,
                    "elapsed_sec": int(time.time() - t0), "path": "presigned", "validated": why}
        else:
            try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception: pass

    # B: повторная попытка тем же presigned, если был внятный stderr (редкие сетевые проблемы)
    go_retry = (ret != 0 and bool((tail or "").strip()))
    if go_retry:
        uploaded2, ret2, tail2 = _run_stream_pipeline(self, task_id, presigned, clip_key, mime, t0)
        if uploaded2 > 0 and ret2 == 0:
            ok2, why2 = _validate_clip_s3(S3_BUCKET, clip_key)
            if ok2:
                clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
                return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded2,
                        "elapsed_sec": int(time.time() - t0), "path": "presigned-retry", "validated": why2}
            else:
                try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
                except Exception: pass
    else:
        ret2, tail2 = 0, ""

    # C: локальный фолбэк
    if ALLOW_DOWNLOAD_FALLBACK:
        with tempfile.TemporaryDirectory() as tmp:
            src_path  = os.path.join(tmp, "src.bin")
            dst_path  = os.path.join(tmp, "clip.mp4")
            s3.download_file(src_bucket, src_key, src_path, Config=TRANSFER_CFG)
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "local_cut"})
            _ffmpeg_local_clip(src_path, dst_path)
            dur = _ffprobe_duration_file(dst_path) or 0.0
            if dur < MIN_OK_DURATION_SEC:
                raise RuntimeError(f"local result too short: {dur:.3f}s < {MIN_OK_DURATION_SEC}s")
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "uploading_result"})
            s3.upload_file(
                dst_path, S3_BUCKET, clip_key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG,
            )
            uploaded3 = os.path.getsize(dst_path)
        if uploaded3 >= MIN_OK_BYTES:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded3,
                    "elapsed_sec": int(time.time() - t0), "path": "download", "validated": f"local:{uploaded3}b,{dur:.3f}s"}
        else:
            try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception: pass
            raise RuntimeError(f"clip too small after local fallback: {uploaded3} bytes (< {MIN_OK_BYTES})")

    # ничего не вышло
    raise RuntimeError(
        "no output produced:\n"
        f"first presigned ret={_fmt_ret(ret)} tail:\n{tail}\n\n"
        f"retry ret={_fmt_ret(locals().get('ret2', 0))} tail:\n{locals().get('tail2','')}\n"
        "local fallback was disabled or failed."
    )
