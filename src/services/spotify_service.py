import spotipy
from spotipy.oauth2 import SpotifyOAuth
import os
import threading

class SpotifyService:
    def __init__(self):
        self.sp = None
        self.user_id = None
        self.is_authenticated = False
        
    def authenticate(self):
        """Authenticates with Spotify using credentials from .env"""
        try:
            client_id = os.getenv("SPOTIPY_CLIENT_ID")
            client_secret = os.getenv("SPOTIPY_CLIENT_SECRET")
            redirect_uri = os.getenv("SPOTIPY_REDIRECT_URI", "http://127.0.0.1:8888/callback")
            
            if not client_id or not client_secret:
                print("Spotify credentials not found in .env")
                return False

            scope = "user-library-read playlist-read-private user-read-private"
            self.sp = spotipy.Spotify(auth_manager=SpotifyOAuth(
                client_id=client_id,
                client_secret=client_secret,
                redirect_uri=redirect_uri,
                scope=scope
            ))
            
            self.user_id = self.sp.current_user()["id"]
            self.is_authenticated = True
            print(f"Spotify Authenticated as {self.user_id}")
            return True
        except Exception as e:
            print(f"Spotify Authentication Failed: {e}")
            self.is_authenticated = False
            return False

    def get_playlists(self):
        """Returns a list of user's playlists."""
        if not self.is_authenticated: return []
        try:
            results = self.sp.current_user_playlists()
            playlists = []
            for item in results['items']:
                playlists.append({
                    "name": item['name'],
                    "id": item['id'],
                    "image": item['images'][0]['url'] if item['images'] else None,
                    "tracks_total": item['tracks']['total']
                })
            return playlists
        except Exception as e:
            print(f"Error fetching playlists: {e}")
            return []

    def get_playlist_tracks(self, playlist_id):
        """Returns tracks from a specific playlist."""
        if not self.is_authenticated: return []
        try:
            results = self.sp.playlist_tracks(playlist_id)
            tracks = []
            for item in results['items']:
                track = item['track']
                if not track: continue
                tracks.append({
                    "name": track['name'],
                    "artist": track['artists'][0]['name'],
                    "album": track['album']['name'],
                    "preview_url": track['preview_url'], # 30s preview
                    "duration_ms": track['duration_ms'],
                    "id": track['id'],
                    "image": track['album']['images'][0]['url'] if track['album']['images'] else None
                })
            return tracks
        except Exception as e:
            print(f"Error fetching tracks: {e}")
            return []
