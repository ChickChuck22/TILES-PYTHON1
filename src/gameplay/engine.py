import pygame
import random
import src.core.constants as constants
# We still import specific colors for convenience, but they are static
from src.core.constants import COLOR_BG, COLOR_LANE_DIVIDER, COLOR_TILE, COLOR_TEXT, COLOR_ACCENT, LANE_WIDTH
import math
from src.core.messages import COMBO_MESSAGES

class FloatingText:
    _FONT = None

    @classmethod
    def get_font(cls):
        if cls._FONT is None:
            try:
                cls._FONT = pygame.font.SysFont("Outfit", 28, bold=True)
            except:
                cls._FONT = pygame.font.SysFont("Arial", 28, bold=True)
        return cls._FONT

    def __init__(self, text, x, y, color):
        self.text = text
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-100, 100)
        self.vy = random.uniform(-300, -150)
        self.alpha = 255
        self.life = 1.5 # Slightly shorter life for snappiness
        self.scale = 1.0
        self.rotation = random.uniform(-15, 15)
        
        # Pre-render
        font = self.get_font()
        self.base_surf = font.render(text, True, color)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt # Gravity
        self.life -= dt
        
        # Fade out logic
        if self.life < 0.5:
             self.alpha = int((self.life / 0.5) * 255)
        else:
             self.alpha = 255
             
        # Scale down slightly at end
        self.scale = 1.0 + (max(0, self.life - 1.0) * 0.2)

    def draw(self, screen):
        if self.alpha <= 0: return
        
        # Rotate and Scale
        # Optimization: Only rotozoom if scale/rotation changed significantly? 
        # For now, rotozoom is acceptable if we don't re-render text.
        s = pygame.transform.rotozoom(self.base_surf, self.rotation, self.scale)
        s.set_alpha(self.alpha)
        rect = s.get_rect(center=(int(self.x), int(self.y)))
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

