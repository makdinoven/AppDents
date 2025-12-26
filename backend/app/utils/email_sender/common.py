import logging
import smtplib
import ssl
import threading
import time
from typing import Optional, Tuple

import dns.resolver
import requests
from email_validator import EmailNotValidError, validate_email

from ...core.config import settings
from ...db.database import SessionLocal
from ...models.models_v2 import SuppressionType

logger = logging.getLogger(__name__)


# ─────────────────────── Rate Limiter ───────────────────────
# Защита от rate limit: минимум MIN_INTERVAL секунд между отправками
MIN_INTERVAL_SECONDS = 5.0  # увеличено с 2 до 5 секунд для снижения throttling

_last_send_time: float = 0.0
_rate_limit_lock = threading.Lock()


def _wait_for_rate_limit() -> None:
    """
    Ждёт, если с последней отправки прошло меньше MIN_INTERVAL_SECONDS.
    Thread-safe для корректной работы в многопоточных Celery воркерах.
    """
    global _last_send_time

    with _rate_limit_lock:
        now = time.time()
        elapsed = now - _last_send_time

        if elapsed < MIN_INTERVAL_SECONDS:
            sleep_time = MIN_INTERVAL_SECONDS - elapsed
            time.sleep(sleep_time)

        _last_send_time = time.time()


# ─────────────────────── Email Validation ───────────────────────

# Доверенные домены - для них достаточно проверить MX записи
TRUSTED_DOMAINS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.co.uk", "yahoo.fr",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "hotmail.it",
    "live.com", "msn.com",
    "icloud.com", "me.com", "mac.com",
    "mail.ru", "yandex.ru", "yandex.com",
    "aol.com", "protonmail.com", "proton.me",
    "comcast.net", "san.rr.com",
}

VALIDATION_TIMEOUT = 3  # секунды


def _check_suppression_list(email: str) -> bool:
    """
    Проверяет, заблокирован ли email в suppression list.
    Возвращает True если email в списке и должен быть пропущен.
    """
    try:
        from ...services_v2.email_suppression_service import is_email_suppressed
        db = SessionLocal()
        try:
            return is_email_suppressed(db, email)
        finally:
            db.close()
    except Exception as e:
        logger.warning("Error checking suppression list for %s: %s", email, e)
        return False  # При ошибке не блокируем отправку


def _add_to_suppression(email: str, suppression_type: SuppressionType, error: str = None, source: str = "validation") -> None:
    """Добавляет email в suppression list."""
    try:
        from ...services_v2.email_suppression_service import add_to_suppression
        db = SessionLocal()
        try:
            add_to_suppression(
                db=db,
                email=email,
                suppression_type=suppression_type,
                error=error,
                source=source
            )
        finally:
            db.close()
    except Exception as e:
        logger.warning("Error adding %s to suppression: %s", email, e)


def _is_throttling_error(error_message: str) -> bool:
    """
    Проверяет, является ли ошибка throttling (rate limit).
    Comcast: "4.2.0 Throttled"
    Gmail: "421 4.7.0 Try again later"
    Yahoo: "421 Message temporarily deferred"
    """
    if not error_message:
        return False
    
    error_lower = error_message.lower()
    throttle_patterns = [
        "throttl",           # throttled, throttling
        "4.2.0",             # Comcast throttle code
        "4.7.0",             # Gmail rate limit
        "try again later",
        "temporarily deferred",
        "rate limit",
        "too many",
        "sending rate",
        "slow down",
    ]
    
    return any(pattern in error_lower for pattern in throttle_patterns)


