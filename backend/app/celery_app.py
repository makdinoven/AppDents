from celery import Celery
from dotenv import load_dotenv
import os

from kombu import Queue, Exchange
from .core.config import settings

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
            "app.tasks.video_maintenance",
            "app.tasks.abandoned_checkouts",
            "app.tasks.book_previews",
            "app.tasks.book_formats",
            "app.tasks.book_covers",
            "app.tasks.creatives",
            "app.tasks.video_summary",
            "app.tasks.clip_tasks",
            "app.tasks.big_cart_reminder",
            "app.tasks.referral_campaign",
            "app.tasks.migrate_abandoned_to_leads",
            "app.tasks.ny2026_leads",
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
        "app.tasks.process_faststart_video": {"rate_limit": "80/m"},
        "app.tasks.ensure_faststart":    {"rate_limit": "50/m"},
        "app.tasks.process_hls_video": {"rate_limit": "15/m"},
        "app.tasks.ensure_hls":        {"rate_limit": "10/m"},
        "app.tasks.video_maintenance.tick": {"rate_limit": "12/m"},
        "app.tasks.video_maintenance.tick_db": {"rate_limit": "30/m"},
        # === Email tasks: суммарно 165 писем/час (55 + 55 + 55) ===
        "app.tasks.abandoned_checkouts.process_abandoned_checkouts": {"rate_limit": "200/h"},
        "app.tasks.big_cart_reminder.process_big_cart_reminders": {"rate_limit": "200/h"},
        "app.tasks.referral_campaign.send_referral_campaign_batch": {"rate_limit": "200/h"},
    },
    beat_schedule={
        "special-offers-every-hour": {
            "task": "app.tasks.special_offers.process_special_offers",
            "schedule": 3600,
            "options": {"queue": "special"},
        },
        # disabled: manual-only maintenance (опасно гонять массовую замену ссылок по расписанию)
        # "replace-storage-links-every-1-hours": {
        #     "task": "app.tasks.storage_links.replace_storage_links",
        #     "schedule": 3600,
        #     "options": {"queue": "special"},
        # },
        # NOTE: legacy video maintenance tasks disabled (replaced by video_maintenance pipeline)
        # "ensure_faststart": {
        #     "task": "app.tasks.ensure_faststart",
        #     "schedule": 10800,              # 3 ч * 3600 с
        #     "options": {"queue": "special"},
        # },
        # "ensure_hls": {
        #     "task": "app.tasks.ensure_hls",
        #     "schedule": 1800,
        #     "options": {"queue": "special"},
        # },
        # HLS legacy maintenance disabled вместе с ensure_hls, чтобы не было гонок
        # (новая video_maintenance сама валидирует/чинит HLS и alias)
        # "recount-hls-daily": {
        #     "task": "app.tasks.ensure_hls.recount_hls_counters",
        #     "schedule": 86400,      # 1 раз в сутки
        #     "options": {"queue": "special"},
        # },
        # "fix-hls-legacy-aliases-hourly": {
        #     "task": "app.tasks.ensure_hls.fix_missing_legacy_aliases",
        #     "schedule": 3600,       # каждый час
        #     "kwargs": {"limit": 500},
        #     "options": {"queue": "special"},
        # },

        # ВКЛЮЧИМ ПОСЛЕ РУЧНОГО ТЕСТА на 2-3 видео:
        # "video-maintenance": {
        #     "task": "app.tasks.video_maintenance.tick",
        #     "schedule": 600,  # каждые 10 минут (батч N видео за тик)
        #     "options": {"queue": "special"},
        # },
        # DB-driven tick: постоянная нагрузка без раздувания очереди:
        # - запускаем часто
        # - expires чуть меньше schedule, чтобы задачи “протухали”, если воркер занят
        # - внутри таски есть lock и max_runtime
        "video-maintenance-db-tick": {
            "task": "app.tasks.video_maintenance.tick_db",
            "schedule": 15,
            "options": {"queue": "special", "expires": 14},
        },
        # === Email tasks: каждый час, ~55 писем каждая = 165/час суммарно ===
        "process-abandoned-checkouts-hourly": {
            "task": "app.tasks.abandoned_checkouts.process_abandoned_checkouts",
            "schedule": 3600,
            "kwargs": {"batch_size": 55},
            "options": {"queue": "email"},
        },
        "process-big-cart-reminders-hourly": {
            "task": "app.tasks.big_cart_reminder.process_big_cart_reminders",
            "schedule": 3600,
            "options": {"queue": "email"},
        },
        "process-referrals-hourly": {
            "task": "app.tasks.referral_campaign.send_referral_campaign_batch",
            "schedule": 3600,
            "kwargs": {"max_per_run": 55},
            "options": {"queue": "email"},
        },
        # Ежедневный перенос «зависших» abandoned_checkouts → leads
        "migrate-abandoned-to-leads-daily": {
            "task": "app.tasks.migrate_abandoned_to_leads.migrate_abandoned_to_leads_daily",
            "schedule": 86400,
            "kwargs": {"batch_limit": 20000},
            "options": {"queue": "email"},
        },
    },
)

