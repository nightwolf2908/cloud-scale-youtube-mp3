![CI/CD Pipeline](https://github.com/nightwolf2908/cloud-scale-youtube-mp3/actions/workflows/ci-cd.yml/badge.svg)
# Cloud-Scale YouTube to MP3 Converter 🚀

Sistema asíncrono y contenerizado de alto rendimiento para la extracción, conversión y almacenamiento en la nube de audio desde plataformas de video. Diseñado bajo una arquitectura agnóstica basada en microservicios, emulación Cloud local y evasión robusta de rate-limiting.

## 🏗️ Arquitectura del Sistema

El ecosistema está fragmentado en componentes independientes coordinados a través de redes aisladas en Docker:

* **FastAPI (API Gateway):** Capa de presentación y endpoints REST de alta velocidad encargada de recibir peticiones, delegar tareas pesadas y firmar URLs de descarga segura.
* **Celery (Distributed Task Queue):** Procesador de trabajos asíncronos en segundo plano que aísla el consumo de CPU del flujo principal de la aplicación.
* **Redis (In-Memory Broker):** Message broker de baja latencia encargado de la sincronización de tareas y estados entre la API y los Workers.
* **LocalStack (AWS S3 Emulation):** Infraestructura de almacenamiento Cloud Object Storage emulada localmente para garantizar un desarrollo agnóstico de costos.
* **FFmpeg Integration:** Motor binario nativo optimizado dentro de Linux para la extracción y transcodificación de audio a formato estéreo a 192kbps de forma eficiente.

## 🧼 Características Avanzadas de Ingeniería

Resiliencia ante Bloqueos (Anti-Bot): El extractor de medios implementa técnicas de suplantación de clientes móviles (android/ios native extraction arguments) junto con rotación dinámica de headers HTTP para mitigar respuestas de tipo 403 Forbidden impuestas por los firewalls de streaming de video.

Manejo Eficiente de Disco: El worker de Celery opera bajo una política de consumo cero persistente. Una vez que el archivo es convertido localmente, se transmite inmediatamente al almacenamiento S3 mediante boto3 y el archivo físico local se destruye instantáneamente para evitar el desbordamiento de almacenamiento en el contenedor.

Descargas Seguras mediante URLs Firmadas: El endpoint de descarga no expone rutas estáticas de servidores internos; en su lugar, utiliza generate_presigned_url de AWS S3 para delegar al cliente final una llave de descarga con tiempo de expiración limitado (1 hora), emulando los estándares más estrictos de seguridad corporativa en la nube.

Garantía de Integración Continua (CI/CD):Implementación de un pipeline automatizado nativo en GitHub Actions que ejecuta pruebas sintácticas estáticas en Python (`flake8`) y valida de forma estricta la compilación y empaquetado de la arquitectura multi-contenedor con `docker compose build` en cada integración.

## 🛠️ Stack Tecnológico

* **Backend:** Python 3.12, FastAPI, Celery, Uvicorn.
* **Infraestructura & DevOps:** Docker, Docker Compose, LocalStack (AWS S3 SDK - Boto3).
* **Procesamiento de Medios:** FFmpeg, yt-dlp (Mobile API Extractor Mocking).
* **Base de Datos/Broker:** Redis 7 (Alpine-lightweight).

---

## 🚦 Requisitos Previos

Asegúrate de tener instalado en tu sistema anfitrión:
* Docker Engine
* Docker Compose V2

*Nota: No se requiere ninguna instalación local de Python, FFmpeg, Redis ni cuentas de AWS (S3). Todo el entorno se auto-aprovisiona de forma aislada.*

---

## 🚀 Despliegue del Entorno Local

1.  **Clonar el repositorio:**
    ```bash
    git clone [https://github.com/tu-usuario/cloud-youtube-mp3.git](https://github.com/tu-usuario/cloud-youtube-mp3.git)
    cd cloud-youtube-mp3
    ```

2.  **Compilar y encender la infraestructura:**
    Este comando descargará las imágenes oficiales, configurará las variables de entorno, inyectará el soporte nativo de codificación internacional `C.UTF-8` para emojis/caracteres especiales y levantará los servicios:
    ```bash
    docker compose up --build
    ```

3.  **Verificación de Salud (Healthchecks):**
    La API cuenta con una directiva de sincronización (`service_healthy`). No aceptará tráfico en el puerto `8000` hasta que LocalStack declare que su servicio de almacenamiento en la nube S3 está 100% operativo. Verás este log en consola al iniciar con éxito:
    ```text
    🚀 AWS S3: Bucket 'youtube-mp3-cloud-storage' creado exitosamente en LocalStack.
    ```

4.  **Acceso al Sistema:**
    * **Interfaz de usuario (Web UI):** `http://localhost:8000`
    * **Endpoints de la API:** `http://localhost:8000/docs` (Swagger UI)
    * **Puerto de AWS S3 Local:** `http://localhost:4566`

---

## 🧼 Mantenimiento y Limpieza de Recursos

Si procesas listas de reproducción (playlists) masivas o deseas restablecer el almacenamiento Cloud local a cero (vaciar el bucket S3), detén el entorno eliminando los volúmenes virtuales asignados:

```bash
# Apagar contenedores y destruir discos virtuales temporales
docker compose down -v

# Limpiar carpetas residuales del sistema anfitrión si es necesario
rm -rf downloads

