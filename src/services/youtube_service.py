import os
import yt_dlp
import threading

class YouTubeService:
    def __init__(self, cache_dir="assets/cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def search(self, query, limit=10):
        """Searches YouTube for videos."""
        ydl_opts = {
            'quiet': True,
            'extract_flat': True,
            'default_search': 'ytsearch',
            'noplaylist': True,
        }
        
        results = []
        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        results.append({
                            'id': entry['id'],
                            'title': entry['title'],
                            'uploader': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry['url'],
                            'thumbnail': f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
                        })
        except Exception as e:
            print(f"YouTube Search Error: {e}")
            
        return results

    def download_audio(self, video_id, callback=None, progress_callback=None):
        """Downloads audio as MP3 to assets/music/youtube."""
        # Use main music directory
        music_dir = os.path.join("assets", "music", "youtube")
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)

        # Get FFmpeg binary (Copy of existing logic)
        ffmpeg_path = None
        bin_ffmpeg = os.path.join(os.getcwd(), "bin", "ffmpeg.exe")
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(bin_ffmpeg): ffmpeg_path = bin_ffmpeg
        elif os.path.exists(local_ffmpeg): ffmpeg_path = local_ffmpeg
        else:
            try:
                import imageio_ffmpeg
                ffmpeg_path = imageio_ffmpeg.get_ffmpeg_exe()
            except: pass
            
        out_template = os.path.join(music_dir, '%(title)s.%(ext)s')

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%','')
                    progress_callback(float(p))
                except: pass
            elif d['status'] == 'finished':
                if progress_callback: progress_callback(100)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [{
                'key': 'FFmpegExtractAudio',
                'preferredcodec': 'mp3',
                'preferredquality': '192',
            }],
            'outtmpl': out_template,
            'restrictfilenames': True,
            'quiet': True,
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
            'http_headers': {'User-Agent': 'Mozilla/5.0 ...'}
        }

        def run():
            try:
                print(f"DEBUG: Starting download for {video_id}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
                    filename = ydl.prepare_filename(info)
                    base, _ = os.path.splitext(filename)
                    final_file = base + ".mp3"
                    
                    print(f"DEBUG: Expected final file: {final_file}")
                    
                    if not os.path.exists(final_file):
                        print(f"DEBUG: File not found at expected path! Checking dir {music_dir} for newest mp3...")
                        # Fallback: Find newest .mp3 in folder
                        try:
                            files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith('.mp3')]
                            if files:
                                newest = max(files, key=os.path.getctime)
                                print(f"DEBUG: Found newest file instead: {newest}")
                                final_file = newest
                        except Exception as e:
                            print(f"DEBUG: Error searching dir: {e}")
                        
                if callback: callback(final_file)
            except Exception as e:
                print(f"Download Error: {e}")
                if callback: callback(None)

        t = threading.Thread(target=run)
        t.start()
        return None
