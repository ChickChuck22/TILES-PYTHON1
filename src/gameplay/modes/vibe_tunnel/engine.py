import pygame
import random
import math
import os
import src.core.constants as constants
from src.gameplay.shared.visuals import FloatingText, Particle

class VibeOrb:
    def __init__(self, angle, spawn_time):
        self.angle = angle # 0 to 2*PI
        self.spawn_time = spawn_time
        self.dist = 0.0 # From center 0.0 to 1.0 (pass camera)
        self.hit = False
        self.passed = False
        self.size = 5

    def update(self, current_time, dt, speed):
        # We want it to be at dist=0.8 (player ring) at spawn_time
        # Let's say it takes 2 seconds to travel from 0 to 1.0
        travel_time = 1.5
        time_until_hit = self.spawn_time - current_time
        self.dist = 0.8 - (time_until_hit / travel_time)
        self.size = 5 + (self.dist * 30)

    def draw(self, screen, cx, cy, fever_mode=False):
        # ALLOW negative dist for countdown visibility (appears near vanishing point)
        visual_dist = self.dist
        draw_opacity = 255
        if visual_dist < 0:
            # Squeeze to keep it near center and dim it
            visual_dist = visual_dist / (1.0 - visual_dist / 0.5)
            draw_opacity = 100

        # Calculate screen pos based on angle and dist
        # We use a non-linear dist for better 3D feel
        # Using abs() for visual_dist so they don't jump when passing center
        screen_dist = (abs(visual_dist) ** 1.5) * (constants.SCREEN_WIDTH // 2)
        x = cx + math.cos(self.angle) * screen_dist
        y = cy + math.sin(self.angle) * screen_dist
        
        color = (0, 255, 255) if not fever_mode else (255, 255, 0)
        
        # Use alpha surface for dimming if needed
        if draw_opacity < 255:
            orb_surf = pygame.Surface((int(self.size*2+4), int(self.size*2+4)), pygame.SRCALPHA)
            pygame.draw.circle(orb_surf, (*color, draw_opacity), (int(self.size+2), int(self.size+2)), int(self.size))
            pygame.draw.circle(orb_surf, (255, 255, 255, draw_opacity), (int(self.size+2), int(self.size+2)), int(self.size), 2)
            screen.blit(orb_surf, (int(x - self.size - 2), int(y - self.size - 2)))
        else:
            pygame.draw.circle(screen, color, (int(x), int(y)), int(self.size))
            pygame.draw.circle(screen, (255, 255, 255), (int(x), int(y)), int(self.size), 2)

class VibeTunnelEngine:
    def __init__(self, screen, song_path, difficulty="Normal", custom_settings=None, song_duration=0, audio_manager=None, current_meta=None, next_meta=None):
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
        
        # Tunnel State
        self.cx = constants.SCREEN_WIDTH // 2
        self.cy = constants.SCREEN_HEIGHT // 2
        self.player_angle = 0.0 # 0 to 2*PI
        self.target_angle = 0.0
        self.rotation_speed = 8.0
        
        self.orbs = []
        self.beat_timestamps = []
        self.rings = [] # Visual hexagons
        
        # Warp Drive (Fever)
        self.vibe_meter = 0
        self.fever_mode = False
        self.fever_timer = 0
        self.auto_align = False
        
        # Visuals
        self.particles = []
        self.floating_texts = []
        self.stars = [ [random.random()*constants.SCREEN_WIDTH, random.random()*constants.SCREEN_HEIGHT, random.random()*2+1] for _ in range(100) ]
        self.energy_profile = self.custom_settings.get("energy_profile", [])
        
        if self.audio_manager:
            for name, file in [("perfect", "hit_perfect.wav"), ("good", "hit_good.wav"), ("miss", "miss.wav")]:
                path = os.path.join("assets", "sfx", file)
                if not os.path.exists(path):
                    path = os.path.join("assets", "sfx", "tap.wav")
                self.audio_manager.load_sfx(name, path)

    def set_beats(self, beats):
        self.beat_timestamps = beats
        self.generate_orbs()
        self.is_ready = True

    def generate_orbs(self):
        self.orbs = []
        for t in self.beat_timestamps:
            # Random angle for each orb
            angle = random.uniform(0, 2 * math.pi)
            self.orbs.append(VibeOrb(angle, t))

    def handle_click(self, x, y):
        return None

    def handle_lane_touch(self, x_ratio, current_time):
        # Orbit towards the touch angle
        dx = (x_ratio * constants.SCREEN_WIDTH) - self.cx
        dy = (pygame.mouse.get_pos()[1]) - self.cy
        self.target_angle = math.atan2(dy, dx)

    def handle_keydown(self, key_id, current_time):
        # Support A/D or Left/Right
        pass # Moving logic in update based on pygame.key.get_pressed

    def handle_keyup(self, lane_index, current_time):
        pass

    def update(self, dt):
        if self.audio_manager and self.audio_manager.is_playing:
            self.current_game_time = self.audio_manager.get_pos()
        else:
            self.current_game_time += dt
        
        # Movement Input
        keys = pygame.key.get_pressed()
        move_dir = 0
        if keys[pygame.K_LEFT] or keys[pygame.K_a]: move_dir -= 1
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]: move_dir += 1
        
        if self.auto_align and self.orbs:
            # Find nearest orb in front
            nearest = None
            min_dist = 999
            for o in self.orbs:
                if not o.hit and not o.passed and 0.4 < o.dist < 0.9:
                    if o.dist < min_dist:
                        min_dist = o.dist
                        nearest = o
            if nearest:
                # Smoothly lerp towards nearest orb angle
                diff = (nearest.angle - self.player_angle + math.pi) % (2*math.pi) - math.pi
                self.player_angle += diff * 10 * dt
        else:
            self.player_angle += move_dir * self.rotation_speed * dt
            
        self.player_angle %= (2 * math.pi)

        # Update Orbs
        for orb in list(self.orbs):
            orb.update(self.current_game_time, dt, 1.0)
            
            if not orb.hit and not orb.passed:
                # Check collision at the player ring (dist ~ 0.8)
                if 0.75 < orb.dist < 0.85:
                    # Angle diff
                    angle_diff = abs((orb.angle - self.player_angle + math.pi) % (2*math.pi) - math.pi)
                    if angle_diff < 0.35: # Close enough
                        orb.hit = True
                        judgment = "PERFECT" if angle_diff < 0.15 else "GOOD"
                        self.register_hit(judgment, orb.angle)
                
                elif orb.dist > 1.0:
                    orb.passed = True
                    self.register_hit("MISS", orb.angle)
            
            if orb.dist > 1.2:
                self.orbs.remove(orb)

        # Fever Logic
        if self.vibe_meter >= 10 and not self.fever_mode:
            self.fever_mode = True
            self.fever_timer = 5.0
            self.auto_align = True
            self.spawn_floating_text("WARP DRIVE!", self.cx, self.cy - 100, (255, 255, 0))
            
        if self.fever_mode:
            self.fever_timer -= dt
            if self.fever_timer <= 0:
                self.fever_mode = False
                self.auto_align = False
                self.vibe_meter = 0

        # Visual Rings
        # Add new ring on major beats if energy is high?
        # For now, just a timed pulse
        if int(self.current_game_time * 4) % 2 == 0:
             if not any(r['age'] < 0.1 for r in self.rings):
                 self.rings.append({'dist': 0.05, 'age': 0.0})
        
        for r in list(self.rings):
            r['dist'] += 1.5 * dt # Expand
            r['age'] += dt
            if r['dist'] > 1.5: self.rings.remove(r)

        # Effects
        for p in list(self.particles):
            p.update(dt)
            if p.life <= 0: self.particles.remove(p)
        for ft in list(self.floating_texts):
            ft.update(dt)
            if ft.alpha <= 0: self.floating_texts.remove(ft)
            
        # Stars
        for s in self.stars:
            s[1] += s[2] * (5 if self.fever_mode else 1)
            if s[1] > constants.SCREEN_HEIGHT:
                s[1] = 0
                s[0] = random.random() * constants.SCREEN_WIDTH

        if self.current_game_time > self.song_duration + 2:
            self.game_over = True

    def register_hit(self, judgment, angle):
        if judgment == "MISS":
            self.combo = 0
            self.health = max(0, self.health - 8)
            self.misses += 1
            self.vibe_meter = 0
            if self.audio_manager: self.audio_manager.play_sfx("miss")
        else:
            self.combo += 1
            mult = 2 if self.fever_mode else 1
            if judgment == "PERFECT":
                self.score += 300 * mult
                self.perfects += 1
                self.vibe_meter += 1
            else:
                self.score += 150 * mult
                self.goods += 1
            if self.audio_manager: 
                self.audio_manager.play_sfx("perfect" if judgment == "PERFECT" else "good")
        
        self.max_combo = max(self.max_combo, self.combo)
        
        # Effects at hit location
        dist = 0.8 * (constants.SCREEN_WIDTH // 2)
        hx = self.cx + math.cos(angle) * dist
        hy = self.cy + math.sin(angle) * dist
        self.spawn_floating_text(judgment, hx, hy, (255, 255, 255) if judgment != "MISS" else (255, 50, 50))
        for _ in range(8):
            self.particles.append(Particle(hx, hy, (0, 255, 255) if judgment != "MISS" else (255, 50, 50)))

    def spawn_floating_text(self, text, x, y, color):
        self.floating_texts.append(FloatingText(text, x, y, color))

    def draw(self, current_time):
        # Dark Background
        bg = (5, 0, 15) if not self.fever_mode else (15, 0, 30)
        self.screen.fill(bg)
        
        # Stars
        for s in self.stars:
            pygame.draw.circle(self.screen, (200, 200, 255), (int(s[0]), int(s[1])), int(s[2]))

        # Tunnel Rings (Hexagons)
        for r in self.rings:
            size = r['dist'] * (constants.SCREEN_WIDTH // 2)
            alpha = max(0, 255 - int(r['dist'] * 180))
            color = (0, 184, 212) if not self.fever_mode else (255, 0, 255)
            
            # Draw hexagon
            pts = []
            for i in range(6):
                a = (i * math.pi / 3) + (self.current_game_time) # Rotating tunnel
                px = self.cx + math.cos(a) * size
                py = self.cy + math.sin(a) * size
                pts.append((px, py))
            
            temp_surf = pygame.Surface((constants.SCREEN_WIDTH, constants.SCREEN_HEIGHT), pygame.SRCALPHA)
            pygame.draw.polygon(temp_surf, (*color, alpha), pts, 2)
            self.screen.blit(temp_surf, (0, 0))

        # Orbs
        for orb in self.orbs:
            orb.draw(self.screen, self.cx, self.cy, self.fever_mode)

        # Player Cursor (Orbiter)
        p_dist = 0.8 * (constants.SCREEN_WIDTH // 2)
        px = self.cx + math.cos(self.player_angle) * p_dist
        py = self.cy + math.sin(self.player_angle) * p_dist
        
        p_color = (255, 255, 255) if not self.fever_mode else (255, 255, 0)
        pygame.draw.circle(self.screen, p_color, (int(px), int(py)), 15)
        pygame.draw.circle(self.screen, (0, 0, 0), (int(px), int(py)), 8)
        # Orbit ring
        pygame.draw.circle(self.screen, (40, 40, 60), (self.cx, self.cy), int(p_dist), 1)

        # Effects
        for p in self.particles: p.draw(self.screen)
        for ft in self.floating_texts: ft.draw(self.screen)

        # HUD
        font = pygame.font.SysFont("Outfit", 40, bold=True)
        score_txt = font.render(f"SCORE: {self.score}", True, (255, 255, 255))
        self.screen.blit(score_txt, (30, 30))
        
        if self.combo > 1:
            c_color = (0, 255, 255) if not self.fever_mode else (255, 255, 0)
            self.screen.blit(font.render(f"{self.combo}x", True, c_color), (30, 80))
            
        # Meters
        pygame.draw.rect(self.screen, (30, 30, 30), (30, 140, 200, 12), border_radius=6)
        vibe_w = int((self.vibe_meter / 10.0) * 200)
        v_color = (0, 255, 255) if not self.fever_mode else (255, 255, 0)
        pygame.draw.rect(self.screen, v_color, (30, 140, vibe_w, 12), border_radius=6)
        
        if self.fever_mode:
            f_txt = font.render("WARP DRIVE ACTIVE", True, (255, 255, 0))
            self.screen.blit(f_txt, (constants.SCREEN_WIDTH//2 - f_txt.get_width()//2, 50))

    def get_progress(self):
        if not self.audio_manager or self.audio_manager.song_duration <= 0: return 0.0
        return (self.audio_manager.get_pos() / self.audio_manager.song_duration) * 100.0
