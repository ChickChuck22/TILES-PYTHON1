import pygame
import os
import json
from mutagen.mp3 import MP3
from mutagen import File as MutagenFile

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.current_song_path = None
        self.song_duration = 0
        self.is_playing = False
        self.sfx = {}
        self.music_volume = 1.0
        self.sfx_volume = 1.0
        self._metadata_cache_file = "metadata_cache.json"
        self._metadata_cache = {}
        self.load_metadata_cache()
        
    def load_metadata_cache(self):
        if os.path.exists(self._metadata_cache_file):
            try:
                with open(self._metadata_cache_file, 'r', encoding='utf-8') as f:
                    self._metadata_cache = json.load(f)
            except: self._metadata_cache = {}
            
    def save_metadata_cache(self):
        try:
            with open(self._metadata_cache_file, 'w', encoding='utf-8') as f:
                json.dump(self._metadata_cache, f, indent=2)
        except: pass

    def load_sfx(self, name, path):
        """Loads a sound effect into memory."""
        try:
            if os.path.exists(path):
                s = pygame.mixer.Sound(path)
                s.set_volume(self.sfx_volume)
                self.sfx[name] = s
                return True
        except Exception as e:
            print(f"Error loading SFX {name}: {e}")
        return False

    def play_sfx(self, name):
        """Plays a loaded sound effect."""
        if name in self.sfx:
            try:
                self.sfx[name].set_volume(self.sfx_volume)
                self.sfx[name].play()
            except:
                pass

    def set_music_volume(self, volume):
        self.music_volume = max(0.0, min(1.0, volume))
        pygame.mixer.music.set_volume(self.music_volume)

    def set_sfx_volume(self, volume):
        self.sfx_volume = max(0.0, min(1.0, volume))
        for sfx in self.sfx.values():
            sfx.set_volume(self.sfx_volume)

    def play_preview(self, song_path, start_time=0.0):
        """Plays a song starting from a specific time for preview."""
        try:
            pygame.mixer.music.load(song_path)
            pygame.mixer.music.set_volume(self.music_volume)
            pygame.mixer.music.play(start=start_time)
            self.current_song_path = song_path
            self.is_playing = True
        except Exception as e:
            print(f"Preview error: {e}")
        self.sfx = {}

    def load_sfx(self, name, path):
        """Loads a sound effect into memory."""
        try:
            if os.path.exists(path):
                self.sfx[name] = pygame.mixer.Sound(path)
                return True
            print(f"SFX not found: {path}")
        except Exception as e:
            print(f"Error loading SFX {name}: {e}")
        return False

    def play_sfx(self, name):
        """Plays a loaded sound effect."""
        if name in self.sfx:
            try:
                self.sfx[name].play()
            except:
                pass

    def load_song(self, path):
        """Loads a song for playback with retry for Windows file conflicts."""
        import time
        max_retries = 5
        for i in range(max_retries):
            try:
                if pygame.mixer.music.get_busy():
                    pygame.mixer.music.stop()
                pygame.mixer.music.load(path)
                self.current_song_path = path
                
                # Get duration
                from mutagen import File as MutagenFile
                audio = MutagenFile(path)
                self.song_duration = audio.info.length if audio else 0
                return True
            except Exception as e:
                print(f"Load Attempt {i+1} Failed: {e}")
                if i < max_retries - 1:
                    time.sleep(0.2) # Wait for other threads (analysis) to release handle
                else:
                    return False
        return False

    def play(self):
        if self.current_song_path:
            print(f"AudioManager playing: {self.current_song_path}")
            pygame.mixer.music.play()
            self.is_playing = True

    def pause(self):
        if self.is_playing:
            pygame.mixer.music.pause()
            self.is_playing = False # Or keep true and add is_paused? 
            # Pygame doesn't easily distinguish pause vs stop. 
            # let's assume is_playing tracks if it *should* be active.

    def unpause(self):
        pygame.mixer.music.unpause()
        self.is_playing = True

    def stop(self):
        pygame.mixer.music.stop()
        self.is_playing = False

    def get_pos(self):
        """Returns current playback position in seconds."""
        if self.is_playing:
            pos = pygame.mixer.music.get_pos()
            if pos < 0: return 0 # Music might have finished
            return pos / 1000.0
        return 0

    def get_busy(self):
        """Checks if music is actually playing in the hardware mixer."""
        return pygame.mixer.music.get_busy()

    def list_songs(self, directory):
        import subprocess # Local import to avoid changing file header for now

        def resolve_shortcut(path):
            try:
                cmd = ["powershell", "-command", f"(New-Object -ComObject WScript.Shell).CreateShortcut('{path}').TargetPath"]
                result = subprocess.run(cmd, capture_output=True, text=True, check=True)
                return result.stdout.strip()
            except:
                return None

        songs = []
        if not os.path.exists(directory):
            os.makedirs(directory)
            
        # Helper to scan a dir
        def scan_dir(path):
            found = []
            try:
                for f in os.listdir(path):
                    full_path = os.path.join(path, f)
                    if os.path.isdir(full_path):
                        # Recursive scan? Maybe depth 1 to avoid infinity
                        pass 
                    elif f.lower().endswith(('.mp3', '.wav', '.ogg')):
                        # If inside assets/music, return relative filename
                        # If external, return absolute path
                        if os.path.abspath(path) == os.path.abspath(directory):
                            found.append(f)
                        else:
                            found.append(full_path)
                    elif f.lower().endswith('.lnk'):
                        target = resolve_shortcut(full_path)
                        if target and os.path.exists(target):
                            if os.path.isdir(target):
                                # Scan the linked folder
                                try:
                                    for root, _, files in os.walk(target):
                                        for file in files:
                                            if file.lower().endswith(('.mp3', '.wav', '.ogg')):
                                                found.append(os.path.join(root, file))
                                except: pass
                            elif target.lower().endswith(('.mp3', '.wav', '.ogg')):
                                found.append(target)
            except: pass
            return found

        # 1. Scan root
        songs.extend(scan_dir(directory))
        
        return songs

    def get_metadata(self, path):
        """Extracts artist, title, and duration from a file."""
        metadata = {
            "title": os.path.splitext(os.path.basename(path))[0],
            "artist": "Unknown Artist",
            "duration": "--:--"
        }
        
        try:
            audio = MutagenFile(path)
            if audio:
                # Duration
                length = audio.info.length
                mins = int(length // 60)
                secs = int(length % 60)
                metadata["duration"] = f"{mins}:{secs:02d}"
                
                # Tags (generic)
                if hasattr(audio, 'tags') and audio.tags:
                    # Try common tag names
                    artist = audio.get('artist') or audio.get('TPE1') or audio.get('TPE2')
                    title = audio.get('title') or audio.get('TIT2')
                    
                    if artist: 
                        # mutagen returns lists/objects often
                        if isinstance(artist, list): metadata["artist"] = str(artist[0])
                        else: metadata["artist"] = str(artist)
                        
                    if title:
                        if isinstance(title, list): metadata["title"] = str(title[0])
                        else: metadata["title"] = str(title)
        except Exception as e:
            print(f"Error reading metadata for {path}: {e}")
            
        return metadata

    def scan_library(self, folders):
        """Scans multiple folders and returns list of dicts with path and metadata."""
        all_songs = []
        seen_paths = set()
        
        for folder in folders:
            if not folder: continue
            try:
                folder = os.path.abspath(folder)
                if not os.path.exists(folder): continue

                print(f"Scanning library folder: {folder}")
                songs = self.list_songs(folder)
                
                for s in songs:
                    full_path = os.path.join(folder, s)
                    norm_path = os.path.normpath(full_path)
                    
                    if norm_path.lower() not in seen_paths:
                        # Check cache vs mtime
                        mtime = os.path.getmtime(full_path)
                        cache_entry = self._metadata_cache.get(norm_path.lower())
                        
                        if cache_entry and cache_entry.get("mtime") == mtime:
                            metadata = cache_entry["metadata"]
                        else:
                            metadata = self.get_metadata(full_path)
                            self._metadata_cache[norm_path.lower()] = {
                                "mtime": mtime,
                                "metadata": metadata
                            }
                            
                        all_songs.append({
                            "path": full_path,
                            **metadata
                        })
                        seen_paths.add(norm_path.lower())
            except Exception as e:
                print(f"Error scanning {folder}: {e}")
                
        self.save_metadata_cache()
        return all_songs
