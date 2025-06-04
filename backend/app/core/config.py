
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

    EMAIL_HOST: str
    EMAIL_PORT: int = 25
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_SENDER: str

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

    class Config:
        env_file = ".env"


# Создаём единственный объект настроек, который будем импортировать
settings = Settings()
