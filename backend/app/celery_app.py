from celery import Celery
from dotenv import load_dotenv
import os

from kombu import Queue

load_dotenv()

celery = Celery(
    "dent_backend",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
)

#    ↓↓↓  вместо include используем autodiscover
celery.autodiscover_tasks(
    ["app"],
    related_name="tasks",
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_annotations={
        "app.tasks.preview_tasks.generate_preview": {"rate_limit": "350/m"},
        "app.tasks.process_faststart_video": {"rate_limit": "15/m"},
        "app.tasks.ensure_faststart":    {"rate_limit": "15/m"},
    },
    beat_schedule={
        "special-offers-every-hour": {
            "task": "app.tasks.special_offers.process_special_offers",
            "schedule": 3600,
            "options": {"queue": "special"},
        },
        "replace-storage-links-every-3-hours": {
                    "task": "app.tasks.special_offers.replace_storage_links",
                    "schedule": 10800,              # 3 ч * 3600 с
                    # crontab(minute=0, hour='*/3')  # <- альтернативный вариант
                    "options": {"queue": "special"},
                },
        "ensure_faststart": {
                    "task": "app.tasks.ensure_faststart",
                    "schedule": 10800,              # 3 ч * 3600 с
                    # crontab(minute=0, hour='*/3')  # <- альтернативный вариант
                    "options": {"queue": "special"},
                },
    },
)

celery.conf.task_queues = (
    Queue("default"),         # превью, e-mails и т.д.
    Queue("special"),         # спец-предложения
)

celery.conf.task_routes = {
    "app.tasks.preview_tasks.*": {"queue": "default"},
    "app.tasks.special_offers.process_special_offers": {"queue": "special"},
    "app.tasks.storage_links.replace_storage_links": {"queue": "special"},
    "app.tasks.process_faststart_video": {"queue": "special"},
    "app.tasks.ensure_faststart": {"queue": "special"},
}
