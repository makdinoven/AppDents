import logging
import hashlib
import datetime as _dt
import requests
import redis
from sqlalchemy.orm import Session

from ..models.models_v2 import LessonPreview, PreviewStatus
from ..tasks.preview_tasks import generate_preview, check_preview_url

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

def get_or_schedule_preview(db: Session, video_link: str, skip_url_check: bool = False) -> str:
    """
    Получить превью для одного видео.
    
    Args:
        db: Сессия БД
        video_link: Ссылка на видео
        skip_url_check: Если True — пропустить HTTP HEAD проверку URL (для быстрых ответов)
    """
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

    # SUCCESS — отдаём, но иногда проверяем (если не skip_url_check)
    if row.status == PreviewStatus.SUCCESS:
        if not skip_url_check and (row.checked_at is None or (now - row.checked_at) > CHECK_TTL):
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


def _schedule_url_check(video_link: str) -> None:
    """Ставит задачу проверки URL в Celery (идемпотентно через Redis)."""
    check_key = _key("preview:checking", video_link)
    # Не ставим задачу, если уже проверяется (TTL 10 минут)
    if rds.set(check_key, b"1", nx=True, ex=600):
        task_id = f"check_{hashlib.sha1(video_link.encode()).hexdigest()}"
        check_preview_url.apply_async((video_link,), task_id=task_id, queue="default")


def get_previews_batch(db: Session, video_links: list[str]) -> dict[str, str]:
    """
    Получить превью для нескольких видео одним батч-запросом.
    Возвращает данные из БД максимально быстро (без блокирующих HTTP проверок).
    
    Для новых видео ставит задачи на генерацию превью.
    Для устаревших SUCCESS превью ставит фоновую задачу проверки URL.
    
    Returns:
        dict: {video_link: preview_url}
    """
    if not video_links:
        return {}
    
    # Убираем дубликаты и None
    unique_links = list({link for link in video_links if link})
    if not unique_links:
        return {}
    
    now = _dt.datetime.utcnow()
    result: dict[str, str] = {}
    urls_to_check: list[str] = []  # URL для фоновой проверки
    
    # 1. Получаем все существующие превью одним запросом
    existing_rows = (
        db.query(LessonPreview)
        .filter(LessonPreview.video_link.in_(unique_links))
        .all()
    )
    
    existing_map = {row.video_link: row for row in existing_rows}
    
    # 2. Обрабатываем существующие записи
    for link, row in existing_map.items():
        if row.status == PreviewStatus.SUCCESS:
            result[link] = row.preview_url
            # Проверяем, нужно ли валидировать URL (если давно не проверяли)
            if row.checked_at is None or (now - row.checked_at) > CHECK_TTL:
                urls_to_check.append(link)
        elif row.status in (PreviewStatus.PENDING, PreviewStatus.RUNNING):
            result[link] = row.preview_url or PLACEHOLDER_URL
        elif row.status == PreviewStatus.FAILED:
            # Ставим задачу если backoff истёк
            wait = _backoff(int(row.attempts or 0))
            if (row.updated_at is None) or (now - row.updated_at >= wait):
                _enqueue_if_needed(row, link)
            result[link] = PLACEHOLDER_URL
        else:
            result[link] = row.preview_url or PLACEHOLDER_URL
    
    # 3. Создаём записи для новых видео
    new_links = [link for link in unique_links if link not in existing_map]
    
    for link in new_links:
        row = LessonPreview(
            video_link=link,
            preview_url=PLACEHOLDER_URL,
            status=PreviewStatus.PENDING,
            enqueued_at=now,
            updated_at=now,
            attempts=0,
        )
        db.add(row)
        result[link] = PLACEHOLDER_URL
    
    if new_links:
        db.commit()
        # Ставим задачи на генерацию
        for link in new_links:
            row = db.query(LessonPreview).filter_by(video_link=link).first()
            if row:
                _enqueue_if_needed(row, link)
        db.commit()
    
    # 4. Ставим фоновые задачи на проверку устаревших URL (не блокирует ответ)
    for link in urls_to_check:
        try:
            _schedule_url_check(link)
        except Exception:
            logger.warning("Failed to schedule URL check for %s", link)
    
    return result
