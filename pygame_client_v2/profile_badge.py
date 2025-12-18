"""
Profile Badge UI Component
Displays in top-right corner with avatar and username.
"""
import pygame
from constants import CHALK_WHITE, SCHOOL_BUS_YELLOW, MAYHEM_PURPLE, SCREEN_WIDTH


class ProfileBadge:
    """Top-right corner profile badge component."""
    
    def __init__(self):
        """Initialize profile badge."""
        self._width: int = 220
        self._height: int = 90
        self._x: int = SCREEN_WIDTH - self._width - 20
        self._y: int = 20
        self._rect: pygame.Rect = pygame.Rect(self._x, self._y, self._width, self._height)
        self._hovered: bool = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events.
        
        Args:
            event: Pygame event
            
        Returns:
            True if badge was clicked
        """
        if event.type == pygame.MOUSEMOTION:
            self._hovered = self._rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._hovered:
                return True
        
        return False
    
    def render(self, surface: pygame.Surface, username: str, color: str, shape: str) -> None:
        """Render the profile badge.
        
        Args:
            surface: Pygame surface to draw on
            username: Player username
            color: Player color
            shape: Player shape
        """
        # Background panel with glow effect if hovered
        bg_color = CHALK_WHITE if not self._hovered else (255, 255, 255)
        pygame.draw.rect(surface, bg_color, self._rect, border_radius=15)
        pygame.draw.rect(surface, SCHOOL_BUS_YELLOW, self._rect, 3, border_radius=15)
        
        # Mini avatar (left side)
        avatar_x = self._x + 20
        avatar_y = self._y + self._height // 2
        self._render_mini_avatar(surface, avatar_x, avatar_y, color, shape, 30)
        
        # Username text
        font = pygame.font.Font(None, 28)
        username_surface = font.render(username, True, MAYHEM_PURPLE)
        username_rect = username_surface.get_rect(midleft=(avatar_x + 45, avatar_y - 10))
        surface.blit(username_surface, username_rect)
        
        # "Edit Profile" link
        link_font = pygame.font.Font(None, 20)
        link_text = "Edit Profile ✎"
        link_color = SCHOOL_BUS_YELLOW if self._hovered else (100, 100, 100)
        link_surface = link_font.render(link_text, True, link_color)
        link_rect = link_surface.get_rect(midleft=(avatar_x + 45, avatar_y + 15))
        surface.blit(link_surface, link_rect)
    
    def _render_mini_avatar(self, surface: pygame.Surface, x: int, y: int, 
                           color: str, shape: str, size: int) -> None:
        """Render mini character avatar.
        
        Args:
            surface: Pygame surface
            x: Center X coordinate
            y: Center Y coordinate
            color: Character color
            shape: Character shape
            size: Avatar size
        """
        # Color mapping
        color_map = {
            "red": (231, 76, 60),
            "blue": (52, 152, 219),
            "green": (46, 204, 113)
        }
        fill_color = color_map.get(color, (231, 76, 60))
        
        # Draw shape
        if shape == "circle":
            pygame.draw.circle(surface, fill_color, (x, y), size // 2)
            pygame.draw.circle(surface, MAYHEM_PURPLE, (x, y), size // 2, 2)
        
        elif shape == "square":
            rect = pygame.Rect(x - size//2, y - size//2, size, size)
            pygame.draw.rect(surface, fill_color, rect)
            pygame.draw.rect(surface, MAYHEM_PURPLE, rect, 2)
        
        elif shape == "triangle":
            points = [
                (x, y - size//2),
                (x - size//2, y + size//2),
                (x + size//2, y + size//2)
            ]
            pygame.draw.polygon(surface, fill_color, points)
            pygame.draw.polygon(surface, MAYHEM_PURPLE, points, 2)
        
        elif shape == "star":
            # 5-pointed star
            points = []
            import math
            for i in range(10):
                angle = math.pi / 2 + (2 * math.pi * i / 10)
                radius = (size // 2) if i % 2 == 0 else (size // 4)
                px = x + radius * math.cos(angle)
                py = y - radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, fill_color, points)
            pygame.draw.polygon(surface, MAYHEM_PURPLE, points, 2)
        
        elif shape == "hexagon":
            import math
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                px = x + (size // 2) * math.cos(angle)
                py = y + (size // 2) * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, fill_color, points)
            pygame.draw.polygon(surface, MAYHEM_PURPLE, points, 2)
