"""
Mailgun Webhook Endpoint
Принимает события от Mailgun (bounce, complaint, unsubscribe) и обновляет suppression list.
"""

import hashlib
import hmac
import logging
import time
from typing import Optional

from fastapi import APIRouter, Request, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..core.config import settings
from ..db.database import get_db
from ..models.models_v2 import SuppressionType
from ..models.models_v2 import EmailCampaign, EmailCampaignRecipient, EmailCampaignRecipientStatus
from ..services_v2.email_suppression_service import add_to_suppression

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/mailgun", tags=["mailgun"])


class MailgunSignature(BaseModel):
    """Структура подписи Mailgun."""
    timestamp: str
    token: str
    signature: str


class MailgunEventData(BaseModel):
    """Данные события из Mailgun webhook."""
    event: str
    recipient: Optional[str] = None
    # Дополнительные поля
    severity: Optional[str] = None  # "permanent" или "temporary"
    reason: Optional[str] = None
    
    class Config:
        extra = "allow"  # Разрешаем дополнительные поля


class MailgunWebhookPayload(BaseModel):
    """Полная структура webhook payload от Mailgun."""
    signature: MailgunSignature
    event_data: Optional[MailgunEventData] = None
    
    class Config:
        extra = "allow"


def verify_mailgun_signature(
    signing_key: str,
    timestamp: str,
    token: str,
    signature: str
) -> bool:
    """
    Верифицирует подпись Mailgun webhook.
    
    Mailgun подписывает webhooks используя HMAC с SHA256:
    HMAC(signing_key, timestamp + token) == signature
    """
    if not signing_key:
        logger.warning("Mailgun signing key not configured, skipping signature verification")
        return True  # Пропускаем если ключ не настроен
    
    # Проверка timestamp (не старше 5 минут)
    try:
        ts = int(timestamp)
        if abs(time.time() - ts) > 300:
            logger.warning("Mailgun webhook timestamp too old: %s", timestamp)
            return False
    except ValueError:
        logger.warning("Invalid Mailgun webhook timestamp: %s", timestamp)
        return False
    
    # Вычисляем HMAC
    expected_signature = hmac.new(
        key=signing_key.encode("utf-8"),
        msg=f"{timestamp}{token}".encode("utf-8"),
        digestmod=hashlib.sha256
    ).hexdigest()
    
    return hmac.compare_digest(expected_signature, signature)


def parse_bounce_code(delivery_status: dict) -> tuple[str, str]:
    """
    Извлекает код и описание ошибки из delivery-status.
    
    Returns:
        (code, error_description)
    """
    code = str(delivery_status.get("code", ""))
    
    # Пытаемся получить enhanced code (5.1.1 формат)
    enhanced_code = delivery_status.get("enhanced-code", "")
    bounce_code = delivery_status.get("bounce-code", "")
    
    if enhanced_code:
        code = enhanced_code
    elif bounce_code:
        code = bounce_code
    
    # Описание ошибки
    error = delivery_status.get("message", "") or delivery_status.get("description", "")
    
    return code, error


def determine_suppression_type(event_data: dict) -> tuple[SuppressionType, str, str]:
    """
    Определяет тип suppression на основе данных события.
    
    Returns:
        (suppression_type, code, error)
    """
    event = event_data.get("event", "").lower()
    severity = event_data.get("severity", "").lower()
    delivery_status = event_data.get("delivery-status", {})
    
    code, error = parse_bounce_code(delivery_status)
    error_lower = (error or "").lower()
    
    # Определяем тип на основе события
    if event == "complained":
        return SuppressionType.COMPLAINT, code, error
    
    if event == "unsubscribed":
        return SuppressionType.UNSUBSCRIBE, code, error
    
    if event in ("failed", "bounced", "dropped"):
        # Mailgun "Too old" (часто code=602 или текст содержит "too old") — это результат
        # длительных временных deferred/rate-limit. Это НЕ hard bounce адреса.
        # Лучше трактовать как временное throttling (на 24 часа), а не навсегда блокировать.
        if str(code).strip() == "602" or "too old" in error_lower:
            return SuppressionType.THROTTLED, code, error
        # Проверяем severity для определения hard/soft bounce
        if severity == "permanent":
            return SuppressionType.HARD_BOUNCE, code, error
        elif severity == "temporary":
            return SuppressionType.SOFT_BOUNCE, code, error
        else:
            # По коду определяем тип
            if code.startswith("5"):
                return SuppressionType.HARD_BOUNCE, code, error
            elif code.startswith("4"):
                return SuppressionType.SOFT_BOUNCE, code, error
            else:
                # По умолчанию hard bounce для безопасности
                return SuppressionType.HARD_BOUNCE, code, error
    
    # Неизвестное событие - игнорируем
    return None, code, error


