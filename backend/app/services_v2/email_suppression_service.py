"""
Email Suppression Service
Управление списком заблокированных email адресов для предотвращения отправки на bounce/complained адреса.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import requests
from sqlalchemy.orm import Session

from ..core.config import settings
from ..models.models_v2 import EmailSuppression, SuppressionType

logger = logging.getLogger(__name__)

# Константы
SOFT_BOUNCE_THRESHOLD = 3          # После 3 soft bounce → hard bounce
SOFT_BOUNCE_WINDOW_DAYS = 7        # Окно для подсчета soft bounce


def is_email_suppressed(db: Session, email: str) -> bool:
    """
    Проверяет, заблокирован ли email для отправки.
    
    Возвращает True если:
    - email в suppression list с типом != SOFT_BOUNCE
    - email в suppression list с SOFT_BOUNCE и soft_bounce_count >= 3
    """
    email_lower = email.lower().strip()
    
    suppression = db.query(EmailSuppression).filter(
        EmailSuppression.email == email_lower
    ).first()
    
    if not suppression:
        return False
    
    # Hard bounce, complaint, unsubscribe, invalid → всегда блокируем
    if suppression.type != SuppressionType.SOFT_BOUNCE:
        return True
    
    # Soft bounce → проверяем счетчик
    if suppression.soft_bounce_count >= SOFT_BOUNCE_THRESHOLD:
        return True
    
    return False


def add_to_suppression(
    db: Session,
    email: str,
    suppression_type: SuppressionType,
    code: Optional[str] = None,
    error: Optional[str] = None,
    source: str = "mailgun_webhook"
) -> EmailSuppression:
    """
    Добавляет email в suppression list или обновляет существующую запись.
    
    Для soft bounce:
    - Увеличивает счетчик
    - Если счетчик >= 3, конвертирует в hard bounce
    """
    email_lower = email.lower().strip()
    now = datetime.utcnow()
    
    existing = db.query(EmailSuppression).filter(
        EmailSuppression.email == email_lower
    ).first()
    
    if existing:
        # Обновляем существующую запись
        if suppression_type == SuppressionType.SOFT_BOUNCE:
            # Soft bounce: увеличиваем счетчик
            window_start = now - timedelta(days=SOFT_BOUNCE_WINDOW_DAYS)
            
            # Сбрасываем счетчик если последний bounce был давно
            if existing.last_soft_bounce_at and existing.last_soft_bounce_at < window_start:
                existing.soft_bounce_count = 1
            else:
                existing.soft_bounce_count += 1
            
            existing.last_soft_bounce_at = now
            
            # Конвертируем в hard bounce если превышен лимит
            if existing.soft_bounce_count >= SOFT_BOUNCE_THRESHOLD:
                existing.type = SuppressionType.HARD_BOUNCE
                logger.info(
                    "Email %s converted to hard_bounce after %d soft bounces",
                    email_lower, existing.soft_bounce_count
                )
        else:
            # Hard bounce, complaint, etc. → перезаписываем тип
            existing.type = suppression_type
        
        existing.code = code or existing.code
        existing.error = error or existing.error
        existing.source = source
        
        db.commit()
        logger.info("Updated suppression for %s: type=%s", email_lower, existing.type.value)
        return existing
    
    # Создаем новую запись
    suppression = EmailSuppression(
        email=email_lower,
        type=suppression_type,
        code=code,
        error=error,
        source=source,
        soft_bounce_count=1 if suppression_type == SuppressionType.SOFT_BOUNCE else 0,
        last_soft_bounce_at=now if suppression_type == SuppressionType.SOFT_BOUNCE else None,
    )
    
    db.add(suppression)
    db.commit()
    logger.info("Added email %s to suppression list: type=%s", email_lower, suppression_type.value)
    return suppression


def remove_from_suppression(db: Session, email: str) -> bool:
    """
    Удаляет email из suppression list.
    Возвращает True если запись была удалена.
    """
    email_lower = email.lower().strip()
    
    result = db.query(EmailSuppression).filter(
        EmailSuppression.email == email_lower
    ).delete()
    
    db.commit()
    
    if result:
        logger.info("Removed email %s from suppression list", email_lower)
    
    return result > 0


def get_suppression(db: Session, email: str) -> Optional[EmailSuppression]:
    """Получает запись о suppression для email."""
    email_lower = email.lower().strip()
    return db.query(EmailSuppression).filter(
        EmailSuppression.email == email_lower
    ).first()


def sync_bounces_from_mailgun(db: Session, limit: int = 1000) -> dict:
    """
    Синхронизирует существующие bounce-ы из Mailgun API в локальную БД.
    Вызывайте один раз при первичной настройке.
    
    Returns:
        dict с количеством импортированных и пропущенных записей
    """
    if not settings.MAILGUN_API_KEY or not settings.MAILGUN_DOMAIN:
        logger.warning("Mailgun not configured, skipping sync")
        return {"imported": 0, "skipped": 0, "error": "Mailgun not configured"}
    
    # Выбираем API endpoint в зависимости от региона
    if settings.MAILGUN_REGION.upper() == "EU":
        api_base = "https://api.eu.mailgun.net/v3"
    else:
        api_base = "https://api.mailgun.net/v3"
    
    imported = 0
    skipped = 0
    
    # Импорт bounce-ов
    try:
        url = f"{api_base}/{settings.MAILGUN_DOMAIN}/bounces"
        response = requests.get(
            url,
            auth=("api", settings.MAILGUN_API_KEY),
            params={"limit": limit},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                email = item.get("address", "").lower().strip()
                if not email:
                    continue
                
                # Определяем тип по коду
                code = item.get("code", "")
                if code.startswith("5"):
                    suppression_type = SuppressionType.HARD_BOUNCE
                elif code.startswith("4"):
                    suppression_type = SuppressionType.SOFT_BOUNCE
                else:
                    suppression_type = SuppressionType.HARD_BOUNCE
                
                existing = db.query(EmailSuppression).filter(
                    EmailSuppression.email == email
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                suppression = EmailSuppression(
                    email=email,
                    type=suppression_type,
                    code=code,
                    error=item.get("error", ""),
                    source="mailgun_sync",
                    soft_bounce_count=1 if suppression_type == SuppressionType.SOFT_BOUNCE else 0,
                )
                db.add(suppression)
                imported += 1
            
            db.commit()
            logger.info("Mailgun sync complete: imported=%d, skipped=%d", imported, skipped)
        else:
            logger.error("Mailgun API error: %s - %s", response.status_code, response.text)
            return {"imported": imported, "skipped": skipped, "error": f"API error: {response.status_code}"}
            
    except Exception as e:
        logger.exception("Error syncing bounces from Mailgun: %s", e)
        return {"imported": imported, "skipped": skipped, "error": str(e)}
    
    # Импорт complaints
    try:
        url = f"{api_base}/{settings.MAILGUN_DOMAIN}/complaints"
        response = requests.get(
            url,
            auth=("api", settings.MAILGUN_API_KEY),
            params={"limit": limit},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                email = item.get("address", "").lower().strip()
                if not email:
                    continue
                
                existing = db.query(EmailSuppression).filter(
                    EmailSuppression.email == email
                ).first()
                
                if existing:
                    # Complaint важнее bounce
                    if existing.type != SuppressionType.COMPLAINT:
                        existing.type = SuppressionType.COMPLAINT
                        existing.source = "mailgun_sync"
                    skipped += 1
                    continue
                
                suppression = EmailSuppression(
                    email=email,
                    type=SuppressionType.COMPLAINT,
                    source="mailgun_sync",
                )
                db.add(suppression)
                imported += 1
            
            db.commit()
            
    except Exception as e:
        logger.exception("Error syncing complaints from Mailgun: %s", e)
    
    # Импорт unsubscribes
    try:
        url = f"{api_base}/{settings.MAILGUN_DOMAIN}/unsubscribes"
        response = requests.get(
            url,
            auth=("api", settings.MAILGUN_API_KEY),
            params={"limit": limit},
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            for item in data.get("items", []):
                email = item.get("address", "").lower().strip()
                if not email:
                    continue
                
                existing = db.query(EmailSuppression).filter(
                    EmailSuppression.email == email
                ).first()
                
                if existing:
                    skipped += 1
                    continue
                
                suppression = EmailSuppression(
                    email=email,
                    type=SuppressionType.UNSUBSCRIBE,
                    source="mailgun_sync",
                )
                db.add(suppression)
                imported += 1
            
            db.commit()
            
    except Exception as e:
        logger.exception("Error syncing unsubscribes from Mailgun: %s", e)
    
    return {"imported": imported, "skipped": skipped}


