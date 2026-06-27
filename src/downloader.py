import os
from yt_dlp import YoutubeDL

def download_youtube_as_mp3(youtube_url: str, output_dir: str = "downloads") -> str:
    """
    Descarga cualquier formato disponible de YouTube y lo fuerza a convertirse en MP3.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        # 'best' le pide a YouTube el mejor flujo combinado disponible (video + audio)
        # Esto soluciona el error de "Requested format is not available"
        'format': 'best',
        'outtmpl': os.path.join(output_dir, '%(title)s.%(ext)s'),
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        # Evitamos problemas de cookies y bloqueos simulando un navegador estándar
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        'quiet': False,  # Ponlo en False temporalmente para ver qué está haciendo en los logs si falla
        'no_warnings': False,
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info_dict)
        
        mp3_filename = os.path.splitext(filename)[0] + ".mp3"
        return mp3_filename