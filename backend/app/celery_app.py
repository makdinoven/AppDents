from celery import Celery
from dotenv import load_dotenv
import os

load_dotenv()

celery = Celery(
    "dent_backend",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

#    ↓↓↓  вместо include используем autodiscover
celery.autodiscover_tasks(
    ["app"],          # ←  это ВАШ корневой пакет
    related_name="tasks",  # default, можно не писать
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_annotations={
        "app.tasks.preview_tasks.generate_preview": {"rate_limit": "40/m"},
    },
    beat_schedule={
        "special-offers-every-hour": {
            "task": "app.tasks.special_offers.process_special_offers",
            "schedule": 3600,
        },
    },
)
