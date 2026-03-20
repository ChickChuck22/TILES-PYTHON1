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
        self._surface_cache = {} # (color, opacity, head_vs_trail, giant_mode) -> surface

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

    def _project_y(self, y):
        """Perspective squeeze for off-screen notes."""
        if y < 0:
            return y / (1.0 - y / 300.0)
        return y

    def _get_draw_params(self, current_time, hidden_mode, sudden_mode, skin):
        # 1. Base Colors
        base_color, hold_color, clicked_color, missed_color = (255, 255, 255), (50, 200, 255), (50, 255, 50), (255, 50, 50)
        
        if skin == "Neon":
            base_color, hold_color, clicked_color, missed_color = COLOR_TILE, (50, 200, 255), (50, 255, 50), (255, 50, 50)
        elif skin == "Piano":
            base_color, hold_color, clicked_color, missed_color = (255, 255, 255), (150, 150, 150), (0, 0, 0), (200, 0, 0)
        elif skin == "Minimal":
            base_color, hold_color, clicked_color, missed_color = (100, 100, 100), (150, 150, 150), (50, 200, 50), (200, 50, 50)
        elif skin == "Toxic":
            base_color, hold_color, clicked_color, missed_color = (0, 200, 0), (150, 0, 200), (0, 255, 0), (255, 0, 0)

        # 2. Final Color
        color = base_color
        if self.is_holding: color = hold_color
        elif self.clicked or self.hold_complete: color = clicked_color
        elif self.missed: color = missed_color

        # 3. Opacity Calculation (Animation)
        draw_opacity = self.opacity
        if self.y < 0:
            draw_opacity = int(draw_opacity * 0.6)

        # 4. Modifiers (Fade In/Out) - Only for active notes
        if not (self.clicked or self.hold_complete or self.missed or self.is_holding):
            hit_line_y = constants.SCREEN_HEIGHT - 150
            if hidden_mode:
                ratio = 1.0 - max(0, min(1, (self.y - (hit_line_y - 500)) / 380))
                draw_opacity = int(draw_opacity * ratio)
            elif sudden_mode:
                ratio = max(0, min(1, (self.y - (-self.height)) / (hit_line_y - 400 - (-self.height))))
                draw_opacity = int(draw_opacity * ratio)

        return color, draw_opacity

    def draw_trail(self, screen, speed, current_time, giant_mode=False, skin="Neon"):
        if self.duration <= 0 or self.hold_complete or self.opacity <= 0: return
        
        color, draw_opacity = self._get_draw_params(current_time, False, False, skin)
        if draw_opacity <= 5: return

        # Calculation
        visible_start_time = max(current_time, self.spawn_time)
        remaining_duration = max(0, self.end_time - visible_start_time)
        raw_trail_height = remaining_duration * speed
        
        if raw_trail_height <= 2: return
        
        # PERSPECTIVE TRAIL
        # The trail should connect to the TOP of the head.
        # Head's visual top is _project_y(y) + (height/2 - draw_h/2)
        v_y_head_top = self._project_y(self.y) + (self.height // 2) - (int(self.height * 1.3 if giant_mode else self.height) // 2)
        v_y_trail_top = self._project_y(self.y - raw_trail_height)
        v_trail_height = int(v_y_head_top - v_y_trail_top)
        
        if v_trail_height <= 2: return
        
        draw_w = int(self.width * 1.4) if giant_mode else self.width
        # Narrower trail to ensure it stays UNDER the head
        trail_w = draw_w - 16
        visual_x = self.x + (self.width // 2) - (trail_w // 2)

        trail_cache_key = (color, draw_opacity, "trail", v_trail_height, trail_w)
        trail_surf = self._surface_cache.get(trail_cache_key)
        if not trail_surf:
            trail_surf = pygame.Surface((trail_w, v_trail_height), pygame.SRCALPHA)
            # Darker, more transparent trail for better depth
            trail_color = [max(0, c - 40) for c in color]
            trail_color = (*trail_color, int(draw_opacity * 0.25)) 
            pygame.draw.rect(trail_surf, trail_color, (0, 0, trail_w, v_trail_height), border_radius=6)
            # Thin border for distinction
            pygame.draw.rect(trail_surf, (255, 255, 255, int(draw_opacity * 0.1)), (0, 0, trail_w, v_trail_height), 1, border_radius=6)
            self._surface_cache[trail_cache_key] = trail_surf
        
        screen.blit(trail_surf, (visual_x, v_y_trail_top))

    def draw_head(self, screen, speed, current_time, hidden_mode=False, sudden_mode=False, giant_mode=False, skin="Neon"):
        if self.opacity <= 0: return
        
        color, draw_opacity = self._get_draw_params(current_time, hidden_mode, sudden_mode, skin)
        if draw_opacity <= 5: return
        
        visual_y = self._project_y(self.y)

        draw_w = int(self.width * 1.4) if giant_mode else self.width
        draw_h = int(self.height * 1.3) if giant_mode else self.height
        
        # ANIMATION: Hit Pop (Scale up on click/complete)
        if self.clicked or self.hold_complete:
            # Scale up by 20% during fade
            scale = 1.0 + (1.0 - draw_opacity / 255.0) * 0.3
            draw_w = int(draw_w * scale)
            draw_h = int(draw_h * scale)

        visual_x = self.x + (self.width // 2) - (draw_w // 2)
        visual_y = visual_y + (self.height // 2) - (draw_h // 2)
        
        head_cache_key = (color, draw_opacity, "head", draw_w, draw_h, skin)
        tile_surf = self._surface_cache.get(head_cache_key)
        
        if not tile_surf:
            tile_surf = pygame.Surface((draw_w - 4, draw_h), pygame.SRCALPHA)
            color_with_alpha = (*color, draw_opacity)
            
            # Simple skin drawing for cache
            if skin == "Neon":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=10)
                pygame.draw.rect(tile_surf, (255, 255, 255, draw_opacity), (0, 0, draw_w - 4, draw_h), 3, border_radius=10)
            elif skin in ["Piano", "Minimal"]:
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h))
                if skin == "Piano" and color == (255, 255, 255):
                    pygame.draw.rect(tile_surf, (0, 0, 0, draw_opacity), (0, 0, draw_w - 4, draw_h), 2)
            elif skin == "Toxic":
                pygame.draw.rect(tile_surf, color_with_alpha, (0, 0, draw_w - 4, draw_h), border_radius=6)
            self._surface_cache[head_cache_key] = tile_surf
            
        screen.blit(tile_surf, (visual_x, visual_y))
        
        if len(self._surface_cache) > 200: # Larger cache to avoid constant clearing
             self._surface_cache.clear()

class GameEngine:
    def __init__(self, screen, song_path, difficulty="Normal", custom_settings=None, song_duration=0, audio_manager=None, current_meta=None, next_meta=None):
        self.screen = screen
        self.audio_manager = audio_manager
        self.song_path = song_path
        self.difficulty = difficulty
        self.custom_settings = custom_settings or {}
        self.song_duration = float(song_duration)
        self.current_meta = current_meta or {}
        self.next_meta = next_meta or {}
        
        # UI Metadata Surfaces
        self.current_art = self._load_py_image(self.current_meta.get("image"))
        self.next_art = self._load_py_image(self.next_meta.get("image"))
        
        # Notification State
        self.notif_timer = 0
        self.notif_duration = 6.0 # Show for 6 seconds
        self.notif_x = -400 # Slide from left
        self.notif_alpha = 0
        
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
        
    def _load_py_image(self, img_source):
        if not img_source: return None
        try:
            path = img_source
            if img_source.startswith("http"):
                import hashlib
                h = hashlib.md5(img_source.encode()).hexdigest()
                path = os.path.join("assets", "cache", "images", f"{h}.png")
            
            if os.path.exists(path):
                img = pygame.image.load(path).convert_alpha()
                return pygame.transform.smoothscale(img, (60, 60))
        except:
            pass
        return None

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
        # Track when each lane is free to prevent physical overlap
        last_end_times = [0.0, 0.0, 0.0, 0.0]
        min_gap = 0.08  # 80ms minimum gap between notes in the same lane
        
        # Sort beat timestamps just in case
        sorted_beats = sorted(self.beat_timestamps)
        
        for t in sorted_beats:
            # 1. Identify which lanes are currently free at time `t`
            free_lanes = [i for i, end in enumerate(last_end_times) if t >= end + min_gap]
            
            if not free_lanes:
                # If no lane is free (dense section), pick a random lane and shorten its previous note
                lane = random.randint(0, 3)
                # Reverse search for the previous tile in this lane to shorten it
                for prev_tile in reversed(self.tiles):
                    if prev_tile.lane == lane:
                        # Shorten the previous hold to make space
                        new_end_time = t - min_gap
                        prev_tile.end_time = new_end_time
                        prev_tile.duration = max(0, new_end_time - prev_tile.spawn_time)
                        break
            else:
                lane = random.choice(free_lanes)
            
            # 2. Determine duration (Hold Note)
            duration = 0
            hold_chance = self.custom_settings.get("hold_chance", 15)
            if random.random() < hold_chance / 100.0:
                # Durations are capped to 1.5s but will be shortened by the next note if needed
                duration = random.uniform(0.5, 1.5)
            
            self.tiles.append(Tile(lane, t, duration))
            last_end_times[lane] = t + duration

    def update(self, dt):
        # Time Sync Logic
        # During countdown, we just use dt (current_game_time starts at -3.0)
        # Once audio is busy, we sync with hardware but only move forward
        if self.audio_manager and self.audio_manager.get_busy():
            new_pos = self.audio_manager.get_pos()
            if new_pos > self.current_game_time:
                self.current_game_time = new_pos
            else:
                self.current_game_time += dt
        else:
            # During countdown or during very final silence, use delta-time
            self.current_game_time += dt
        
        current_time = self.current_game_time
        
        # Natural Song Completion: Only check after countdown finishes
        if current_time >= 0:
            if self.song_duration > 0:
                if current_time >= self.song_duration:
                    self.game_over = True
                elif not self.audio_manager.get_busy() and current_time > self.song_duration - 1.0:
                     self.game_over = True
            elif self.audio_manager and not self.audio_manager.get_busy() and current_time > 10.0:
                self.game_over = True
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
        
        self.update_notifications(dt)

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
        # ALWAYS draw to gameplay_surf for consistent Alpha/Layering
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
        # --- TWO-PASS RENDERING (Fixes Slider Layering) ---
        # Sort tiles by Y so that notes closer to the bottom are drawn LAST (on top)
        sorted_tiles = sorted(self.tiles, key=lambda t: t.y)
        
        # 1. DRAW ALL TRAILS FIRST (So they are always behind all heads)
        for tile in sorted_tiles:
            tile.draw_trail(target_surf, self.tile_speed, current_time, 
                            giant_mode=self.giant_tiles,
                            skin=self.selected_skin)

        # 2. DRAW ALL HEADS SECOND
        for tile in sorted_tiles:
            tile.draw_head(target_surf, self.tile_speed, current_time, 
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
        else:
            # Just blit the gameplay surface directly
            self.screen.blit(self.gameplay_surf, (0, 0))

        main_font = pygame.font.SysFont("Outfit", 50, bold=True)
        score_surf = main_font.render(str(self.score), True, COLOR_TEXT)
        self.screen.blit(score_surf, (constants.SCREEN_WIDTH // 2 - score_surf.get_width() // 2, 50))
        
        if self.combo > 1:
            combo_font = pygame.font.SysFont("Outfit", int(30 * self.combo_scale), bold=True)
            combo_surf = combo_font.render(f"{self.combo} COMBO", True, (255, 215, 0) if self.combo >= 10 else COLOR_ACCENT)
            self.screen.blit(combo_surf, (constants.SCREEN_WIDTH // 2 - combo_surf.get_width() // 2, 110))

        self.draw_timer(current_time)
        if self.paused: self.draw_pause_overlay()
        self.draw_notifications()

    def update_notifications(self, dt):
        if self.notif_timer < self.notif_duration:
            self.notif_timer += dt
            # Slide in (0 to 1.5s)
            if self.notif_timer < 1.5:
                t = self.notif_timer / 1.5
                self.notif_x = -400 + (420 * t) # Slide to x=20
                self.notif_alpha = int(255 * t)
            # Slide out (last 1.5s)
            elif self.notif_timer > self.notif_duration - 1.5:
                t = (self.notif_timer - (self.notif_duration - 1.5)) / 1.5
                self.notif_x = 20 - (420 * t)
                self.notif_alpha = int(255 * (1.0 - t))
            else:
                self.notif_x = 20
                self.notif_alpha = 255

    def draw_notifications(self):
        if self.notif_timer >= self.notif_duration: return
        
        # Now Playing Box
        notif_w, notif_h = 360, 80
        box = pygame.Surface((notif_w, notif_h), pygame.SRCALPHA)
        pygame.draw.rect(box, (30, 30, 30, int(self.notif_alpha * 0.8)), (0, 0, notif_w, notif_h), border_radius=12)
        pygame.draw.rect(box, (*COLOR_ACCENT, self.notif_alpha), (0, 0, notif_w, notif_h), 2, border_radius=12)
        
        # Album Art
        if self.current_art:
            art_copy = self.current_art.copy()
            art_copy.set_alpha(self.notif_alpha)
            box.blit(art_copy, (10, 10))
        else:
            pygame.draw.rect(box, (50, 50, 50, self.notif_alpha), (10, 10, 60, 60), border_radius=6)
            font_icon = pygame.font.SysFont("Segoe UI Symbol", 30)
            icon = font_icon.render("🎵", True, (255, 255, 255))
            icon.set_alpha(self.notif_alpha)
            box.blit(icon, (25, 20))
            
        # Text
        font_main = pygame.font.SysFont("Outfit", 20, bold=True)
        font_sub = pygame.font.SysFont("Outfit", 14)
        
        title = self.current_meta.get("title", os.path.splitext(os.path.basename(self.song_path))[0])
        artist = self.current_meta.get("artist", "Unknown Artist")
        
        txt_playing = font_sub.render("NOW PLAYING", True, COLOR_ACCENT)
        txt_title = font_main.render(title[:25], True, (255, 255, 255))
        txt_artist = font_sub.render(artist[:30], True, (180, 180, 180))
        
        for t in [txt_playing, txt_title, txt_artist]: t.set_alpha(self.notif_alpha)
        
        box.blit(txt_playing, (80, 12))
        box.blit(txt_title, (80, 30))
        box.blit(txt_artist, (80, 52))
        
        # Next Up (Small tag at bottom)
        if self.next_meta:
            next_title = self.next_meta.get("title", "Next Track")
            txt_next = font_sub.render(f"NEXT: {next_title[:20]}...", True, (120, 120, 120))
            txt_next.set_alpha(self.notif_alpha)
            box.blit(txt_next, (80, 68))

        self.screen.blit(box, (self.notif_x, 100))

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

    def get_results(self):
        """Returns the final game statistics."""
        return {
            "score": self.score,
            "max_combo": self.max_combo,
            "perfects": self.perfects,
            "goods": self.goods,
            "misses": self.misses,
            "song": os.path.basename(self.song_path),
            "rank": "F", # Rank is calculated in run.py
            "duration": self.song_duration
        }
