"""
API endpoint для восстановления фотографий из веб-архива.

Использование:
POST /api/restore-photos
Body: {"photos": ["https://dent-s.com/assets/img/preview_img/photo1.png", ...]}

Требует роль admin.
"""

import os
import time
import logging
import uuid
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
import requests
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db, DATABASE_URL
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Landing, Author

# Настройка логгера
logger = logging.getLogger(__name__)

router = APIRouter()

# Хранилище для отслеживания прогресса задач (в продакшене использовать Redis)
tasks_progress: Dict[str, Dict] = {}

# URL веб-архива
WAYBACK_TIMESTAMP = "20250809140805if_"

# Настройки retry для скачивания
MAX_RETRIES = 5
RETRY_DELAY_SECONDS = 2  # начальная задержка
RETRY_BACKOFF_MULTIPLIER = 1.5  # множитель для экспоненциальной задержки


# ─────────────── Pydantic Models ───────────────

class RestorePhotosRequest(BaseModel):
    """Запрос на восстановление фотографий."""
    photos: List[str]  # Список URL фотографий


class PhotoResult(BaseModel):
    """Результат обработки одной фотографии."""
    original_url: str
    status: str  # success, skipped, already_updated, not_found, download_error, upload_error
    message: str
    entity_type: str = None  # landing_preview или author_preview
    entity_id: int = None
    new_url: str = None


class RestorePhotosResponse(BaseModel):
    """Ответ с результатами восстановления."""
    total: int
    success: int
    skipped: int
    not_found: int
    errors: int
    results: List[PhotoResult]


class StartTaskResponse(BaseModel):
    """Ответ при запуске фоновой задачи."""
    task_id: str
    message: str
    total_photos: int
    check_status_url: str


class TaskProgressResponse(BaseModel):
    """Ответ с прогрессом выполнения задачи."""
    task_id: str
    status: str  # pending, processing, completed, failed
    total: int
    processed: int
    success: int
    skipped: int
    not_found: int
    errors: int
    progress_percent: float
    started_at: Optional[str] = None
    completed_at: Optional[str] = None
    results: List[PhotoResult] = []


# ─────────────── Вспомогательные функции ───────────────

def _find_entity_in_db(db: Session, photo_url: str) -> tuple:
    """
    Ищет фотографию в БД по полной ссылке.
    
    Returns:
        (entity_type, entity_id, entity_object) или (None, None, None)
    """
    # Ищем в лендингах
    landing = db.query(Landing).filter(Landing.preview_photo == photo_url).first()
    if landing:
        return ("landing_preview", landing.id, landing)
    
    # Ищем в авторах
    author = db.query(Author).filter(Author.photo == photo_url).first()
    if author:
        return ("author_preview", author.id, author)
    
    return (None, None, None)


