import logging
import os
from typing import Optional, Dict, Any
from celery import shared_task
from sqlalchemy.orm import Session
import redis

from ..db.database import SessionLocal
from ..services_v2.creative_service import (
    generate_all_creatives,
    generate_single_creative,
    BookAIValidationError,
    BookAIServiceUnavailableError,
    PlacidQuotaError,
    PlacidServiceError,
)

logger = logging.getLogger(__name__)

# Redis клиент для отслеживания активных задач
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
rds = redis.Redis.from_url(REDIS_URL, decode_responses=True)

# TTL для маппинга task_id (15 минут)
TASK_MAPPING_TTL = 900


def _task_key(book_id: int, language: str, target: Optional[str] = None) -> str:
    """Генерирует ключ Redis для отслеживания активных задач."""
    if target:
        return f"creative_task:{book_id}:{language}:{target}"
    return f"creative_task:{book_id}:{language}"


def set_active_task(book_id: int, language: str, task_id: str, target: Optional[str] = None) -> None:
    """Сохраняет активную задачу в Redis."""
    key = _task_key(book_id, language, target)
    rds.set(key, task_id, ex=TASK_MAPPING_TTL)
    logger.info(f"Set active task {task_id} for {key}")


def get_active_task(book_id: int, language: str, target: Optional[str] = None) -> Optional[str]:
    """Получает ID активной задачи из Redis."""
    key = _task_key(book_id, language, target)
    task_id = rds.get(key)
    if task_id:
        logger.info(f"Found active task {task_id} for {key}")
    return task_id


def clear_active_task(book_id: int, language: str, target: Optional[str] = None) -> None:
    """Удаляет маппинг активной задачи."""
    key = _task_key(book_id, language, target)
    rds.delete(key)
    logger.info(f"Cleared active task for {key}")


