import hashlib, logging, re, uuid, requests
from datetime import datetime
from ..core.config import settings

REQUEST_TIMEOUT = 3
_log = logging.getLogger(__name__)

# ────────────────────────────── hash helpers
_sha256 = lambda s: hashlib.sha256(s.strip().lower().encode()).hexdigest()


def _hash_email(email: str) -> str:
    """Нормализуем e-mail и хэшируем его (SHA-256 → hexdigest)."""
    return hashlib.sha256(email.strip().lower().encode("utf-8")).hexdigest()


def _hash_plain(value: str) -> str:
    """Trim → lower → SHA-256. Для first_name / last_name и др. персональных полей."""
    return hashlib.sha256(value.strip().lower().encode("utf-8")).hexdigest()

def _user_data(email: str,
               client_ip: str,
               user_agent: str,
               fbp: str | None = None,
               fbc: str | None = None) -> dict:
    ud = {
        "em": [_sha256(email)],
        "client_ip_address": None if client_ip == "0.0.0.0" else client_ip,
        "client_user_agent": user_agent or None,
    }
    if fbp:
        ud["fbp"] = fbp
    if fbc:
        ud["fbc"] = fbc
    return ud

def _build_fb_event(
    *,
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    event_time: int,
    event_id: str,
    event_name: str = "Purchase",
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> dict:
    """
    Формирует payload для Facebook Conversions API.
    ``event_name`` — "Purchase" или "Donate".
    """

    if not email:
        raise ValueError("Empty email for Facebook event")

    # ---------- 1. user_data ----------
    user_data: dict = {
        "em": [_hash_email(email)],
        "client_ip_address": None if client_ip == "0.0.0.0" else client_ip,
        "client_user_agent": user_agent or None,
    }

    # дополнительные Facebook-идентификаторы
    if external_id:
        user_data["external_id"] = [external_id]
    if fbp:
        user_data["fbp"] = fbp
    if fbc:
        user_data["fbc"] = fbc

    # персональные поля
    if first_name:
        user_data["fn"] = [_hash_plain(first_name)]
    if last_name and last_name != first_name:
        user_data["ln"] = [_hash_plain(last_name)]

    # ---------- 2. финальный event ----------
    event = {
        "data": [
            {
                "event_name": event_name,          # <-- главное отличие
                "event_time": event_time,
                "event_id": event_id,
                "user_data": user_data,
                "custom_data": {
                    "currency": currency,
                    "value": amount,
                    "content_ids": [str(cid) for cid in course_ids],
                    "content_type": "course",
                },
            }
        ]
    }

    logging.info(
        "FB event built → %s | %s | amount=%s %s | courses=%s",
        email, event_name, amount, currency.upper(), course_ids,
    )
    return event

def send_facebook_events(
    *,
    region: str,
    event_id: str,
    email: str,
    amount: float,
    currency: str,
    course_ids: list[int],
    client_ip: str,
    user_agent: str,
    event_time: int,
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
    last_name: str | None = None,
) -> None:
    """
    Отправляет события Purchase и Donate в Facebook Conversions API.

    ─ Purchase ≥ 2 USD → два глобальных, LearnWorlds и регион-специфичный пиксели
    ─ Purchase < 2 USD → **только микропиксель**
    ─ Donate → всегда отдельный donation-пиксель
    """
    if not event_id:
        raise ValueError("event_id is required for FB deduplication")

    # ---------- 1. payload'ы ----------
    purchase_payload = _build_fb_event(
        event_name="Purchase",
        email=email,
        amount=amount,
        currency=currency,
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        event_time=event_time,
        event_id=event_id,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
        last_name=last_name,
    )
    donate_payload = _build_fb_event(
        event_name="Donate",
        email=email,
        amount=amount,
        currency=currency,
        course_ids=course_ids,
        client_ip=client_ip,
        user_agent=user_agent,
        event_time=event_time,
        event_id=event_id,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
        last_name=last_name,
    )

    # ---------- 2. выбор Purchase-пикселей ----------
    micro_purchase = (
        amount < 2
        and settings.FACEBOOK_PIXEL_ID_1_DOLLAR
        and settings.FACEBOOK_ACCESS_TOKEN_1_DOLLAR
    )

    if micro_purchase:
        # < 2 USD — отправляем только в микропиксель
        pixels_purchase: list[dict] = [{
            "id":    settings.FACEBOOK_PIXEL_ID_1_DOLLAR,
            "token": settings.FACEBOOK_ACCESS_TOKEN_1_DOLLAR,
        }]
        _log.info("Using MICRO FB pixel only (amount=%.2f %s)", amount, currency.upper())
    else:
        # ≥ 2 USD — стандартный набор
        pixels_purchase: list[dict] = [
            {"id": settings.FACEBOOK_PIXEL_ID,             "token": settings.FACEBOOK_ACCESS_TOKEN},
            {"id": settings.FACEBOOK_PIXEL_ID_LEARNWORLDS, "token": settings.FACEBOOK_ACCESS_TOKEN_LEARNWORLDS},
            {"id": settings.FACEBOOK_PIXEL_ID_NEW_2, "token": settings.FACEBOOK_ACCESS_TOKEN_NEW_2},

        ]

        # ─ регион-специфичный пиксель (если сконфигурирован) ─
        REGIONAL_PURCHASE_PIXELS: dict[str, dict] = {
            "RU": {"id": settings.FACEBOOK_PIXEL_ID_RU, "token": settings.FACEBOOK_ACCESS_TOKEN_RU},
            "EN": {"id": settings.FACEBOOK_PIXEL_ID_EN, "token": settings.FACEBOOK_ACCESS_TOKEN_EN},
            "ES": {"id": settings.FACEBOOK_PIXEL_ID_ES, "token": settings.FACEBOOK_ACCESS_TOKEN_ES},
            "IT": {"id": settings.FACEBOOK_PIXEL_ID_IT, "token": settings.FACEBOOK_ACCESS_TOKEN_IT},
        }
        region_key = (region or "").upper()
        regional_pixel = REGIONAL_PURCHASE_PIXELS.get(region_key)
        if regional_pixel and regional_pixel["id"] and regional_pixel["token"]:
            pixels_purchase.append(regional_pixel)
        else:
            _log.warning("Regional FB pixel is not configured for region=%s", region_key)

    # ---------- 3. Donation-пиксель ----------
    pixel_donation = {
        "id": settings.FACEBOOK_PIXEL_ID_DONATION,
        "token": settings.FACEBOOK_ACCESS_TOKEN_DONATION,
    }

    # ---------- 4. отправка ----------
    def _post(pixel: dict, payload: dict, tag: str) -> None:
        try:
            resp = requests.post(
                f"https://graph.facebook.com/v18.0/{pixel['id']}/events",
                params={"access_token": pixel["token"]},
                json=payload,
                timeout=3,
            )
            if resp.status_code == 200:
                _log.info("FB %s Pixel %s — OK (email=%s)", tag, pixel['id'], email)
            else:
                _log.error("FB %s Pixel %s — %s %s", tag, pixel['id'],
                           resp.status_code, resp.text)
        except Exception as exc:
            _log.error("FB %s Pixel %s failed: %s", tag, pixel['id'], exc, exc_info=True)

    # Purchase
    for p in pixels_purchase:
        _post(p, purchase_payload, "Purchase")

    # Donate
    _post(pixel_donation, donate_payload, "Donate")


def _build_fb_registration_event(
    *,
    email: str,
    client_ip: str,
    user_agent: str,
    event_id: str,
    event_time: int,
    region: str,
    event_source_url: str | None = None,
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
) -> dict:

    user_data = {
        "em": [_hash_email(email)],
        "client_ip_address": None if client_ip in ("0.0.0.0", "") else client_ip,
        "client_user_agent": user_agent or None,
    }
    if external_id: user_data["external_id"] = [external_id]
    if first_name:  user_data["fn"] = [_hash_plain(first_name)]
    if fbp:         user_data["fbp"] = fbp
    if fbc:         user_data["fbc"] = fbc

    return {
        "data": [{
            "event_name": "CompleteRegistration",
            "event_time": event_time,
            "event_id": event_id,
            "action_source": "website",
            "event_source_url": event_source_url,
            "user_data": user_data,
            "custom_data": { "currency": "usd", "value": 0.0 },
        }]
    }


def send_registration_event(
    *,
    email: str,
    region: str,
    client_ip: str,
    user_agent: str,
    event_id: str,
    event_source_url: str | None = None,
    external_id: str | None = None,
    fbp: str | None = None,
    fbc: str | None = None,
    first_name: str | None = None,
):
    event_time = int(datetime.utcnow().timestamp())

    payload = _build_fb_registration_event(
        email=email,
        client_ip=client_ip,
        user_agent=user_agent,
        event_id=event_id,
        event_time=event_time,
        region=region,
        event_source_url=event_source_url,
        external_id=external_id,
        fbp=fbp,
        fbc=fbc,
        first_name=first_name,
    )

    PIXELS = {
        "RU": (settings.FACEBOOK_PIXEL_ID_RU, settings.FACEBOOK_ACCESS_TOKEN_RU),
        "EN": (settings.FACEBOOK_PIXEL_ID_EN, settings.FACEBOOK_ACCESS_TOKEN_EN),
        "ES": (settings.FACEBOOK_PIXEL_ID_ES, settings.FACEBOOK_ACCESS_TOKEN_ES),
        "IT": (settings.FACEBOOK_PIXEL_ID_IT, settings.FACEBOOK_ACCESS_TOKEN_IT),
    }
    pixel_id, token = PIXELS.get(region.upper(), PIXELS["EN"])

    resp = requests.post(
        f"https://graph.facebook.com/v18.0/{pixel_id}/events",
        params={"access_token": token},
        json=payload,
        timeout=3,
    )
    logging.info("FB registration → %s %s", resp.status_code, resp.text[:200])