from celery import Celery
from dotenv import load_dotenv
import os

from kombu import Queue, Exchange

load_dotenv()

celery = Celery(
    "dent_backend",
    broker=os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0"),
    backend=os.getenv("CELERY_RESULT_BACKEND", "redis://redis:6379/1"),
    include=[
            "app.tasks.fast_start",
            "app.tasks.preview_tasks",
            "app.tasks.special_offers",
            "app.tasks.storage_links",
            "app.tasks.ensure_hls",
            "app.tasks.abandoned_checkouts",
            "app.tasks.clip_tasks"
        ],
)

celery.conf.update(
    task_default_queue="default",
    task_default_exchange="celery",
    task_default_exchange_type="direct",
    task_default_routing_key="celery",
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
        "app.tasks.preview_tasks.generate_preview": {"rate_limit": "800/m"},
        "app.tasks.process_faststart_video": {"rate_limit": "20/m"},
        "app.tasks.ensure_faststart":    {"rate_limit": "20/m"},
        "app.tasks.process_hls_video": {"rate_limit": "15/m"},
        "app.tasks.ensure_hls":        {"rate_limit": "5/m"},
        "app.tasks.abandoned_checkouts.process_abandoned_checkouts": {"rate_limit": "50/h"},
    },
    beat_schedule={
        "special-offers-every-hour": {
            "task": "app.tasks.special_offers.process_special_offers",
            "schedule": 3600,
            "options": {"queue": "special"},
        },
        "replace-storage-links-every-1-hours": {
                    "task": "app.tasks.storage_links.replace_storage_links",
                    "schedule": 3600,              # 3 ч * 3600 с
                    "options": {"queue": "special"},
                },
        "ensure_faststart": {
                    "task": "app.tasks.ensure_faststart",
                    "schedule": 10800,              # 3 ч * 3600 с
                    "options": {"queue": "special"},
                },
        "ensure_hls": {
                    "task": "app.tasks.ensure_hls",
                    "schedule": 1800,
                    "options": {"queue": "special"},
                },
        "recount-hls-daily": {
                "task": "app.tasks.ensure_hls.recount_hls_counters",
                "schedule": 86400,      # 1 раз в сутки
                "options": {"queue": "special"},
            },
        "process-abandoned-checkouts-each-60m": {
                    "task": "app.tasks.abandoned_checkouts.process_abandoned_checkouts",
                    "schedule": 3600,           # каждый час
                    "options": {"queue": "special"},
                },
    },
)

default_exc = Exchange("celery", type="direct")

celery.conf.task_queues = (
    Queue("default",      default_exc, routing_key="celery"),
    Queue("special",      default_exc, routing_key="special"),
    Queue("special_hls",  default_exc, routing_key="special_hls"),
)

celery.conf.task_routes = {
    "app.tasks.preview_tasks.*": {"queue": "default"},
    "app.tasks.special_offers.process_special_offers": {"queue": "special"},
    "app.tasks.storage_links.replace_storage_links": {"queue": "special"},
    "app.tasks.process_faststart_video": {"queue": "special"},
    "app.tasks.ensure_faststart": {"queue": "special"},
    "app.tasks.ensure_hls.recount_hls_counters": {"queue": "special"},
    "app.tasks.clip_tasks.*": {"queue": "special"}
}
