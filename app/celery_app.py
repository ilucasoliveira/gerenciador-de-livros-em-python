from celery import Celery

celery_app = Celery(
    "tarefas_livros",
    broker="redis://redis:6379/0",
    backend="redis://redis:6379/0",
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