@shared_task(
    name="app.tasks.creatives.generate_all_creatives_task",
    bind=True,
    track_started=True,
    soft_time_limit=30 * 60,  # 30 минут
    time_limit=35 * 60,  # 35 минут
    autoretry_for=(),
    max_retries=0,
)
def generate_all_creatives_task(
    self,
    book_id: int,
    language: str,
    manual_payload: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    """
    Генерирует все три креатива для книги асинхронно.
    
    Возвращает:
        {
            "status": "success" | "error",
            "items": [...],  # при успехе
            "error": "...",  # при ошибке
            "error_type": "validation" | "service_unavailable" | "quota" | "placid" | "general"
        }
    """
    db: Session = SessionLocal()
    try:
        # Обновляем статус - начало работы
        self.update_state(state="PROGRESS", meta={"stage": "started", "book_id": book_id, "language": language})
        logger.info(f"Starting creative generation task for book_id={book_id}, language={language}")
        
        # Генерируем креативы
        self.update_state(state="PROGRESS", meta={"stage": "generating_v1", "book_id": book_id})
        items = generate_all_creatives(db, book_id, language, manual_payload=manual_payload)
        
        # Успех - формируем результат
        self.update_state(state="PROGRESS", meta={"stage": "completed", "book_id": book_id})
        result = {
            "status": "success",
            "items": [
                {
                    "code": x.creative_code,
                    "creative_code": x.creative_code,
                    "status": x.status.value,
                    "s3_url": x.s3_url or "",
                    "payload_used": x.payload_used or {},
                }
                for x in items
            ],
        }
        logger.info(f"Creative generation completed successfully for book_id={book_id}")
        return result
        
    except BookAIValidationError as e:
        logger.error(f"BookAI validation error for book_id={book_id}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "validation",
        }
    except BookAIServiceUnavailableError as e:
        logger.error(f"BookAI service unavailable for book_id={book_id}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "service_unavailable",
        }
    except PlacidQuotaError as e:
        logger.error(f"Placid quota error for book_id={book_id}: {e}")
        return {
            "status": "error",
            "error": "Placid: Requires Subscription and Credits",
            "error_type": "quota",
        }
    except PlacidServiceError as e:
        logger.error(f"Placid service error for book_id={book_id}: {e}")
        return {
            "status": "error",
            "error": f"Placid error: {str(e)}",
            "error_type": "placid",
        }
    except ValueError as e:
        logger.error(f"ValueError for book_id={book_id}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "validation",
        }
    except Exception as e:
        logger.exception(f"Unexpected error in creative generation for book_id={book_id}")
        return {
            "status": "error",
            "error": f"Failed to generate creatives: {str(e)}",
            "error_type": "general",
        }
    finally:
        db.close()
        # Очищаем маппинг активной задачи
        clear_active_task(book_id, language)


@shared_task(
    name="app.tasks.creatives.generate_single_creative_task",
    bind=True,
    track_started=True,
    soft_time_limit=15 * 60,  # 15 минут
    time_limit=18 * 60,  # 18 минут
    autoretry_for=(),
    max_retries=0,
)
def generate_single_creative_task(
    self,
    book_id: int,
    language: str,
    target: str,
    overrides: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Генерирует один креатив для книги асинхронно.
    
    Args:
        book_id: ID книги
        language: Язык креатива
        target: Целевой креатив ('v1', 'v2', 'v3' или creative_code)
        overrides: Переопределения полей
        
    Возвращает:
        {
            "status": "success" | "error",
            "item": {...},  # при успехе
            "error": "...",  # при ошибке
            "error_type": "validation" | "service_unavailable" | "quota" | "placid" | "general"
        }
    """
    db: Session = SessionLocal()
    try:
        # Обновляем статус - начало работы
        self.update_state(
            state="PROGRESS",
            meta={"stage": "started", "book_id": book_id, "language": language, "target": target}
        )
        logger.info(f"Starting single creative generation for book_id={book_id}, language={language}, target={target}")
        
        # Генерируем креатив
        self.update_state(
            state="PROGRESS",
            meta={"stage": "generating", "book_id": book_id, "target": target}
        )
        item = generate_single_creative(db, book_id, language, target, overrides=overrides)
        
        # Успех
        self.update_state(
            state="PROGRESS",
            meta={"stage": "completed", "book_id": book_id, "target": target}
        )
        result = {
            "status": "success",
            "item": {
                "code": item.creative_code,
                "creative_code": item.creative_code,
                "status": item.status.value,
                "s3_url": item.s3_url or "",
                "payload_used": item.payload_used or {},
            },
        }
        logger.info(f"Single creative generation completed for book_id={book_id}, target={target}")
        return result
        
    except BookAIValidationError as e:
        logger.error(f"BookAI validation error for book_id={book_id}, target={target}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "validation",
        }
    except BookAIServiceUnavailableError as e:
        logger.error(f"BookAI service unavailable for book_id={book_id}, target={target}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "service_unavailable",
        }
    except PlacidQuotaError as e:
        logger.error(f"Placid quota error for book_id={book_id}, target={target}: {e}")
        return {
            "status": "error",
            "error": "Placid: Requires Subscription and Credits",
            "error_type": "quota",
        }
    except PlacidServiceError as e:
        logger.error(f"Placid service error for book_id={book_id}, target={target}: {e}")
        return {
            "status": "error",
            "error": f"Placid error: {str(e)}",
            "error_type": "placid",
        }
    except ValueError as e:
        logger.error(f"ValueError for book_id={book_id}, target={target}: {e}")
        return {
            "status": "error",
            "error": str(e),
            "error_type": "validation",
        }
    except Exception as e:
        logger.exception(f"Unexpected error in single creative generation for book_id={book_id}, target={target}")
        return {
            "status": "error",
            "error": f"Failed to generate creative: {str(e)}",
            "error_type": "general",
        }
    finally:
        db.close()
        # Очищаем маппинг активной задачи
        clear_active_task(book_id, language, target)


