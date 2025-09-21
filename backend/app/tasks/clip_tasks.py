# app/tasks/clip_tasks.py
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
from typing import Callable, Optional

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

# Таймауты стриминга
START_TIMEOUT       = int(os.getenv("CLIP_START_TIMEOUT", "600"))   # ждать первые байты, сек
NOPROGRESS_TIMEOUT  = int(os.getenv("CLIP_NOPROGRESS_TIMEOUT", "120"))

# Минимальный «разумный» размер клипа (защита от пустых заголовков)
MIN_OK_BYTES        = int(os.getenv("CLIP_MIN_OK_BYTES", str(1_000_000)))  # 1 MB по умолчанию

# Разрешить фолбэк на локальную загрузку/обрезку
ALLOW_DOWNLOAD_FALLBACK = os.getenv("CLIP_ALLOW_DOWNLOAD_FALLBACK", "true").lower() == "true"

# Размер части для multipart (≥ 5MiB)
MIN_PART     = 5 * 1024 * 1024
DEFAULT_PART = max(int(os.getenv("CLIP_PART_SIZE", str(8 * 1024 * 1024))), MIN_PART)

# основной клиент
s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# presigned V4 клиент
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

def _make_presigned(bucket: str, key: str) -> str:
    return s3_v4.generate_presigned_url(
        "get_object", Params={"Bucket": bucket, "Key": key}, ExpiresIn=3600
    )

# ---- ручной multipart upload из pipe (вместо upload_fileobj) ----
def multipart_upload_from_pipe(
    pipe,
    *,
    bucket: str,
    key: str,
    content_type: str = "video/mp4",
    content_disposition: str = "inline",
    part_size: int = DEFAULT_PART,
    progress_cb: Optional[Callable[[int], None]] = None,
) -> int:
    """
    Читает байты из pipe (ffmpeg stdout) и загружает их в S3 через Multipart Upload.
    Возвращает общее число отправленных байт.
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
        finally:
            pass
        raise

# ---- FFmpeg (HTTP input → stdout) ----
def _spawn_ffmpeg_http(in_url: str, length_sec: int = 300) -> subprocess.Popen:
    """
    Вход по HTTP(S) (seekable), выход в fMP4 на stdout (pipe:1)
    """
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-threads", "1",

        # сетевые страховки
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

        # запись в не-seekable stdout → fragmented MP4
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
    FFmpeg HTTP → stdout → S3 (ручной multipart), прогресс и двухфазный watchdog.
    Возвращает (uploaded_bytes, ffmpeg_ret, stderr_tail)
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
            )
        except Exception as e:
            upload_err["exc"] = e

    th = Thread(target=_uploader, daemon=True)
    th.start()

    try:
        while th.is_alive():
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

# ---- локальная загрузка/обрезка (fallback) ----
def _ffmpeg_local_clip(src_path: str, dst_path: str):
    """
    Обрезка 0..300 c без перекодирования, +faststart (moov в начало) — файл на диске.
    """
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-nostdin",
        "-loglevel", "error",
        "-threads", "2",
        "-i", src_path,
        "-t", "300",
        "-c", "copy",
        "-movflags", "+faststart",
        "-y",
        dst_path,
    ]
    completed = subprocess.run(cmd, capture_output=True)
    if completed.returncode != 0:
        raise RuntimeError(f"local ffmpeg failed: {completed.stderr.decode('utf-8', 'ignore')[:2000]}")

# ---------------- task ----------------
@shared_task(
    bind=True,
    track_started=True,
    soft_time_limit=20 * 60,
    time_limit=30 * 60,
)
def clip_video(self, src_url: str) -> dict:
    """
    Попытка A: прямой URL (HTTP) → ffmpeg → S3 (стрим, multipart).
    Попытка B: presigned V4 → ffmpeg → S3 (стрим, multipart).
    Фолбэк C: S3 → локальный файл → ffmpeg (файл) → локальный файл → S3.
    """
    t0 = time.time()
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    # 0) HEAD исходника — быстрый 404/403/размер
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

    # ===== A: прямой URL как есть =====
    uploaded, ret, tail = _run_stream_pipeline(self, task_id, src_url, clip_key, mime, t0)
    if uploaded >= MIN_OK_BYTES and ret == 0:
        clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
        return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded, "elapsed_sec": int(time.time() - t0), "path": "direct"}
    # если байт мало — удалим «пустышку» и пойдём дальше
    if uploaded and uploaded < MIN_OK_BYTES:
        try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
        except Exception: pass

    # ===== B: presigned V4 (пробуем только если ffmpeg реально упал сообщением) =====
    go_presigned = (ret != 0 and bool((tail or "").strip()))
    if go_presigned:
        presigned = _make_presigned(src_bucket, src_key)
        uploaded2, ret2, tail2 = _run_stream_pipeline(self, task_id, presigned, clip_key, mime, t0)
        if uploaded2 >= MIN_OK_BYTES and ret2 == 0:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded2, "elapsed_sec": int(time.time() - t0), "path": "presigned"}
        if uploaded2 and uploaded2 < MIN_OK_BYTES:
            try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception: pass
    else:
        uploaded2, ret2, tail2 = 0, 0, ""

    # ===== C: локальный фолбэк (если разрешён) =====
    if ALLOW_DOWNLOAD_FALLBACK:
        with tempfile.TemporaryDirectory() as tmp:
            src_path  = os.path.join(tmp, "src.bin")
            dst_path  = os.path.join(tmp, "clip.mp4")

            # прогресс загрузки
            downloaded = {"n": 0}
            last_report = {"t": time.time()}

            def _dl_cb(nbytes):
                downloaded["n"] += nbytes
                now = time.time()
                if now - last_report["t"] >= 2:
                    self.update_state(
                        task_id=task_id,
                        state="PROGRESS",
                        meta={
                            "stage": "downloading",
                            "downloaded_bytes": downloaded["n"],
                            "source_bytes": size,
                            "elapsed_sec": int(now - t0),
                        },
                    )
                    last_report["t"] = now

            # скачиваем целиком (S3 → файл)
            s3.download_file(src_bucket, src_key, src_path, Callback=_dl_cb, Config=TRANSFER_CFG)

            # локальная обрезка без перекодирования + faststart в файл
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "local_cut"})
            _ffmpeg_local_clip(src_path, dst_path)

            # аплоад результата (из файла)
            self.update_state(task_id=task_id, state="PROGRESS", meta={"stage": "uploading_result"})
            s3.upload_file(
                dst_path,
                S3_BUCKET,
                clip_key,
                ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
                Config=TRANSFER_CFG,
            )
            uploaded3 = os.path.getsize(dst_path)

        if uploaded3 >= MIN_OK_BYTES:
            clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
            return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded3, "elapsed_sec": int(time.time() - t0), "path": "download"}
        else:
            try: s3.delete_object(Bucket=S3_BUCKET, Key=clip_key)
            except Exception: pass
            raise RuntimeError(f"clip too small after local fallback: {uploaded3} bytes (< {MIN_OK_BYTES})")

    # Если дошли сюда — стрим не пошёл, фолбэк выключен
    raise RuntimeError(
        "no output produced:\n"
        f"direct ret={_fmt_ret(ret)} tail:\n{tail}\n\n"
        f"presigned ret={_fmt_ret(locals().get('ret2', 0))} tail:\n{locals().get('tail2','')}\n\n"
        "download fallback disabled (set CLIP_ALLOW_DOWNLOAD_FALLBACK=true to enable)."
    )
