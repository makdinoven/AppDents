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
from ..core.storage import S3_BUCKET, S3_PUBLIC_HOST, s3_client

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

# ===== NEW: вотчдог скорости стрима =====
MIN_STREAM_BPS      = 200 * 1024  # 200 KB/s — порог «слишком медленно»
SLOW_WINDOW_SEC     = 30          # окно усреднения
HARD_SLOW_GUARD_SEC = 45          # жёсткий предохранитель

# =========================
# S3 clients
# =========================
s3 = s3_client(signature_version="s3v4")
s3_v4 = s3

# ===== NEW: разные конфиги для upload / download =====
TRANSFER_CFG_UPLOAD = TransferConfig(
    multipart_threshold=DEFAULT_PART,
    multipart_chunksize=DEFAULT_PART,
    max_concurrency=2,
    use_threads=True,
)

TRANSFER_CFG_DOWNLOAD = TransferConfig(
    multipart_threshold=DEFAULT_PART,
    multipart_chunksize=DEFAULT_PART,
    max_concurrency=8,   # можно 8-16, если есть CPU/сеть
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
            ["ffprobe", "-v", "fatal", "-show_format", "-of", "json", url],
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
            ["ffprobe", "-v", "fatal", "-show_format", "-of", "json", path],
            capture_output=True, timeout=timeout
        )
        if cp.returncode != 0:
            return None
        data = json.loads(cp.stdout.decode("utf-8", "ignore"))
        dur = data.get("format", {}).get("duration")
        return float(dur) if dur is not None else None
    except Exception:
        return None

def _download_with_progress(bucket: str, key: str, dst_path: str,
                            report_every_sec: float,
                            progress_cb: Callable[[int, float], None]) -> int:
    """
    Скачивает объект S3 -> dst_path с прогрессом.
    Возвращает суммарно скачанные байты.
    Делает жёсткие проверки наличия/размера файла на диске.
    """
    os.makedirs(os.path.dirname(dst_path), exist_ok=True)

    downloaded = 0
    t0 = time.time()
    last = t0

    def _cb(n):
        nonlocal downloaded, last
        downloaded += n
        now = time.time()
        if now - last >= report_every_sec:
            speed = downloaded / max(1.0, now - t0)
            try:
                progress_cb(downloaded, speed)
            except Exception:
                pass
            last = now

    try:
        s3.download_file(bucket, key, dst_path, Callback=_cb, Config=TRANSFER_CFG_DOWNLOAD)
    except Exception as e:
        raise RuntimeError(f"S3 download failed: {bucket}/{key}: {e}")

    # финальный пуш
    now = time.time()
    speed = downloaded / max(1.0, now - t0)
    try:
        progress_cb(downloaded, speed)
    except Exception:
        pass

    if not os.path.exists(dst_path):
        raise RuntimeError(f"Downloaded file is missing on disk: {dst_path}")
    size_on_disk = os.path.getsize(dst_path)
    if size_on_disk <= 0:
        raise RuntimeError(f"Downloaded file is empty: {dst_path}")

    if downloaded <= 0:
        downloaded = size_on_disk

    return downloaded


