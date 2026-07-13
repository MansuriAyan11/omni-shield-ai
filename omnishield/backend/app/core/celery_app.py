from celery import Celery
from app.core.config import settings

# Initialize Celery app instance
celery_app = Celery(
    "moderation_workers",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND
)

# Optional configuration settings
celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Auto-import tasks from the tasks module
    imports=["app.tasks"]
)
