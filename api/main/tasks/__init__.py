# Tasks package – explicitly import all modules so Celery registers them.
from main.tasks import processing, matching  # noqa: F401