# NY2026 — акция только для Dent-S. На Med-G не запускаем тик вовсе, чтобы не было шума/лишних запросов к БД.
if (getattr(settings, "PROJECT_BRAND", "") or "").upper() == "DENTS":
    ny2026_tick_seconds = int(getattr(settings, "NY2026_TICK_SECONDS", 60) or 60)
    ny2026_max_per_run = int(getattr(settings, "NY2026_MAX_PER_RUN", 500) or 500)
    # expires делаем чуть меньше schedule, чтобы тик не копился в очереди, если воркер занят
    ny2026_expires = max(1, ny2026_tick_seconds - 1)
    celery.conf.beat_schedule["ny2026-leads-tick"] = {
        "task": "app.tasks.ny2026_leads.send_ny2026_tick",
        # Реже запускаем, но берём пачку (меньше overhead и CPU, лучше throughput)
        "schedule": ny2026_tick_seconds,
        "kwargs": {"max_per_run": ny2026_max_per_run},
        "options": {"queue": "email", "expires": ny2026_expires},
    }

celery.conf.update(
    task_track_started=True,
    task_ignore_result=False,
    result_expires=86400,
)

default_exc = Exchange("celery", type="direct")

celery.conf.task_queues = (
    Queue("default",      default_exc, routing_key="celery"),
    Queue("special_priority", default_exc, routing_key="special_priority"),
    Queue("special",      default_exc, routing_key="special"),
    Queue("special_hls",  default_exc, routing_key="special_hls"),
    Queue("book",         default_exc, routing_key="book"),
    Queue("email",        default_exc, routing_key="email"),
)

celery.conf.task_routes = {
    "app.tasks.preview_tasks.*": {"queue": "default"},
    "app.tasks.special_offers.process_special_offers": {"queue": "special"},
    # storage_links.replace_storage_links — оставляем роутинг на special,
    # если вдруг вызовете вручную через apply_async
    "app.tasks.storage_links.replace_storage_links": {"queue": "special"},
    "app.tasks.process_faststart_video": {"queue": "special"},
    "app.tasks.ensure_faststart": {"queue": "special"},
    "app.tasks.ensure_hls.recount_hls_counters": {"queue": "special"},
    "app.tasks.ensure_hls.fix_missing_legacy_aliases": {"queue": "special"},
    # manual video maintenance (API/админка) — высокий приоритет
    "app.tasks.video_maintenance.process_list": {"queue": "special_priority"},
    "app.tasks.book_formats.*": {"queue": "book"},
    "app.tasks.book_previews.*": {"queue": "book"},
    "app.tasks.book_covers.*": {"queue": "book"},
    "app.tasks.creatives.*": {"queue": "book"},
    "app.tasks.clip_tasks.*": {"queue": "default"},
    "app.tasks.video_summary.*": {"queue": "default"},
    # Email tasks → отдельная очередь email
    "app.tasks.abandoned_checkouts.process_abandoned_checkouts": {"queue": "email"},
    "app.tasks.big_cart_reminder.process_big_cart_reminders": {"queue": "email"},
    "app.tasks.referral_campaign.send_referral_campaign_batch": {"queue": "email"},
}
