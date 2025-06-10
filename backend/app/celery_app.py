"""
Единый Celery-инстанс для всего проекта.
Импортируйте как:  from backend.celery_app import celery
(замените 'backend' на фактическое имя корневого пакета).
"""
import os
from celery import Celery
from dotenv import load_dotenv

# подгружаем .env ещё до создания Celery, чтобы переменные были в os.environ
load_dotenv()

# адрес брокера и бэкенда можно менять в .env
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery(
    "dent_backend",                      # любое название
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "backend.tasks.preview_tasks",   # пути до ваших модулей с тасками
        # добавляйте другие tasks-модули сюда
    ],
)

# Настройки по умолчанию (можно дополнять)
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
)
