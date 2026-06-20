from celery import Celery
from app.config import settings

celery_app = Celery(
    "camera_cafe",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.tasks.ai_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="Asia/Jakarta",
    enable_utc=True,
    task_track_started=True,
)