def _validate_email_sync(email: str) -> Tuple[bool, str]:
    """
    Синхронная валидация email перед отправкой.
    Проверяет синтаксис и наличие MX записей.
    
    Returns:
        (is_valid, error_message)
    """
    email_lower = email.lower().strip()
    
    # 1. Синтаксическая проверка
    try:
        validate_email(email_lower, check_deliverability=False)
    except EmailNotValidError as e:
        return False, f"Invalid syntax: {e}"
    
    # 2. Извлекаем домен
    if "@" not in email_lower:
        return False, "Invalid email format"
    
    domain = email_lower.split("@", 1)[1]
    
    # 3. Проверка MX записей
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=VALIDATION_TIMEOUT)
        if not answers:
            return False, f"No MX records for domain {domain}"
    except dns.resolver.NXDOMAIN:
        return False, f"Domain {domain} does not exist"
    except dns.resolver.NoAnswer:
        return False, f"No MX records for domain {domain}"
    except dns.resolver.Timeout:
        # При таймауте пропускаем проверку - не блокируем отправку
        logger.warning("MX lookup timeout for %s", domain)
        return True, ""
    except Exception as e:
        # При других ошибках DNS пропускаем проверку
        logger.warning("MX lookup error for %s: %s", domain, e)
        return True, ""
    
    return True, ""


# ────────────────────────────────────────────────────────────


def send_html_email(
    recipient_email: str,
    subject: str,
    html_body: str,
    *,
    text_body: str | None = None,
    headers: dict[str, str] | None = None,
    mailgun_options: dict[str, str] | None = None,
    mailgun_domain_override: str | None = None,
    from_override: str | None = None,
) -> bool:
    """
    Отправка HTML-писем через Mailgun API.
    Если Mailgun не настроен или не работает — fallback на SMTP.

    Включает:
    - Проверку suppression list (bounce, complaint, unsubscribe)
    - Валидацию email (синтаксис, MX записи)
    - Rate limiter для защиты от throttling
    """
    email_lower = recipient_email.lower().strip()
    
    # 1. Проверяем suppression list
    if _check_suppression_list(email_lower):
        logger.info("Skipping suppressed email: %s", email_lower)
        return False
    
    # 2. Валидация email
    is_valid, error_msg = _validate_email_sync(email_lower)
    if not is_valid:
        logger.info("Invalid email %s: %s", email_lower, error_msg)
        _add_to_suppression(email_lower, SuppressionType.INVALID, error_msg)
        return False
    
    # 3. Отправляем через Mailgun или SMTP
    mg_domain = (mailgun_domain_override or settings.MAILGUN_DOMAIN or "").strip()
    if settings.MAILGUN_API_KEY and mg_domain:
        result = _send_via_mailgun(
            recipient_email,
            subject,
            html_body,
            text_body=text_body,
            headers=headers,
            mailgun_options=mailgun_options,
            mailgun_domain_override=mg_domain,
            from_override=from_override,
        )
        if result:
            return True
        # Fallback на SMTP если Mailgun не сработал
        logger.warning("Mailgun failed for %s, falling back to SMTP...", email_lower)
        return _send_via_smtp(
            recipient_email, subject, html_body, text_body=text_body, headers=headers
        )
    else:
        # SMTP если Mailgun не настроен
        return _send_via_smtp(
            recipient_email, subject, html_body, text_body=text_body, headers=headers
        )


def _send_via_mailgun(
    recipient_email: str,
    subject: str,
    html_body: str,
    *,
    text_body: str | None = None,
    headers: dict[str, str] | None = None,
    mailgun_options: dict[str, str] | None = None,
    mailgun_domain_override: str | None = None,
    from_override: str | None = None,
) -> bool:
    """
    Отправка через Mailgun HTTP API.
    Включён rate limiter для защиты от rate limit.
    """
    # Rate limit: ждём если слишком частые отправки
    _wait_for_rate_limit()

    # Выбираем API endpoint в зависимости от региона
    if settings.MAILGUN_REGION.upper() == "EU":
        api_base = "https://api.eu.mailgun.net/v3"
    else:
        api_base = "https://api.mailgun.net/v3"

    domain = (mailgun_domain_override or settings.MAILGUN_DOMAIN or "").strip()
    url = f"{api_base}/{domain}/messages"

    data = {
        "from": (from_override or settings.EMAIL_SENDER),
        "to": recipient_email,
        "subject": subject,
        "text": text_body
        or "If you see this text, your email client does not support HTML.",
        "html": html_body,
    }

    # Mailgun message options (o:tracking, o:tag, o:dkim, etc.)
    if mailgun_options:
        for k, v in mailgun_options.items():
            if k:
                data[str(k)] = "" if v is None else str(v)

    # Custom MIME headers via Mailgun HTTP API: h:Header-Name
    if headers:
        for name, value in headers.items():
            if name:
                data[f"h:{name}"] = "" if value is None else str(value)

    try:
        response = requests.post(
            url,
            auth=("api", settings.MAILGUN_API_KEY),
            data=data,
            timeout=30
        )

        if response.status_code == 200:
            logger.debug("Email sent via Mailgun to %s", recipient_email)
            return True
        else:
            logger.error("Mailgun error for %s: %s - %s", recipient_email, response.status_code, response.text)
            return False

    except Exception as e:
        logger.error("Mailgun request error for %s: %s", recipient_email, repr(e))
        return False


