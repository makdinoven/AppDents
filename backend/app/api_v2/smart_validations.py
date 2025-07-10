import asyncio
import random
import smtplib
import socket
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
def domain_has_mx(domain: str, timeout: float = 1.5) -> bool:
    """True ⇢ домен публикует MX, иначе False."""
    try:
        return bool(dns.resolver.resolve(domain, "MX", lifetime=timeout))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


def _smtp_probe_sync(email: str, timeout: float = SMTP_TIMEOUT) -> Tuple[bool, str]:
    """Sync SMTP `RCPT TO` check. Returns (exists?, message)."""
    local, _, domain = email.partition("@")
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx_host = str(sorted(mx_records, key=lambda r: r.preference)[0].exchange).rstrip(".")
    except Exception as exc:  # pragma: no cover
        return False, f"MX resolve failed: {exc}"  # Shouldn't happen — checked earlier

    from_addr = f"probe-{random.randint(0, 1_000_000)}@example.com"

    try:
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.helo("example.com")
        server.mail(from_addr)
        code, resp = server.rcpt(email)

        # Detect catch‑all: ask random address; if it also 250 → uncertain
        rand_local = "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        code_rand, _ = server.rcpt(f"{rand_local}@{domain}")
        server.quit()

        if code_rand == 250:
            return False, "Server is catch‑all; address existence uncertain"

        if code == 250:
            return True, "SMTP 250 OK — mailbox exists"
        else:
            return False, f"SMTP {code} {resp.decode(errors='ignore')}"

    except (socket.timeout, smtplib.SMTPServerDisconnected, smtplib.SMTPConnectError) as exc:
        return False, f"SMTP error/timeout: {exc}"  # treat as invalid to be safe


async def smtp_probe(email: str) -> Tuple[bool, str]:
    """Run sync probe in threadpool so we don't block the event loop."""
    return await asyncio.to_thread(_smtp_probe_sync, email)


def make_suggestion(email: str) -> str | None:
    local, _, domain = email.partition("@")
    match = get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.8)
    if match and match[0] != domain:
        return f"{local}@{match[0]}"
    return None


# ───────────────────────────── Endpoint ──────────────────────────── #
@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(payload: EmailRequest):
    email = payload.email
    domain = email.split("@", 1)[1]

    if not domain_has_mx(domain):
        return EmailValidationResponse(
            valid=False,
            reason="MX record not found; domain likely invalid or mis‑typed",
            suggestion=make_suggestion(email),
        )

    # SMTP probe (can take ~1 s). You might want to cache the result.
    exists, smtp_msg = await smtp_probe(email)

    if not exists:
        return EmailValidationResponse(
            valid=False,
            reason=smtp_msg,
            suggestion=make_suggestion(email),
        )

    return EmailValidationResponse(valid=True)
