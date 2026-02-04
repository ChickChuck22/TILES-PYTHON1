import pygame
import random
import src.core.constants as constants
# We still import specific colors for convenience, but they are static
from src.core.constants import COLOR_BG, COLOR_LANE_DIVIDER, COLOR_TILE, COLOR_TEXT, COLOR_ACCENT, LANE_WIDTH
import math
from src.core.messages import COMBO_MESSAGES

class FloatingText:
    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-300, -150)
        self.alpha = 255
        self.life = 2.0
        self.scale = 1.0
        self.rotation = random.uniform(-15, 15)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt
        self.life -= dt
        self.alpha = int((self.life / 2.0) * 255)
        self.scale = 1.0 + (1.0 - (self.life / 2.0)) * 0.5

    def draw(self, screen):
        if self.alpha <= 0: return
        font = pygame.font.SysFont("Outfit", 40, bold=True)
        text_surf = font.render(self.text, True, self.color)
        s = pygame.transform.rotozoom(text_surf, self.rotation, self.scale)
        s.set_alpha(self.alpha)
        rect = s.get_rect(center=(self.x, self.y))
        screen.blit(s, rect)

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-200, 200)
        self.vy = random.uniform(-400, -100)
        self.life = 1.0
        self.size = random.randint(2, 6)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 800 * dt
        self.life -= dt

    def draw(self, screen):
        alpha = int(self.life * 255)
        if alpha > 0:
            s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
            pygame.draw.rect(s, (*self.color, alpha), (0, 0, self.size, self.size))
            screen.blit(s, (self.x, self.y))

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
            self.opacity = max(0, self.opacity - 800 * dt)
            return
        time_diff = current_time - self.spawn_time
        self.y = hit_line_y + (time_diff * speed)

    def draw(self, screen, speed, current_time):
        if self.opacity <= 0: return
        color = COLOR_TILE
        if self.is_holding: color = (50, 200, 255)
        elif self.clicked or self.hold_complete: color = (50, 255, 50)
        elif self.missed: color = (255, 50, 50)
        tile_surf = pygame.Surface((self.width - 4, self.height), pygame.SRCALPHA)
        color_with_alpha = (*color, self.opacity)
        if self.duration > 0 and not self.hold_complete:
            visible_start_time = max(current_time, self.spawn_time)
            remaining_duration = max(0, self.end_time - visible_start_time)
            trail_height = int(remaining_duration * speed)
            if trail_height > 0:
                trail_surf = pygame.Surface((self.width - 8, trail_height), pygame.SRCALPHA)
                trail_color = (*color, int(self.opacity * 0.4))
                pygame.draw.rect(trail_surf, trail_color, (0, 0, self.width - 8, trail_height), border_radius=4)
                screen.blit(trail_surf, (self.x + 4, self.y - trail_height))
            pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, self.width - 4, self.height), border_radius=10)
            pygame.draw.rect(tile_surf, (255, 255, 255, self.opacity), (0, 0, self.width - 4, self.height), 3, border_radius=10)
        else:
            pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, self.width - 4, self.height), border_radius=6)
        screen.blit(tile_surf, (self.x + 2, self.y))

