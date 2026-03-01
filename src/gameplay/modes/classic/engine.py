import pygame
import random
import os
import math
import src.core.constants as constants
from src.core.constants import COLOR_BG, COLOR_LANE_DIVIDER, COLOR_TILE, COLOR_TEXT, COLOR_ACCENT, LANE_WIDTH
from src.core.messages import COMBO_MESSAGES
from src.gameplay.shared.visuals import ShoutoutText, FloatingText, ConfettiParticle, Particle, SnowParticle

class Tile:
    def __init__(self, lane, spawn_time, duration=0):
        self.lane = lane
        self.spawn_time = spawn_time
        self.duration = duration
        self.end_time = spawn_time + duration
        self.clicked = False
        self.missed = False
        self.is_holding = False
        self.hold_complete = False
        self.hit_time_audio = None
        self.opacity = 255
        self.width = LANE_WIDTH
        self.height = 130
        self.x = lane * LANE_WIDTH
        self.y = -self.height

    def update(self, current_time, dt, speed):
        hit_line_y = constants.SCREEN_HEIGHT - 150
        if self.is_holding:
            self.y = hit_line_y
            if current_time >= self.end_time:
                self.is_holding = False
                self.hold_complete = True
            return
        if self.clicked or self.hold_complete:
            self.opacity = max(0, self.opacity - 400 * dt)
            return
        time_diff = current_time - self.spawn_time
        self.y = hit_line_y + (time_diff * speed)

    def draw(self, screen, speed, current_time, hidden_mode=False, sudden_mode=False, giant_mode=False, skin="Neon"):
        if self.opacity <= 0: return
        draw_opacity = self.opacity
        
        if hidden_mode and not (self.clicked or self.hold_complete or self.missed or self.is_holding):
            hit_line_y = constants.SCREEN_HEIGHT - 150
            fade_start = hit_line_y - 500
            fade_end = hit_line_y - 120
            if self.y > fade_start:
                dist_traveled = self.y - fade_start
                total_fade_dist = fade_end - fade_start
                ratio = 1.0 - max(0, min(1, dist_traveled / total_fade_dist))
                draw_opacity = int(draw_opacity * ratio)

        if sudden_mode and not (self.clicked or self.hold_complete or self.missed or self.is_holding):
            hit_line_y = constants.SCREEN_HEIGHT - 150
            sudden_start = -self.height
            sudden_end = hit_line_y - 400
            if self.y < sudden_end:
                dist_traveled = self.y - sudden_start
                total_fade_dist = sudden_end - sudden_start
                ratio = max(0, min(1, dist_traveled / total_fade_dist))
                draw_opacity = int(draw_opacity * ratio)
                
        if draw_opacity <= 1: return

        base_color = (100, 100, 100)
        hold_color = (50, 200, 255)
        clicked_color = (50, 255, 50)
        missed_color = (255, 50, 50)

        if skin == "Neon":
            base_color = COLOR_TILE
            hold_color = (50, 200, 255)
            clicked_color = (50, 255, 50)
            missed_color = (255, 50, 50)
        elif skin == "Piano":
            base_color = (255, 255, 255)
            hold_color = (150, 150, 150)
            clicked_color = (0, 0, 0)
            missed_color = (200, 0, 0)
        elif skin == "Minimal":
            base_color = (100, 100, 100)
            hold_color = (150, 150, 150)
            clicked_color = (50, 200, 50)
            missed_color = (200, 50, 50)
        elif skin == "Toxic":
            base_color = (0, 200, 0)
            hold_color = (150, 0, 200)
            clicked_color = (0, 255, 0)
            missed_color = (255, 0, 0)

        color = base_color
        if self.is_holding: color = hold_color
        elif self.clicked or self.hold_complete: color = clicked_color
        elif self.missed: color = missed_color
        
        draw_w = self.width
        draw_h = self.height
        visual_x = self.x + 2
        visual_y = self.y
        if giant_mode:
            draw_w = int(self.width * 1.4)
            draw_h = int(self.height * 1.3)
            visual_x -= (draw_w - self.width) // 2
        
        tile_surf = pygame.Surface((draw_w - 4, draw_h), pygame.SRCALPHA)
        color_with_alpha = (*color, draw_opacity)
        
        if self.duration > 0 and not self.hold_complete:
            visible_start_time = max(current_time, self.spawn_time)
            remaining_duration = max(0, self.end_time - visible_start_time)
            trail_height = int(remaining_duration * speed)
            
            if trail_height > 0:
                trail_surf = pygame.Surface((draw_w - 8, trail_height), pygame.SRCALPHA)
                trail_color = (*color, int(draw_opacity * 0.4))
                pygame.draw.rect(trail_surf, trail_color, (0, 0, draw_w - 8, trail_height), border_radius=4)
                screen.blit(trail_surf, (visual_x + 2, self.y - trail_height))
                
            if skin == "Neon":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=10)
                pygame.draw.rect(tile_surf, (255, 255, 255, draw_opacity), (0, 0, draw_w - 4, draw_h), 3, border_radius=10)
            elif skin == "Piano":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h))
                if color == (255, 255, 255):
                    pygame.draw.rect(tile_surf, (0, 0, 0, draw_opacity), (0, 0, draw_w - 4, draw_h), 2)
            elif skin == "Minimal":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h))
            elif skin == "Toxic":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=6)
                glow_surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color, int(draw_opacity * 0.5)), (0, 0, draw_w, draw_h), border_radius=6)
                screen.blit(glow_surf, (visual_x - 2, visual_y - 2))
                screen.blit(tile_surf, (visual_x, visual_y))
                return
        else:
            if skin == "Neon":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=6)
            elif skin == "Piano":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h))
                if color == (255, 255, 255):
                    pygame.draw.rect(tile_surf, (0, 0, 0, draw_opacity), (0, 0, draw_w - 4, draw_h), 2)
            elif skin == "Minimal":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h))
            elif skin == "Toxic":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=6)
                glow_surf = pygame.Surface((draw_w, draw_h), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*color, int(draw_opacity * 0.5)), (0, 0, draw_w, draw_h), border_radius=6)
                screen.blit(glow_surf, (visual_x - 2, visual_y - 2))
                screen.blit(tile_surf, (visual_x, visual_y))
                return
            
        screen.blit(tile_surf, (visual_x, visual_y))