@router.post("/webhooks")
async def mailgun_webhook(request: Request, db: Session = Depends(get_db)):
    """
    Принимает webhook события от Mailgun.
    
    Обрабатываемые события:
    - failed (permanent/temporary) - bounce
    - bounced - bounce
    - dropped - suppression
    - complained - spam complaint
    - unsubscribed - отписка
    """
    try:
        payload = await request.json()
    except Exception as e:
        logger.error("Failed to parse Mailgun webhook payload: %s", e)
        raise HTTPException(status_code=400, detail="Invalid JSON payload")
    
    # Извлекаем данные подписи
    signature_data = payload.get("signature", {})
    timestamp = signature_data.get("timestamp", "")
    token = signature_data.get("token", "")
    signature = signature_data.get("signature", "")
    
    # Верифицируем подпись
    signing_key = getattr(settings, "MAILGUN_WEBHOOK_SIGNING_KEY", "")
    if signing_key and not verify_mailgun_signature(signing_key, timestamp, token, signature):
        logger.warning("Invalid Mailgun webhook signature")
        raise HTTPException(status_code=401, detail="Invalid signature")
    
    # Извлекаем данные события
    event_data = payload.get("event-data", {})
    if not event_data:
        # Старый формат webhook (legacy)
        event_data = payload
    
    event = event_data.get("event", "").lower()
    recipient = event_data.get("recipient", "")
    
    if not recipient:
        logger.debug("Mailgun webhook without recipient, ignoring")
        return {"status": "ok", "message": "no recipient"}
    
    logger.info("Mailgun webhook received: event=%s, recipient=%s", event, recipient)
    
    # ── Обновляем статусы получателей кампаний (минимально-инвазивно) ─────────────
    # Сейчас в БД `status=sent` означает "мы отправили/приняли к отправке", но фактический delivery/fail
    # может прийти позже. Чтобы статистика в БД не расходилась с Mailgun, обновляем статус по webhooks:
    # - complained → COMPLAINED
    # - permanent failed/bounced/dropped (5xx) → BOUNCED
    #
    # ВАЖНО: temporary (4xx / severity=temporary) НЕ считаем финальным фейлом и не портим статус.
    try:
        tags = event_data.get("tags") or []
        if isinstance(tags, str):
            tags = [tags]
        tags = [str(t) for t in tags]

        user_vars = event_data.get("user-variables") or {}
        campaign_code = (user_vars.get("campaign_code") or "").strip()

        is_ny2026 = ("NY2026" in tags) or (campaign_code == "NY2026")
        if is_ny2026:
            campaign = db.query(EmailCampaign).filter(EmailCampaign.code == "NY2026").first()
            if campaign:
                recipient_lower = (recipient or "").strip().lower()
                if recipient_lower:
                    # complained → финально
                    if event == "complained":
                        db.query(EmailCampaignRecipient).filter(
                            EmailCampaignRecipient.campaign_id == campaign.id,
                            EmailCampaignRecipient.email == recipient_lower,
                        ).update(
                            {"status": EmailCampaignRecipientStatus.COMPLAINED},
                            synchronize_session=False,
                        )
                        db.commit()
                    # failed/bounced/dropped: финально только если это hard/permanent
                    elif event in ("failed", "bounced", "dropped"):
                        suppression_type, _, _ = determine_suppression_type(event_data)
                        if suppression_type == SuppressionType.HARD_BOUNCE:
                            db.query(EmailCampaignRecipient).filter(
                                EmailCampaignRecipient.campaign_id == campaign.id,
                                EmailCampaignRecipient.email == recipient_lower,
                            ).update(
                                {"status": EmailCampaignRecipientStatus.BOUNCED},
                                synchronize_session=False,
                            )
                            db.commit()
    except Exception as e:
        logger.warning("Failed to update campaign recipient status from webhook: %s", e)

    # Определяем тип suppression
    suppression_type, code, error = determine_suppression_type(event_data)
    
    if suppression_type is None:
        logger.debug("Mailgun event %s not handled", event)
        return {"status": "ok", "message": f"event {event} not handled"}
    
    # Добавляем в suppression list
    try:
        add_to_suppression(
            db=db,
            email=recipient,
            suppression_type=suppression_type,
            code=code,
            error=error[:500] if error else None,  # Ограничиваем длину ошибки
            source="mailgun_webhook"
        )
        
        logger.info(
            "Added to suppression: email=%s, type=%s, code=%s",
            recipient, suppression_type.value, code
        )
        
    except Exception as e:
        logger.exception("Failed to add email to suppression list: %s", e)
        # Не выбрасываем ошибку, чтобы Mailgun не делал retry
    
    return {"status": "ok", "message": f"processed {event}"}


@router.get("/sync-suppressions")
async def sync_suppressions(db: Session = Depends(get_db)):
    """
    Одноразовая синхронизация существующих suppression-ов из Mailgun.
    Вызывайте после первичной настройки.
    
    ВАЖНО: Защитите этот endpoint авторизацией в продакшене!
    """
    from ..services_v2.email_suppression_service import sync_bounces_from_mailgun
    
    result = sync_bounces_from_mailgun(db)
    return result


