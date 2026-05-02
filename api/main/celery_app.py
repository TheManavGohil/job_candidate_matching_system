"""
Celery application instance.
Tasks are auto-discovered from `main.tasks` sub-package.
"""

from __future__ import annotations

from celery import Celery

from main.config import get_settings

settings = get_settings()

celery = Celery(
    "matcher",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
)

celery.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    result_expires=3600,
    broker_connection_retry_on_startup=True,
)

# Auto-discover tasks in main.tasks package
celery.autodiscover_tasks(["main.tasks"])
