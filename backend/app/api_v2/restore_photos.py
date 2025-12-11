"""
API endpoint для восстановления фотографий из веб-архива.

Использование:
POST /api/restore-photos
Body: {"photos": ["https://dent-s.com/assets/img/preview_img/photo1.png", ...]}

Требует роль admin.
"""

from io import BytesIO
from typing import List, Dict, Any

import requests
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..db.database import get_db
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Landing, Author
from .media import upload_image

router = APIRouter()

# URL веб-архива
WAYBACK_TIMESTAMP = "20250809140805if_"


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
    """Скачивает фотографию из веб-архива."""
    wayback_url = f"https://web.archive.org/web/{WAYBACK_TIMESTAMP}/{original_url}"
    
    response = requests.get(wayback_url, timeout=30)
    response.raise_for_status()
    
    return response.content


async def _process_single_photo(db: Session, photo_url: str, current_user) -> Dict[str, Any]:
    """
    Обрабатывает одну фотографию.
    
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
        
        # 4. Создаем UploadFile объект
        upload_file = UploadFile(
            file=BytesIO(image_bytes),
            filename=filename,
            headers={'content-type': content_type}
        )
        
        # 5. Загружаем через существующий роут upload_image
        try:
            upload_result = await upload_image(
                entity_type=entity_type,
                entity_id=entity_id,
                file=upload_file,
                db=db,
                current_user=current_user
            )
            
            result["status"] = "success"
            result["new_url"] = upload_result.get("url")
            result["message"] = f"Успешно загружено через upload_image"
            
        except HTTPException as e:
            result["status"] = "upload_error"
            result["message"] = f"Ошибка загрузки: {e.detail}"
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
    3. Загружает через существующий роут /upload-image
    4. Автоматически обновляет ссылку в БД
    
    Требует роль admin.
    """,
)
async def restore_photos_from_archive(
    request: RestorePhotosRequest,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("admin")),
):
    """Восстанавливает фотографии из веб-архива."""
    
    results = []
    stats = {
        "total": len(request.photos),
        "success": 0,
        "not_found": 0,
        "errors": 0,
    }
    
    # Обрабатываем каждую фотографию
    for photo_url in request.photos:
        result = await _process_single_photo(db, photo_url, current_user)
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
