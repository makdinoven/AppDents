"""
API endpoint для миграции preview-фотографий лендингов из старой системы в S3/CDN.

Использование:
POST /api/migrate-landing-photos
Body: {"dry_run": true, "min_score": 80}

Требует роль admin.
"""

import os
import json
import uuid
import logging
from io import BytesIO
from typing import List, Dict, Any, Optional
from datetime import datetime

import httpx
import requests
from rapidfuzz import fuzz
from fastapi import APIRouter, Depends, HTTPException, Request, BackgroundTasks
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..db.database import get_db, DATABASE_URL
from ..dependencies.role_checker import require_roles
from ..models.models_v2 import Landing

# Настройка логгера
logger = logging.getLogger(__name__)

router = APIRouter()

# Хранилище для отслеживания прогресса задач (в продакшене использовать Redis)
tasks_progress: Dict[str, Dict] = {}

# Путь к дампу
DUMP_FILE_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
    "scripts",
    "swagger_request.json"
)


# ─────────────── Pydantic Models ───────────────

class MigrationRequest(BaseModel):
    """Запрос на миграцию фотографий."""
    dry_run: bool = Field(True, description="Тестовый прогон без реальной загрузки")
    min_score: int = Field(80, ge=0, le=100, description="Минимальный порог fuzzy matching (0-100)")


class MigrationDetail(BaseModel):
    """Детали обработки одной записи."""
    dump_page_name: str
    dump_course_name: str
    dump_photo_preview: Optional[str] = None  # Полная ссылка на фото из дампа
    matched_landing_id: Optional[int] = None
    matched_landing_name: Optional[str] = None
    fuzzy_score: Optional[float] = None
    action: str  # success, skip_cdn_exists, skip_no_photo, skip_low_score, failed
    new_url: Optional[str] = None
    error: Optional[str] = None


class StartTaskResponse(BaseModel):
    """Ответ при запуске фоновой задачи."""
    task_id: str
    message: str
    total_records: int
    check_status_url: str


class TaskProgressResponse(BaseModel):
    """Ответ с прогрессом выполнения задачи."""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: Dict[str, Any]
    stats: Dict[str, int]
    details: List[MigrationDetail] = []
    started_at: Optional[str] = None
    completed_at: Optional[str] = None


# ─────────────── Вспомогательные функции ───────────────

def normalize_text(text: str) -> str:
    """Нормализует текст для fuzzy matching (lowercase, strip)."""
    if not text:
        return ""
    return text.lower().strip()


def fuzzy_match_landing(
    dump_page_name: str,
    dump_course_name: str,
    db_landings: List[Landing],
    min_score: int = 80
) -> tuple:
    """
    Находит наиболее подходящий лендинг через fuzzy matching.
    
    Returns:
        (landing_object, score) или (None, 0) если не найдено
    """
    best_match = None
    best_score = 0
    
    for landing in db_landings:
        # Пробуем exact match по page_name
        if landing.page_name and normalize_text(landing.page_name) == normalize_text(dump_page_name):
            return (landing, 100.0)
        
        # Fuzzy matching по page_name
        page_name_score = 0
        if landing.page_name and dump_page_name:
            page_name_score = fuzz.ratio(
                normalize_text(dump_page_name),
                normalize_text(landing.page_name)
            )
        
        # Fuzzy matching по landing_name (course_name)
        landing_name_score = 0
        if landing.landing_name and dump_course_name:
            landing_name_score = fuzz.ratio(
                normalize_text(dump_course_name),
                normalize_text(landing.landing_name)
            )
        
        # Берем максимальный score
        current_score = max(page_name_score, landing_name_score)
        
        if current_score > best_score:
            best_score = current_score
            best_match = landing
    
    # Возвращаем только если score >= min_score
    if best_score >= min_score:
        return (best_match, best_score)
    
    return (None, 0)


