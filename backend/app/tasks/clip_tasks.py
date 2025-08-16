# app/tasks/clip_tasks.py
import mimetypes
import os
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse, quote
from threading import Thread, Event
from collections import deque
import signal

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# ---------------- ENV / S3 ----------------
S3_BUCKET      = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

# Двухфазные таймауты
START_TIMEOUT       = int(os.getenv("CLIP_START_TIMEOUT", "120"))   # ждать «первые байты», сек
NOPROGRESS_TIMEOUT  = int(os.getenv("CLIP_NOPROGRESS_TIMEOUT", "60"))  # молчание после старта, сек

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

TRANSFER_CFG = TransferConfig(
    multipart_threshold=8 * 1024 * 1024,
    multipart_chunksize=8 * 1024 * 1024,
    max_concurrency=2,
    use_threads=True,
)

# ---------------- helpers ----------------
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

def _spawn_ffmpeg(in_url: str, length_sec: int = 300) -> subprocess.Popen:
    """
    ffmpeg пишет fragmented MP4 в stdout (pipe:1).
    """
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-threads", "1",

        # сетевые «страховки» для HTTP(S)
        "-rw_timeout", "30000000",          # 30s (микросекунды)
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "3",
        "-reconnect_on_network_error", "1",

        "-ss", "0",
        "-i", in_url,
        "-t", str(length_sec),

        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-movflags", "frag_keyframe+empty_moov",
        "-muxpreload", "0",
        "-muxdelay", "0",
        "-flush_packets", "1",

        "-f", "mp4",
        "pipe:1",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

def _fmt_ret(ret: int) -> str:
    # человекочитаемый вывод кода/сигнала
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

# ---------------- task ----------------
@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=20 * 60,
    time_limit=25 * 60,
)
def clip_video(self, src_url: str) -> dict:
    """
    S3 presigned → ffmpeg(stdout) → S3 upload_fileobj (streaming).
    """
    t0 = time.time()
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    # 0) HEAD исходника
    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "preparing"})
    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)
    try:
        head = s3.head_object(Bucket=src_bucket, Key=src_key)
    except ClientError as e:
        raise RuntimeError(f"source head failed: {e}")
    size = head.get("ContentLength", 0)
    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "source_ok", "source_bytes": size})

    # 1) presigned URL на чтение
    presigned = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": src_bucket, "Key": src_key},
        ExpiresIn=3600,
    )

    # 2) стартуем ffmpeg
    clip_key = _unique_clip_name(src_key)
    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
    proc = _spawn_ffmpeg(presigned, length_sec=300)
    if not proc.stdout:
        raise RuntimeError("ffmpeg stdout is not available")

    # хвост stderr
    stderr_tail = deque(maxlen=200)
    stop_stderr = Event()

    def _stderr_reader():
        try:
            while not stop_stderr.is_set():
                line = proc.stderr.readline()
                if not line:
                    break
                text = line.decode("utf-8", "ignore").strip() or None
                if text:
                    stderr_tail.append(text)
        finally:
            stop_stderr.set()

    th_stderr = Thread(target=_stderr_reader, daemon=True)
    th_stderr.start()

    # загрузчик в отдельном треде
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
        # лёгкий репорт прогресса
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
            s3.upload_fileobj(
                proc.stdout,
                S3_BUCKET,
                clip_key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG,
                Callback=_cb,
            )
        except Exception as e:
            upload_err["exc"] = e

    th_up = Thread(target=_uploader, daemon=True)
    th_up.start()

    try:
        while th_up.is_alive():
            time.sleep(1)

            # фаза 1: ждём первых байт
            if first_byte_ts is None and (time.time() - t0) > START_TIMEOUT:
                try:
                    proc.terminate()
                except Exception:
                    pass
                break

            # фаза 2: после старта — контролируем «тишину»
            if first_byte_ts is not None and (time.time() - last_progress) > NOPROGRESS_TIMEOUT:
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
        th_up.join(timeout=15)
        stop_stderr.set()
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        try:
            ret = proc.wait(timeout=5)
        except Exception:
            ret = 0

    # Обработка ошибок
    tail = "\n".join(list(stderr_tail)[-30:])  # может быть пустым — это нормально

    if upload_err["exc"] is not None:
        raise RuntimeError(f"S3 upload failed: {upload_err['exc']}; ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}")

    # если не пошли первые байты — сообщим явно, а не загадочным 255
    if first_byte_ts is None:
        raise RuntimeError(
            f"No data from ffmpeg for {START_TIMEOUT}s (input stalled or unreachable); ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}"
        )

    # если после старта застыло
    if (time.time() - last_progress) > NOPROGRESS_TIMEOUT:
        raise RuntimeError(
            f"No progress for {NOPROGRESS_TIMEOUT}s after start; ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}"
        )

    # ffmpeg должен завершиться с 0
    if ret != 0:
        raise RuntimeError(f"ffmpeg exited with {_fmt_ret(ret)}; stderr tail:\n{tail}")

    if uploaded == 0:
        raise RuntimeError(f"No data produced by ffmpeg; ffmpeg ret={_fmt_ret(ret)}; stderr tail:\n{tail}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
    return {
        "clip_url": clip_url,
        "length_sec": 300,
        "uploaded_bytes": uploaded,
        "elapsed_sec": int(time.time() - t0),
    }
