# backend/app/core/config.py

import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    PROJECT_NAME: str = "My Project"
    DATABASE_URL: str = os.getenv("DATABASE_URL", "mysql+pymysql://your_user:your_password@db/your_database")
    SECRET_KEY: str = os.getenv("SECRET_KEY", "your_secret_key")
    # Добавьте другие настройки по необходимости

    class Config:
        case_sensitive = True

settings = Settings()
