from pypresence import Presence
import time
import threading

class DiscordRPC:
    def __init__(self, client_id):
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        self.start_time = None

    def connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            self.start_time = time.time()
            print(f"Discord RPC Connected! ID: {self.client_id}")
        except Exception as e:
            print(f"Discord RPC Error: {e}")
            self.connected = False

    def update_menu(self, song_count=0):
        if not self.connected: return
        try:
            self.rpc.update(
                state="Browsing Songs",
                details=f"Library: {song_count} Songs",
                large_image="logo_large", # User needs to upload this asset key
                large_text="Piano Tiles Python",
                start=self.start_time
            )
        except Exception as e:
            print(f"RPC Update Failed: {e}")

    def update_playing(self, song_title, difficulty, progress_percent, score, combo):
        if not self.connected: return
        try:
            self.rpc.update(
                state=f"Score: {score} | Combo: {combo}",
                details=f"Playing: {song_title} [{difficulty}]",
                large_image="logo_large",
                large_text="Piano Tiles Python",
                small_image="play_icon", # User needs to upload
                small_text=f"{progress_percent:.1f}%",
                start=self.start_time
            )
        except Exception as e:
            print(f"RPC Update Failed: {e}")

    def update_results(self, song_title, rank, score, max_combo):
        if not self.connected: return
        try:
            self.rpc.update(
                state=f"Rank: {rank} | Score: {score}",
                details=f"Finished: {song_title}",
                large_image="logo_large",
                large_text="Piano Tiles Python",
                small_image="rank_icon", # User needs to upload
                small_text=f"Max Combo: {max_combo}"
            )
        except Exception as e:
            print(f"RPC Update Failed: {e}")

    def close(self):
        if self.rpc:
            self.rpc.close()
