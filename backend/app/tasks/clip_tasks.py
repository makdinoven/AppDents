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
START_TIMEOUT       = int(os.getenv("CLIP_START_TIMEOUT", "120"))   # ждать первые байты (сек)
NOPROGRESS_TIMEOUT  = int(os.getenv("CLIP_NOPROGRESS_TIMEOUT", "60"))  # молчание после старта (сек)

# основной S3-клиент (операции/метаданные)
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# отдельный клиент для presigned V4
s3_v4 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3v4", s3={"addressing_style": "path"}),
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

def _stderr_collector(proc) -> deque:
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
    t = Thread(target=_reader, daemon=True)
    t.start()
    return tail, stop

# ---- FFmpeg spawners ----
def _spawn_ffmpeg_http(in_url: str, length_sec: int = 300) -> subprocess.Popen:
    # HTTP(S) → stdout
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-threads", "1",

        # страховки для HTTP-ввода
        "-rw_timeout", "30000000",  # 30s, μs
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

def _spawn_ffmpeg_stdin(length_sec: int = 300) -> subprocess.Popen:
    # stdin (pipe:0) → stdout (pipe:1)
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-threads", "1",

        "-ss", "0",
        "-i", "pipe:0",
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
    return subprocess.Popen(cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

# ---------------- task ----------------
@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=20 * 60,
    time_limit=25 * 60,
)
def clip_video(self, src_url: str) -> dict:
    """
    Попытка 1: presigned V4 → FFmpeg (HTTP input) → stdout → S3.
    Фолбэк:   boto3 get_object → feed в stdin FFmpeg → stdout → S3.
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

    clip_key = _unique_clip_name(src_key)
    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"

    # ===== TRY #1: presigned V4 → http input =====
    presigned_v4 = s3_v4.generate_presigned_url(
        "get_object",
        Params={"Bucket": src_bucket, "Key": src_key},
        ExpiresIn=3600,
    )

    def _pipeline_with_proc(proc) -> tuple[int, int, str]:
        """Общий аплоад stdout в S3, с колбэком прогресса и двухфазным watchdog."""
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
            # лёгкий прогресс
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
            th_up.join(timeout=15)
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
        # 0 — успех, >0/negative — ошибка/сигнал
        # вернём: uploaded, ret, tail
        return uploaded, ret, tail

    # Попытка 1: http input
    proc1 = _spawn_ffmpeg_http(presigned_v4, length_sec=300)
    uploaded1, ret1, tail1 = _pipeline_with_proc(proc1)

    if uploaded1 > 0 and ret1 == 0:
        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
        return {
            "clip_url": clip_url,
            "length_sec": 300,
            "uploaded_bytes": uploaded1,
            "elapsed_sec": int(time.time() - t0),
            "path": "http",
        }

    # ===== TRY #2 (fallback): boto3 get_object → stdin → stdout =====
    # читаем из S3 сами и кормим ffmpeg по pipe:0
    obj = s3.get_object(Bucket=src_bucket, Key=src_key)
    body = obj["Body"]  # botocore.response.StreamingBody

    proc2 = _spawn_ffmpeg_stdin(length_sec=300)

    # pump S3→stdin
    pump_err = {"exc": None}
    def _pump():
        try:
            for chunk in body.iter_chunks(8 * 1024 * 1024):
                if not chunk:
                    continue
                proc2.stdin.write(chunk)
        except Exception as e:
            pump_err["exc"] = e
        finally:
            try:
                proc2.stdin.close()
            except Exception:
                pass

    th_pump = Thread(target=_pump, daemon=True)
    th_pump.start()

    uploaded2, ret2, tail2 = _pipeline_with_proc(proc2)

    if pump_err["exc"] is not None:
        raise RuntimeError(f"input pump failed: {pump_err['exc']}; ffmpeg ret={_fmt_ret(ret2)}; stderr tail:\n{tail2}")

    if uploaded2 > 0 and ret2 == 0:
        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
        return {
            "clip_url": clip_url,
            "length_sec": 300,
            "uploaded_bytes": uploaded2,
            "elapsed_sec": int(time.time() - t0),
            "path": "stdin",
        }

    # если обе попытки не дали байтов — формируем осмысленную ошибку
    if uploaded1 == 0 and uploaded2 == 0:
        raise RuntimeError(
            "no output produced: "
            f"http: ret={_fmt_ret(ret1)} tail:\n{tail1}\n\n"
            f"stdin: ret={_fmt_ret(ret2)} tail:\n{tail2}"
        )

    # если байты были, но ffmpeg завершился не 0 — тоже покажем хвост
    raise RuntimeError(
        f"ffmpeg failed after producing {uploaded1 or uploaded2} bytes; "
        f"http ret={_fmt_ret(ret1)} tail:\n{tail1}\n\nstdin ret={_fmt_ret(ret2)} tail:\n{tail2}"
    )
