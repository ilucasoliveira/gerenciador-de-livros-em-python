import os
from dotenv import load_dotenv
from app.cache import REDIS_HOST, REDIS_PORT
from celery import Celery

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL", f"redis://{REDIS_HOST}:{REDIS_PORT}/0")

celery_app = Celery(
    "tarefas_livros",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app.tasks"]
)

celery_app.conf.update(
    task_track_started=True,
    task_routes={"app.tasks.*":{"queue":"livros"}},
    result_expires=3600,
    result_persistent=True,
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"]
)