import pygame
import os
from mutagen.mp3 import MP3

class AudioManager:
    def __init__(self):
        pygame.mixer.init()
        self.current_song_path = None
        self.song_duration = 0
        self.is_playing = False

    def load_song(self, song_path):
        try:
            pygame.mixer.music.load(song_path)
            self.current_song_path = song_path
            audio = MP3(song_path)
            self.song_duration = audio.info.length
            return True
        except Exception as e:
            print(f"Error loading song: {e}")
            return False

    def play(self):
        if self.current_song_path:
            pygame.mixer.music.play()
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
