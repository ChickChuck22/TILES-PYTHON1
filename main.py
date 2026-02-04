import pygame
import sys
import os
import traceback

# Add src to path just in case
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from src.core.constants import *
from src.core.state_manager import StateManager, GameState
from src.core.audio_manager import AudioManager
from src.ui.menu_qt import run_menu
from src.gameplay.engine import GameEngine

class PianoTilesApp:
    def __init__(self):
        pygame.init() # Init once here
        self.state_manager = StateManager()
        self.audio_manager = AudioManager()
        
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
            
            songs = self.audio_manager.list_songs("assets/music")
            print(f"Starting menu with {len(songs)} songs...")
            
            # Check for Android environment
            import platform
            is_android = 'ANDROID_ARGUMENT' in os.environ
            
            if is_android:
                from src.ui.menu_pygame import run_menu
                selected_song, difficulty, beats, custom_settings = run_menu(songs, self.audio_manager)
            else:
                from src.ui.menu_qt import run_menu
                selected_song, difficulty, beats, custom_settings = run_menu(songs, self.audio_manager)
            
            if selected_song and beats:
                print(f"Selected: {selected_song} | Difficulty: {difficulty} | Custom: {custom_settings}")
                self.init_game(selected_song, difficulty, beats, custom_settings)
                self.run_game_loop()
            else:
                print("Launcher exited without selection.")
                self.cleanup()
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
        pygame.display.init()
        
        # Get Monitor Height for vertical maximization
        info = pygame.display.Info()
        # Set height to monitor height minus a small margin for window borders/taskbar
        max_h = info.current_h - 100 
        
        # Update global constant for other modules
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

        pygame.display.set_caption(f"Playing: {song_name}")
        self.clock = pygame.time.Clock()
        self.running = True
        self.return_to_menu = False
        
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
        frame_count = 0
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            if not self.handle_events():
                print("Exit signal via events.")
                break
            
            try:
                self.update(dt)
                self.draw()
                pygame.display.flip()
                frame_count += 1
                if frame_count % 300 == 0:
                    print(f"Loop heartbeat: frame={frame_count} | state={self.state_manager.get_state()}")
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
                        self.game_engine.handle_keydown(lane_idx, self.game_engine.current_game_time)
                    elif event.key == pygame.K_ESCAPE:
                        return False
                
                # TOUCH SUPPORT (ANDROID)
                elif event.type == pygame.FINGERDOWN:
                    # FINGERDOWN x,y are normalized 0-1
                    x_pixel = event.x * SCREEN_WIDTH
                    y_pixel = event.y * SCREEN_HEIGHT
                    action = self.game_engine.handle_click(x_pixel, y_pixel)
                    
                    if action == "PAUSE":
                        self.state_manager.change_state(GameState.PAUSED)
                        self.audio_manager.pause()
                        self.game_engine.paused = True
                    else:
                        self.game_engine.handle_lane_touch(event.x, self.game_engine.current_game_time)
                
                elif event.type == pygame.KEYUP:
                    if event.key in LANE_KEYS:
                        lane_idx = LANE_KEYS.index(event.key)
                        self.game_engine.handle_keyup(lane_idx, self.game_engine.current_game_time)

            elif state == GameState.PAUSED:
                if event.type == pygame.MOUSEBUTTONDOWN:
                    x, y = event.pos
                    action = self.game_engine.handle_click(x, y)
                    if action == "RESUME":
                        self.game_engine.paused = False
                        self.is_resuming = True
                        self.game_engine.countdown = 3
                        # We need to set countdown start? Engine uses countdown_start for logic?
                        # In update(), we use main's countdown_start? No, main uses engine.countdown_start.
                        self.game_engine.countdown_start = pygame.time.get_ticks()
                        self.state_manager.change_state(GameState.COUNTDOWN)
                    elif action == "MENU":
                        self.running = False
                        self.return_to_menu = True
                
                elif event.type == pygame.FINGERDOWN:
                    x = event.x * SCREEN_WIDTH
                    y = event.y * SCREEN_HEIGHT
                    action = self.game_engine.handle_click(x, y)
                    if action == "RESUME":
                        self.game_engine.paused = False
                        self.is_resuming = True
                        self.game_engine.countdown = 3
                        self.game_engine.countdown_start = pygame.time.get_ticks()
                        self.state_manager.change_state(GameState.COUNTDOWN)
                    elif action == "MENU":
                        self.running = False
                        self.return_to_menu = True
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
                
                if self.game_engine.game_over:
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
