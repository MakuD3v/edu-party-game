"""
Asset Generator for EDU-PARTY - School Supplies Theme
Creates notebook paper backgrounds, crayon fonts, chalkboard UI elements.
"""
import pygame
import math
from typing import Tuple

# Educational Color Palette
PENCIL_YELLOW = (255, 223, 0)
CHALKBOARD_GREEN = (56, 87, 35)
ERASER_PINK = (255, 192, 203)
NOTEBOOK_BLUE = (135, 206, 250)
PAPER_WHITE = (255, 255, 248)
LINED_BLUE = (173, 216, 230)
CRAYON_RED = (237, 41, 57)
CRAYON_BLUE = (31, 117, 254)
CRAYON_GREEN = (28, 172, 120)
CHALK_WHITE = (245, 245, 245)
BLACKBOARD = (40, 54, 24)


def create_notebook_paper(width: int, height: int) -> pygame.Surface:
    """Generate notebook paper background with horizontal lines."""
    surface = pygame.Surface((width, height))
    surface.fill(PAPER_WHITE)
    
    # Draw horizontal lines
    line_spacing = 30
    for y in range(40, height, line_spacing):
        pygame.draw.line(surface, LINED_BLUE, (60, y), (width - 20, y), 1)
    
    # Draw vertical margin line
    pygame.draw.line(surface, ERASER_PINK, (60, 0), (60, height), 2)
    
    # Add some texture (slight noise)
    for i in range(100):
        x = pygame.math.Vector2(
            pygame.math.Vector2(0, 0).x + (hash(i * 13) % width),
            pygame.math.Vector2(0, 0).y + (hash(i * 17) % height)
        )
        color = (250, 250, 240)
        pygame.draw.circle(surface, color, (int(x.x), int(x.y)), 1)
    
    return surface


def create_chalkboard_panel(width: int, height: int) -> pygame.Surface:
    """Create chalkboard-style panel for UI elements."""
    surface = pygame.Surface((width, height))
    surface.fill(BLACKBOARD)
    
    # Add border (wooden frame effect)
    border_color = (139, 90, 43)
    pygame.draw.rect(surface, border_color, (0, 0, width, height), 8)
    
    # Add chalk dust texture
    for i in range(50):
        x = hash(i * 23) % width
        y = hash(i * 29) % height
        alpha = hash(i * 31) % 50
        color = (255, 255, 255, alpha)
        temp = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(temp, color, (1, 1), 1)
        surface.blit(temp, (x, y))
    
    return surface


def render_crayon_text(text: str, size: int, color: Tuple[int, int, int]) -> pygame.Surface:
    """Render text in crayon-style (thick, playful font)."""
    # Use bold font for crayon effect
    font = pygame.font.Font(None, size)
    font.set_bold(True)
    
    # Render with slight outline for thickness
    text_surface = font.render(text, True, color)
    
    # Add outline for crayon thickness effect
    outline_surface = pygame.Surface(
        (text_surface.get_width() + 4, text_surface.get_height() + 4),
        pygame.SRCALPHA
    )
    
    # Draw outline
    for dx in [-1, 0, 1]:
        for dy in [-1, 0, 1]:
            if dx != 0 or dy != 0:
                outline_surface.blit(
                    font.render(text, True, tuple(max(0, c - 50) for c in color)),
                    (2 + dx, 2 + dy)
                )
    
    # Draw main text
    outline_surface.blit(text_surface, (2, 2))
    
    return outline_surface


def render_chalk_text(text: str, size: int) -> pygame.Surface:
    """Render text in chalk style (white, slightly rough)."""
    font = pygame.font.Font(None, size)
    text_surface = font.render(text, True, CHALK_WHITE)
    
    # Add slight roughness
    result = pygame.Surface(text_surface.get_size(), pygame.SRCALPHA)
    result.blit(text_surface, (0, 0))
    
    # Add chalk dust particles
    for i in range(20):
        x = hash(text + str(i) + "x") % text_surface.get_width()
        y = hash(text + str(i) + "y") % text_surface.get_height()
        pygame.draw.circle(result, (255, 255, 255, 50), (x, y), 1)
    
    return result


def create_desk_widget(width: int, height: int, color: Tuple[int, int, int]) -> pygame.Surface:
    """Create a student desk widget for lobby display."""
    surface = pygame.Surface((width, height), pygame.SRCALPHA)
    
    # Draw desk (brown rectangle)
    desk_color = (139, 90, 43)
    pygame.draw.rect(surface, desk_color, (10, height - 40, width - 20, 35), border_radius=5)
    
    # Draw chair back
    chair_color = (101, 67, 33)
    pygame.draw.rect(surface, chair_color, (width // 2 - 15, height - 50, 30, 15), border_radius=3)
    
    # Draw seat
    pygame.draw.ellipse(surface, chair_color, (width // 2 - 20, height - 38, 40, 20))
    
    return surface


def create_raised_hand_icon(size: int) -> pygame.Surface:
    """Create a raised hand icon for ready status."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Draw hand (simplified)
    hand_color = (255, 220, 177)
    # Palm
    pygame.draw.circle(surface, hand_color, (size // 2, size // 2), size // 3)
    # Fingers
    for i in range(4):
        x = size // 2 - 10 + i * 7
        pygame.draw.rect(surface, hand_color, (x, size // 4, 5, size // 3), border_radius=2)
    
    # Thumb
    pygame.draw.ellipse(surface, hand_color, (size // 2 + 8, size // 2 - 5, 8, 15))
    
    return surface


def create_platform_sprite(width: int, height: int, color: Tuple[int, int, int]) -> pygame.Surface:
    """Create a platform for Math Dash game."""
    surface = pygame.Surface((width, height))
    
    # Main platform
    pygame.draw.rect(surface, color, (0, 0, width, height), border_radius=10)
    
    # Add highlight for 3D effect
    highlight = tuple(min(255, c + 30) for c in color)
    pygame.draw.rect(surface, highlight, (5, 5, width - 10, height // 2), border_radius=5)
    
    return surface


def create_timer_bell(size: int) -> pygame.Surface:
    """Create a school bell icon for timer."""
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    
    # Bell body
    bell_color = (218, 165, 32)
    points = [
        (size // 2, size // 4),
        (size // 4, size * 3 // 4),
        (size * 3 // 4, size * 3 // 4)
    ]
    pygame.draw.polygon(surface, bell_color, points)
    pygame.draw.circle(surface, bell_color, (size // 2, size // 4), size // 8)
    
    # Clapper
    pygame.draw.circle(surface, (150, 150, 150), (size // 2, size * 3 // 4), size // 10)
    
    return surface


# Pre-generate common assets on module load (after pygame.init())
_assets_cache = {}


def init_assets():
    """Initialize and cache common assets. Call after pygame.init()."""
    global _assets_cache
    
    # Cache notebook background
    _assets_cache["notebook_1280x720"] = create_notebook_paper(1280, 720)
    _assets_cache["chalkboard_400x300"] = create_chalkboard_panel(400, 300)
    _assets_cache["desk_120x100"] = create_desk_widget(120, 100, CRAYON_RED)
    _assets_cache["hand_icon_32"] = create_raised_hand_icon(32)
    _assets_cache["bell_icon_48"] = create_timer_bell(48)
    
    print("Assets initialized!")


def get_asset(key: str) -> pygame.Surface:
    """Get a cached asset."""
    return _assets_cache.get(key)
