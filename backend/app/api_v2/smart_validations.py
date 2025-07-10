from functools import lru_cache
from difflib import get_close_matches

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
    """Return **True only if the domain publishes at least one MX record**.

    Спецификация SMTP допускает fallback на A‑record, но большинство
    современных MTA требуют MX. Чтобы ловить опечатки (gmai.com и т.п.)
    надёжнее, считаем домен *непригодным*, если MX нет.
    """
    try:
        answers = dns.resolver.resolve(domain, "MX", lifetime=timeout)
        return bool(answers)
    except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN, dns.resolver.Timeout):
        return False


def make_suggestion(email: str) -> str | None:
    """If domain is a close typo of a popular domain, suggest a corrected e‑mail."""
    local, _, domain = email.partition("@")
    match = get_close_matches(domain, POPULAR_DOMAINS, n=1, cutoff=0.8)
    if match and match[0] != domain:
        return f"{local}@{match[0]}"
    return None


# ──────────────────────────────── Endpoint ──────────────────────────────── #
@router.post("/validate-email", response_model=EmailValidationResponse)
async def validate_email(payload: EmailRequest):
    email = payload.email
    domain = email.split("@", maxsplit=1)[1]

    if not domain_has_mx(domain):
        return EmailValidationResponse(
            valid=False,
            reason="MX record not found (domain likely invalid)",
            suggestion=make_suggestion(email),
        )

    # Place for optional SMTP‑ping / external API call → increase confidence.
    return EmailValidationResponse(valid=True)
