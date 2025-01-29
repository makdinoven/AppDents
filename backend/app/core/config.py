
import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    DB_USER: str = "admin"
    DB_PASSWORD: str = "mysqlpassword"
    DB_HOST: str = "mysql"
    DB_PORT: str = "3306"
    DB_NAME: str = "dentsdatabase"

    SECRET_KEY: str = "CHANGE_ME"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    class Config:
        env_file = None


# Создаём единственный объект настроек, который будем импортировать
settings = Settings()
