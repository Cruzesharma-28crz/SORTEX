from celery import Celery
from sortex_cloud.config import get_settings
settings = get_settings()
celery_app = Celery("sortex", broker=settings.redis_url, backend=settings.redis_url, include=["sortex_cloud.tasks"])
celery_app.conf.update(task_serializer="json", accept_content=["json"], result_serializer="json", task_track_started=True, worker_prefetch_multiplier=1, task_acks_late=True)
