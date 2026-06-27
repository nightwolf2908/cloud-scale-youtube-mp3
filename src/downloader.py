import os
from yt_dlp import YoutubeDL

def download_youtube_as_mp3(youtube_url: str, output_dir: str = "downloads") -> str:
    """
    Descarga cualquier formato disponible de YouTube y lo fuerza a convertirse en MP3.
    """
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    ydl_opts = {
        # 1. Pedimos el formato mixto estándar (suele ser mp4/webm) que no requiere firmas raras
        'format': 'mp4/ext/mp3/best',
        
        'outtmpl': f'{output_dir}/%(title)s.%(ext)s',
        'noplaylist': True,
        
        # 2. SEÑAL INTERNACIONAL: Forzamos a yt-dlp a usar clientes específicos para saltar el 403
        'extractor_args': {
            'youtube': {
                'player_client': ['android_vr', 'web'],
                'skip': ['dash', 'hls']
            }
        },
        
        # Cabeceras limpias para simular un navegador
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
        },
        
        # El postprocesador que transformará lo que sea que baje a un hermoso MP3
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
    }

    with YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_url, download=True)
        filename = ydl.prepare_filename(info_dict)
        
        mp3_filename = os.path.splitext(filename)[0] + ".mp3"
        return mp3_filename