import asyncio
import random
import smtplib
import socket
import ssl
import string
from functools import lru_cache
from difflib import get_close_matches
from typing import Tuple, Literal

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
    email: EmailStr  # синтаксис + punycode/IDN проверка (ASCII‑only)


class EmailValidationResponse(BaseModel):
    exists: bool
    reason: str | None = None


# ────────────────────────── Helper functions ─────────────────────── #
@lru_cache(maxsize=4096)
def domain_has_mx(domain: str, timeout: float = 2.0) -> bool:
    try:
        return bool(dns.resolver.resolve(domain, "MX", lifetime=timeout))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


def _contains_non_ascii(s: str) -> bool:
    return any(ord(ch) > 127 for ch in s)


# –––––––––––––––––––––––– SMTP probe –––––––––––––––––––––––––––– #

def _smtp_probe_sync(email: str, timeout: float = SMTP_TIMEOUT) -> Tuple[bool, str]:
    """Return (exists, reason).  exists=True ⇢ сервер подтвердил ящик однозначно."""

    if _contains_non_ascii(email):
        return False, "SMTPUTF8 not supported by probe"

    local, _, domain = email.partition("@")
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx_host = str(min(mx_records, key=lambda r: r.preference).exchange).rstrip(".")
    except Exception as exc:
        return False, f"MX resolve failed: {exc}"

    from_addr = f"probe@{domain}"
    try:
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.ehlo("validator")
        if server.has_extn("STARTTLS"):
            server.starttls(context=ssl.create_default_context())
            server.ehlo("validator")

        server.mail(from_addr)
        code_target, resp_target = server.rcpt(email)

        # Проверяем случайный ящик для catch‑all
        rand_local = "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        code_rand, _ = server.rcpt(f"{rand_local}@{domain}")
        server.quit()

        # Логика: подтверждаем существование, только если целевой =250 и рандом !=250
        if 200 <= code_target < 300 and code_rand not in range(200, 300):
            return True, "SMTP 250 OK and not catch‑all"

        # целевой не 2xx или домен catch‑all ⇒ считаем несуществующим
        if code_target in {550, 551, 553}:
            return False, f"SMTP {code_target} {resp_target.decode(errors='ignore')}"
        return False, "Server did not unequivocally confirm mailbox (catch‑all or ambiguous)"

    except (
        socket.timeout,
        smtplib.SMTPConnectError,
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPHeloError,
        smtplib.SMTPException,
    ) as exc:
        return False, f"SMTP probe error: {exc}"


async def smtp_probe(email: str) -> Tuple[bool, str]:
    return await asyncio.to_thread(_smtp_probe_sync, email)


# ───────────────────────────── Endpoint ──────────────────────────── #
@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(payload: EmailRequest):
    email = payload.email
    domain = email.split("@", 1)[1]

    if not domain_has_mx(domain):
        return EmailValidationResponse(exists=False, reason="No MX records found")

    exists, msg = await smtp_probe(email)
    return EmailValidationResponse(exists=exists, reason=None if exists else msg)