def _send_via_smtp(
    recipient_email: str,
    subject: str,
    html_body: str,
    *,
    text_body: str | None = None,
    headers: dict[str, str] | None = None,
) -> bool:
    """
    Fallback: SMTP-отправка HTML-писем.
    Работает с портами 25 (без TLS), 465 (SMTPS), 587 (STARTTLS).
    Включён rate limiter для защиты от Gmail rate limit.
    """
    # Rate limit: ждём если слишком частые отправки
    _wait_for_rate_limit()

    from email.mime.text import MIMEText
    from email.mime.multipart import MIMEMultipart
    from email.header import Header

    smtp_server = settings.EMAIL_HOST
    smtp_port = int(settings.EMAIL_PORT or 0)
    smtp_username = (getattr(settings, "EMAIL_USERNAME", "") or "").strip()
    smtp_password = (getattr(settings, "EMAIL_PASSWORD", "") or "").strip()
    sender_email = settings.EMAIL_SENDER

    if not smtp_server:
        logger.error("SMTP error: EMAIL_HOST not configured")
        return False

    msg = MIMEMultipart("alternative")
    msg["From"] = sender_email
    msg["To"] = recipient_email
    msg["Subject"] = Header(subject, "utf-8")
    if headers:
        for name, value in headers.items():
            if name and value is not None:
                msg[str(name)] = str(value)

    msg.attach(
        MIMEText(
            text_body
            or "If you see this text, your email client does not support HTML.",
            "plain",
            "utf-8",
        )
    )
    msg.attach(MIMEText(html_body, "html", "utf-8"))

    ctx = ssl.create_default_context()

    try:
        if smtp_port == 465:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=15, context=ctx) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        elif smtp_port == 587:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=15) as s:
                s.ehlo()
                s.starttls(context=ctx)
                s.ehlo()
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        else:
            with smtplib.SMTP(smtp_server, smtp_port or 25, timeout=15) as s:
                if smtp_username and smtp_password:
                    s.login(smtp_username, smtp_password)
                s.sendmail(sender_email, [recipient_email], msg.as_string())

        logger.debug("Email sent via SMTP to %s", recipient_email)
        return True

    except smtplib.SMTPResponseException as e:
        error_msg = f"{e.smtp_code} {e.smtp_error}"
        logger.error("SMTP error for %s: %s", recipient_email, error_msg)
        
        # Проверяем на throttling
        if _is_throttling_error(str(e.smtp_error)):
            logger.warning("Throttling detected for %s, adding to suppression (24h)", recipient_email)
            _add_to_suppression(
                recipient_email, 
                SuppressionType.THROTTLED, 
                error=error_msg,
                source="smtp_throttle"
            )
        return False

    except Exception as e:
        error_msg = repr(e)
        logger.error("SMTP error for %s: %s", recipient_email, error_msg)
        
        # Проверяем на throttling в общем случае
        if _is_throttling_error(error_msg):
            logger.warning("Throttling detected for %s, adding to suppression (24h)", recipient_email)
            _add_to_suppression(
                recipient_email, 
                SuppressionType.THROTTLED, 
                error=error_msg,
                source="smtp_throttle"
            )
        return False
