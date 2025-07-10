import asyncio
import random
import smtplib
import socket
import ssl
import string
from functools import lru_cache
from difflib import get_close_matches
from typing import Tuple

import dns.resolver  # type: ignore
from fastapi import APIRouter
from pydantic import BaseModel, EmailStr

router = APIRouter()

# A small list of popular domains to catch the 90 % самых частых опечаток.
POPULAR_DOMAINS = [
    "gmail.com",
    "yahoo.com",
    "outlook.com",
    "hotmail.com",
    "hotmail.co.uk"
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
    "live.com",
    "abv.bg",
    "hotmail.it",
    "yahoo.fr",
    "wp.pl",
    "libero.it",
    "ymail.com",
]
SMTP_TIMEOUT = 5
# ──────────────────────────────── Schemas ──────────────────────────────── #
class EmailRequest(BaseModel):
    email: EmailStr  # базовая RFC‑проверка делает Pydantic


class EmailValidationResponse(BaseModel):
    valid: bool
    reason: str | None = None
    suggestion: str | None = None


# ───────────────────────────── Helper functions ─────────────────────────── #
@lru_cache(maxsize=1024)
def domain_has_mx(domain: str, timeout: float = 2.0) -> bool:
    try:
        return bool(dns.resolver.resolve(domain, "MX", lifetime=timeout))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


def _contains_non_ascii(s: str) -> bool:
    return any(ord(ch) > 127 for ch in s)


# ––––––––––––––––––––––––– SMTP probe –––––––––––––––––––––––––––– #

def _smtp_probe_sync(email: str, timeout: float = SMTP_TIMEOUT) -> Tuple[bool, str]:
    """Low‑level SMTP `RCPT TO` validation.

    Returns:
        exists (bool) — e‑mail точно существует (True) / точно не существует (False)
        message (str) — подробное пояснение
    """

    if _contains_non_ascii(email):
        return False, "SMTPUTF8 (non‑ASCII) not supported by probe"

    local, _, domain = email.partition("@")
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx_host = str(min(mx_records, key=lambda r: r.preference).exchange).rstrip(".")
    except Exception as exc:
        return False, f"MX resolve failed: {exc}"

    # Use probe@<domain> to avoid ‘Sender address rejected’
    from_addr = f"probe@{domain}"

    try:
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.ehlo("validator")
        if server.has_extn("STARTTLS"):
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo("validator")

        server.mail(from_addr)
        code, resp = server.rcpt(email)

        # Catch‑all detection
        rand_local = "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        code_rand, _ = server.rcpt(f"{rand_local}@{domain}")
        server.quit()

        if code_rand == 250:
            return False, "Domain is catch‑all; address existence uncertain"

        # Positive case
        if 200 <= code < 300:
            return True, f"SMTP {code} OK — mailbox accepts RCPT"

        # Definitive negative (non‑existent)
        if code in {550, 551, 553}:
            return False, f"SMTP {code} {resp.decode(errors='ignore')}"

        # Temporary / ambiguous – treat as **valid** to avoid false‑negatives
        return True, f"SMTP {code} {resp.decode(errors='ignore')} (treated as valid)"

    except (
        socket.timeout,
        smtplib.SMTPConnectError,
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPHeloError,
    ) as exc:
        # Network or handshake problems → let’s be permissive
        return True, f"SMTP probe error: {exc} (treated as valid)"


async def smtp_probe(email: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_smtp_probe_sync, email)


# ––––––––––––––––––––––––– Suggestion –––––––––––––––––––––––––––– #

def make_suggestion(email: str) -> str | None:
    local, _, domain = email.partition("@")
    match = get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.8)
    return f"{local}@{match[0]}" if match and match[0] != domain else None


# ───────────────────────────── Endpoint ──────────────────────────── #
@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(payload: EmailRequest):
    email = payload.email
    domain = email.split("@", 1)[1]

    if not domain_has_mx(domain):
        return EmailValidationResponse(
            valid=False,
            reason="MX record not found; domain likely invalid",
            suggestion=make_suggestion(email),
        )

    exists, smtp_msg = await smtp_probe(email)

    return EmailValidationResponse(
        valid=exists,
        reason=None if exists else smtp_msg,
        suggestion=None if exists else make_suggestion(email),
    )
