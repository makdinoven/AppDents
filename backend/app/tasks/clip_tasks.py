# app/tasks/clip_tasks.py
import mimetypes
import os
import subprocess
import time
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse, quote

import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
from boto3.s3.transfer import TransferConfig

from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded

# ---------------- S3 / ENV ----------------
S3_BUCKET      = os.getenv("S3_BUCKET", "604b5d90-c6193c9d-2b0b-4d55-83e9-d8732c532254")
S3_ENDPOINT    = os.getenv("S3_ENDPOINT", "https://s3.timeweb.com")
S3_REGION      = os.getenv("S3_REGION", "ru-1")
S3_PUBLIC_HOST = os.getenv("S3_PUBLIC_HOST", "https://cdn.dent-s.com")

s3 = boto3.client(
    "s3",
    endpoint_url=S3_ENDPOINT,
    region_name=S3_REGION,
    aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
    aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY"),
    config=Config(signature_version="s3", s3={"addressing_style": "path"}),
)

# Умеренный параллелизм multipart-аплоада (не душит CPU/сеть)
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
    # S3 ждёт декодированный ключ
    return unquote(urlparse(url).path.lstrip("/"))

def _unique_clip_name(original_key: str) -> str:
    p = Path(original_key)
    return str(p.parent / "narezki" / f"{p.stem}_clip_{uuid.uuid4().hex}{p.suffix or '.mp4'}")

def _encode_for_url(key: str) -> str:
    # для ответа оставляем %-кодировку, '/' не трогаем
    return quote(key, safe="/")

def _run_ffmpeg_stream(in_url: str, out_pipe, length: int = 300) -> subprocess.Popen:
    """
    Стримим фрагментированный MP4 в stdout.
    Важно: -movflags frag_keyframe+empty_moov позволяет писать в не-seekable pipe.
    """
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-loglevel", "error",
        "-threads", "1",

        # сетевые опции, чтобы не висеть молча на HTTP-вводе
        "-rw_timeout", "30000000",          # 30s, микросекунды
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_delay_max", "3",

        "-ss", "0",
        "-i", in_url,
        "-t", str(length),

        "-c", "copy",
        "-bsf:a", "aac_adtstoasc",
        "-movflags", "frag_keyframe+empty_moov",
        "-f", "mp4",
        "pipe:1",
    ]
    return subprocess.Popen(cmd, stdout=out_pipe, stderr=subprocess.PIPE)

# ---------------- task ----------------
@shared_task(
    bind=True,
    track_started=True,
    # подберите под вашу инфраструктуру (в секундах)
    soft_time_limit=20 * 60,   # мягкий предел — даёт шанс прибрать за собой
    time_limit=25 * 60,        # жёсткий предел от Celery
)
def clip_video(self, src_url: str) -> dict:
    """
    Фоновая обрезка 5 минут: S3 presigned (HTTPS) → ffmpeg (stdout) → S3 upload_fileobj.
    Возвращает: {"clip_url": ..., "length_sec": 300, "uploaded_bytes": ..., "elapsed_sec": ...}
    """
    t0 = time.time()

    # сохраняем task_id, чтобы update_state работать из любых потоков/колбэков
    task_id = getattr(self.request, "id", None) or getattr(self.request, "root_id", None)
    if not task_id:
        raise RuntimeError("No Celery task_id in context")

    # 0) HEAD исходника — быстро ловим 404/403/ошибки доступа
    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "preparing"})
    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)
    try:
        head = s3.head_object(Bucket=src_bucket, Key=src_key)
    except ClientError as e:
        raise RuntimeError(f"source head failed: {e}")
    size = head.get("ContentLength", 0)
    self.update_state(task_id=task_id, state="STARTED", meta={"stage": "source_ok", "source_bytes": size})

    # 1) presigned на чтение
    presigned = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": src_bucket, "Key": src_key},
        ExpiresIn=3600,
    )

    # 2) запуск ffmpeg → stdout
    clip_key = _unique_clip_name(src_key)
    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
    proc = _run_ffmpeg_stream(presigned, subprocess.PIPE)

    uploaded = 0
    last_report = t0

    def _progress_cb(nbytes: int):
        nonlocal uploaded, last_report
        uploaded += nbytes
        now = time.time()
        if now - last_report >= 2:  # репортим раз в ~2 секунды
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
            last_report = now

    # 3) потоковый аплоад в S3
    try:
        s3.upload_fileobj(
            proc.stdout,
            S3_BUCKET,
            clip_key,
            ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
            Config=TRANSFER_CFG,
            Callback=_progress_cb,
        )
    except SoftTimeLimitExceeded:
        # мягкий тайм-аут: корректно завершаем ffmpeg
        try:
            proc.terminate()
        finally:
            try:
                proc.wait(timeout=5)
            except Exception:
                pass
        raise
    finally:
        # собираем stderr для диагностики
        try:
            if proc.stdout:
                proc.stdout.close()
        except Exception:
            pass
        try:
            stderr = proc.stderr.read().decode("utf-8", errors="ignore") if proc.stderr else ""
        except Exception:
            stderr = ""
        try:
            ret = proc.wait()
        except Exception:
            ret = 0
        if ret != 0:
            # обрежем stderr, чтобы не взорвать лог
            raise RuntimeError(f"ffmpeg exited with {ret}; stderr: {stderr[:2000]}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
    return {
        "clip_url": clip_url,
        "length_sec": 300,
        "uploaded_bytes": uploaded,
        "elapsed_sec": int(time.time() - t0),
    }
