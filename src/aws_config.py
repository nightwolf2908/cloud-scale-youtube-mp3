import boto3
import os

# Nombre del bucket donde guardaremos las canciones
BUCKET_NAME = "youtube-mp3-cloud-storage"

def get_s3_client():
    """
    Retorna un cliente de S3 configurado para apuntar a LocalStack 
    dentro del entorno de Docker.
    """
    return boto3.client(
        "s3",
        region_name="us-east-1",
        # Dentro de Docker, el contenedor de LocalStack se llama 'localstack'
        endpoint_url="http://localstack:4566",
        aws_access_key_id="mock_key",
        aws_secret_access_key="mock_secret"
    )

def init_s3_bucket():
    """
    Crea el bucket de S3 automáticamente si no existe.
    """
    s3 = get_s3_client()
    try:
        s3.head_bucket(Bucket=BUCKET_NAME)
        print(f"🌲 AWS S3: El bucket '{BUCKET_NAME}' ya existe y está listo.")
    except Exception:
        # Si head_bucket falla, significa que el bucket no existe, así que lo creamos
        s3.create_bucket(Bucket=BUCKET_NAME)
        print(f"🚀 AWS S3: Bucket '{BUCKET_NAME}' creado exitosamente en LocalStack.")
