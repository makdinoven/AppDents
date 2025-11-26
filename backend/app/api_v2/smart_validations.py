import asyncio
import difflib
import smtplib
import ssl
import time
from typing import Optional, Tuple

import dns.resolver
from email_validator import EmailNotValidError, validate_email
from fastapi import FastAPI, APIRouter, Query
from pydantic import BaseModel, Field

# --------------------- Константы ---------------------
POPULAR_DOMAINS: list[str] = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.uk",
    "live.com",
    "icloud.com",
    "mail.ru",
    "yandex.ru",
    "aol.com",
    "ukr.net",
    "yahoo.co.uk",
    "me.com",
    "msn.com",
    "comcast.net",
    "abv.bg",
    "hotmail.it",
    "yahoo.fr",
    "wp.pl",
    "libero.it",
    "ymail.com",
]

# SMTP‑check settings
DEFAULT_HELO_HOST = "validator.local"
SMTP_TIMEOUT = 3  # seconds - уменьшено с 8 до 3

# Кеш для результатов проверки (простой in-memory кеш)
# В продакшене лучше использовать Redis
_email_cache: dict[str, tuple[Optional[bool], str, float]] = {}

# Домены, для которых можно пропустить полную SMTP проверку
# (достаточно проверить наличие MX записей)
TRUSTED_DOMAINS = {
    "gmail.com", "googlemail.com",
    "yahoo.com", "yahoo.co.uk", "yahoo.fr",
    "outlook.com", "hotmail.com", "hotmail.co.uk", "hotmail.it",
    "live.com", "msn.com",
    "icloud.com", "me.com",
    "mail.ru", "yandex.ru", "yandex.com",
    "aol.com", "protonmail.com", "proton.me",
}

# --------------------- FastAPI ---------------------
router=APIRouter()


class EmailRequest(BaseModel):
    """Frontend sends only this field."""
    email: str = Field(..., examples=["user@gmai.com"])


class EmailResponse(BaseModel):
    is_syntactically_valid: bool
    suggestion: Optional[str] = None  # corrected email, if any
    mailbox_exists: Optional[bool] = None  # null if check inconclusive
    message: str  # human‑readable details


# --------------------- Utilities ---------------------

def suggest_domain(full_email: str) -> Optional[str]:
    if "@" not in full_email:
        return None
    local, domain = full_email.rsplit("@", 1)
    domain = domain.lower()
    match = difflib.get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.8)
    return f"{local}@{match[0]}" if match and match[0] != domain else None


def _mx_lookup(domain: str) -> list[str]:
    """Return MX hosts sorted by priority."""
    answers = dns.resolver.resolve(domain, "MX", lifetime=SMTP_TIMEOUT)
    return [str(r.exchange).rstrip(".") for r in sorted(answers, key=lambda r: r.preference)]


def _smtp_verify(
    email: str,
    mx_hosts: list[str],
    helo_host: str = DEFAULT_HELO_HOST,
    timeout: int = SMTP_TIMEOUT,
    max_hosts: int = 2,  # Проверяем только первые 2 MX хоста вместо всех
) -> Tuple[bool, str]:
    """RCPT TO handshake. Returns (exists?, debug)."""
    from_addr = f"validator@{helo_host}"
    # Ограничиваем количество проверяемых хостов для ускорения
    for host in mx_hosts[:max_hosts]:
        try:
            with smtplib.SMTP(host, timeout=timeout) as server:
                try:
                    server.starttls(context=ssl.create_default_context())
                except smtplib.SMTPException:
                    pass  # TLS unsupported — продолжим без него
                server.helo(helo_host)
                server.mail(from_addr)
                code, msg = server.rcpt(email)
                server.quit()
                msg_text = msg.decode() if isinstance(msg, bytes) else str(msg)
                if code in (250, 251):
                    return True, f"{host} → {code} {msg_text}"
                if code in (550, 551, 553):
                    return False, f"{host} → {code} {msg_text}"
        except (smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError, smtplib.SMTPHeloError):
            continue
        except Exception as exc:  # noqa: BLE001
            return False, f"SMTP error: {exc}"
    return False, f"Checked {min(len(mx_hosts), max_hosts)} MX hosts - all rejected or unresponsive"


async def smtp_check(email: str, use_cache: bool = True, cache_ttl: int = 3600) -> Tuple[Optional[bool], str]:
    """Asynchronous wrapper for SMTP verification with caching."""
    email_lower = email.lower()
    
    # Проверка кеша
    if use_cache and email_lower in _email_cache:
        exists, debug, timestamp = _email_cache[email_lower]
        if time.time() - timestamp < cache_ttl:
            return exists, f"{debug} (cached)"
    
    domain = email.split("@", 1)[1].lower()
    
    # Быстрая проверка для доверенных доменов - только MX lookup
    if domain in TRUSTED_DOMAINS:
        try:
            mx_hosts = _mx_lookup(domain)
            if mx_hosts:
                result = (True, f"Trusted domain with valid MX records ({len(mx_hosts)} hosts)")
                if use_cache:
                    _email_cache[email_lower] = (*result, time.time())
                return result
        except Exception as exc:  # noqa: BLE001
            result = (None, f"MX lookup failed for trusted domain: {exc}")
            if use_cache:
                _email_cache[email_lower] = (*result, time.time())
            return result
    
    # Полная SMTP проверка для остальных доменов
    try:
        mx_hosts = _mx_lookup(domain)
    except Exception as exc:  # noqa: BLE001
        result = (None, f"MX lookup failed: {exc}")
        if use_cache:
            _email_cache[email_lower] = (*result, time.time())
        return result

    loop = asyncio.get_running_loop()
    exists, debug = await loop.run_in_executor(
        None, _smtp_verify, email, mx_hosts, DEFAULT_HELO_HOST, SMTP_TIMEOUT
    )
    
    # Сохранение в кеш
    if use_cache:
        _email_cache[email_lower] = (exists, debug, time.time())
    
    return exists, debug


# --------------------- API Endpoint ---------------------

@router.post("/check-email", response_model=EmailResponse, summary="Validate & verify email")
async def check_email(payload: EmailRequest):
    email_input = payload.email.strip()

    # 1. Syntax validation
    try:
        validate_email(email_input, check_deliverability=False)
        syntax_ok = True
        message = "Адрес выглядит корректно."
    except EmailNotValidError as exc:
        syntax_ok = False
        message = str(exc)

    # 2. Domain suggestion (typo‑fix)
    suggestion = suggest_domain(email_input)

    # 3. SMTP mailbox existence check (только если email валиден)
    mailbox_exists = None
    if syntax_ok:
        # Используем кеширование для ускорения повторных проверок
        mailbox_exists, debug_msg = await smtp_check(email_input, use_cache=True)
        message += f"\nSMTP: {debug_msg}"
    else:
        # Пропускаем SMTP проверку для невалидных email - экономим время
        message += "\nSMTP: проверка пропущена (невалидный синтаксис)"

    # 4. Response
    return EmailResponse(
        is_syntactically_valid=syntax_ok,
        suggestion=suggestion,
        mailbox_exists=mailbox_exists,
        message=message.strip(),
    )