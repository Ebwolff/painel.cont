from celery import Celery
import os
from dotenv import load_dotenv

load_dotenv()

# URL do Redis para Broker e Backend de resultados
REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "end_monitor_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["app_v5.worker"]
)

# Configurações adicionais
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="America/Sao_Paulo",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300, # 5 min limite por nota
)
