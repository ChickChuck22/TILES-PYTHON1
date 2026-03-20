import pygame
import random
import math
import src.core.constants as constants

class ShoutoutText:
    def __init__(self, text, color):
        self.text = text
        self.color = color
        self.life = 1.0
        self.size = 20
        self.font = pygame.font.SysFont("Arial", 60, bold=True)
        self.y = constants.SCREEN_HEIGHT // 2 - 100

    def update(self, dt):
        self.life -= dt * 0.8
        self.size = 60 + int((1.0 - self.life) * 40) # Grows

    def draw(self, screen):
        if self.life <= 0: return
        alpha = int(255 * self.life)
        s = self.font.render(self.text, True, self.color)
        s.set_alpha(alpha)
        rect = s.get_rect(center=(constants.SCREEN_WIDTH // 2, self.y))
        screen.blit(s, rect)

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
        self.life = 1.5
        self.scale = 1.0
        self.rotation = random.uniform(-15, 15)
        
        # Ensure text is not empty to avoid Pygame crash
        if not text or text.strip() == "":
            text = " "
            
        font = self.get_font()
        self.base_surf = font.render(text, True, color)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 400 * dt
        self.life -= dt
        
        if self.life < 0.5:
             self.alpha = int((self.life / 0.5) * 255)
        else:
             self.alpha = 255
        self.scale = 1.0 + (max(0, self.life - 1.0) * 0.2)

    def draw(self, screen):
        if self.alpha <= 0: return
        s = pygame.transform.rotozoom(self.base_surf, self.rotation, self.scale)
        s.set_alpha(self.alpha)
        rect = s.get_rect(center=(int(self.x), int(self.y)))
        screen.blit(s, rect)

class ConfettiParticle:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.vx = random.uniform(-300, 300)
        self.vy = random.uniform(-600, -200)
        self.life = 1.0
        self.size = random.randint(4, 8)
        self.color = (random.randint(50, 255), random.randint(50, 255), random.randint(50, 255))
        self.rotation = random.uniform(0, 360)
        self.rv = random.uniform(-10, 10)

    def update(self, dt):
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.vy += 800 * dt
        self.life -= dt * 1.5
        self.rotation += self.rv

    def draw(self, screen):
        if self.life <= 0: return
        alpha = int(255 * self.life)
        s = pygame.Surface((self.size, self.size), pygame.SRCALPHA)
        s.fill((*self.color, alpha))
        rotated = pygame.transform.rotate(s, self.rotation)
        screen.blit(rotated, (self.x, self.y))

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
        if pulse_force > 0:
            self.vy -= pulse_force * 300 * dt
            if self.vy < -200: self.vy = -200
        
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