def load_dump_data() -> List[Dict]:
    """Загружает данные из JSON дампа."""
    try:
        with open(DUMP_FILE_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # Дамп это массив с header, database, table
        # Данные находятся в table.data
        for item in data:
            if item.get("type") == "table" and item.get("name") == "landings":
                return item.get("data", [])
        
        logger.error("В дампе не найдена таблица 'landings'")
        return []
    
    except FileNotFoundError:
        logger.error(f"Файл дампа не найден: {DUMP_FILE_PATH}")
        return []
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON дампа: {e}")
        return []
    except Exception as e:
        logger.error(f"Неожиданная ошибка при чтении дампа: {e}")
        return []


async def _background_migration_task(
    task_id: str,
    dry_run: bool,
    min_score: int,
    api_base_url: str,
    auth_token: str,
    db_connection_string: str
):
    """Фоновая задача для миграции фотографий."""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # Создаем новую сессию БД для фоновой задачи
    engine = create_engine(db_connection_string)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()
    
    try:
        tasks_progress[task_id]["status"] = "processing"
        tasks_progress[task_id]["started_at"] = datetime.utcnow().isoformat()
        
        # Загружаем дамп
        dump_records = load_dump_data()
        tasks_progress[task_id]["progress"]["total"] = len(dump_records)
        
        if not dump_records:
            tasks_progress[task_id]["status"] = "failed"
            tasks_progress[task_id]["error"] = "Не удалось загрузить данные из дампа"
            return
        
        # Получаем все лендинги из БД
        db_landings = db.query(Landing).all()
        logger.info(f"[Task {task_id}] Загружено {len(db_landings)} лендингов из БД")
        
        # Обрабатываем каждую запись
        for idx, record in enumerate(dump_records, 1):
            detail = await _process_single_record(
                db=db,
                record=record,
                db_landings=db_landings,
                min_score=min_score,
                dry_run=dry_run,
                api_base_url=api_base_url,
                auth_token=auth_token
            )
            
            # Обновляем прогресс
            tasks_progress[task_id]["progress"]["processed"] = idx
            tasks_progress[task_id]["progress"]["percent"] = round((idx / len(dump_records)) * 100, 2)
            tasks_progress[task_id]["details"].append(detail)
            
            # Обновляем статистику
            action = detail["action"]
            if action == "success":
                tasks_progress[task_id]["stats"]["success"] += 1
            elif action == "skip_cdn_exists":
                tasks_progress[task_id]["stats"]["skip_cdn_exists"] += 1
            elif action == "skip_no_photo":
                tasks_progress[task_id]["stats"]["skip_no_photo"] += 1
            elif action == "skip_low_score":
                tasks_progress[task_id]["stats"]["skip_low_score"] += 1
            else:
                tasks_progress[task_id]["stats"]["failed"] += 1
            
            if idx % 10 == 0:
                logger.info(f"[Task {task_id}] Обработано {idx}/{len(dump_records)}")
        
        # Завершаем задачу
        tasks_progress[task_id]["status"] = "completed"
        tasks_progress[task_id]["completed_at"] = datetime.utcnow().isoformat()
        logger.info(f"[Task {task_id}] Задача завершена успешно")
        
    except Exception as e:
        tasks_progress[task_id]["status"] = "failed"
        tasks_progress[task_id]["error"] = str(e)
        logger.error(f"[Task {task_id}] Ошибка выполнения задачи: {str(e)}", exc_info=True)
    finally:
        db.close()


async def _process_single_record(
    db: Session,
    record: Dict,
    db_landings: List[Landing],
    min_score: int,
    dry_run: bool,
    api_base_url: str,
    auth_token: str
) -> Dict[str, Any]:
    """
    Обрабатывает одну запись из дампа.
    
    Returns:
        dict с деталями обработки
    """
    dump_page_name = record.get("page_name", "")
    dump_course_name = record.get("course_name", "")
    dump_preview_photo = record.get("preview_photo", "")
    
    # Формируем полную ссылку на фото из дампа
    dump_photo_url = None
    if dump_preview_photo:
        photo_path = dump_preview_photo.replace("\\", "/")
        if not photo_path.startswith("/"):
            photo_path = "/" + photo_path
        dump_photo_url = f"https://dent-s.com{photo_path}"
    
    detail = {
        "dump_page_name": dump_page_name,
        "dump_course_name": dump_course_name,
        "dump_photo_preview": dump_photo_url,
        "matched_landing_id": None,
        "matched_landing_name": None,
        "fuzzy_score": None,
        "action": "unknown",
        "new_url": None,
        "error": None,
    }
    
    # Проверяем наличие фото в дампе
    if not dump_preview_photo:
        detail["action"] = "skip_no_photo"
        return detail
    
    # Fuzzy matching
    matched_landing, score = fuzzy_match_landing(
        dump_page_name, dump_course_name, db_landings, min_score
    )
    
    if not matched_landing:
        detail["action"] = "skip_low_score"
        detail["fuzzy_score"] = 0
        return detail
    
    detail["matched_landing_id"] = matched_landing.id
    detail["matched_landing_name"] = matched_landing.landing_name or ""
    detail["fuzzy_score"] = round(score, 2)
    
    # Проверяем, не обновлена ли уже фотография
    if matched_landing.preview_photo and "cdn.dent-s.com" in matched_landing.preview_photo:
        detail["action"] = "skip_cdn_exists"
        detail["new_url"] = matched_landing.preview_photo
        return detail
    
    # Если dry_run - не загружаем, только проверяем
    if dry_run:
        detail["action"] = "success"
        detail["new_url"] = "[dry_run - не загружено]"
        return detail
    
    # Скачиваем и загружаем фото
    try:
        # Формируем URL фотографии: заменяем \ на /
        photo_path = dump_preview_photo.replace("\\", "/")
        if not photo_path.startswith("/"):
            photo_path = "/" + photo_path
        photo_url = f"https://dent-s.com{photo_path}"
        
        # Скачиваем
        response = requests.get(photo_url, timeout=30)
        response.raise_for_status()
        image_bytes = response.content
        
        # Определяем content-type
        file_extension = photo_path.split('.')[-1].lower()
        content_type_map = {
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'png': 'image/png',
            'webp': 'image/webp',
            'gif': 'image/gif',
        }
        content_type = content_type_map.get(file_extension, 'image/jpeg')
        filename = photo_path.split('/')[-1]
        
        # Загружаем через /upload-image
        async with httpx.AsyncClient(timeout=60.0) as client:
            files = {
                'file': (filename, image_bytes, content_type)
            }
            data = {
                'entity_type': 'landing_preview',
                'entity_id': str(matched_landing.id),
            }
            headers = {
                'Authorization': f'Bearer {auth_token}'
            }
            
            upload_url = f"{api_base_url}/api/media/upload-image"
            upload_response = await client.post(
                upload_url,
                files=files,
                data=data,
                headers=headers
            )
            
            if upload_response.status_code == 201:
                upload_result = upload_response.json()
                detail["action"] = "success"
                detail["new_url"] = upload_result.get("url")
            else:
                detail["action"] = "failed"
                detail["error"] = f"Upload failed: HTTP {upload_response.status_code}"
    
    except requests.RequestException as e:
        detail["action"] = "failed"
        detail["error"] = f"Download error: {str(e)}"
    except httpx.RequestError as e:
        detail["action"] = "failed"
        detail["error"] = f"Upload error: {str(e)}"
    except Exception as e:
        detail["action"] = "failed"
        detail["error"] = f"Unexpected error: {str(e)}"
    
    return detail


# ─────────────── API Endpoints ───────────────

@router.post(
    "/migrate-landing-photos",
    response_model=StartTaskResponse,
    summary="Запуск миграции preview-фотографий лендингов",
    description="""
    Запускает фоновую задачу миграции preview-фотографий лендингов из старой системы в S3/CDN.
    
    Параметры:
    - dry_run (default: true): Тестовый прогон без реальной загрузки
    - min_score (default: 80): Минимальный порог fuzzy matching (0-100)
    
    Для каждой записи из дампа:
    1. Fuzzy matching с лендингами в БД (по page_name и landing_name)
    2. Проверка что фото еще не в CDN
    3. Скачивание с dent-s.com
    4. Загрузка через /upload-image (конвертация WebP + S3 + обновление БД)
    
    Требует роль admin.
    """,
)
async def start_migration(
    migration_request: MigrationRequest,
    fastapi_request: Request,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user = Depends(require_roles("admin")),
):
    """Запускает фоновую задачу миграции фотографий."""
    
    # Получаем токен авторизации
    auth_header = fastapi_request.headers.get("Authorization")
    if not auth_header or not auth_header.startswith("Bearer "):
        raise HTTPException(401, "Отсутствует или некорректный токен авторизации")
    
    auth_token = auth_header.replace("Bearer ", "")
    
    # Базовый URL API
    api_base_url = os.getenv("API_BASE_URL", "https://dent-s.com")
    
    # Проверяем наличие дампа
    if not os.path.exists(DUMP_FILE_PATH):
        raise HTTPException(404, f"Файл дампа не найден: {DUMP_FILE_PATH}")
    
    # Создаем уникальный ID задачи
    task_id = str(uuid.uuid4())
    
    # Инициализируем прогресс задачи
    tasks_progress[task_id] = {
        "status": "pending",
        "progress": {
            "total": 0,
            "processed": 0,
            "percent": 0.0,
        },
        "stats": {
            "success": 0,
            "skip_cdn_exists": 0,
            "skip_no_photo": 0,
            "skip_low_score": 0,
            "failed": 0,
        },
        "details": [],
        "started_at": None,
        "completed_at": None,
    }
    
    # Запускаем фоновую задачу
    background_tasks.add_task(
        _background_migration_task,
        task_id=task_id,
        dry_run=migration_request.dry_run,
        min_score=migration_request.min_score,
        api_base_url=api_base_url,
        auth_token=auth_token,
        db_connection_string=DATABASE_URL
    )
    
    logger.info(
        f"[Task {task_id}] Запущена задача миграции "
        f"(dry_run={migration_request.dry_run}, min_score={migration_request.min_score})"
    )
    
    return StartTaskResponse(
        task_id=task_id,
        message="Задача запущена. Используйте task_id для отслеживания прогресса.",
        total_records=0,  # Будет заполнено после загрузки дампа
        check_status_url=f"/api/migrate-landing-photos/status/{task_id}"
    )


@router.get(
    "/migrate-landing-photos/status/{task_id}",
    response_model=TaskProgressResponse,
    summary="Проверка статуса задачи миграции",
    description="""
    Возвращает текущий прогресс выполнения задачи миграции фотографий.
    
    Результаты отсортированы:
    - Сначала ошибки (failed)
    - Затем по возрастанию fuzzy_score (самый низкий вверху)
    
    Статусы:
    - pending: Задача в очереди
    - processing: Задача выполняется
    - completed: Задача завершена успешно
    - failed: Задача завершена с ошибкой
    """,
)
async def get_migration_status(
    task_id: str,
    current_user = Depends(require_roles("admin")),
):
    """Возвращает статус выполнения задачи миграции."""
    
    if task_id not in tasks_progress:
        raise HTTPException(404, f"Задача с ID {task_id} не найдена")
    
    task = tasks_progress[task_id]
    
    # Сортируем детали: ошибки вверху, затем по fuzzy_score (низкий вверху)
    sorted_details = sorted(
        task["details"],
        key=lambda x: (
            0 if x.get("action") == "failed" else 1,  # Ошибки первыми
            x.get("fuzzy_score") if x.get("fuzzy_score") is not None else 999  # По возрастанию score
        )
    )
    
    return TaskProgressResponse(
        task_id=task_id,
        status=task["status"],
        progress=task["progress"],
        stats=task["stats"],
        started_at=task.get("started_at"),
        completed_at=task.get("completed_at"),
        details=sorted_details,
    )


@router.get(
    "/migrate-landing-photos/tasks",
    response_model=List[TaskProgressResponse],
    summary="Список всех задач миграции",
    description="Возвращает список всех задач миграции фотографий (активных и завершенных).",
)
async def list_migration_tasks(
    current_user = Depends(require_roles("admin")),
):
    """Возвращает список всех задач миграции."""
    
    tasks = []
    for task_id, task in tasks_progress.items():
        # Сортируем детали: ошибки вверху, затем по fuzzy_score (низкий вверху)
        sorted_details = sorted(
            task["details"],
            key=lambda x: (
                0 if x.get("action") == "failed" else 1,  # Ошибки первыми
                x.get("fuzzy_score") if x.get("fuzzy_score") is not None else 999  # По возрастанию score
            )
        )
        
        tasks.append(TaskProgressResponse(
            task_id=task_id,
            status=task["status"],
            progress=task["progress"],
            stats=task["stats"],
            started_at=task.get("started_at"),
            completed_at=task.get("completed_at"),
            details=sorted_details,
        ))
    
    return tasks