class SnowParticle:
    def __init__(self, width, height):
        self.x = random.randint(0, width)
        self.y = random.randint(-height, constants.SCREEN_HEIGHT)
        self.base_speed = random.uniform(50, 150)
        self.vy = self.base_speed
        self.size = random.randint(2, 4)
        self.sway = random.uniform(0, 2 * math.pi)
        self.opacity = random.randint(100, 200)

    def update(self, dt, width, height, pulse_force=0):
        # Pulse force pushes UP (negative Y)
        # Apply force, but clamp max upward velocity
        if pulse_force > 0:
            self.vy -= pulse_force * 300 * dt
            # Clamp max upward speed to -200 (don't let it fly too fast)
            if self.vy < -200:
                self.vy = -200
        
        # Gravity / Return to base speed
        # If moving up (vy < 0), apply stronger gravity to bring it down fast
        if self.vy < self.base_speed:
            recovery_speed = 800 if self.vy < 0 else 200
            self.vy += recovery_speed * dt
        
        self.y += self.vy * dt
        self.x += math.sin(self.sway) * 50 * dt
        self.sway += 2 * dt
        
        if self.y > height:
            self.y = -10
            self.x = random.randint(0, width)
            self.vy = self.base_speed

    def draw(self, screen):
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        pygame.draw.circle(s, (255, 255, 255, self.opacity), (self.size//2, self.size//2), self.size//2)
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
            self.opacity = max(0, self.opacity - 400 * dt)
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
        self.health = 100.0 # Standard health logic
        self.multiplier = 1.0
        
        self.game_over = False
        self.paused = False
        self.pause_rect = pygame.Rect(20, 20, 50, 50) # Top-Left
        
        # Overlay UI
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
        
        # SNOW
        self.snow_particles = [SnowParticle(constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT) for _ in range(50)]
        self.current_game_time = -3.0
        
    def set_beats(self, beats):
        self.beat_timestamps = beats
        self.generate_tiles()
        self.is_ready = True


        
    def handle_click(self, x, y):
        # Check Pause
        if not self.paused:
            if self.pause_rect.collidepoint(x, y):
                return "PAUSE"
        else:
            # Check Resume/Menu
            if self.resume_rect and self.resume_rect.collidepoint(x, y):
                return "RESUME"
            if self.menu_rect and self.menu_rect.collidepoint(x, y):
                return "MENU"
        return None

    def handle_lane_touch(self, x_ratio, current_time):
        # Map 0-1 to 4 lanes
        lane_idx = int(x_ratio * 4)
        lane_idx = max(0, min(3, lane_idx)) # Clamp
        return self.handle_keydown(lane_idx, current_time) # Reuse keydown logic


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
        
        last_lane_times = [-10.0] * 4
        
        for i, timestamp in enumerate(self.beat_timestamps):
            num_notes = 1
            if random.random() < chord_chance:
                max_notes = 3 if self.difficulty in ["Impossible", "God", "Beyond"] else 2
                num_notes = random.randint(2, max_notes)
            
            # Smart Lane Selection (Anti-Collision)
            # Find available lanes where enough time has passed since last note
            
            # Dynamic Gap Calculation:
            # We want to ensure notes don't visually overlap.
            # Time gap needed = (Tile Height + Padding) / Speed
            # Tile Height is approx 130.
            # We use base speed for calculation (worst case).
            
            safe_pixel_gap = 140.0 # 130 height + 10 padding
            dynamic_min_gap = safe_pixel_gap / max(100, self.tile_speed)
            
            # Hard limit for physics (never below 0.05s)
            min_gap = max(0.05, dynamic_min_gap)
            
            candidates = [l for l in range(4) if timestamp - last_lane_times[l] >= min_gap]
            
            if not candidates:
                # COLLISION DETECTED -> DELETE NOTE
                # As requested: "se detectar, deleta"
                # We simply skip spawning this note.
                continue
            
            # Reduce note count if we don't have enough candidates
            actual_count = min(num_notes, len(candidates))
            if actual_count == 0: continue
            
            lanes = random.sample(candidates, actual_count)
            
            # Update last times
            for l in lanes:
                last_lane_times[l] = timestamp
            
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


    def reset_combo(self):
        self.combo = 0
        self.multiplier = 1.0
        # self.health -= 5 # Punishment
        
    def register_hit(self, score_add, judgment, x_pos, y_pos):
        self.score += int(score_add * self.multiplier)
        self.increment_combo()
        self.health = min(100, self.health + 2)
        
        # Color based on judgment
        text_color = (255, 215, 0) # Gold
        if judgment == "PERFECT":
            self.perfects += 1
            text_color = (50, 255, 50) # Green (Matches Note)
        elif judgment == "GOOD":
            self.goods += 1
            text_color = (0, 184, 212) # Blue/Cyan
            
        print(f"DEBUG HIT: {judgment} | Score: {self.score} | Combo: {self.combo}")
        self.spawn_floating_text(judgment, x_pos, y_pos, text_color)
        self.spawn_particles(x_pos, y_pos, text_color)

    def spawn_floating_text(self, text, x, y, color):
        self.floating_texts.append(FloatingText(text, x, y, color))

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
        self.game_over = False
        self.countdown = 3
        self.countdown_start = pygame.time.get_ticks()
        self.last_energy_idx = 0
        for tile in self.tiles:
            tile.clicked = False
            tile.missed = False
            tile.is_holding = False
            tile.hold_complete = False
            tile.opacity = 255
            tile.y = -tile.height

    def update(self, current_time_unused, dt):
        # We ignore current_time passed from main, because we manage our own sync for the delay
        self.current_game_time += dt
        
        real_time = self.current_game_time
        
        # Handle Music Start
        if real_time >= 0 and self.audio_manager and not self.audio_manager.is_playing:
            self.audio_manager.play()
            
        # If music IS playing, we could verify sync? 
        if self.audio_manager and self.audio_manager.is_playing:
            music_pos = self.audio_manager.get_pos()
            # If significant drift, sync? For now, let's use music position if positive
            if music_pos > 0:
                real_time = music_pos
        
        current_time = real_time

        # --- SMART SPEED LOGIC ---
        if self.custom_settings.get("smart_speed", False):
            # Get energy at current_time
            energy = 0.0
            profile = self.custom_settings.get("energy_profile", [])
            
            # Simple linear search or lookup (optimization: keep index hints)
            # Profile is sorted by time [[t, e], ...]]
            # Using binary search or just iterating if small enough.
            if not hasattr(self, 'last_energy_idx'): self.last_energy_idx = 0
            
            idx = self.last_energy_idx
            while idx < len(profile) - 1 and profile[idx+1][0] < current_time:
                idx += 1
            self.last_energy_idx = idx
            
            if 0 <= idx < len(profile):
                # Interpolate
                t1, e1 = profile[idx]
                if idx + 1 < len(profile):
                    t2, e2 = profile[idx+1]
                    ratio = (current_time - t1) / (t2 - t1) if (t2 - t1) > 0 else 0
                    ratio = max(0.0, min(1.0, ratio))
                    energy = e1 + (e2 - e1) * ratio
                else:
                    energy = e1
            
            # Map Energy 0.0-1.0 to Speed factor 1.0x - 1.7x (User Request)
            # 0.0 -> 1.0x (Base Speed - Never slower)
            # 1.0 -> 1.7x (Fast Climax, but readable)
            speed_factor = 1.0 + (energy * 0.7)
            
            # Base speed depends on difficulty too
            diff_speeds = {"Easy": 350, "Normal": 500, "Hard": 700, "Insane": 900, "Impossible": 1200, "God": 1600, "Beyond": 2100}
            base_diff_speed = diff_speeds.get(self.difficulty, 500)
            
            # Apply
            self.tile_speed = base_diff_speed * speed_factor

        if self.is_ready and self.beat_timestamps and current_time >= self.beat_timestamps[-1] + 2.0:
            self.game_over = True
        
        # Beat Pulse Logic
        snow_pulse = 0
        if self.beat_timestamps:
            # Find closest beat
            if not hasattr(self, 'next_beat_index'):
                 self.next_beat_index = 0
            
            while self.next_beat_index < len(self.beat_timestamps) and self.beat_timestamps[self.next_beat_index] < current_time:
                self.next_beat_index += 1
                # Scale pulse: 500 is normal speed. If 1200 (fast), reduce pulse.
                # factor = 500 / speed
                scale_factor = max(0.4, min(1.0, 500.0 / self.tile_speed))
                snow_pulse = 2.0 * scale_factor 
                
        # Also use lane pulses if manual hit
        manual_pulse = max(self.lane_pulses) if self.lane_pulses else 0
        snow_pulse = max(snow_pulse, manual_pulse * 3.0)
        
        for snow in self.snow_particles:
            snow.update(dt, constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT, snow_pulse)

        # GET READY VISUAL CUE (during negative time)
        if self.current_game_time < 0:
            if -3.0 <= self.current_game_time < -2.0 and not any(t.text == "GET READY" for t in self.floating_texts):
                 self.spawn_shoutout("GET READY")
            elif -1.0 <= self.current_game_time < 0.0 and not any(t.text == "GO!" for t in self.floating_texts):
                 pass

        for tile in self.tiles:
            was_holding = tile.is_holding
            tile.update(current_time, dt, self.tile_speed)
            if tile.is_holding:
                self.score += int(100 * dt)
            if was_holding and tile.hold_complete:
                # Do NOT call increment_combo here again if handle_keyup already did it.
                # But Natural Finish (no keyup) needs it?
                # Actually, natural finishes are rare if player is holding.
                # Let's ensure it's only called once.
                if not tile.clicked: # Re-use clicked for 'stats_registered' on natural finish
                     tile.clicked = True
                     self.increment_combo()
                     self.perfects += 1 # Natural complete = perfect
                     self.spawn_floating_text("PERFECT", tile.x + LANE_WIDTH//2, constants.SCREEN_HEIGHT-150, (50, 255, 50))
            
            if not tile.clicked and not tile.missed and not tile.is_holding and not tile.hold_complete:
                # Tighten miss threshold: 50 pixels past line
                if tile.y > constants.SCREEN_HEIGHT - 100:
                    tile.missed = True
                    self.trigger_damage()
                    print(f"DEBUG MISS: Lane {tile.lane}")
        self.particles = [p for p in self.particles if p.life > 0]
        for p in self.particles: p.update(dt)
        self.floating_texts = [t for t in self.floating_texts if t.life > 0]
        for t in self.floating_texts: t.update(dt)
        self.damage_alpha = max(0, self.damage_alpha - 400 * dt)
        self.combo_scale = max(1.0, self.combo_scale - 5 * dt)
        for i in range(4):
            self.lane_pulses[i] = max(0.0, self.lane_pulses[i] - 4.0 * dt)
            
        # CRITICAL FIX: Remove tiles that are way off screen or fully processed to prevent lag
        # Keep tiles if they are visible OR if they are active/holding
        self.tiles = [
            tile for tile in self.tiles 
            if tile.y < constants.SCREEN_HEIGHT + 200 or tile.is_holding or (tile.opacity > 0)
        ]

    def trigger_damage(self):
        self.damage_alpha = 180
        self.combo = 0
        self.multiplier = 1.0
        self.misses += 1

    def handle_keydown(self, lane_index, current_time):
        self.lane_pulses[lane_index] = 1.0
        hit_line_y = constants.SCREEN_HEIGHT - 150
        tolerance = 100 # Tightened from 120
        target_tile = None
        min_dist = 999
        
        # Logic: Find the closest note to the hit line
        for tile in self.tiles:
            # Optimization: Ignore tiles already being held or completed
            if tile.lane == lane_index and not tile.clicked and not tile.missed and not tile.is_holding and not tile.hold_complete:
                dist = abs(tile.y - hit_line_y)
                if dist < tolerance and dist < min_dist:
                    min_dist = dist
                    target_tile = tile

        if target_tile:
            if target_tile.duration > 0:
                # Hold note start
                target_tile.is_holding = True
                target_tile.hit_time_audio = current_time
                # Window for perfect: 25 pixels
                judgment = "PERFECT" if min_dist < 25 else "GOOD"
                self.register_hit(50, judgment, target_tile.x + LANE_WIDTH//2, hit_line_y)
                if self.audio_manager: self.audio_manager.play_sfx("tap")
            else:
                # Tap note
                target_tile.clicked = True
                judgment = "PERFECT" if min_dist < 25 else "GOOD"
                score_add = 300 if judgment == "PERFECT" else 150
                self.register_hit(score_add, judgment, target_tile.x + LANE_WIDTH//2, hit_line_y)
                if self.audio_manager: self.audio_manager.play_sfx("tap")
        else:
            # Ghost tap (Miss)
            print(f"DEBUG GHOST TAP: Lane {lane_index}")
            self.trigger_damage()
            self.spawn_floating_text("MISS!", lane_index * LANE_WIDTH + LANE_WIDTH//2, hit_line_y, (255, 50, 50))

    def handle_keyup(self, lane_index, current_time):
        if current_time is None: return
        for tile in self.tiles:
            if tile.lane == lane_index and tile.is_holding:
                # If we release near the end, it's a success
                if current_time >= tile.end_time - 0.2: # Slightly more lenient window
                    tile.is_holding = False
                    tile.hold_complete = True
                    # HOLDS now count as PERFECT for accuracy/stats
                    self.register_hit(150, "PERFECT", tile.x + LANE_WIDTH//2, constants.SCREEN_HEIGHT-150)
                else:
                    # Early release - Break combo
                    tile.is_holding = False
                    tile.missed = True
                    self.trigger_damage()
                    self.spawn_floating_text("DROP!", tile.x + LANE_WIDTH//2, constants.SCREEN_HEIGHT-150, (255, 50, 50))
                return

    def increment_combo(self):
        self.combo += 1
        self.max_combo = max(self.combo, self.max_combo)
        self.multiplier = 1.0 + (min(self.combo, 100) / 25.0) # Up to 5x multiplier
        self.combo_scale = 1.5
        
        show_combo = self.custom_settings.get("show_combo", True)
        if show_combo and self.combo in COMBO_MESSAGES:
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
                
        # Draw Snow
        for snow in self.snow_particles:
            snow.draw(self.screen)
            
        for p in self.particles: p.draw(self.screen)
        for t in self.floating_texts: t.draw(self.screen)
        if self.damage_alpha > 0:
            border_surf = pygame.Surface((screen_w, screen_h), pygame.SRCALPHA)
            pygame.draw.rect(border_surf, (255, 0, 0, int(self.damage_alpha)), (0, 0, screen_w, screen_h), 30)
            self.screen.blit(border_surf, (0, 0))
        main_font = pygame.font.SysFont("Outfit", 50, bold=True)
        score_surf = main_font.render(str(self.score), True, COLOR_TEXT)
        self.screen.blit(score_surf, (screen_w // 2 - score_surf.get_width() // 2, 50))
        
        # Check setting for Combo Text
        show_combo = self.custom_settings.get("show_combo", True)
        if show_combo and self.combo > 1:
            combo_font = pygame.font.SysFont("Outfit", int(30 * self.combo_scale), bold=True)
            combo_surf = combo_font.render(f"{self.combo} COMBO", True, (255, 215, 0) if self.combo >= 10 else COLOR_ACCENT)
            self.screen.blit(combo_surf, (screen_w // 2 - combo_surf.get_width() // 2, 110))
        diff_font = pygame.font.SysFont("Outfit", 18)
        diff_surf = diff_font.render(f"Difficulty: {self.difficulty}", True, (100, 100, 100))
        self.screen.blit(diff_surf, (10, 10))
        
        self.draw_timer(current_time)
        
        # Draw Pause Button (only if not paused, or maybe always?)
        if not self.paused and not self.game_over:
            pygame.draw.rect(self.screen, (200, 200, 200), self.pause_rect, border_radius=5)
            # Draw Pause Icon (||)
            pygame.draw.rect(self.screen, (0, 0, 0), (self.pause_rect.x + 15, self.pause_rect.y + 12, 6, 26))
            pygame.draw.rect(self.screen, (0, 0, 0), (self.pause_rect.x + 29, self.pause_rect.y + 12, 6, 26))

        if self.paused:
            self.draw_pause_overlay()

    def draw_pause_overlay(self):
        # Dark overlay
        overlay = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        font_title = pygame.font.SysFont("Outfit", 60, bold=True)
        text_title = font_title.render("PAUSED", True, (255, 255, 255))
        self.screen.blit(text_title, (constants.SCREEN_WIDTH//2 - text_title.get_width()//2, 200))

        # Buttons
        btn_w, btn_h = 240, 70
        cx = constants.SCREEN_WIDTH // 2
        
        self.resume_rect = pygame.Rect(cx - btn_w//2, 350, btn_w, btn_h)
        self.menu_rect = pygame.Rect(cx - btn_w//2, 450, btn_w, btn_h)
        
        # Resume Button
        pygame.draw.rect(self.screen, (0, 184, 212), self.resume_rect, border_radius=10)
        font_btn = pygame.font.SysFont("Outfit", 30, bold=True)
        text_resume = font_btn.render("RESUME", True, (255, 255, 255))
        self.screen.blit(text_resume, (self.resume_rect.centerx - text_resume.get_width()//2, self.resume_rect.centery - text_resume.get_height()//2))

        # Menu Button
        pygame.draw.rect(self.screen, (200, 50, 50), self.menu_rect, border_radius=10)
        text_menu = font_btn.render("MENU", True, (255, 255, 255))
        self.screen.blit(text_menu, (self.menu_rect.centerx - text_menu.get_width()//2, self.menu_rect.centery - text_menu.get_height()//2))

    def get_progress(self):
        if not self.audio_manager or self.audio_manager.song_duration <= 0:
            return 0.0
        return (self.audio_manager.get_pos() / self.audio_manager.song_duration) * 100.0

    def draw_timer(self, current_time):
        if self.song_duration <= 0: return
        
        # Calculate progress
        progress = min(1.0, max(0.0, current_time / self.song_duration))
        remaining = max(0, int(self.song_duration - current_time))
        
        # Positioning (Top Right)
        center_x, center_y = constants.SCREEN_WIDTH - 60, 60
        radius = 35
        rect = pygame.Rect(center_x - radius, center_y - radius, radius * 2, radius * 2)
        
        # 1. Background Circle (Grey)
        pygame.draw.circle(self.screen, (40, 40, 40), (center_x, center_y), radius, 5)
        
        # 2. Progress Arc (Cyan)
        # Angle in radians. Start at top (-pi/2) and go clockwise.
        # pygame.draw.arc uses start_angle, stop_angle.
        start_angle = -math.pi / 2
        # Flip progress for clockwise effect: end_angle = start_angle + (progress * 2*pi)
        # Note: Pygame arcs go counter-clockwise, so we subtract from the start to go "clockwise" visually.
        end_angle = start_angle - (progress * 2 * math.pi)
        
        # Fix: Pygame requires start_angle < stop_angle.
        # So for a sweep, we use (end_angle, start_angle)
        pygame.draw.arc(self.screen, COLOR_ACCENT, rect, min(start_angle, end_angle), max(start_angle, end_angle), 6)
        
        # 3. Digital Clock
        minutes = remaining // 60
        seconds = remaining % 60
        time_str = f"{minutes:02}:{seconds:02}"
        font = pygame.font.SysFont("Outfit", 22, bold=True)
        time_surf = font.render(time_str, True, COLOR_TEXT)
        # Position to the left of the circle
        self.screen.blit(time_surf, (center_x - radius - 70, center_y - time_surf.get_height() // 2))