class GameEngine:
    def __init__(self, screen, song_path, difficulty="Normal", custom_settings=None):
        self.screen = screen
        self.song_path = song_path
        self.difficulty = difficulty
        self.custom_settings = custom_settings or {}
        self.tiles = []
        self.beat_timestamps = []
        self.score = 0
        self.combo = 0
        self.max_combo = 0
        self.game_over = False
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
        
    def set_beats(self, beats):
        self.beat_timestamps = beats
        self.generate_tiles()
        self.countdown_start = pygame.time.get_ticks()
        self.is_ready = True

    def generate_tiles(self):
        self.tiles = []
        lane_map = []
        chord_chance = self.custom_settings.get("chord_chance", None)
        if chord_chance is None:
            if self.difficulty in ["God", "Beyond"]: chord_chance = 0.35
            elif self.difficulty == "Impossible": chord_chance = 0.25
            elif self.difficulty == "Hard": chord_chance = 0.15
            elif self.difficulty == "Insane": chord_chance = 0.25
            else: chord_chance = 0.05
        hold_chance = self.custom_settings.get("hold_chance", 0.15)
        for timestamp in self.beat_timestamps:
            num_notes = 1
            if random.random() < chord_chance:
                max_notes = 3 if self.difficulty in ["Impossible", "God", "Beyond"] else 2
                num_notes = random.randint(2, max_notes)
            lanes = random.sample(range(4), num_notes)
            lane_map.append((timestamp, lanes))
        for i, (timestamp, lanes) in enumerate(lane_map):
            for lane in lanes:
                next_time_in_lane = 9999.0
                for j in range(i + 1, len(lane_map)):
                    if lane in lane_map[j][1]:
                        next_time_in_lane = lane_map[j][0]
                        break
                duration = 0
                if random.random() < hold_chance:
                    ideal_duration = random.uniform(0.6, 2.0)
                    safety_gap = 0.2
                    max_safe_duration = (next_time_in_lane - timestamp) - safety_gap
                    if max_safe_duration > 0.4:
                        duration = min(ideal_duration, max_safe_duration)
                self.tiles.append(Tile(lane, timestamp, duration))

    def spawn_particles(self, x, y, color):
        for _ in range(15):
            self.particles.append(Particle(x, y, color))

    def spawn_shoutout(self, text):
        self.floating_texts.append(FloatingText(text, constants.SCREEN_WIDTH // 2, constants.SCREEN_HEIGHT // 2, (255, 255, 0)))

    def restart(self):
        self.score = 0
        self.combo = 0
        self.damage_alpha = 0
        self.lane_pulses = [0.0] * 4
        self.floating_texts = []
        self.game_over = False
        self.countdown = 3
        self.countdown_start = pygame.time.get_ticks()
        for tile in self.tiles:
            tile.clicked = False
            tile.missed = False
            tile.is_holding = False
            tile.hold_complete = False
            tile.opacity = 255
            tile.y = -tile.height

    def update(self, current_time, dt):
        if self.is_ready and self.beat_timestamps and current_time >= self.beat_timestamps[-1] + 2.0:
            self.game_over = True
        for tile in self.tiles:
            was_holding = tile.is_holding
            tile.update(current_time, dt, self.tile_speed)
            if tile.is_holding:
                self.score += int(100 * dt)
            if was_holding and tile.hold_complete:
                self.increment_combo()
            if not tile.clicked and not tile.missed and not tile.is_holding and not tile.hold_complete:
                if tile.y > constants.SCREEN_HEIGHT:
                    tile.missed = True
                    self.trigger_damage()
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.life > 0]
        for t in self.floating_texts: t.update(dt)
        self.damage_alpha = max(0, self.damage_alpha - 400 * dt)
        self.combo_scale = max(1.0, self.combo_scale - 5 * dt)
        for i in range(4):
            self.lane_pulses[i] = max(0.0, self.lane_pulses[i] - 4.0 * dt)

    def trigger_damage(self):
        self.damage_alpha = 180
        self.combo = 0

    def handle_keydown(self, lane_index, current_time):
        self.lane_pulses[lane_index] = 1.0
        hit_line_y = constants.SCREEN_HEIGHT - 150
        tolerance = 120
        target_tile = None
        min_dist = 9999
        for tile in self.tiles:
            if tile.lane == lane_index and tile.is_holding:
                tile.is_holding = False
                tile.hold_complete = True
                self.increment_combo()
                break
        for tile in self.tiles:
            if tile.lane == lane_index and not tile.clicked and not tile.missed and not tile.is_holding and not tile.hold_complete:
                dist = abs(tile.y - hit_line_y)
                if dist < min_dist:
                    min_dist = dist
                    target_tile = tile
        if target_tile and min_dist < tolerance:
            if target_tile.duration > 0:
                target_tile.is_holding = True
                target_tile.hit_time_audio = current_time
            else:
                target_tile.clicked = True
                self.score += 10
                self.increment_combo()
            color = (0, 184, 212) if self.combo < 10 else (255, 215, 0)
            self.spawn_particles(target_tile.x + LANE_WIDTH//2, hit_line_y, color)
            return True
        self.trigger_damage()
        return False

    def handle_keyup(self, lane_index, current_time):
        for tile in self.tiles:
            if tile.lane == lane_index and tile.is_holding:
                if current_time >= tile.end_time - 0.1:
                    tile.is_holding = False
                    tile.hold_complete = True
                    self.increment_combo()
                else:
                    tile.is_holding = False
                    tile.missed = True
                    self.trigger_damage()
                return

    def increment_combo(self):
        self.combo += 1
        self.max_combo = max(self.combo, self.max_combo)
        self.combo_scale = 1.5
        if self.combo in COMBO_MESSAGES:
            self.spawn_shoutout(COMBO_MESSAGES[self.combo])

    def draw(self, current_time):
        screen_w = constants.SCREEN_WIDTH
        screen_h = constants.SCREEN_HEIGHT
        hit_line_y = screen_h - 150
        
        for i in range(1, 4):
            pygame.draw.line(self.screen, COLOR_LANE_DIVIDER, (i * LANE_WIDTH, 0), (i * LANE_WIDTH, screen_h))
        
        pygame.draw.rect(self.screen, (25, 25, 25), (0, hit_line_y - 30, screen_w, 60))
        for i in range(4):
            intensity = self.lane_pulses[i]
            x_start = i * LANE_WIDTH
            pulse_color = [min(255, c + int(intensity * 100)) for c in COLOR_ACCENT]
            thickness = 3 + int(intensity * 10)
            if intensity > 0:
                glow_surf = pygame.Surface((LANE_WIDTH, 60), pygame.SRCALPHA)
                glow_alpha = int(intensity * 100)
                pygame.draw.rect(glow_surf, (*COLOR_ACCENT, glow_alpha), (0, 0, LANE_WIDTH, 60))
                self.screen.blit(glow_surf, (x_start, hit_line_y - 30))
            pygame.draw.line(self.screen, pulse_color, (x_start, hit_line_y), (x_start + LANE_WIDTH, hit_line_y), thickness)
        for tile in self.tiles:
            if -500 < tile.y < screen_h + 100 or tile.clicked or tile.is_holding or tile.hold_complete:
                tile.draw(self.screen, self.tile_speed, current_time)
        for p in self.particles: p.draw(self.screen)
        for t in self.floating_texts: t.draw(self.screen)
        if self.damage_alpha > 0:
            border_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (255, 0, 0, int(self.damage_alpha)), (0, 0, screen_w, screen_h), 30)
            self.screen.blit(border_surf, (0, 0))
        main_font = pygame.font.SysFont("Outfit", 50, bold=True)
        score_surf = main_font.render(str(self.score), True, COLOR_TEXT)
        self.screen.blit(score_surf, (screen_w // 2 - score_surf.get_width() // 2, 50))
        if self.combo > 1:
            combo_font = pygame.font.SysFont("Outfit", int(30 * self.combo_scale), bold=True)
            combo_surf = combo_font.render(f"{self.combo} COMBO", True, (255, 215, 0) if self.combo >= 10 else COLOR_ACCENT)
            self.screen.blit(combo_surf, (screen_w // 2 - combo_surf.get_width() // 2, 110))
        diff_font = pygame.font.SysFont("Outfit", 18)
        diff_surf = diff_font.render(f"Difficulty: {self.difficulty}", True, (100, 100, 100))
        self.screen.blit(diff_surf, (10, 10))
