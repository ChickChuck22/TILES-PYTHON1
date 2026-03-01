import pygame
import random
import math
import os
import src.core.constants as constants
from src.gameplay.shared.visuals import FloatingText, Particle, SnowParticle, ConfettiParticle

class Obstacle:
    def __init__(self, x, spawn_time, obs_type="spike"):
        self.x = x
        self.spawn_time = spawn_time
        self.type = obs_type # "spike", "wall", "orb", "barrier"
        self.hit = False
        self.passed = False
        self.width = 60
        self.height = 60
        
        # Type-specific properties
        if self.type == "wall":
            self.height = 120
            self.color = (255, 200, 0) # Yellow
        elif self.type == "orb":
            self.height = 40
            self.width = 40
            self.color = (0, 150, 255) # Blue
        elif self.type == "barrier":
            self.height = 180
            self.width = 25
            self.color = (180, 0, 255) # Purple
        else: # spike
            self.color = (255, 50, 50) # Red

    def update(self, current_time, dt, speed):
        time_diff = self.spawn_time - current_time
        self.x = 150 + (time_diff * speed)

    def draw(self, screen, ground_y, fever_mode=False):
        draw_color = self.color
        if fever_mode: 
            # Rainbow/Neon shift in fever
            t = pygame.time.get_ticks() / 200.0
            draw_color = (
                int(127 + 127 * math.sin(t)),
                int(127 + 127 * math.sin(t + 2)),
                int(127 + 127 * math.sin(t + 4))
            )

        if self.type == "spike":
            pts = [(self.x, ground_y), (self.x + self.width, ground_y), (self.x + self.width//2, ground_y - self.height)]
            pygame.draw.polygon(screen, draw_color, pts)
            pygame.draw.polygon(screen, (255, 255, 255), pts, 2)
        elif self.type == "wall":
            rect = pygame.Rect(self.x, ground_y - self.height - 60, self.width, self.height)
            pygame.draw.rect(screen, draw_color, rect, border_radius=8)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=8)
        elif self.type == "orb":
            center = (int(self.x + self.width//2), int(ground_y - 80))
            pygame.draw.circle(screen, draw_color, center, self.width//2)
            pygame.draw.circle(screen, (255, 255, 255), center, self.width//2, 2)
        elif self.type == "barrier":
            rect = pygame.Rect(self.x, ground_y - self.height, self.width, self.height)
            pygame.draw.rect(screen, draw_color, rect, border_radius=4)
            pygame.draw.rect(screen, (255, 255, 255), rect, 2, border_radius=4)

class CyberRunEngine:
    def __init__(self, screen, song_path, difficulty="Normal", custom_settings=None, song_duration=0, audio_manager=None):
        self.screen = screen
        self.audio_manager = audio_manager
        self.song_path = song_path
        self.difficulty = difficulty
        self.custom_settings = custom_settings or {}
        self.song_duration = float(song_duration)
        
        # Core State
        self.is_ready = False
        self.game_over = False
        self.paused = False
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfects = 0
        self.goods = 0
        self.misses = 0
        self.health = 100.0
        self.current_game_time = -3.0
        self.countdown = 3
        self.countdown_start = 0
        self.hit_log = []
        
        # Mechanics (4 Keys)
        self.ground_y = constants.SCREEN_HEIGHT - 100
        self.player_y = self.ground_y
        self.player_vel_y = 0
        self.is_jumping = False
        self.can_double_jump = False
        self.is_sliding = False
        self.slide_timer = 0
        self.is_dashing = False
        self.dash_timer = 0
        self.dash_cooldown = 0
        
        self.last_action = None # "PARRY", "STRIKE" timers
        self.action_timer = 0
        
        # Meter System
        self.vibe_meter = 0.0
        self.fever_mode = False
        self.fever_timer = 0
        self.cam_shake = 0
        
        self.obstacles = []
        self.beat_timestamps = []
        
        diff_speeds = {"Easy": 450, "Normal": 650, "Hard": 850, "Insane": 1100, "Impossible": 1500}
        self.scroll_speed = self.custom_settings.get("speed", diff_speeds.get(difficulty, 650))
        
        # Visuals
        self.particles = []
        self.floating_texts = []
        self.snow_particles = [SnowParticle(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT) for _ in range(50)]
        self.energy_profile = self.custom_settings.get("energy_profile", [])
        
        if self.audio_manager:
            for name, file in [("perfect", "hit_perfect.wav"), ("good", "hit_good.wav"), 
                             ("miss", "miss.wav"), ("dash", "dash.wav"), ("parry", "parry.wav"), ("strike", "strike.wav")]:
                path = os.path.join("assets", "sfx", file)
                if not os.path.exists(path):
                    path = os.path.join("assets", "sfx", "tap.wav")
                self.audio_manager.load_sfx(name, path)

    def set_beats(self, beats):
        self.beat_timestamps = beats
        self.generate_obstacles()
        self.is_ready = True

    def generate_obstacles(self):
        self.obstacles = []
        types = ["spike", "wall", "orb", "barrier"]
        for t in self.beat_timestamps:
            # Weighted random or pattern based on energy? 
            # Simple weighted for now
            weights = [0.4, 0.3, 0.15, 0.15] # spike, wall, orb, barrier
            obs_type = random.choices(types, weights=weights)[0]
            self.obstacles.append(Obstacle(constants.SCREEN_WIDTH, t, obs_type))

    def handle_click(self, x, y):
        return None

    def handle_lane_touch(self, x_ratio, current_time):
        # Support touch by splitting into 4 zones
        lane = int(x_ratio * 4)
        self.handle_keydown(lane, current_time)

    def handle_keydown(self, key_id, current_time):
        if key_id == "SPACE":
            if self.dash_cooldown <= 0:
                self.is_dashing = True
                self.dash_timer = 0.3
                self.dash_cooldown = 0.8
                if self.audio_manager: self.audio_manager.play_sfx("dash")
                self.spawn_particles(150, self.player_y - 20, (255, 255, 255))
            return

        # 4 Key Redesign:
        # D (0) -> Parry
        # F (1) -> Jump
        # J (2) -> Slide
        # K (3) -> Strike
        
        if key_id == 0: # PARRY (D)
            self.last_action = "PARRY"
            self.action_timer = 0.15
            if self.audio_manager: self.audio_manager.play_sfx("parry")
        elif key_id == 1: # JUMP (F)
            if not self.is_jumping and not self.is_sliding:
                self.player_vel_y = -1000
                self.is_jumping = True
                self.can_double_jump = True
            elif self.can_double_jump:
                self.player_vel_y = -900
                self.can_double_jump = False
                self.spawn_particles(150, self.player_y, (255, 255, 255))
        elif key_id == 2: # SLIDE (J)
            if not self.is_jumping:
                self.is_sliding = True
                self.slide_timer = 0.5
        elif key_id == 3: # STRIKE (K)
            self.last_action = "STRIKE"
            self.action_timer = 0.15
            if self.audio_manager: self.audio_manager.play_sfx("strike")

    def handle_keyup(self, lane_index, current_time):
        pass

    def update(self, _, dt):
        self.current_game_time += dt
        if self.dash_cooldown > 0: self.dash_cooldown -= dt
        if self.action_timer > 0:
            self.action_timer -= dt
            if self.action_timer <= 0: self.last_action = None
        
        # Dash Logic
        if self.is_dashing:
            self.dash_timer -= dt
            if self.dash_timer <= 0: self.is_dashing = False

        # Player Physics
        if self.is_jumping:
            self.player_y += self.player_vel_y * dt
            self.player_vel_y += 2800 * dt # Gravity
            if self.player_y >= self.ground_y:
                self.player_y = self.ground_y
                self.is_jumping = False
                self.player_vel_y = 0
        
        if self.is_sliding:
            self.slide_timer -= dt
            if self.slide_timer <= 0: self.is_sliding = False

        # Fever Mode
        if self.vibe_meter >= 100 and not self.fever_mode:
            self.fever_mode = True
            self.fever_timer = 10.0
            self.spawn_floating_text("FEVER MODE!", constants.SCREEN_WIDTH//2, 200, (255, 255, 0))
            
        if self.fever_mode:
            self.fever_timer -= dt
            self.cam_shake = 5
            if self.fever_timer <= 0:
                self.fever_mode = False
                self.vibe_meter = 0
        else:
             self.cam_shake = max(0, self.cam_shake - 20 * dt)

        # Update Obstacles
        speed = self.scroll_speed * (1.5 if self.fever_mode else 1.0)
        for obs in list(self.obstacles):
            obs.update(self.current_game_time, dt, speed)
            
            if not obs.hit and not obs.passed:
                if 100 < obs.x < 210: # Wider window for action checks
                    collision = False
                    action_success = False
                    
                    if self.is_dashing: 
                        action_success = True # Dash passes all
                    else:
                        if obs.type == "spike":
                            if self.is_jumping: action_success = True
                            else: collision = True
                        elif obs.type == "wall":
                            if self.is_sliding: action_success = True
                            else: collision = True
                        elif obs.type == "orb":
                            if self.last_action == "PARRY": action_success = True
                            else: collision = True
                        elif obs.type == "barrier":
                            if self.last_action == "STRIKE": action_success = True
                            else: collision = True
                    
                    if action_success:
                        diff = abs(obs.spawn_time - self.current_game_time)
                        if diff < 0.2: # Successful action in window
                            obs.passed = True
                            judgment = "PERFECT" if diff < 0.08 else "GOOD"
                            self.register_hit(300 if judgment=="PERFECT" else 150, judgment, obs.x, self.player_y)
                    elif collision:
                        obs.hit = True
                        self.register_hit(0, "MISS", obs.x, self.player_y)

            if obs.x < -100:
                if not obs.hit and not obs.passed:
                     self.register_hit(0, "MISS", 0, self.player_y)
                self.obstacles.remove(obs)

        # SFX/Visuals logic
        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0: self.particles.remove(p)
        for ft in list(self.floating_texts):
            ft.update(dt)
            if ft.alpha <= 0: self.floating_texts.remove(ft)
        for snow in self.snow_particles:
            snow.update(dt, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, pulse_force=2 if self.fever_mode else 0)

        if self.current_game_time > self.song_duration + 2:
            self.game_over = True

    def register_hit(self, score_add, judgment, x_pos, y_pos):
        mult = 2 if self.fever_mode else 1
        self.score += score_add * mult
        self.hit_log.append((self.current_game_time, judgment))
        
        if judgment == "MISS":
            self.combo = 0
            self.health = max(0, self.health - 12)
            self.misses += 1
            self.vibe_meter = max(0, self.vibe_meter - 10)
            if self.audio_manager: self.audio_manager.play_sfx("miss")
            self.cam_shake = 10
        else:
            self.combo += 1
            if judgment == "PERFECT": 
                self.perfects += 1
                self.vibe_meter = min(100, self.vibe_meter + 5)
            else: 
                self.goods += 1
                self.vibe_meter = min(100, self.vibe_meter + 2)
            if self.audio_manager: 
                name = "perfect" if judgment=="PERFECT" else "good"
                self.audio_manager.play_sfx(name)
            
        self.max_combo = max(self.max_combo, self.combo)
        self.spawn_floating_text(judgment, 200, y_pos - 50, (255, 255, 255) if judgment != "MISS" else (255, 50, 50))
        
        color = (0, 255, 255) if judgment != "MISS" else (255, 50, 50)
        self.spawn_particles(200, y_pos, color)

    def spawn_particles(self, x, y, color):
        for _ in range(12): self.particles.append(Particle(x, y, color))

    def spawn_floating_text(self, text, x, y, color):
        self.floating_texts.append(FloatingText(text, x, y, color))

    def draw(self, current_time):
        off_x = random.randint(-self.cam_shake, self.cam_shake) if self.cam_shake > 0 else 0
        off_y = random.randint(-self.cam_shake, self.cam_shake) if self.cam_shake > 0 else 0
        
        bg_color = (5, 5, 20)
        if self.fever_mode: bg_color = (25, 5, 45)
        self.screen.fill(bg_color)
        
        # Parallax/Grid
        grid_color = (25, 25, 50)
        grid_spacing = 100
        shift = (self.current_game_time * self.scroll_speed * 0.5) % grid_spacing
        for i in range(0, constants.SCREEN_WIDTH + grid_spacing, grid_spacing):
            pygame.draw.line(self.screen, grid_color, (i - shift, 0), (i - shift, self.ground_y))

        # Ground
        ground_color = (30, 30, 55) if not self.fever_mode else (80, 20, 100)
        pygame.draw.rect(self.screen, ground_color, (0, self.ground_y, constants.SCREEN_WIDTH, 100))
        line_color = (0, 255, 255) if not self.fever_mode else (255, 0, 255)
        pygame.draw.line(self.screen, line_color, (0, self.ground_y), (constants.SCREEN_WIDTH, self.ground_y), 5)

        for snow in self.snow_particles: snow.draw(self.screen)

        # Player Visuals
        p_width, p_height = 54, 64
        if self.is_sliding: p_height = 32
        
        p_color = (0, 255, 255)
        if self.last_action == "PARRY": p_color = (0, 150, 255)
        elif self.last_action == "STRIKE": p_color = (180, 0, 255)
        if self.is_dashing: p_color = (255, 255, 255)
        if self.fever_mode: 
             # Pulse color in fever
             fact = (math.sin(pygame.time.get_ticks() / 100.0) + 1) / 2
             p_color = (int(255 * fact), 255, int(150 * (1-fact)))

        player_rect = pygame.Rect(150 + off_x, self.player_y - p_height + off_y, p_width, p_height)
        
        # Action Aura
        if self.last_action:
             aura_rect = player_rect.inflate(20, 20)
             pygame.draw.rect(self.screen, p_color, aura_rect, 2, border_radius=10)

        pygame.draw.rect(self.screen, p_color, player_rect, border_radius=8)
        pygame.draw.rect(self.screen, (255, 255, 255), player_rect, 2, border_radius=8)

        # Obstacles
        for obs in self.obstacles:
            obs.draw(self.screen, self.ground_y, self.fever_mode)

        # Visuals
        for p in self.particles: p.draw(self.screen)
        for ft in self.floating_texts: ft.draw(self.screen)

        # HUD
        font_large = pygame.font.SysFont("Outfit", 45, bold=True)
        self.screen.blit(font_large.render(f"{self.score}", True, (255, 255, 255)), (30, 30))
        
        if self.combo > 1:
            c_color = (0, 255, 255) if not self.fever_mode else (255, 255, 0)
            self.screen.blit(font_large.render(f"{self.combo}x", True, c_color), (30, 85))
            
        # Vibe Meter
        pygame.draw.rect(self.screen, (20, 20, 20), (30, 150, 200, 12), border_radius=6)
        vibe_w = int(self.vibe_meter * 2)
        v_color = (0, 255, 255) if not self.fever_mode else (255, 0, 255)
        pygame.draw.rect(self.screen, v_color, (30, 150, vibe_w, 12), border_radius=6)

        # Health
        pygame.draw.rect(self.screen, (20, 20, 20), (constants.SCREEN_WIDTH - 230, 30, 200, 12), border_radius=6)
        pygame.draw.rect(self.screen, (255, 50, 50), (constants.SCREEN_WIDTH - 230, 30, int(self.health * 2), 12), border_radius=6)

        # Key Guide (Helper)
        g_font = pygame.font.SysFont("Outfit", 20, bold=True)
        guides = [("D: Parry", (0, 150, 255)), ("F: Jump", (255, 50, 50)), 
                  ("J: Slide", (255, 200, 0)), ("K: Strike", (180, 0, 255))]
        for i, (txt, clr) in enumerate(guides):
            self.screen.blit(g_font.render(txt, True, clr), (30, constants.SCREEN_HEIGHT - 80 + i*18))

    def get_progress(self):
        if not self.audio_manager or self.audio_manager.song_duration <= 0: return 0.0
        return (self.audio_manager.get_pos() / self.audio_manager.song_duration) * 100.0
