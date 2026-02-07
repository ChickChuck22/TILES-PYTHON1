import pygame
import sys
import os
import traceback

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.constants import *
from src.core.state_manager import StateManager, GameState
from src.core.audio_manager import AudioManager
from src.core.discord_rpc import DiscordRPC
from src.ui.menu_qt import run_menu
from src.gameplay.engine import GameEngine
from src.core.settings import SettingsManager

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
        self.screen = None
        self.clock = None
        self.running = True
        self.is_resuming = False
        self.return_to_menu = False

    def start_launcher(self):
        try:
            # Ensure any old display is closed before showing Qt menu
            pygame.display.quit()
            
            # Load songs from settings + default
            folders = self.settings_manager.get_music_folders()
            folders.append("assets/music")
            print(f"Scanning folders: {folders}")
            
            songs = self.audio_manager.scan_library(folders)
            print(f"Starting menu with {len(songs)} songs...")
            
            last_results = None
            
            while True:
                # Ensure mixer is alive for menu previews
                if not pygame.mixer.get_init():
                    try: pygame.mixer.init()
                    except: pass
                
                # Start Qt Menu directly
                print(f"DEBUG: Calling run_menu with results={last_results}")
                from src.ui.modern_menu import run_menu
                selected_song, difficulty, beats, custom_settings = run_menu(songs, self.audio_manager, self.discord_rpc, results=last_results)
                
                # Reset results after showing them
                last_results = None 
                
                if selected_song:
                    print(f"Selected: {selected_song} | Difficulty: {difficulty} | Custom: {custom_settings}")
                    self.init_game(selected_song, difficulty, beats, custom_settings)
                    last_results = self.run_game_loop()
                    print(f"DEBUG: Game Loop Ended. Results: {last_results}")
                    
                    # Force window close significantly
                    pygame.display.quit()
                    pygame.quit()
                else:
                    print("Launcher exited without selection.")
                    self.cleanup()
                    break
                    
        except Exception:
            traceback.print_exc()
            input("Press Enter to close...")
            sys.exit()
        except Exception as e:
            msg = traceback.format_exc()
            with open("crash_log.txt", "w") as f:
                f.write(msg)
            print(f"CRASH: {e}\n{msg}")
            self.cleanup()
            sys.exit()

    def init_game(self, song_name, difficulty, beats, custom_settings):
        print("Initializing game...")
        if not pygame.get_init():
            pygame.init()
        
        if not pygame.display.get_init():
            pygame.display.init()
            
        # Store metadata for RPC/Results
        self.selected_song_title = os.path.splitext(os.path.basename(song_name))[0]
        self.difficulty = difficulty

        # Get Monitor Height for vertical maximization
        info = pygame.display.Info()
        max_h = info.current_h - 50
        
        # We need to update constants before creating screen?
        import src.core.constants as constants
        constants.SCREEN_HEIGHT = max_h
        global SCREEN_HEIGHT
        SCREEN_HEIGHT = max_h
        
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
        
        if os.path.isabs(song_name):
            song_path = song_name
        else:
            song_path = os.path.join("assets/music", song_name)
        if self.audio_manager.load_song(song_path):
            duration = self.audio_manager.song_duration
            self.game_engine = GameEngine(self.screen, song_path, difficulty, custom_settings, duration, self.audio_manager)
            self.game_engine.set_beats(beats)
            self.state_manager.change_state(GameState.COUNTDOWN)
            print("Game state is now COUNTDOWN")
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
        if state == GameState.COUNTDOWN:
            elapsed = (pygame.time.get_ticks() - self.game_engine.countdown_start) / 1000.0
            if elapsed >= 3.0:
                self.state_manager.change_state(GameState.GAMEPLAY)
                if getattr(self, 'is_resuming', False):
                    self.audio_manager.unpause()
                    self.is_resuming = False
                # DO NOT play music here otherwise (Engine handles initial start)
            else:
                self.game_engine.countdown = 3 - int(elapsed)
        elif state == GameState.GAMEPLAY:
            if self.game_engine:
                # We let the engine manage its time (starts at -3.0)
                # calculate proper dt
                self.game_engine.update(0, dt)
                
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
                            "rank": "F" # Calculate rank here or in menu
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

                        # Small delay before exiting (simulated by not returning immediately if we wanted visuals)
                        # But for now, let's just exit to show the menu
                        pygame.time.wait(1000) 
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
                current_time = self.audio_manager.get_pos()
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
