from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
import os
from celery.result import AsyncResult
from src.worker import celery_app, download_video_task
import urllib.parse

app = FastAPI(title="Cloud-Scale YouTube Converter - Fase 2")

class VideoRequest(BaseModel):
    url: str

@app.get("/")
def read_root():
    return {"message": "API Asíncrona Funcional. Usa /convert para enviar una tarea."}

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
        
    mp3_path = task_result.result.get("file_path")
    file_name = task_result.result.get("file_name")
    
    if os.path.exists(mp3_path):
        # SOLUCCIÓN: Convertimos el nombre a un formato seguro para URLs (ej: %E2%99%AB)
        # para que los caracteres como '♫' no rompan las cabeceras HTTP
        encoded_filename = urllib.parse.quote(file_name)
        
        # Usamos el estándar 'filename*=UTF-8''; esto le dice explícitamente 
        # al navegador que decodifique el nombre usando UTF-8.
        headers = {
            'Content-Disposition': f"attachment; filename*=UTF-8''{encoded_filename}"
        }
        
        return FileResponse(path=mp3_path, media_type="audio/mpeg", headers=headers)
    else:
        raise HTTPException(status_code=404, detail="El archivo físico no se encontró en el servidor.")

