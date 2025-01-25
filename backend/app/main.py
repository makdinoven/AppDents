# backend/app/main.py

from fastapi import FastAPI
from app.api import test
from app.core.config import settings
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(
    title=settings.PROJECT_NAME,
    description="Описание вашего проекта",
    version="1.0.0",
)

# Настройка CORS
origins = [
    "http://localhost",
    "http://localhost:3000",
    "http://your_domain.com",  # Замените на ваш домен
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Разрешенные источники
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Подключение маршрутов
app.include_router(test.router, tags=["Test"])
