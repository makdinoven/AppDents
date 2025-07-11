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
    email: EmailStr  # базовая RFC‑проверка делает Pydantic



class EmailValidationResponse(BaseModel):
    status: Literal["valid", "invalid", "unknown"]
    deliverable: bool
    reason: str | None = None
    suggestion: str | None = None


# ───────────────────────────── Helper functions ─────────────────────────── #
@lru_cache(maxsize=4096)
def domain_has_mx(domain: str, timeout: float = 2.0) -> bool:
    try:
        return bool(dns.resolver.resolve(domain, "MX", lifetime=timeout))
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


def _contains_non_ascii(s: str) -> bool:
    return any(ord(ch) > 127 for ch in s)


# –––––––––––––––––––––––– SMTP probe –––––––––––––––––––––––––––– #

def _smtp_probe_sync(email: str, timeout: float = SMTP_TIMEOUT) -> Tuple[str, str]:
    """Return (status, msg) where status ∈ {valid, invalid, unknown}."""

    if _contains_non_ascii(email):
        return "unknown", "SMTPUTF8 not supported by probe"

    local, _, domain = email.partition("@")
    try:
        mx_records = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        mx_host = str(min(mx_records, key=lambda r: r.preference).exchange).rstrip(".")
    except Exception as exc:
        return "invalid", f"MX resolve failed: {exc}"

    from_addr = f"probe@{domain}"
    try:
        server = smtplib.SMTP(mx_host, timeout=timeout)
        server.ehlo("validator")
        if server.has_extn("STARTTLS"):
            server.starttls(context=ssl.create_default_context())
            server.ehlo("validator")

        server.mail(from_addr)
        code, resp = server.rcpt(email)

        # Catch‑all detection
        rand_local = "_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=24))
        code_rand, _ = server.rcpt(f"{rand_local}@{domain}")
        server.quit()

        if code_rand == 250:
            return "unknown", "Domain is catch‑all; mailbox existence not verifiable"

        if 200 <= code < 300:
            return "valid", f"SMTP {code} OK — mailbox accepts RCPT"
        if code in {550, 551, 553}:
            return "invalid", f"SMTP {code} {resp.decode(errors='ignore')}"
        # 4xx / ambiguous → unknown
        return "unknown", f"SMTP {code} {resp.decode(errors='ignore')}"

    except (
        socket.timeout,
        smtplib.SMTPConnectError,
        smtplib.SMTPServerDisconnected,
        smtplib.SMTPHeloError,
    ) as exc:
        return "unknown", f"SMTP probe error: {exc}"


async def smtp_probe(email: str) -> Tuple[str, str]:
    return await asyncio.to_thread(_smtp_probe_sync, email)


# ––––––––––––––––––––– Suggestion –––––––––––––––––––––––––––––––– #

def make_suggestion(email: str) -> str | None:
    local, _, domain = email.partition("@")
    match = get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.8)
    return f"{local}@{match[0]}" if match and match[0] != domain else None


# ───────────────────────────── Endpoint ──────────────────────────── #
@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(payload: EmailRequest):
    email = payload.email
    strict = payload.strict
    domain = email.split("@", 1)[1]

    if not domain_has_mx(domain):
        return EmailValidationResponse(
            status="invalid",
            deliverable=False,
            reason="MX record not found; domain likely invalid",
            suggestion=make_suggestion(email),
        )

    status, msg = await smtp_probe(email)

    if strict and status == "unknown":
        status = "invalid"  # promote unknown → invalid under strict policy

    return EmailValidationResponse(
        status=status,
        deliverable=status == "valid",
        reason=None if status == "valid" else msg,
        suggestion=None if status == "valid" else make_suggestion(email),
    )
