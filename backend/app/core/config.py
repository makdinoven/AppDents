# app/core/config.py

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # MySQL / БД
    MYSQL_ROOT_PASSWORD: str = "root"
    MYSQL_USER: str = "admin"
    MYSQL_PASSWORD: str = "mysqlpassword"
    MYSQL_DATABASE: str = "dentsdatabase"
    DB_HOST: str = "mysql"
    DB_PORT: str = "3306"
    DB_USER: str = "admin"
    DB_PASSWORD: str = "mysqlpassword"
    DB_NAME: str = "dentsdatabase"

    # JWT
    SECRET_KEY: str = "DEV_SUPER_SECRET"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        # Настраиваем pydantic для чтения файла .env
        # Или оставляем None, если полагаемся только на Docker окружение
        env_file = ".env"
        env_file_encoding = "utf-8"

# Инициализируем единый объект настроек, который будем импортировать в коде
settings = Settings()