def _ffprobe_codecs(url_or_path: str, timeout: int = 20) -> Tuple[Optional[str], Optional[str]]:
    """Возвращает (audio_codec, video_codec)."""
    a = v = None
    try:
        p = subprocess.run(
            ["ffprobe", "-v", "fatal", "-select_streams", "a:0",
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
            ["ffprobe", "-v", "fatal", "-select_streams", "v:0",
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


def _apply_faststart(bucket: str, key: str, mime: str) -> Tuple[bool, str]:
    """
    Скачивает клип из S3, применяет faststart (перемещает moov атом в начало),
    загружает обратно. Без перекодирования — только ремуксинг.
    Возвращает (success, message).
    """
    with tempfile.TemporaryDirectory() as tmp:
        src_path = os.path.join(tmp, "frag.mp4")
        dst_path = os.path.join(tmp, "fast.mp4")

        # 1. Скачиваем текущий клип
        try:
            s3.download_file(bucket, key, src_path, Config=TRANSFER_CFG_DOWNLOAD)
        except Exception as e:
            return False, f"download failed: {e}"

        if not os.path.exists(src_path) or os.path.getsize(src_path) < MIN_OK_BYTES:
            return False, f"downloaded file missing or too small"

        # 2. Ремуксинг с faststart (без перекодирования)
        cmd = [
            "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "error",
            "-i", src_path,
            "-c", "copy",
            "-movflags", "+faststart",
            "-y", dst_path,
        ]
        try:
            cp = subprocess.run(cmd, capture_output=True, timeout=120)
            if cp.returncode != 0:
                err = cp.stderr.decode("utf-8", "ignore")[:500]
                return False, f"ffmpeg remux failed: {err}"
        except subprocess.TimeoutExpired:
            return False, "ffmpeg remux timeout"
        except Exception as e:
            return False, f"ffmpeg remux error: {e}"

        if not os.path.exists(dst_path) or os.path.getsize(dst_path) < MIN_OK_BYTES:
            return False, "remuxed file missing or too small"

        # 3. Загружаем обратно в S3 (перезаписываем)
        try:
            s3.upload_file(
                dst_path,
                bucket,
                key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG_UPLOAD,
            )
        except Exception as e:
            return False, f"upload failed: {e}"

        final_size = os.path.getsize(dst_path)
        return True, f"faststart applied: {final_size} bytes"


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
    """
    Читает байты из pipe и грузит в S3 через MPU.
    ВАЖНО: если суммарно пришло < min_ok_bytes — делаем AbortMultipartUpload и
    ВОЗВРАЩАЕМ 0 вместо исключения. Таким образом, вызывающий код сможет
    корректно уйти на фолбэк, а задача не упадёт.
    """
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

        # ключевое изменение: если получили слишком мало — не кидаем исключение
        if sent_total < max(min_ok_bytes, 1):
            try:
                s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)
            except Exception:
                pass
            return 0  # сигнализируем вызывающему коду: «ничего годного не выгрузили»

        s3.complete_multipart_upload(
            Bucket=bucket,
            Key=key,
            UploadId=upload_id,
            MultipartUpload={"Parts": parts},
        )
        return sent_total

    except Exception:
        # при любой ошибке аккуратно абортим MPU
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
        "-hide_banner", "-nostdin", "-loglevel", "fatal",
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
    HTTPS → ffmpeg(stdout) → S3 (ручной MPU), расширенный прогресс и watchdog скорости.
    Возвращает (uploaded_bytes, ffmpeg_ret, stderr_tail).
    """
    a_codec, _ = _ffprobe_codecs(in_url, timeout=20)
    proc = _spawn_ffmpeg_http(in_url, length_sec=300, audio_codec=a_codec)
    if not proc.stdout:
        return 0, -1, "ffmpeg stdout is not available"

    stderr_tail, stop_stderr = _stderr_collector(proc)
    uploaded = 0
    first_byte_ts = None
    last_progress = time.time()
    last_push = 0.0
    upload_err = {"exc": None}
    upload_total = {"n": None}  # <-- добавили контейнер для возврата из MPU

    def _cb(nbytes: int):
        nonlocal uploaded, last_progress, first_byte_ts
        uploaded += nbytes
        now = time.time()
        last_progress = now
        if first_byte_ts is None and uploaded > 0:
            first_byte_ts = now

    def _uploader():
        try:
            n = multipart_upload_from_pipe(
                proc.stdout,
                bucket=S3_BUCKET,
                key=clip_key,
                content_type=mime,
                content_disposition="inline",
                part_size=DEFAULT_PART,
                progress_cb=_cb,
                min_ok_bytes=MIN_OK_BYTES,
            )
            upload_total["n"] = n  # <-- сохранили реальный объём, загруженный в S3
        except Exception as e:
            upload_err["exc"] = e

    th = Thread(target=_uploader, daemon=True)
    th.start()

    try:
        while th.is_alive():
            time.sleep(0.5)
            now = time.time()

            # --- периодически публикуем расширенный статус (всегда виден в /clip/{job_id}) ---
            if now - last_push >= 2.5:
                avg_bps = (uploaded / max(1.0, (now - (first_byte_ts or now)))) if first_byte_ts else 0.0
                since_fb = (now - first_byte_ts) if first_byte_ts else 0.0
                last_gap = (now - last_progress) if first_byte_ts else 0.0

                if first_byte_ts and avg_bps < MIN_STREAM_BPS:
                    if since_fb >= SLOW_WINDOW_SEC:
                        switch_in = 0
                    else:
                        switch_in = int(SLOW_WINDOW_SEC - since_fb)
                else:
                    switch_in = None

                tail_lines = list(stderr_tail)[-3:]  # последние 3 строки

                self.update_state(
                    task_id=task_id,
                    state="PROGRESS",
                    meta={
                        "stage": "uploading",
                        "attempt": "stream",
                        "uploaded_bytes": uploaded,
                        "elapsed_sec": int(now - t0),
                        "speed_bytes_per_sec": int(uploaded / max(1.0, now - t0)),
                        "avg_bytes_per_sec": int(avg_bps),
                        "since_first_byte_sec": int(since_fb) if first_byte_ts else None,
                        "last_progress_ago_sec": int(last_gap) if first_byte_ts else None,
                        "min_stream_bps": MIN_STREAM_BPS,
                        "slow_window_sec": SLOW_WINDOW_SEC,
                        "switch_to_local_in_sec": switch_in,
                        "stderr_tail": tail_lines,
                        "input_url_host": urlparse(in_url).hostname if in_url else None,
                    },
                )
                last_push = now

            # --- Вотчдоги ---
            if first_byte_ts is None and (now - t0) > START_TIMEOUT:
                self.update_state(task_id=task_id, state="PROGRESS", meta={
                    "stage": "stream_stopped", "attempt": "stream",
                    "switch_reason": "no_first_byte", "next": "local",
                })
                try:
                    proc.terminate()
                except Exception:
                    pass
                break

            if first_byte_ts is not None and (now - last_progress) > NOPROGRESS_TIMEOUT:
                self.update_state(task_id=task_id, state="PROGRESS", meta={
                    "stage": "stream_stopped", "attempt": "stream",
                    "switch_reason": "no_progress", "next": "local",
                })
                try:
                    proc.terminate()
                except Exception:
                    pass
                break

            if first_byte_ts is not None and (now - first_byte_ts) >= HARD_SLOW_GUARD_SEC:
                avg = uploaded / max(1.0, now - first_byte_ts)
                if avg < MIN_STREAM_BPS:
                    self.update_state(task_id=task_id, state="PROGRESS", meta={
                        "stage": "stream_stopped", "attempt": "stream",
                        "switch_reason": "hard_slow_guard",
                        "avg_bytes_per_sec": int(avg),
                        "min_stream_bps": MIN_STREAM_BPS,
                        "since_first_byte_sec": int(now - first_byte_ts),
                        "next": "local",
                    })
                    try:
                        proc.terminate()
                    except Exception:
                        pass
                    break

    except SoftTimeLimitExceeded:
            try:
                    proc.terminate()
            finally:
                try:
                    proc.wait(timeout=5)
                except Exception:
                    pass
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

        # <-- критично: переписываем 'uploaded' фактическим объёмом, который попал в S3
    if upload_total["n"] is not None:
        uploaded = upload_total["n"]

    tail = "\n".join(list(stderr_tail)[-30:])
    if upload_err["exc"] is not None:
        raise RuntimeError(f"S3 upload failed: {upload_err['exc']}; ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}")

    return uploaded, ret, tail

# =========================
# Локальный fallback
# =========================
def _ffmpeg_local_clip(src_path: str, dst_path: str):
    if (not os.path.exists(src_path)) or (os.path.getsize(src_path) <= 0):
        raise RuntimeError(f"local ffmpeg: source file not found or empty: {src_path}")

    a_codec, _ = _ffprobe_codecs(src_path, timeout=15)
    cmd = [
        "ffmpeg", "-hide_banner", "-nostdin", "-loglevel", "fatal",
        "-threads", "2",
        "-i", src_path,
        "-t", "300",
        "-c:v", "copy",
    ]
    if a_codec == "aac":
        cmd += ["-c:a", "copy"]
    else:
        cmd += ["-c:a", "aac", "-b:a", AUDIO_BR] if TRANSCODE_NON_AAC else ["-c:a", "copy"]

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
    B: retry presigned (если был явный stderr).
    C: локальный фолбэк.
    """
    t0 = time.time()
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "preparing"})

    # нормализация источника
    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)

    # HEAD
    try:
        head = s3.head_object(Bucket=src_bucket, Key=src_key)
    except ClientError as e:
        raise RuntimeError(f"source head failed: {e}")
    size = head.get("ContentLength", 0)
    self.update_state(task_id=task_id, state="STARTED",
                      meta={"stage": "source_ok", "source_bytes": size})

    clip_key = dest_key if dest_key else _unique_clip_name(src_key)
    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"

    # ===== A: presigned-stream =====
    presigned = _make_presigned(src_bucket, src_key)
    uploaded = ret = 0
    tail = ""

    if not force_download:
        try:
            uploaded, ret, tail = _run_stream_pipeline(self, task_id, presigned, clip_key, mime, t0)
        except Exception as e:
            # Любая ошибка стриминга не фатальна: уходим на фолбэк дальше.
            tail = (str(e) or "")[:2000]
            uploaded, ret = 0, -1

        # успех?
        if uploaded > 0 and ret == 0:
            ok, why = _validate_clip_s3(S3_BUCKET, clip_key)
            if ok:
                # Пост-обработка: применяем faststart для корректных метаданных
                self.update_state(task_id=task_id, state="PROGRESS",
                                  meta={"stage": "applying_faststart"})
                fs_ok, fs_msg = _apply_faststart(S3_BUCKET, clip_key, mime)
                if fs_ok:
                    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
                    return {
                        "clip_url": clip_url,
                        "length_sec": 300,
                        "uploaded_bytes": uploaded,
                        "elapsed_sec": int(time.time() - t0),
                        "path": "presigned",
                        "validated": why,
                        "postprocessed": True,
                        "faststart": fs_msg,
                    }
                # faststart не удался — удаляем и уходим на fallback
                try:
                    s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
                except Exception:
                    pass
            else:
                # подчищаем мусор и продолжаем
                try:
                    s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
                except Exception:
                    pass

        # ===== B: retry presigned — только если реально был stderr (сигнал «что-то пошло не так»)
        if ret != 0 and bool((tail or "").strip()):
            try:
                uploaded2, ret2, tail2 = _run_stream_pipeline(self, task_id, presigned, clip_key, mime, t0)
            except Exception:
                uploaded2, ret2, tail2 = 0, -1, ""
            if uploaded2 > 0 and ret2 == 0:
                ok2, why2 = _validate_clip_s3(S3_BUCKET, clip_key)
                if ok2:
                    # Пост-обработка: применяем faststart для корректных метаданных
                    self.update_state(task_id=task_id, state="PROGRESS",
                                      meta={"stage": "applying_faststart"})
                    fs_ok2, fs_msg2 = _apply_faststart(S3_BUCKET, clip_key, mime)
                    if fs_ok2:
                        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
                        return {
                            "clip_url": clip_url,
                            "length_sec": 300,
                            "uploaded_bytes": uploaded2,
                            "elapsed_sec": int(time.time() - t0),
                            "path": "presigned-retry",
                            "validated": why2,
                            "postprocessed": True,
                            "faststart": fs_msg2,
                        }
                    # faststart не удался — удаляем и уходим на fallback
                    try:
                        s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
                    except Exception:
                        pass
                else:
                    try:
                        s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
                    except Exception:
                        pass

    # ===== C: локальный фолбэк (S3 → диск → ffmpeg → S3) =====
    if ALLOW_DOWNLOAD_FALLBACK or force_download:
        with tempfile.TemporaryDirectory() as tmp:
            src_path = os.path.join(tmp, "src.bin")
            dst_path = os.path.join(tmp, "clip.mp4")

            self.update_state(task_id=task_id, state="PROGRESS",
                              meta={"stage": "downloading_source", "source_bytes": size})

            downloaded_bytes = _download_with_progress(
                src_bucket, src_key, src_path, report_every_sec=2.0,
                progress_cb=lambda n, sp: self.update_state(
                    task_id=task_id, state="PROGRESS",
                    meta={
                        "stage": "downloading_source",
                        "downloaded_bytes": n,
                        "source_bytes": size,
                        "download_bps": int(sp),
                    }
                )
            )
            if downloaded_bytes <= 0 or not os.path.exists(src_path):
                raise RuntimeError(f"Download produced no data: {src_bucket}/{src_key}")

            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "local_cut"})
            _ffmpeg_local_clip(src_path, dst_path)

            dur = _ffprobe_duration_file(dst_path) or 0.0
            if dur < MIN_OK_DURATION_SEC:
                raise RuntimeError(f"local result too short: {dur:.3f}s < {MIN_OK_DURATION_SEC}s")

            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "uploading_result"})
            s3.upload_file(
                dst_path,
                S3_BUCKET,
                clip_key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG_UPLOAD,
            )
            uploaded3 = os.path.getsize(dst_path)

        if uploaded3 >= MIN_OK_BYTES:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {
                "clip_url": clip_url,
                "length_sec": 300,
                "uploaded_bytes": uploaded3,
                "elapsed_sec": int(time.time() - t0),
                "path": "download",
                "validated": f"local:{uploaded3}b,{dur:.3f}s",
            }
        else:
            try:
                s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception:
                pass
            raise RuntimeError(f"clip too small after local fallback: {uploaded3} bytes (< {MIN_OK_BYTES})")

    # дошли сюда — ни стрим, ни фолбэк не сработали
    raise RuntimeError(
        "no output produced:\n"
        f"presigned ret={_fmt_ret(ret)} tail:\n{tail or ''}\n"
        "local fallback disabled or failed."
    )

