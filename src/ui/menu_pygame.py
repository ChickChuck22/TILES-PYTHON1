import pygame
import os
import json
from src.core.constants import *
from src.core.beat_detector import BeatDetector

def run_menu(songs, audio_manager):
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Titanium Piano - Android Menu")
    clock = pygame.time.Clock()
    
    # Fonts
    font_title = pygame.font.SysFont("Arial", 50, bold=True)
    font_item = pygame.font.SysFont("Arial", 40)
    font_small = pygame.font.SysFont("Arial", 30)
    
    # Colors
    COLOR_BG_MENU = (20, 20, 20)
    COLOR_ITEM = (200, 200, 200)
    COLOR_SELECTED = (0, 184, 212)
    COLOR_BTN = (60, 60, 60)
    
    scroll_y = 0
    item_height = 80
    
    buttons = []
    for i, song in enumerate(songs):
        buttons.append({"text": song, "rect": pygame.Rect(50, 150 + i * item_height, SCREEN_WIDTH - 100, 60)})

    # Volume Buttons
    vol_rects = {
        "m_minus": pygame.Rect(50, 600, 60, 60),
        "m_plus": pygame.Rect(250, 600, 60, 60),
        "s_minus": pygame.Rect(450, 600, 60, 60),
        "s_plus": pygame.Rect(650, 600, 60, 60)
    }
    
    # Combo Toggle Button
    combo_rect = pygame.Rect(50, 520, 260, 50)
    show_combo = True

    running = True
    selected_song = None
    
    # Cache for preview start times to avoid blocking
    preview_cache = {}
    
    def play_song_preview(song_name):
        song_path = os.path.join("assets/music", song_name)
        start_time = 0.0
        
        # Check cache logic duplicated from beat_detector to be fast
        import hashlib
        file_hash = hashlib.md5(song_name.encode()).hexdigest()
        cache_path = os.path.join("assets/cache", f"{file_hash}_Normal.json")
        
        if os.path.exists(cache_path):
            try:
                with open(cache_path, 'r') as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        start_time = data.get("preview_start", 0.0)
            except:
                pass
        
        audio_manager.play_preview(song_path, start_time)

    while running:
        dt = clock.tick(60) / 1000.0
        
        # Input
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return None, "Normal", [], {}
            
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.FINGERDOWN:
                if event.type == pygame.FINGERDOWN:
                    x = event.x * SCREEN_WIDTH
                    y = event.y * SCREEN_HEIGHT
                else:
                    x, y = event.pos
                
                # Volume Controls
                if vol_rects["m_minus"].collidepoint(x, y):
                    audio_manager.set_music_volume(audio_manager.music_volume - 0.1)
                elif vol_rects["m_plus"].collidepoint(x, y):
                    audio_manager.set_music_volume(audio_manager.music_volume + 0.1)
                elif vol_rects["s_minus"].collidepoint(x, y):
                    audio_manager.set_sfx_volume(audio_manager.sfx_volume - 0.1)
                elif vol_rects["s_plus"].collidepoint(x, y):
                    audio_manager.set_sfx_volume(audio_manager.sfx_volume + 0.1)
                    
                # Combo Toggle
                elif combo_rect.collidepoint(x, y):
                    show_combo = not show_combo
                
                # Check songs
                adjusted_y = y - scroll_y
                hit_song = False
                for i, btn in enumerate(buttons):
                    real_rect = btn["rect"].copy()
                    real_rect.y += scroll_y
                    if real_rect.collidepoint(x, y):
                        if selected_song == btn["text"]:
                            # Double tap to confirm? Or just tap button.
                            # For now, let's say tap selects, second tap plays?
                            # Actually, let's keep it simple: Tap selects and plays preview.
                            # We need a "START" button or just start.
                            # Let's make it: Tap selects & previews.
                            pass
                        selected_song = btn["text"]
                        play_song_preview(selected_song)
                        hit_song = True
                        break
                
                if not hit_song and selected_song:
                    # If tapped outside list (maybe on a Start button we should add?)
                    # For simplicity in this version, let's assume selecting is just preview, 
                    # we need a CONFIRM button.
                    pass

        # Draw
        screen.fill(COLOR_BG_MENU)
        
        # Title
        title_surf = font_title.render("Titanium Piano", True, COLOR_SELECTED)
        screen.blit(title_surf, (50, 50))
        
        # Volume UI
        pygame.draw.rect(screen, COLOR_BTN, vol_rects["m_minus"], border_radius=5)
        pygame.draw.rect(screen, COLOR_BTN, vol_rects["m_plus"], border_radius=5)
        text_mv = font_small.render(f"Music: {int(audio_manager.music_volume*100)}%", True, (255,255,255))
        screen.blit(text_mv, (120, 615))
        
        pygame.draw.rect(screen, COLOR_BTN, vol_rects["s_minus"], border_radius=5)
        pygame.draw.rect(screen, COLOR_BTN, vol_rects["s_plus"], border_radius=5)
        text_sv = font_small.render(f"SFX: {int(audio_manager.sfx_volume*100)}%", True, (255,255,255))
        screen.blit(text_sv, (520, 615))
        
        # Draw Combo Toggle
        color_combo = (0, 184, 212) if show_combo else (100, 100, 100)
        pygame.draw.rect(screen, color_combo, combo_rect, border_radius=5)
        text_combo = font_small.render(f"COMBO TEXT: {'ON' if show_combo else 'OFF'}", True, (255,255,255))
        screen.blit(text_combo, (combo_rect.x + 20, combo_rect.y + 10))
        
        # START BUTTON (if song selected)
        if selected_song:
            start_rect = pygame.Rect(SCREEN_WIDTH - 250, 600, 200, 60)
            pygame.draw.rect(screen, COLOR_SELECTED, start_rect, border_radius=10)
            start_text = font_item.render("PLAY", True, (255,255,255))
            screen.blit(start_text, (start_rect.x + 60, start_rect.y + 10))
            
            # Check Start Click
            if (pygame.mouse.get_pressed()[0]) and start_rect.collidepoint(pygame.mouse.get_pos()):
                 running = False
        
        # List
        for btn in buttons:
            real_rect = btn["rect"].copy()
            real_rect.y += scroll_y
            if -100 < real_rect.y < 600: # Limit list view
                color = COLOR_SELECTED if btn["text"] == selected_song else (40, 40, 40)
                pygame.draw.rect(screen, color, real_rect, border_radius=10)
                text_surf = font_item.render(btn["text"], True, COLOR_ITEM)
                screen.blit(text_surf, (real_rect.x + 20, real_rect.y + 10))
        
        pygame.display.flip()
        
    if not selected_song:
        return None, "Normal", [], {}

    # Default settings for Android
    detector = BeatDetector(os.path.join("assets/music", selected_song))
    beats_data = detector.analyze("Normal") 
    beats = beats_data["beats"] if isinstance(beats_data, dict) else beats_data
    
    return selected_song, "Normal", beats, {"chord_chance": None, "hold_chance": 0.15, "speed": 500, "show_combo": show_combo}
