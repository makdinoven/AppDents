# импортируем «настоящий» Celery‑app, чтобы он создался
from .celery import celery as celery_app  # noqa: F401
