import os
from celery import Celery
from dotenv import load_dotenv

load_dotenv()  # .env → os.environ

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1")

celery = Celery(
    "dent_backend",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "app.tasks.preview_tasks",      # генерация превью
        "app.tasks.special_offers",     # спец-офферы ← добавили
    ],
)

# базовые настройки Celery
celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_annotations={
        # ограничиваем скорость тяжёлого таска
        "app.tasks.preview_tasks.generate_preview": {"rate_limit": "40/m"},
    },
)

# расписание Beat
celery.conf.beat_schedule = {
    "special-offers-every-hour": {
        "task": "app.tasks.special_offers.process_special_offers",
        "schedule": 3600,   # сек
    },
}
