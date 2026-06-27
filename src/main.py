from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles  # <--- NUEVA
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
from celery.result import AsyncResult
from src.worker import celery_app, download_video_task
import urllib.parse
from src.aws_config import init_s3_bucket, BUCKET_NAME, get_s3_client # <--- AGREGA ESTA IMPORTACIÓN

app = FastAPI(title="Cloud-Scale YouTube Converter - Fase 2")

@app.on_event("startup")
def startup_event():
    # Esto corre automáticamente en cuanto Docker enciende el contenedor de la API
    init_s3_bucket()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if not os.path.exists("src/static"):
    os.makedirs("src/static")

class VideoRequest(BaseModel):
    url: str

# 1. ENDPOINT PARA INICIAR LA DESCARGA
@app.post("/convert")
def convert_video(request: VideoRequest):
    try:
        # En lugar de llamar a la función directo, usamos .delay()
        # Esto le dice a Celery: "Pon esta tarea en Redis y regresa de inmediato"
        task = download_video_task.delay(request.url)
        
        # Le respondemos al usuario al instante con el ID de su tarea
        return {
            "message": "Tarea agregada con éxito a la fila de espera.",
            "task_id": task.id,
            "status": "PENDING"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"No se pudo crear la tarea: {str(e)}")

# 2. ENDPOINT PARA CONSULTAR EL ESTADO DE LA TAREA
@app.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    # Conectamos con Celery/Redis para buscar el estado de ese ticket/ID
    task_result = AsyncResult(task_id, app=celery_app)
    
    # Verificamos en qué estado se encuentra
    if task_result.status == "PENDING":
        return {"task_id": task_id, "status": "Procesando en segundo plano... Ten paciencia."}
        
    elif task_result.status == "SUCCESS":
        # Si terminó con éxito, el "result" contiene el diccionario que definimos en worker.py
        result_data = task_result.result
        return {
            "task_id": task_id,
            "status": "COMPLETED",
            "file_name": result_data.get("file_name"),
            "download_url": f"http://127.0.0.1:8000/download/{task_id}" # Le damos el link de descarga
        }
        
    elif task_result.status == "FAILURE":
        return {"task_id": task_id, "status": "FAILED", "error": str(task_result.info)}
        
    return {"task_id": task_id, "status": task_result.status}

# 3. ENDPOINT PARA DESCARGAR EL ARCHIVO TERMINADO
@app.get("/download/{task_id}")
def download_file(task_id: str):
    task_result = AsyncResult(task_id, app=celery_app)
    
    if task_result.status != "SUCCESS":
        raise HTTPException(status_code=400, detail="El archivo aún no está listo o la tarea falló.")
        
    s3_key = task_result.result.get("s3_key")
    file_name = task_result.result.get("file_name")
    
    s3 = get_s3_client()
    
    try:
        # Generamos una URL firmada y directa de S3 para descargar el archivo de forma segura
        # Como estamos en LocalStack, esta URL apuntará al puerto 4566
        download_url = s3.generate_presigned_url(
            'get_object',
            Params={'Bucket': BUCKET_NAME, 'Key': s3_key},
            ExpiresIn=3600 # La URL expira en 1 hora
        )
        
        # Como LocalStack corre dentro de la red de Docker con el nombre 'localstack',
        # para que tu navegador web (que está afuera de Docker) pueda descargarla, 
        # reemplazamos el host interno por '127.0.0.1'
        public_url = download_url.replace("http://localstack:4566", "http://127.0.0.1:4566")
        
        return {"download_url": public_url}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al conectar con la infraestructura Cloud: {str(e)}")

app.mount("/", StaticFiles(directory="src/static", html=True), name="static")
