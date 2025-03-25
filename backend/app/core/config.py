
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
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
    EMAIL_PORT: int
    EMAIL_USERNAME: str = ""
    EMAIL_PASSWORD: str = ""
    EMAIL_SENDER: str = "no-reply@dent-s.com"

    class Config:
        env_file = ".env"


# Создаём единственный объект настроек, который будем импортировать
settings = Settings()
