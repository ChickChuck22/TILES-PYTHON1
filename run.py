import sys
import os
os.environ["MPG123_QUIET"] = "1" # Suppress noisy ID3/MP3 warnings
import traceback
import pygame
from dotenv import load_dotenv

# Local imports
from src.core.constants import *
from src.core.state_manager import StateManager, GameState
from src.core.audio_manager import AudioManager
from src.services.discord_rpc import DiscordRPC
from src.gameplay.modes.classic.engine import GameEngine
from src.gameplay.modes.cyber_run.engine import CyberRunEngine
from src.gameplay.modes.vibe_tunnel.engine import VibeTunnelEngine
from src.core.settings import SettingsManager
from src.ui.launcher import run_launcher

load_dotenv() # Load environment variables

DISCORD_APP_ID = "1469770191582789885"

class PianoTilesApp:
    def __init__(self):
        pygame.init() # Init once here
        self.state_manager = StateManager()
        self.audio_manager = AudioManager()
        self.settings_manager = SettingsManager()
        
        # Discord RPC
        self.discord_rpc = DiscordRPC(DISCORD_APP_ID)
        self.discord_rpc.connect()
        self.discord_rpc.update_menu()
        
        # Load SFX
        sfx_path = os.path.join("assets", "sfx", "tap.wav")
        self.audio_manager.load_sfx("tap", sfx_path)
        
        self.game_engine = None
        self.screen = None
        self.clock = None
        self.running = True
        self.is_resuming = False
        self.return_to_menu = False
        self.selected_mode = None

    def start_launcher(self):
        try:
            while True:
                # 1. Choose Mode if not set
                pygame.display.quit()
                self.selected_mode = run_launcher()
                if not self.selected_mode:
                    break # Exit App

                # Load songs (Only if not already loaded or first time)
                if not 'songs' in locals() or not songs:
                    folders = self.settings_manager.get_music_folders()
                    folders.append("assets/music")
                    folders.append(os.path.join("assets", "music", "youtube"))
                    folders.append(os.path.join("assets", "music", "spotify"))
                    songs = self.audio_manager.scan_library(folders)
                
                last_results = None
                
                # 2. Song Menu Loop
                while True:
                    if not pygame.mixer.get_init():
                        try: pygame.mixer.init()
                        except: pass
                    
                    from src.ui.modern_menu import run_menu
                    selected_song, difficulty, beats, custom_settings, metadata, updated_songs = run_menu(songs, self.audio_manager, self.discord_rpc, results=last_results)
                    if updated_songs:
                        songs = updated_songs
                    last_results = None 
                    
                    if selected_song:
                        from src.ui.bootstrapper import run_bootstrapper
                        
                        if isinstance(selected_song, list):
                            # Playlist Mode
                            for i, song in enumerate(selected_song):
                                print(f"Playing playlist song {i+1}/{len(selected_song)}: {song}")
                                
                                # Use Bootstrapper for Beats
                                current_meta = next((s for s in songs if os.path.normpath(s["path"]) == os.path.normpath(song)), {})
                                
                                # Determine Next Song for UI
                                next_meta = None
                                if i + 1 < len(selected_song):
                                    next_p = selected_song[i+1]
                                    next_meta = next((s for s in songs if os.path.normpath(s["path"]) == os.path.normpath(next_p)), None)

                                current_beats = run_bootstrapper(song, difficulty, custom_settings, current_meta)
                                if current_beats is None: break # Skip if cancelled
                                
                                # Add metadata to game init
                                self.init_game(song, difficulty, current_beats, custom_settings, current_meta, next_meta)
                                last_results = self.run_game_loop()
                                
                                # If the game loop stopped but we aren't returning to menu, continue playlist
                                # If self.running is False because of game_over, we WANT to continue.
                                # If self.running is False because user closed window, we want to break.
                                if not self.running and not getattr(self.game_engine, 'game_over', False):
                                    break
                                
                                # Reset for next song
                                self.running = True
                                pygame.display.quit()
                            
                            # Clean up after playlist
                            pygame.quit()
                        else:
                            # Single Song
                            current_meta = next((s for s in songs if os.path.normpath(s["path"]) == os.path.normpath(selected_song)), {})
                            current_beats = run_bootstrapper(selected_song, difficulty, custom_settings, current_meta)
                            if current_beats is not None:
                                self.init_game(selected_song, difficulty, current_beats, custom_settings, current_meta)
                                last_results = self.run_game_loop()
                                pygame.quit()
                    else:
                        # Exit back to Launcher
                        break
            
            self.cleanup()
            sys.exit()

        except Exception as e:
            msg = traceback.format_exc()
            with open("crash_log.txt", "w") as f:
                f.write(msg)
            print(f"CRASH: {e}\n{msg}")
            self.cleanup()
            sys.exit()

    def init_game(self, song_name, difficulty, beats, custom_settings, current_meta=None, next_meta=None):
        print("Initializing game...")
        self.selected_song_title = os.path.splitext(os.path.basename(song_name))[0]
        self.selected_difficulty = difficulty
        self.selected_custom_settings = custom_settings
        self.current_meta = current_meta
        self.next_meta = next_meta
        
        # Force re-init display to avoid "video system not initialized" after Qt
        if pygame.display.get_init():
            pygame.display.quit()
        pygame.display.init()
            
        if not pygame.get_init():
            pygame.init()
            
        # Store metadata for RPC/Results
        self.selected_song_title = os.path.splitext(os.path.basename(song_name))[0]
        self.difficulty = difficulty

        # Dynamic Screen Size
        if self.selected_mode == "vibe_tunnel":
            target_w, target_h = 1280, 720
        else:
            info = pygame.display.Info()
            target_w = 400
            target_h = info.current_h - 50
        
        import src.core.constants as constants
        constants.SCREEN_WIDTH = target_w
        constants.SCREEN_HEIGHT = target_h
        constants.LANE_WIDTH = target_w // 4 # Fix stale constant
        global SCREEN_WIDTH, SCREEN_HEIGHT
        SCREEN_WIDTH, SCREEN_HEIGHT = target_w, target_h
        
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        
        # Set Icon
        try:
            icon_surf = pygame.image.load("assets/icon.png")
            pygame.display.set_icon(icon_surf)
        except Exception as e:
            print(f"Could not load icon: {e}")

        pygame.display.set_caption(f"Playing: {self.selected_song_title}")
        self.clock = pygame.time.Clock()
        self.running = True
        self.return_to_menu = False
        
        if os.path.isabs(song_name) or song_name.startswith("assets"):
            song_path = song_name
        else:
            song_path = os.path.join("assets", "music", song_name)
        if self.audio_manager.load_song(song_path):
            duration = self.audio_manager.song_duration
            
            # Select Engine based on Mode
            if self.selected_mode == "classic":
                self.game_engine = GameEngine(self.screen, song_path, difficulty, custom_settings, duration, self.audio_manager, self.current_meta, self.next_meta)
            elif self.selected_mode == "cyber_run":
                self.game_engine = CyberRunEngine(self.screen, song_path, difficulty, custom_settings, duration, self.audio_manager, self.current_meta, self.next_meta)
            elif self.selected_mode == "vibe_tunnel":
                self.game_engine = VibeTunnelEngine(self.screen, song_path, difficulty, custom_settings, duration, self.audio_manager, self.current_meta, self.next_meta)
            else:
                # Default to classic if mode is not recognized or not set
                self.game_engine = GameEngine(self.screen, song_path, difficulty, custom_settings, duration, self.audio_manager, self.current_meta, self.next_meta)
            
            self.game_engine.set_beats(beats)
            self.game_engine.countdown_start = pygame.time.get_ticks()
            self.state_manager.change_state(GameState.COUNTDOWN)
            print(f"Game engine created for mode: {self.selected_mode}")
        else:
            print("Failed to load song audio.")
            self.start_launcher()

    def run_game_loop(self):
        print("Entering game loop...")
        self.running = True
        self.game_results = None # Store results here
        
        while self.running:
            dt = self.clock.tick(60) / 1000.0
            
            if not self.handle_events():
                self.running = False
                
            try:
                self.update(dt)
                self.draw()
                pygame.display.flip()
            except Exception as e:
                msg = traceback.format_exc()
                with open("crash_log.txt", "a") as f:
                    f.write("\nLoop Error:\n" + msg)
                print(f"Loop Error: {e}")
                break
        
        print("Exiting game loop...")
        self.audio_manager.stop()
        if self.return_to_menu:
            self.start_launcher()
        return self.game_results

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                return False
            
            state = self.state_manager.get_state()
            if state == GameState.GAMEPLAY:
                # MOUSE / PAUSE UI CHECK
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    action = self.game_engine.handle_click(x, y)
                    if action == "PAUSE":
                        self.state_manager.change_state(GameState.PAUSED)
                        self.audio_manager.pause()
                        self.game_engine.paused = True
                    else:
                        # If not hitting UI, treat as lane input (strictly for testing on PC with mouse)
                        # We map mouse X to lanes if not paused
                        if not self.game_engine.paused:
                             self.game_engine.handle_lane_touch(x / SCREEN_WIDTH, self.audio_manager.get_pos())

                elif event.type == pygame.KEYDOWN:
                    if event.key in LANE_KEYS:
                        lane_idx = LANE_KEYS.index(event.key)
                        # Use engine time for consistency during delay
                        self.game_engine.handle_keydown(lane_idx, self.audio_manager.get_pos())
                    elif event.key == pygame.K_SPACE:
                        # Dedicated key for Dash in Cyber Run or other actions
                        self.game_engine.handle_keydown("SPACE", self.audio_manager.get_pos())
                    elif event.key == pygame.K_ESCAPE:
                        return False
                

                elif event.type == pygame.KEYUP:
                    # Map keys to lanes
                    keys = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
                    if event.key in keys:
                        lane_index = keys.index(event.key)
                        if self.game_engine:
                            self.game_engine.handle_keyup(lane_index, self.audio_manager.get_pos())
                            
        return True

    def update(self, dt):
        state = self.state_manager.get_state()
        if state in [GameState.COUNTDOWN, GameState.GAMEPLAY]:
            if self.game_engine:
                self.game_engine.update(dt)
                
            if state == GameState.COUNTDOWN:
                elapsed = (pygame.time.get_ticks() - self.game_engine.countdown_start) / 1000.0
                if elapsed >= 3.0:
                    self.state_manager.change_state(GameState.GAMEPLAY)
                    self.audio_manager.play()
                    if getattr(self, 'is_resuming', False):
                        self.audio_manager.unpause()
                        self.is_resuming = False
                else:
                    self.game_engine.countdown = 3 - int(elapsed)
                
                # Discord RPC Update (Every 5s)
                now = pygame.time.get_ticks()
                last_update = getattr(self, 'last_rpc_update', 0)
                if now - last_update > 5000:
                    self.last_rpc_update = now
                    progress = self.game_engine.get_progress()
                    score = self.game_engine.score
                    combo = self.game_engine.combo
                    
                    self.discord_rpc.update_playing(self.selected_song_title, self.difficulty, progress, score, combo)
                
                if self.game_engine.game_over:
                    # Capture results immediately
                    if self.game_results is None:
                        print("Game Over! Collecting stats...")
                        self.game_results = {
                            "score": self.game_engine.score,
                            "max_combo": self.game_engine.max_combo,
                            "perfects": self.game_engine.perfects,
                            "goods": self.game_engine.goods,
                            "misses": self.game_engine.misses,
                            "song": self.selected_song_title,
                            "rank": "F",
                            "hit_log": list(self.game_engine.hit_log), # Precision data
                            "duration": getattr(self.game_engine, 'song_duration', 0)
                        }
                        
                        # Calculating Rank
                        total_notes = self.game_results["perfects"] + self.game_results["goods"] + self.game_results["misses"]
                        if total_notes > 0:
                            accuracy = (self.game_results["perfects"] + self.game_results["goods"] * 0.5) / total_notes
                        else:
                            accuracy = 0
                            
                        if accuracy >= 0.95: rank = "S"
                        elif accuracy >= 0.90: rank = "A"
                        elif accuracy >= 0.80: rank = "B"
                        elif accuracy >= 0.70: rank = "C"
                        else: rank = "F"
                        self.game_results["rank"] = rank
                        self.game_results["accuracy"] = accuracy * 100
                        
                        # RPC Update - Finished
                        self.discord_rpc.update_results(
                            self.selected_song_title, 
                            rank, 
                            self.game_engine.score, 
                            self.game_engine.max_combo
                        )

                        # Rapid transition for playlists
                        self.running = False

                    self.audio_manager.stop()
                    self.state_manager.change_state(GameState.GAME_OVER)
        
        elif state == GameState.PAUSED:
            if self.game_engine:
                 # Just draw, no buffer updates?
                 # Engine draw_pause_overlay uses static text mostly
                 pass

    def draw(self):
        self.screen.fill(COLOR_BG)
        state = self.state_manager.get_state()
        if state in [GameState.COUNTDOWN, GameState.GAMEPLAY, GameState.GAME_OVER, GameState.PAUSED]:
            if self.game_engine:
                current_time = self.game_engine.current_game_time
                self.game_engine.draw(current_time)
            if state == GameState.COUNTDOWN:
                font = pygame.font.SysFont("Arial", 140, bold=True)
                text = font.render(str(self.game_engine.countdown), True, COLOR_ACCENT)
                self.screen.blit(text, (SCREEN_WIDTH//2 - text.get_width()//2, SCREEN_HEIGHT//2 - text.get_height()//2))

    def cleanup(self):
        pygame.quit()

if __name__ == "__main__":
    app = PianoTilesApp()
    app.start_launcher()
