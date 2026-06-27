import os
from celery import Celery
from src.downloader import download_youtube_as_mp3

# Configuramos Celery para que use Redis como su "broker" (fila de espera)
# y también para que guarde ahí mismo el resultado/estado de las tareas (backend)
CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND
)

@celery_app.task(name="download_video_task")
def download_video_task(url: str) -> dict:
    # Eliminamos el try/except de aquí para que Celery maneje el estado nativamente
    print(f"[Worker] Iniciando descarga asíncrona para: {url}")
    mp3_path = download_youtube_as_mp3(url)
    
    return {
        "file_path": mp3_path,
        "file_name": os.path.basename(mp3_path)
    }