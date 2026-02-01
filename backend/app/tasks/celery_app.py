"""
Celery application configuration
For async PDF conversion tasks (Phase 2)
"""
from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "cleanread",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.conversion_tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
)

# For MVP, we're doing synchronous conversion
# This Celery app is set up for Phase 2 async processing
# No tasks defined yet - will add conversion tasks in Phase 2
