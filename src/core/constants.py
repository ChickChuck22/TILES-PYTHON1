import pygame

# Screen Settings
SCREEN_WIDTH = 400
SCREEN_HEIGHT = 800
FPS = 60

# Colors
COLOR_BG = (18, 18, 18)
COLOR_LANE_DIVIDER = (40, 40, 40)
COLOR_TILE = (255, 255, 255)
COLOR_TILE_HIT = (100, 255, 100, 150)
COLOR_TILE_MISS = (255, 100, 100, 150)
COLOR_TEXT = (255, 255, 255)
COLOR_ACCENT = (0, 184, 212)

# Keys
LANE_KEYS = [pygame.K_d, pygame.K_f, pygame.K_j, pygame.K_k]
LANE_NAMES = ['D', 'F', 'J', 'K']

# Game settings
TILE_SPEED = 500  # pixels per second
LANE_WIDTH = SCREEN_WIDTH // 4
