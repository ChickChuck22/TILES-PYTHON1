import os
import threading
import sys
import yt_dlp
from youtubesearchpython import VideosSearch

class YouTubeService:
    def __init__(self, cache_dir="assets/cache"):
        self.cache_dir = cache_dir
        if not os.path.exists(self.cache_dir):
            os.makedirs(self.cache_dir)

    def search(self, query, limit=10):
        """Searches YouTube for videos. Tries youtube-search-python first, then fallbacks to yt-dlp."""
        results = []
        
        # 1. Try youtube-search-python (preferred for cleaner results)
        try:
            videos_search = VideosSearch(query, limit=limit)
            search_results = videos_search.result()

            if 'result' in search_results and search_results['result']:
                for entry in search_results['result']:
                    results.append({
                        'id': entry['id'],
                        'title': entry['title'],
                        'uploader': entry['channel']['name'] if 'channel' in entry else 'Unknown',
                        'duration': entry.get('duration', '0:00'),
                        'url': entry['link'],
                        'thumbnail': entry['thumbnails'][0]['url'] if entry.get('thumbnails') else ""
                    })
                if results: return results
        except Exception as e:
            print(f"YouTube Search Error (Hybrid - Primary): {e}")

        # 2. Fallback to yt-dlp (extremely robust)
        print("DEBUG: Falling back to yt-dlp search...")
        try:
            ydl_opts = {
                'quiet': True,
                'extract_flat': True,
                'default_search': 'ytsearch',
                'noplaylist': True,
            }
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(f"ytsearch{limit}:{query}", download=False)
                if 'entries' in info:
                    for entry in info['entries']:
                        results.append({
                            'id': entry['id'],
                            'title': entry['title'],
                            'uploader': entry.get('uploader', 'Unknown'),
                            'duration': entry.get('duration', 0),
                            'url': entry.get('url', f"https://www.youtube.com/watch?v={entry['id']}"),
                            'thumbnail': f"https://img.youtube.com/vi/{entry['id']}/mqdefault.jpg"
                        })
        except Exception as e:
            print(f"YouTube Search Error (Hybrid - Fallback): {e}")
            
        return results

    def _get_ffmpeg_path(self):
        """Helper to find ffmpeg in portable or system paths."""
        # 1. Check if frozen (PyInstaller)
        if hasattr(sys, '_MEIPASS'):
            # When using --onefile, files are unpacked to _MEIPASS
            bundle_ffmpeg = os.path.join(sys._MEIPASS, "bin", "ffmpeg.exe")
            if os.path.exists(bundle_ffmpeg): 
                print(f"DEBUG: Found bundled FFmpeg at {bundle_ffmpeg}")
                return bundle_ffmpeg
            
        # 2. Check executable directory (next to .exe or in dev)
        exe_dir = os.path.dirname(sys.executable)
        portable_ffmpeg = os.path.join(exe_dir, "bin", "ffmpeg.exe")
        if os.path.exists(portable_ffmpeg): return portable_ffmpeg
            
        # 3. Check CWD (dev mode)
        bin_ffmpeg = os.path.join(os.getcwd(), "bin", "ffmpeg.exe")
        local_ffmpeg = os.path.join(os.getcwd(), "ffmpeg.exe")
        if os.path.exists(bin_ffmpeg): return bin_ffmpeg
        if os.path.exists(local_ffmpeg): return local_ffmpeg
            
        # 4. Fallback to imageio_ffmpeg
        try:
            import imageio_ffmpeg
            return imageio_ffmpeg.get_ffmpeg_exe()
        except: return None

    def download_audio(self, video_id, callback=None, progress_callback=None):
        """Downloads audio as MP3 to assets/music/youtube using yt-dlp."""
        music_dir = os.path.join("assets", "music", "youtube")
        if not os.path.exists(music_dir):
            os.makedirs(music_dir)

        ffmpeg_path = self._get_ffmpeg_path()
        out_template = os.path.join(music_dir, '%(title)s.%(ext)s')

        def progress_hook(d):
            if d['status'] == 'downloading':
                try:
                    p = d.get('_percent_str', '0%').replace('%','').strip()
                    if progress_callback: progress_callback(float(p))
                except: pass
            elif d['status'] == 'finished':
                if progress_callback: progress_callback(100)

        ydl_opts = {
            'format': 'bestaudio/best',
            'postprocessors': [
                {
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                },
                {
                    'key': 'FFmpegMetadata',
                    'add_metadata': True,
                }
            ],
            'outtmpl': out_template,
            'restrictfilenames': True,
            'quiet': True,
            'ffmpeg_location': ffmpeg_path,
            'progress_hooks': [progress_hook] if progress_callback else [],
            'extractor_args': {'youtube': {'player_client': ['android', 'web']}},
        }

        def run():
            try:
                print(f"DEBUG: Starting hybrid yt-dlp download for {video_id}...")
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
                    filename = ydl.prepare_filename(info)
                    base, _ = os.path.splitext(filename)
                    final_file = base + ".mp3"
                    
                    # Double check if file moved/renamed by post-processor
                    if not os.path.exists(final_file):
                        # Manual fallback search in directory
                        files = [os.path.join(music_dir, f) for f in os.listdir(music_dir) if f.endswith('.mp3')]
                        if files:
                            final_file = max(files, key=os.path.getctime)

                if callback: callback(final_file)
            except Exception as e:
                err_msg = str(e)
                print(f"Hybrid Download Error: {err_msg}")
                if callback: callback(f"ERROR: {err_msg}")

        t = threading.Thread(target=run)
        t.start()
        return None
