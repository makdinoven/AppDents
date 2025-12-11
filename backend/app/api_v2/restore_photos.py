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
from io import BytesIO
from typing import List, Dict, Any

import httpx
import requests
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Landing, Author

# Настройка логгера
logger = logging.getLogger(__name__)

router = APIRouter()

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
    status: str  # success, not_found, download_error, upload_error
    message: str
    entity_type: str = None  # landing_preview или author_preview
    entity_id: int = None
    new_url: str = None


class RestorePhotosResponse(BaseModel):
    """Ответ с результатами восстановления."""
    total: int
    success: int
    not_found: int
    errors: int
    results: List[PhotoResult]


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
            result["status"] = "not_found"
            result["message"] = "Фотография не найдена в БД"
            return result
        
        result["entity_type"] = entity_type
        result["entity_id"] = entity_id
        
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
        
        # 4. Загружаем через HTTP запрос к роуту /upload-image
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
                
                upload_url = f"{api_base_url}/api/upload-image"
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
    response_model=RestorePhotosResponse,
    summary="Восстановление фотографий из веб-архива",
    description="""
    Восстанавливает фотографии из веб-архива и обновляет ссылки в БД.
    
    Для каждой фотографии:
    1. Ищет в БД (landings.preview_photo и authors.photo)
    2. Скачивает из веб-архива
    3. Загружает через HTTP запрос к роуту /upload-image
    4. Автоматически обновляет ссылку в БД
    
    Требует роль admin.
    """,
)
async def restore_photos_from_archive(
    photos_request: RestorePhotosRequest,
    fastapi_request: Request,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("admin")),
):
    """Восстанавливает фотографии из веб-архива через HTTP запросы к API."""
    
    # Получаем токен авторизации из заголовков
    auth_header = fastapi_request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Отсутствует или некорректный токен авторизации")
    
    auth_token = auth_header.replace("Bearer ", "")
    
    # Получаем базовый URL API из переменных окружения или используем localhost
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    
    results = []
    stats = {
        "total": len(photos_request.photos),
        "success": 0,
        "not_found": 0,
        "errors": 0,
    }
    
    # Обрабатываем каждую фотографию
    for photo_url in photos_request.photos:
        result = await _process_single_photo(
            db=db,
            photo_url=photo_url,
            api_base_url=api_base_url,
            auth_token=auth_token
        )
        results.append(PhotoResult(**result))
        
        if result["status"] == "success":
            stats["success"] += 1
        elif result["status"] == "not_found":
            stats["not_found"] += 1
        else:
            stats["errors"] += 1
    
    return RestorePhotosResponse(
        total=stats["total"],
        success=stats["success"],
        not_found=stats["not_found"],
        errors=stats["errors"],
        results=results,
    )
