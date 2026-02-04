import pygame
import os
from mutagen.mp3 import MP3

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.current_song_path = None
        self.song_duration = 0
        self.is_playing = False
        self.sfx = {}
        self.music_volume = 1.0
        self.sfx_volume = 1.0

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

    def load_song(self, song_path):
        try:
            pygame.mixer.music.load(song_path)
            self.current_song_path = song_path
            # Reset playing state because load stops the previous music
            self.is_playing = False
            audio = MP3(song_path)
            self.song_duration = audio.info.length
            return True
        except Exception as e:
            print(f"Error loading song: {e}")
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
            return pygame.mixer.music.get_pos() / 1000.0
        return 0

    def list_songs(self, directory):
        songs = []
        if not os.path.exists(directory):
            os.makedirs(directory)
        for file in os.listdir(directory):
            if file.endswith(".mp3"):
                songs.append(file)
        return songs
