# app/tasks/clip_tasks.py
import mimetypes
import os
import subprocess
import uuid
from pathlib import Path
from urllib.parse import unquote, urlparse, quote

import boto3
from boto3.s3.transfer import TransferConfig
from botocore.config import Config
from celery import shared_task
from celery.exceptions import SoftTimeLimitExceeded
import time

# --- S3/ENV ---
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

TRANSFER_CFG = TransferConfig(
    multipart_threshold=8 * 1024 * 1024,
    multipart_chunksize=8 * 1024 * 1024,
    max_concurrency=2,          # не душим сеть/ЦП
    use_threads=True,
)

def _run_ffmpeg_stream(in_url: str, out_pipe, length: int = 300):
    # HTTP-реконнекты + таймауты чтения, безопасный вывод (fMP4) и ADTS→ASC
    cmd = [
        "nice", "-n", "10",
        "ffmpeg",
        "-loglevel", "error",
        "-threads", "1",
        # сетевые опции (часть может быть проигнорирована старым билдом ffmpeg, но не вредит)
        "-rw_timeout", "30000000",                 # 30s на I/O (в микросекундах)
        "-reconnect", "1",
        "-reconnect_streamed", "1",
        "-reconnect_on_network_error", "1",

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

@shared_task(
    bind=True,
    track_started=True,
    # тайм-лимиты: подберите под ваши реалии
    soft_time_limit=20 * 60,   # 20 минут — мягкий предел
    time_limit=25 * 60,        # 25 минут — жёсткий килл от Celery
)
def clip_video(self, src_url: str) -> dict:
    start_ts = time.time()
    self.update_state(state="STARTED", meta={"msg": "preparing"})

    src_bucket = _bucket_from_url(src_url)
    src_key    = _key_from_url(src_url)
    clip_key   = _unique_clip_name(src_key)

    presigned = s3.generate_presigned_url(
        "get_object",
        Params={"Bucket": src_bucket, "Key": src_key},
        ExpiresIn=3600,
    )

    mime = mimetypes.guess_type(clip_key)[0] or "video/mp4"
    proc = _run_ffmpeg_stream(presigned, subprocess.PIPE)

    uploaded = 0
    last_report = start_ts

    def _cb(chunk: int):
        nonlocal uploaded, last_report
        uploaded += chunk
        now = time.time()
        # отдаём прогресс раз в ~2 сек
        if now - last_report >= 2:
            speed = uploaded / max(1.0, now - start_ts)  # bytes/s
            self.update_state(
                state="PROGRESS",
                meta={
                    "uploaded_bytes": uploaded,
                    "elapsed_sec": int(now - start_ts),
                    "speed_bytes_per_sec": int(speed),
                },
            )
            last_report = now

    try:
        # потоковый аплоад из stdout ffmpeg
        s3.upload_fileobj(
            proc.stdout,
            S3_BUCKET,
            clip_key,
            ExtraArgs={"ContentType": mime, "ContentDisposition": "inline"},
            Config=TRANSFER_CFG,
            Callback=_cb,   # ← прогресс
        )
    except SoftTimeLimitExceeded:
        # мягкий тайм-аут: аккуратно прибиваем ffmpeg, чтобы не остался зомби
        try:
            proc.terminate()
        except Exception:
            pass
        finally:
            proc.wait(timeout=5)
        raise
    finally:
        try:
            proc.stdout.close()
        except Exception:
            pass
        # прочтём stderr — если ошибка, будет понятнее почему
        try:
            stderr = proc.stderr.read().decode("utf-8", errors="ignore")
        except Exception:
            stderr = ""
        ret = proc.wait()
        if ret != 0:
            # положим stderr в исключение — удобно дебажить прямо из статуса
            raise RuntimeError(f"ffmpeg exited with {ret}; stderr: {stderr[:3000]}")

    clip_url = f"{S3_PUBLIC_HOST}/{_encode_for_url(clip_key)}"
    return {"clip_url": clip_url, "length_sec": 300, "uploaded_bytes": uploaded}
