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

# Таймаут до «первых байт»/после старта
START_TIMEOUT       = int(os.getenv("CLIP_START_TIMEOUT", "600"))   # сек
NOPROGRESS_TIMEOUT  = int(os.getenv("CLIP_NOPROGRESS_TIMEOUT", "60"))

# основной клиент для HEAD/загрузок
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

def _src_host(url: str) -> str:
    return urlparse(url).hostname or ""

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

def _stderr_collector(proc) -> tuple[deque, Event]:
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

def _make_presigned_for_host(bucket: str, key: str, src_host: str) -> str:
    """
    Для ссылок *.s3.twcstorage.ru делаем V4 presign на общем эндпоинте 'https://s3.twcstorage.ru'
    c виртуальным адресованием (итоговый URL → https://<bucket>.s3.twcstorage.ru/key?...).
    Иначе — на S3_ENDPOINT.
    """
    if src_host.endswith(".s3.twcstorage.ru"):
        ep = "https://s3.twcstorage.ru"
    else:
        ep = S3_ENDPOINT

    client = boto3.client(
        "s3",
        endpoint_url=ep,
        region_name=S3_REGION,
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
        config=Config(signature_version="s3v4", s3={"addressing_style": "virtual"}),
    )
    return client.generate_presigned_url(
        "get_object",
        Params={"Bucket": bucket, "Key": key},
        ExpiresIn=3600,
    )

# ---- FFmpeg (HTTP input → stdout) ----
def _spawn_ffmpeg_http(in_url: str, length_sec: int = 300) -> subprocess.Popen:
    """
    ВАЖНО: читаем по HTTP(S) — это позволяет ffmpeg делать byte-range seek (нужно для MP4 с moov в конце).
    НИКАких stdin-пайпов для MP4: pipe не seekable → 'moov atom not found'.
    """
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
        # (опционально можно указать seekable=1 для http, но по умолчанию оно 1)

        "-ss", "0",
        "-i", in_url,
        "-t", str(length_sec),

        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",

        # запись в не-seekable stdout → fragmented MP4
        "-movflags", "frag_keyframe+empty_moov",
        "-muxpreload", "0",
        "-muxdelay", "0",
        "-flush_packets", "1",

        "-f", "mp4",
        "pipe:1",
    ]
    return subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, bufsize=0)

def _run_pipeline(self, task_id: str, in_url: str, clip_key: str, mime: str, t0: float) -> tuple[int, int, str]:
    """
    Общая обвязка: FFmpeg HTTP → stdout → S3 upload_fileobj, с прогрессом и двухфазным watchdog.
    Возвращает: (uploaded_bytes, ffmpeg_retcode, stderr_tail)
    """
    proc = _spawn_ffmpeg_http(in_url, length_sec=300)
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

    up_th = Thread(target=_uploader, daemon=True)
    up_th.start()

    try:
        while up_th.is_alive():
            time.sleep(1)

            # фаза 1: ждем первых байт
            if first_byte_ts is None and (time.time() - t0) > START_TIMEOUT:
                try: proc.terminate()
                except Exception: pass
                break

            # фаза 2: после старта — молчание
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
        up_th.join(timeout=15)
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

# ---------------- task ----------------
@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=20 * 60,
    time_limit=25 * 60,
)
def clip_video(self, src_url: str) -> dict:
    """
    Путь данных: (A) direct HTTP из src_url → ffmpeg → S3; при неудаче (B) presigned V4 → ffmpeg → S3.
    Никакого stdin: mp4 с moov-в-конце требует seek → только HTTP с Range.
    """
    t0 = time.time()
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    # 0) HEAD исходника (S3 API — быстро поймать 404/403)
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

    # ===== TRY #A: прямой URL как есть =====
    # Работает для публичных ссылок на twcstorage/cdn.
    try_url = src_url
    uploaded, ret, tail = _run_pipeline(self, task_id, try_url, clip_key, mime, t0)
    if uploaded > 0 and ret == 0:
        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
        return {
            "clip_url": clip_url,
            "length_sec": 300,
            "uploaded_bytes": uploaded,
            "elapsed_sec": int(time.time() - t0),
            "path": "direct",
        }

    # ===== TRY #B: presigned V4 под корректный хост =====
    presigned = _make_presigned_for_host(src_bucket, src_key, _src_host(src_url))
    uploaded2, ret2, tail2 = _run_pipeline(self, task_id, presigned, clip_key, mime, t0)
    if uploaded2 > 0 and ret2 == 0:
        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
        return {
            "clip_url": clip_url,
            "length_sec": 300,
            "uploaded_bytes": uploaded2,
            "elapsed_sec": int(time.time() - t0),
            "path": "presigned",
        }

    # если обе попытки не дали данных — вернём осмысленную ошибку
    if uploaded == 0 and uploaded2 == 0:
        raise RuntimeError(
            "no output produced: "
            f"direct ret={_fmt_ret(ret)} tail:\n{tail}\n\n"
            f"presigned ret={_fmt_ret(ret2)} tail:\n{tail2}"
        )

    raise RuntimeError(
        f"ffmpeg failed after producing {uploaded or uploaded2} bytes; "
        f"direct ret={_fmt_ret(ret)} tail:\n{tail}\n\npresigned ret={_fmt_ret(ret2)} tail:\n{tail2}"
    )
