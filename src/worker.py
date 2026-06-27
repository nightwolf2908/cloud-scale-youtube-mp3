from celery import Celery
import os
from src.downloader import download_youtube_as_mp3
from src.aws_config import get_s3_client, BUCKET_NAME

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://localhost:6379/0")
CELERY_RESULT_BACKEND = os.getenv("CELERY_RESULT_BACKEND", "redis://localhost:6379/0")

celery_app = Celery("tasks", broker=CELERY_BROKER_URL, backend=CELERY_RESULT_BACKEND)

@celery_app.task(name="download_video_task")
def download_video_task(url: str):
    # 1. Descargamos y convertimos localmente de forma temporal
    local_mp3_path = download_youtube_as_mp3(url)
    file_name = os.path.basename(local_mp3_path)
    
    # 2. Nos conectamos al S3 emulado de LocalStack
    s3 = get_s3_client()
    
    # 3. Subimos el archivo a la "nube"
    print(f"☁️ Subiendo '{file_name}' a LocalStack S3...")
    s3.upload_file(local_mp3_path, BUCKET_NAME, file_name)
    
    # 4. Destruimos el archivo temporal local del contenedor para dejarlo limpio
    if os.path.exists(local_mp3_path):
        os.remove(local_mp3_path)
        
    # 5. Retornamos los datos para que FastAPI sepa cómo exponer el archivo
    return {
        "file_name": file_name,
        "s3_key": file_name
    }
