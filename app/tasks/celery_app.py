"""Celery application configuration."""
from celery import Celery
from app.config import settings

celery_app = Celery(
    "product_importer",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max
    worker_max_tasks_per_child=50,
    imports=('app.tasks.import_tasks',)  # Import tasks so they're discovered
)

# Import tasks to register them
from app.tasks import import_tasks  # noqa

