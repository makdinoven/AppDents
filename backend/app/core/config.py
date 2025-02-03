

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # MySQL / БД
    MYSQL_ROOT_PASSWORD: str
    MYSQL_USER: str
    MYSQL_PASSWORD: str
    MYSQL_DATABASE: str
    DB_HOST: str
    DB_PORT: str
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str

    # Настройки почтового сервера:
    EMAIL_HOST: str = "hostch02.fornex.host"
    EMAIL_PORT: int = 465
    EMAIL_USERNAME: str = "info@d-is.org"
    EMAIL_PASSWORD: str = "Iveter88=*"
    EMAIL_SENDER: str = "info@d-is.org"

    # JWT
    SECRET_KEY: str = "DEV_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    STRIPE_SECRET_KEY: str
    STRIPE_PUBLISHABLE_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    class Config:
        # Настраиваем pydantic для чтения файла .env
        # Или оставляем None, если полагаемся только на Docker окружение
        env_file = ".env"
        env_file_encoding = "utf-8"

# Инициализируем единый объект настроек, который будем импортировать в коде
settings = Settings()
