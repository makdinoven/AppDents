
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    APP_URL: str

    DB_USER: str
    DB_PASSWORD: str
    DB_HOST: str
    DB_PORT: str
    DB_NAME: str

    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    STRIPE_SECRET_KEY_RU: str
    STRIPE_PUBLISHABLE_KEY_RU: str
    STRIPE_WEBHOOK_SECRET_RU: str

    # Ключи для EN
    STRIPE_SECRET_KEY_EN: str
    STRIPE_PUBLISHABLE_KEY_EN: str
    STRIPE_WEBHOOK_SECRET_EN: str

    # Ключи для ES
    STRIPE_SECRET_KEY_ES: str
    STRIPE_PUBLISHABLE_KEY_ES: str
    STRIPE_WEBHOOK_SECRET_ES: str

    STRIPE_PMC_RU: str
    STRIPE_PMC_ES: str
    STRIPE_PMC_EN: str

    EMAIL_HOST: str = ""
    EMAIL_PORT: int = 25
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_SENDER: str
    # Маркетинговые/рекламные письма (можно отправлять с отдельного домена/поддомена)
    EMAIL_MARKETING_SENDER: str = ""

    # Mailgun
    MAILGUN_API_KEY: str = ""
    MAILGUN_DOMAIN: str = ""
    MAILGUN_MARKETING_DOMAIN: str = ""
    MAILGUN_REGION: str = "EU"
    MAILGUN_WEBHOOK_SIGNING_KEY: str = ""  # Webhook signing key from Mailgun dashboard

    # Facebook
    FACEBOOK_PIXEL_ID : str
    FACEBOOK_ACCESS_TOKEN : str

    FACEBOOK_PIXEL_ID_LEARNWORLDS: str
    FACEBOOK_ACCESS_TOKEN_LEARNWORLDS: str

    FACEBOOK_PIXEL_ID_DONATION: str
    FACEBOOK_ACCESS_TOKEN_DONATION: str

    # Facebook Pixels — региональные «Purchase»
    FACEBOOK_PIXEL_ID_RU: str
    FACEBOOK_ACCESS_TOKEN_RU: str
    FACEBOOK_PIXEL_ID_EN: str
    FACEBOOK_ACCESS_TOKEN_EN: str
    FACEBOOK_PIXEL_ID_ES: str
    FACEBOOK_ACCESS_TOKEN_ES: str
    FACEBOOK_PIXEL_ID_IT: str
    FACEBOOK_ACCESS_TOKEN_IT: str
    FACEBOOK_PIXEL_ID_1_DOLLAR: str
    FACEBOOK_ACCESS_TOKEN_1_DOLLAR: str

    FACEBOOK_ACCESS_TOKEN_NEW_4:str
    FACEBOOK_PIXEL_ID_NEW_4: str
    FACEBOOK_ACCESS_TOKEN_NEW_5: str
    FACEBOOK_PIXEL_ID_NEW_5: str
    FACEBOOK_ACCESS_TOKEN_NEW_11: str
    FACEBOOK_PIXEL_ID_NEW_11: str
    FACEBOOK_ACCESS_TOKEN_NEW_10: str
    FACEBOOK_PIXEL_ID_NEW_10: str
    FACEBOOK_ACCESS_TOKEN_NEW_12: str
    FACEBOOK_PIXEL_ID_NEW_12: str
    FACEBOOK_ACCESS_TOKEN_NEW_13: str
    FACEBOOK_PIXEL_ID_NEW_13: str

    # Med-G Facebook Pixels
    PROJECT_BRAND: str = "DENTS"  # DENTS или MEDG
    FACEBOOK_PIXEL_ID_MEDG_GENERAL: str = ""
    FACEBOOK_ACCESS_TOKEN_MEDG_GENERAL: str = ""
    FACEBOOK_PIXEL_ID_MEDG_COSMETOLOGY: str = ""
    FACEBOOK_ACCESS_TOKEN_MEDG_COSMETOLOGY: str = ""

    # === NY2026 campaign tuning (Celery beat) ===
    # Уменьшайте частоту тиков, если CPU/DB нагружены.
    # Сама отправка идёт батчами внутри тика.
    NY2026_TICK_SECONDS: int = 200
    NY2026_MAX_PER_RUN: int = 10

    # BookAI / Placid
    BOOKAI_BASE_URL: str = "https://bookai.dent-s.com/api"
    PLACID_API_KEY: str
    PLACID_BASE_URL: str = "https://api.placid.app/api/rest"

    # Telegram Bot
    TELEGRAM_BOT_TOKEN: str = ""
    TELEGRAM_CHAT_ID: str = ""  # Для заявок на курсы
    TELEGRAM_MONITORING_CHAT_ID: str = ""  # Для ошибок и мониторинга


    class Config:
        env_file = ".env"


# Создаём единственный объект настроек, который будем импортировать
settings = Settings()