def _download_from_wayback(original_url: str) -> bytes:
    """
    Скачивает фотографию из веб-архива с retry логикой.
    
    Делает до MAX_RETRIES попыток с экспоненциальной задержкой между попытками.
    """
    wayback_url = f"https://web.archive.org/web/{WAYBACK_TIMESTAMP}/{original_url}"
    
    last_exception = None
    delay = RETRY_DELAY_SECONDS
    
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            response = requests.get(
                wayback_url, 
                timeout=30,
                headers={
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            )
            response.raise_for_status()
            
            # Логируем успешное скачивание
            if attempt > 1:
                logger.info(f"[Retry] Успешно скачано после {attempt} попыток: {original_url}")
            
            return response.content
            
        except (
            requests.exceptions.ConnectionError,
            requests.exceptions.Timeout,
            requests.exceptions.RequestException
        ) as e:
            last_exception = e
            
            if attempt < MAX_RETRIES:
                # Логируем попытку
                logger.warning(
                    f"[Retry {attempt}/{MAX_RETRIES}] Ошибка скачивания из web.archive.org: {str(e)[:100]}"
                )
                logger.info(f"[Retry] Ожидание {delay:.1f} секунд перед следующей попыткой...")
                
                # Ждем перед следующей попыткой
                time.sleep(delay)
                
                # Увеличиваем задержку для следующей попытки (экспоненциальная задержка)
                delay *= RETRY_BACKOFF_MULTIPLIER
            else:
                # Последняя попытка не удалась
                logger.error(
                    f"[Retry] Все {MAX_RETRIES} попыток исчерпаны для {original_url}. "
                    f"Последняя ошибка: {str(last_exception)}"
                )
    
    # Если все попытки не удались, выбрасываем последнее исключение
    raise last_exception


async def _background_restore_task(
    task_id: str,
    photos: List[str],
    api_base_url: str,
    auth_token: str,
    db_connection_string: str
):
    """Фоновая задача для восстановления фотографий."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Создаем новую сессию БД для фоновой задачи
    engine = create_engine(db_connection_string)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        tasks_progress[task_id]["status"] = "processing"
        tasks_progress[task_id]["started_at"] = datetime.utcnow().isoformat()
        
        for idx, photo_url in enumerate(photos, 1):
            result = await _process_single_photo(
                db=db,
                photo_url=photo_url,
                api_base_url=api_base_url,
                auth_token=auth_token
            )
            
            # Обновляем прогресс
            tasks_progress[task_id]["processed"] = idx
            tasks_progress[task_id]["results"].append(PhotoResult(**result))
            tasks_progress[task_id]["progress_percent"] = (idx / len(photos)) * 100
            
            if result["status"] == "success":
                tasks_progress[task_id]["success"] += 1
            elif result["status"] in ("skipped", "already_updated"):
                tasks_progress[task_id]["skipped"] += 1
            elif result["status"] == "not_found":
                tasks_progress[task_id]["not_found"] += 1
            else:
                tasks_progress[task_id]["errors"] += 1
            
            logger.info(f"[Task {task_id}] Обработано {idx}/{len(photos)} фотографий")
        
        # Завершаем задачу
        tasks_progress[task_id]["status"] = "completed"
        tasks_progress[task_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[Task {task_id}] Задача завершена успешно")
        
    except Exception as e:
        tasks_progress[task_id]["status"] = "failed"
        tasks_progress[task_id]["error"] = str(e)
        logger.error(f"[Task {task_id}] Ошибка выполнения задачи: {str(e)}")
    finally:
        db.close()


async def _process_single_photo(
    db: Session, 
    photo_url: str, 
    api_base_url: str,
    auth_token: str
) -> Dict[str, Any]:
    """
    Обрабатывает одну фотографию.
    
    Args:
        db: Сессия БД
        photo_url: URL фотографии для восстановления
        api_base_url: Базовый URL API (например, http://localhost:8000)
        auth_token: JWT токен для авторизации
    
    Returns:
        dict с результатом обработки
    """
    result = {
        "original_url": photo_url,
        "status": "unknown",
        "message": "",
        "entity_type": None,
        "entity_id": None,
        "new_url": None,
    }
    
    try:
        # 1. Поиск в БД
        entity_type, entity_id, entity_obj = _find_entity_in_db(db, photo_url)
        if not entity_type:
            result["status"] = "skipped"
            result["message"] = "Фотография не найдена в БД - пропущена"
            return result
        
        result["entity_type"] = entity_type
        result["entity_id"] = entity_id
        
        # 2. Проверяем, не обновлена ли уже фотография
        # Если URL уже не содержит dent-s.com, значит уже загружена в CDN
        current_photo_url = None
        if entity_type == "landing_preview":
            current_photo_url = entity_obj.preview_photo
        elif entity_type == "author_preview":
            current_photo_url = entity_obj.photo
        
        if current_photo_url and "dent-s.com" not in current_photo_url:
            result["status"] = "already_updated"
            result["message"] = f"Фотография уже обновлена (текущий URL: {current_photo_url}) - пропущена"
            result["new_url"] = current_photo_url
            return result
        
        # 2. Скачивание из веб-архива
        try:
            image_bytes = _download_from_wayback(photo_url)
        except Exception as e:
            result["status"] = "download_error"
            result["message"] = f"Ошибка скачивания: {str(e)}"
            return result
        
        # 3. Определяем тип файла по расширению URL
        file_extension = photo_url.split('.')[-1].lower()
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif',
        }
        content_type = content_type_map.get(file_extension, 'image/jpeg')
        filename = photo_url.split('/')[-1]
        
        # 4. Загружаем через HTTP запрос к роуту /api/media/upload-image
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                # Готовим multipart/form-data запрос
                files = {
                    'file': (filename, image_bytes, content_type)
                }
                data = {
                    'entity_type': entity_type,
                    'entity_id': entity_id,
                }
                headers = {
                    'Authorization': f'Bearer {auth_token}'
                }
                
                upload_url = f"{api_base_url}/api/media/upload-image"
                response = await client.post(
                    upload_url,
                    files=files,
                    data=data,
                    headers=headers
                )
                
                if response.status_code == 201:
                    upload_result = response.json()
                    result["status"] = "success"
                    result["new_url"] = upload_result.get("url")
                    result["message"] = f"Успешно загружено через HTTP API"
                else:
                    result["status"] = "upload_error"
                    result["message"] = f"Ошибка загрузки: HTTP {response.status_code} - {response.text}"
                    return result
            
        except httpx.RequestError as e:
            result["status"] = "upload_error"
            result["message"] = f"Ошибка HTTP запроса: {str(e)}"
            return result
        except Exception as e:
            result["status"] = "upload_error"
            result["message"] = f"Ошибка загрузки: {str(e)}"
            return result
        
    except Exception as e:
        result["status"] = "unexpected_error"
        result["message"] = f"Неожиданная ошибка: {str(e)}"
    
    return result


# ─────────────── API Endpoint ───────────────

@router.post(
    "/restore-photos",
    response_model=StartTaskResponse,
    summary="Запуск восстановления фотографий из веб-архива (async)",
    description="""
    Запускает фоновую задачу восстановления фотографий из веб-архива.
    
    Возвращает task_id для отслеживания прогресса через GET /restore-photos/status/{task_id}
    
    Для каждой фотографии:
    1. Ищет в БД (landings.preview_photo и authors.photo)
    2. Скачивает из веб-архива (с retry логикой)
    3. Загружает через HTTP запрос к роуту /api/media/upload-image
    4. Автоматически обновляет ссылку в БД
    
    Требует роль admin.
    """,
)
async def restore_photos_from_archive(
    photos_request: RestorePhotosRequest,
    fastapi_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("admin")),
):
    """Запускает фоновую задачу восстановления фотографий из веб-архива."""
    
    # Получаем токен авторизации из заголовков
    auth_header = fastapi_request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Отсутствует или некорректный токен авторизации")
    
    auth_token = auth_header.replace("Bearer ", "")
    
    # Базовый URL API
    api_base_url = "https://dent-s.com"
    
    # Создаем уникальный ID задачи
    task_id = str(uuid.uuid4())
    
    # Инициализируем прогресс задачи
    tasks_progress[task_id] = {
        "status": "pending",
        "total": len(photos_request.photos),
        "processed": 0,
        "success": 0,
        "skipped": 0,
        "not_found": 0,
        "errors": 0,
        "progress_percent": 0.0,
        "results": [],
        "started_at": None,
        "completed_at": None,
    }
    
    # Запускаем фоновую задачу
    background_tasks.add_task(
        _background_restore_task,
        task_id=task_id,
        photos=photos_request.photos,
        api_base_url=api_base_url,
        auth_token=auth_token,
        db_connection_string=DATABASE_URL
    )
    
    logger.info(f"[Task {task_id}] Запущена задача восстановления {len(photos_request.photos)} фотографий")
    
    return StartTaskResponse(
        task_id=task_id,
        message="Задача запущена. Используйте task_id для отслеживания прогресса.",
        total_photos=len(photos_request.photos),
        check_status_url=f"/api/restore-photos/status/{task_id}"
    )


@router.get(
    "/restore-photos/status/{task_id}",
    response_model=TaskProgressResponse,
    summary="Проверка статуса задачи восстановления",
    description="""
    Возвращает текущий прогресс выполнения задачи восстановления фотографий.
    
    Статусы:
    - pending: Задача в очереди
    - processing: Задача выполняется
    - completed: Задача завершена успешно
    - failed: Задача завершена с ошибкой
    """,
)
async def get_restore_task_status(
    task_id: str,
    current_user = Depends(require_roles("admin")),
):
    """Возвращает статус выполнения задачи восстановления."""
    
    if task_id not in tasks_progress:
        raise HTTPException(404, f"Задача с ID {task_id} не найдена")
    
    task = tasks_progress[task_id]
    
    return TaskProgressResponse(
        task_id=task_id,
        status=task["status"],
        total=task["total"],
        processed=task["processed"],
        success=task["success"],
        skipped=task["skipped"],
        not_found=task["not_found"],
        errors=task["errors"],
        progress_percent=task["progress_percent"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        results=task["results"],
    )


@router.get(
    "/restore-photos/tasks",
    response_model=List[TaskProgressResponse],
    summary="Список всех задач восстановления",
    description="Возвращает список всех задач восстановления фотографий (активных и завершенных).",
)
async def list_restore_tasks(
    current_user = Depends(require_roles("admin")),
):
    """Возвращает список всех задач восстановления."""
    
    tasks = []
    for task_id, task in tasks_progress.items():
        tasks.append(TaskProgressResponse(
            task_id=task_id,
            status=task["status"],
            total=task["total"],
            processed=task["processed"],
            success=task["success"],
            skipped=task["skipped"],
            not_found=task["not_found"],
            errors=task["errors"],
            progress_percent=task["progress_percent"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at"),
            results=task["results"],
        ))
    
    return tasks