class GameEngine:
    def __init__(self, screen, song_path, difficulty="Normal", custom_settings=None, song_duration=0, audio_manager=None):
        self.screen = screen
        self.audio_manager = audio_manager
        self.song_path = song_path
        self.difficulty = difficulty
        self.custom_settings = custom_settings or {}
        self.song_duration = float(song_duration)
        
        self.tiles = []
        self.beat_timestamps = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfects = 0
        self.goods = 0
        self.misses = 0
        self.health = 100.0
        self.multiplier = 1.0
        
        self.game_over = False
        self.paused = False
        self.pause_rect = pygame.Rect(20, 20, 50, 50)
        
        self.resume_rect = None
        self.menu_rect = None
        
        self.countdown = 3
        self.countdown_start = 0
        self.is_ready = False
        diff_speeds = {"Easy": 350, "Normal": 500, "Hard": 700, "Insane": 900, "Impossible": 1200, "God": 1600, "Beyond": 2100}
        self.tile_speed = self.custom_settings.get("speed", diff_speeds.get(difficulty, 500))
        self.particles = []
        self.floating_texts = []
        self.damage_alpha = 0
        self.combo_scale = 1.0
        self.lane_pulses = [0.0] * 4
        
        self.snow_particles = [SnowParticle(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT) for _ in range(50)]
        self.current_game_time = -3.0
        
        self.hidden_mode = self.custom_settings.get("hidden_notes", False)
        self.sudden_mode = self.custom_settings.get("sudden_notes", False)
        self.flashlight_mode = self.custom_settings.get("flashlight_mode", False)
        self.rainbow_road = self.custom_settings.get("rainbow_road", False)
        self.confetti_hit = self.custom_settings.get("confetti_hit", False)
        self.drunk_mode = self.custom_settings.get("drunk_mode", False)
        self.giant_tiles = self.custom_settings.get("giant_tiles", False)
        
        self.gameplay_surf = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        self.confetti = []
        self.hit_log = []
        self.shoutouts = []
        self.energy_profile = self.custom_settings.get("energy_profile", [])
        
        if self.audio_manager:
            for name, file in [("perfect", "hit_perfect.wav"), ("good", "hit_good.wav"), ("miss", "miss.wav")]:
                path = os.path.join("assets", "sfx", file)
                if not os.path.exists(path):
                    path = os.path.join("assets", "sfx", "tap.wav")
                self.audio_manager.load_sfx(name, path)

        self.selected_skin = self.custom_settings.get("selected_skin", "Neon")
        self.background_image = None
        if self.custom_settings.get("custom_background", True):
            song_dir = os.path.dirname(self.song_path)
            for ext in [".jpg", ".png", ".jpeg"]:
                bg_path = os.path.join(song_dir, "bg" + ext)
                if os.path.exists(bg_path):
                    try:
                        self.background_image = pygame.image.load(bg_path).convert_alpha()
                        self.background_image = pygame.transform.smoothscale(self.background_image, (constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT))
                    except:
                        pass
                    break
        
    def set_beats(self, beats):
        self.beat_timestamps = beats
        self.generate_tiles()
        self.is_ready = True

    def handle_click(self, x, y):
        if not self.paused:
            if self.pause_rect.collidepoint(x, y):
                return "PAUSE"
        else:
            if self.resume_rect and self.resume_rect.collidepoint(x, y):
                return "RESUME"
            if self.menu_rect and self.menu_rect.collidepoint(x, y):
                return "MENU"
        return None

    def handle_lane_touch(self, x_ratio, current_time):
        lane_idx = int(x_ratio * 4)
        lane_idx = max(0, min(3, lane_idx))
        return self.handle_keydown(lane_idx, current_time)

    def generate_tiles(self):
        self.tiles = []
        for t in self.beat_timestamps:
            lane = random.randint(0, 3)
            duration = 0
            if random.random() < self.custom_settings.get("hold_chance", 15) / 100.0:
                duration = random.uniform(0.5, 1.5)
            self.tiles.append(Tile(lane, t, duration))

    def update(self, dt, current_time):
        self.current_game_time = current_time
        for pulse in range(len(self.lane_pulses)):
            self.lane_pulses[pulse] = max(0, self.lane_pulses[pulse] - 5 * dt)
        
        self.combo_scale = max(1.0, self.combo_scale - 2 * dt)
        
        for tile in list(self.tiles):
            tile.update(current_time, dt, self.tile_speed)
            if not tile.missed and not tile.clicked and not tile.hold_complete:
                hit_line_y = constants.SCREEN_HEIGHT - 150
                if tile.y > hit_line_y + 100:
                    tile.missed = True
                    self.misses += 1
                    self.register_hit(0, "MISS", tile.x + constants.LANE_WIDTH//2, hit_line_y)
            
            if (tile.clicked or tile.hold_complete or tile.missed) and tile.opacity <= 0:
                self.tiles.remove(tile)

        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0: self.particles.remove(p)
        for c in list(self.confetti):
            c.update(dt)
            if c.life <= 0: self.confetti.remove(c)
        for ft in list(self.floating_texts):
            ft.update(dt)
            if ft.alpha <= 0: self.floating_texts.remove(ft)
        for s in list(self.shoutouts):
            s.update(dt)
            if s.life <= 0: self.shoutouts.remove(s)
            
        for snow in self.snow_particles:
            snow.update(dt, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT)

    def increment_combo(self):
        self.combo += 1
        self.max_combo = max(self.max_combo, self.combo)
        self.combo_scale = 1.5
        self.multiplier = 1.0 + (min(self.combo, 50) / 50.0)
        
        if self.combo % 50 == 0:
            msg = random.choice(COMBO_MESSAGES.get(self.combo, ["AWESOME!"]))
            self.shoutouts.append(ShoutoutText(msg, COLOR_ACCENT))

    def reset_combo(self):
        self.combo = 0
        self.multiplier = 1.0

    def trigger_damage(self):
        self.health = max(0, self.health - 10)
        self.damage_alpha = 150
        if self.health <= 0:
            self.game_over = True

    def register_hit(self, score_add, judgment, x_pos, y_pos):
        self.score += int(score_add * self.multiplier)
        self.hit_log.append((self.current_game_time, judgment))

        if self.audio_manager:
            if judgment == "PERFECT": self.audio_manager.play_sfx("perfect")
            elif judgment == "GOOD": self.audio_manager.play_sfx("good")

        if self.confetti_hit and judgment == "PERFECT":
            for _ in range(20):
                self.confetti.append(ConfettiParticle(x_pos, y_pos))

        text_color = (255, 255, 255)
        if judgment == "MISS":
            self.reset_combo()
            self.trigger_damage()
            text_color = (255, 50, 50)
        else:
            self.increment_combo()
            if judgment == "PERFECT":
                self.perfects += 1
                text_color = (50, 255, 50)
            elif judgment == "GOOD":
                self.goods += 1
                text_color = (0, 184, 212)
            self.spawn_particles(x_pos, y_pos, text_color)
        
        lane_idx = int(x_pos // constants.LANE_WIDTH)
        if 0 <= lane_idx < 4:
            self.lane_pulses[lane_idx] = 1.0
            
        self.spawn_floating_text(judgment, x_pos, y_pos, text_color)

    def spawn_floating_text(self, text, x, y, color):
        self.floating_texts.append(FloatingText(text, x, y, color))

    def spawn_particles(self, x, y, color):
        for _ in range(15):
             self.particles.append(Particle(x, y, color))

    def restart(self):
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.perfects = 0
        self.goods = 0
        self.misses = 0
        self.health = 100.0
        self.multiplier = 1.0
        self.floating_texts = []
        self.shoutouts = []
        self.particles = []
        self.hit_log = []
        self.game_over = False
        self.current_game_time = -3.0
        if self.audio_manager: self.audio_manager.stop()
        for tile in self.tiles:
            tile.clicked = False
            tile.missed = False
            tile.is_holding = False
            tile.hold_complete = False
            tile.opacity = 255
            tile.y = -tile.height

    def handle_keydown(self, lane_index, current_time):
        hit_line_y = constants.SCREEN_HEIGHT - 150
        tolerance = 100 
        target_tile = None
        min_dist = 999
        
        for tile in self.tiles:
            if tile.lane == lane_index and not tile.clicked and not tile.missed and not tile.is_holding and not tile.hold_complete:
                dist = abs(tile.y - hit_line_y)
                if dist < tolerance and dist < min_dist:
                    min_dist = dist
                    target_tile = tile

        if target_tile:
            if target_tile.duration > 0:
                target_tile.is_holding = True
                target_tile.hit_time_audio = current_time
                judgment = "PERFECT" if min_dist < 25 else "GOOD"
                self.register_hit(50, judgment, target_tile.x + constants.LANE_WIDTH//2, hit_line_y)
                # Removed redundant tap sound
            else:
                target_tile.clicked = True
                judgment = "PERFECT" if min_dist < 25 else "GOOD"
                score_add = 300 if judgment == "PERFECT" else 150
                self.register_hit(score_add, judgment, target_tile.x + constants.LANE_WIDTH//2, hit_line_y)
                # Removed redundant tap sound
        else:
            self.register_hit(0, "MISS", lane_index * constants.LANE_WIDTH + constants.LANE_WIDTH//2, hit_line_y)

    def handle_keyup(self, lane_index, current_time):
        if current_time is None: return
        for tile in self.tiles:
            if tile.lane == lane_index and tile.is_holding:
                if current_time >= tile.end_time - 0.2:
                    tile.is_holding = False
                    tile.hold_complete = True
                    self.register_hit(150, "PERFECT", tile.x + constants.LANE_WIDTH//2, constants.SCREEN_HEIGHT-150)
                else:
                    tile.is_holding = False
                    tile.missed = True
                    self.register_hit(0, "MISS", tile.x + constants.LANE_WIDTH//2, constants.SCREEN_HEIGHT-150)
                return

    def draw(self, current_time):
        target_surf = self.screen
        if self.drunk_mode:
            target_surf = self.gameplay_surf
            target_surf.fill((0, 0, 0, 0))

        if self.background_image:
            bg_copy = self.background_image.copy()
            bg_copy.set_alpha(80)
            target_surf.blit(bg_copy, (0, 0))

        lane_color = COLOR_LANE_DIVIDER
        if self.rainbow_road:
             t = pygame.time.get_ticks() / 1000.0
             lane_color = (int(127+127*math.sin(t)), int(127+127*math.sin(t+2)), int(127+127*math.sin(t+4)), 100)
        
        for i in range(1, 4):
            pygame.draw.line(target_surf, lane_color, (i * constants.LANE_WIDTH, 0), (i * constants.LANE_WIDTH, constants.SCREEN_HEIGHT))
        
        pygame.draw.rect(target_surf, (25, 25, 25), (0, constants.SCREEN_HEIGHT - 180, constants.SCREEN_WIDTH, 60))
        for i in range(4):
            intensity = self.lane_pulses[i]
            x_start = i * constants.LANE_WIDTH
            pulse_base = COLOR_ACCENT if not self.rainbow_road else lane_color[:3]
            if intensity > 0:
                glow_surf = pygame.Surface((constants.LANE_WIDTH, 60), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*pulse_base, int(intensity * 100)), (0, 0, constants.LANE_WIDTH, 60))
                target_surf.blit(glow_surf, (x_start, constants.SCREEN_HEIGHT - 180))
            pygame.draw.line(target_surf, pulse_base, (x_start, constants.SCREEN_HEIGHT-150), (x_start+constants.LANE_WIDTH, constants.SCREEN_HEIGHT-150), 3 + int(intensity*10))

        for tile in self.tiles:
            tile.draw(target_surf, self.tile_speed, current_time, 
                      hidden_mode=self.hidden_mode, 
                      sudden_mode=self.sudden_mode,
                      giant_mode=self.giant_tiles,
                      skin=self.selected_skin)
                      
        if self.flashlight_mode:
            f_surf = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            f_surf.fill((0, 0, 0, 245))
            pygame.draw.circle(f_surf, (0, 0, 0, 0), (constants.SCREEN_WIDTH//2, constants.SCREEN_HEIGHT-150), 200)
            target_surf.blit(f_surf, (0,0))

        for snow in self.snow_particles: snow.draw(target_surf)
        for p in self.particles: p.draw(target_surf)
        for c in self.confetti: c.draw(target_surf)
        for ft in self.floating_texts: ft.draw(target_surf)
        for s in self.shoutouts: s.draw(target_surf)
        if self.energy_profile: self.draw_visualizer(target_surf)

        if self.drunk_mode:
            t = pygame.time.get_ticks() / 1000.0
            rotated = pygame.transform.rotate(self.gameplay_surf, math.sin(t*2)*3)
            self.screen.blit(rotated, rotated.get_rect(center=(constants.SCREEN_WIDTH//2 + math.sin(t*5)*10, constants.SCREEN_HEIGHT//2 + math.cos(t*4)*5)).topleft)

        main_font = pygame.font.SysFont("Outfit", 50, bold=True)
        score_surf = main_font.render(str(self.score), True, COLOR_TEXT)
        self.screen.blit(score_surf, (constants.SCREEN_WIDTH // 2 - score_surf.get_width() // 2, 50))
        
        if self.combo > 1:
            combo_font = pygame.font.SysFont("Outfit", int(30 * self.combo_scale), bold=True)
            combo_surf = combo_font.render(f"{self.combo} COMBO", True, (255, 215, 0) if self.combo >= 10 else COLOR_ACCENT)
            self.screen.blit(combo_surf, (constants.SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, 110))

        self.draw_timer(current_time)
        if self.paused: self.draw_pause_overlay()

    def draw_visualizer(self, screen):
        current_energy = 0
        for t, e in self.energy_profile:
            if t > self.current_game_time:
                current_energy = e
                break
        bar_count = 30
        gap = 10
        total_w = constants.SCREEN_WIDTH - 100
        bar_w = (total_w - (bar_count-1)*gap) // bar_count
        for i in range(bar_count):
            h = int(current_energy * 500 * (math.sin(self.current_game_time * 10 + i) * 0.2 + 0.8))
            pygame.draw.rect(screen, (*COLOR_ACCENT, 100), (50 + (bar_w + gap) * i, constants.SCREEN_HEIGHT - 20 - max(2, h), bar_w, max(2, h)), border_radius=4)

    def draw_pause_overlay(self):
        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        font_title = pygame.font.SysFont("Outfit", 60, bold=True)
        text_title = font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text_title, (constants.SCREEN_WIDTH//2 - text_title.get_width()//2, 200))
        self.resume_rect = pygame.Rect(constants.SCREEN_WIDTH//2 - 120, 350, 240, 70)
        self.menu_rect = pygame.Rect(constants.SCREEN_WIDTH//2 - 120, 450, 240, 70)
        pygame.draw.rect(self.screen, (0, 184, 212), self.resume_rect, border_radius=10)
        pygame.draw.rect(self.screen, (200, 50, 50), self.menu_rect, border_radius=10)

    def draw_timer(self, current_time):
        if self.song_duration <= 0: return
        progress = min(1.0, max(0.0, current_time / self.song_duration))
        center_x, center_y = constants.SCREEN_WIDTH - 60, 60
        pygame.draw.circle(self.screen, (40, 40, 40), (center_x, center_y), 35, 5)
        rect = pygame.Rect(center_x-35, center_y-35, 70, 70)
        pygame.draw.arc(self.screen, COLOR_ACCENT, rect, -math.pi/2 - progress*2*math.pi, -math.pi/2, 6)
        minutes, seconds = max(0, int(self.song_duration - current_time)) // 60, max(0, int(self.song_duration - current_time)) % 60
        time_surf = pygame.font.SysFont("Outfit", 22, bold=True).render(f"{minutes:02}:{seconds:02}", True, COLOR_TEXT)
        self.screen.blit(time_surf, (center_x - 105, center_y - time_surf.get_height() // 2))

    def get_progress(self):
        if not self.audio_manager or self.audio_manager.song_duration <= 0: return 0.0
        return (self.audio_manager.get_pos() / self.audio_manager.song_duration) * 100.0
