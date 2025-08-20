import logging
import hashlib
import datetime as _dt
import requests
import redis
from sqlalchemy.orm import Session

from ..models.models_v2 import LessonPreview, PreviewStatus
from ..tasks.preview_tasks import generate_preview

logger = logging.getLogger(__name__)

PLACEHOLDER_URL = "https://cdn.dent-s.com/previews/placeholder.jpg"
CHECK_TTL = _dt.timedelta(hours=6)
HEAD_TIMEOUT = 4

REDIS_URL = "redis://redis:6379/0"
rds = redis.Redis.from_url(REDIS_URL, decode_responses=False)

LOCK_TTL = 15 * 60
QUEUED_TTL = 45 * 60

def _is_url_alive(url: str) -> bool:
    try:
        r = requests.head(url, timeout=HEAD_TIMEOUT, allow_redirects=True)
        return r.status_code == 200
    except requests.RequestException:
        return False

def _key(prefix: str, video_link: str) -> str:
    h = hashlib.sha1(video_link.encode()).hexdigest()
    return f"{prefix}:{h}"

def try_mark_queued(video_link: str) -> bool:
    """Ставит флаг 'этот video_link уже поставлен в очередь'."""
    k = _key("preview:queued", video_link)
    ok = rds.set(k, b"1", nx=True, ex=QUEUED_TTL)
    return bool(ok)

def clear_queued(video_link: str) -> None:
    rds.delete(_key("preview:queued", video_link))

def _task_id(video_link: str) -> str:
    return hashlib.sha1(video_link.encode()).hexdigest()

def _backoff(attempts: int) -> _dt.timedelta:
    # 0→немедленно, 1→15m, 2→60m, 3+→6h
    if attempts <= 0:
        return _dt.timedelta(seconds=0)
    if attempts == 1:
        return _dt.timedelta(minutes=15)
    if attempts == 2:
        return _dt.timedelta(hours=1)
    return _dt.timedelta(hours=6)

def _enqueue_if_needed(row: LessonPreview, video_link: str) -> None:
    """Идемпотентная постановка задачи (по флагу в Redis)."""
    if try_mark_queued(video_link):
        row.status = PreviewStatus.PENDING
        row.enqueued_at = _dt.datetime.utcnow()
        row.updated_at = row.enqueued_at
        logger.info("[preview] enqueue generate_preview %s", video_link)
        generate_preview.apply_async((video_link,), task_id=_task_id(video_link), queue="default")

def get_or_schedule_preview(db: Session, video_link: str) -> str:
    now = _dt.datetime.utcnow()
    row = db.query(LessonPreview).filter_by(video_link=video_link).first()

    if not row:
        row = LessonPreview(
            video_link=video_link,
            preview_url=PLACEHOLDER_URL,
            status=PreviewStatus.PENDING,
            enqueued_at=now,
            updated_at=now,
            attempts=0,
        )
        db.add(row)
        db.commit()
        _enqueue_if_needed(row, video_link)
        db.commit()
        return PLACEHOLDER_URL

    # SUCCESS — отдаём, но иногда проверяем
    if row.status == PreviewStatus.SUCCESS:
        if row.checked_at is None or (now - row.checked_at) > CHECK_TTL:
            row.checked_at = now
            db.commit()
            if not _is_url_alive(row.preview_url):
                logger.warning("[preview] dead url %s → reschedule", row.preview_url)
                row.status = PreviewStatus.FAILED
                row.updated_at = now
                db.commit()
                _enqueue_if_needed(row, video_link)
                db.commit()
                return PLACEHOLDER_URL
        return row.preview_url

    # RUNNING или PENDING — просто возвращаем текущее (обычно плейсхолдер)
    if row.status in (PreviewStatus.PENDING, PreviewStatus.RUNNING):
        return row.preview_url or PLACEHOLDER_URL

    # FAILED — применяем backoff
    if row.status == PreviewStatus.FAILED:
        wait = _backoff(int(row.attempts or 0))
        if (row.updated_at is None) or (now - row.updated_at >= wait):
            _enqueue_if_needed(row, video_link)
            db.commit()
        return PLACEHOLDER_URL

    # Защитный fallback
    return row.preview_url or PLACEHOLDER_URL
