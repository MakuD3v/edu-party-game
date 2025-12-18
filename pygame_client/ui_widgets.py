"""
UI Widgets for EDU-PARTY - School-themed interactive components
"""
import pygame
from typing import Callable, Optional, Tuple, List
from assets import render_crayon_text, render_chalk_text, PENCIL_YELLOW, CHALKBOARD_GREEN, ERASER_PINK


class Button:
    """School-themed clickable button."""
    
    def __init__(self, x: int, y: int, width: int, height: int, text: str, 
                 color: Tuple[int, int, int] = PENCIL_YELLOW,
                 text_color: Tuple[int, int, int] = (0, 0, 0),
                 on_click: Optional[Callable] = None):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.color = color
        self.text_color = text_color
        self.on_click = on_click
        self.hovered = False
        self.pressed = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle mouse events. Returns True if button was clicked."""
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                self.pressed = True
        
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed and self.hovered:
                self.pressed = False
                if self.on_click:
                    self.on_click()
                return True
            self.pressed = False
        
        return False
    
    def draw(self, screen: pygame.Surface):
        """Draw the button."""
        # Adjust color if hovered/pressed
        color = self.color
        if self.pressed:
            color = tuple(max(0, c - 40) for c in self.color)
        elif self.hovered:
            color = tuple(min(255, c + 20) for c in self.color)
        
        # Draw button background
        pygame.draw.rect(screen, color, self.rect, border_radius=10)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 3, border_radius=10)
        
        # Draw text
        text_surface = render_crayon_text(self.text, 32, self.text_color)
        text_rect = text_surface.get_rect(center=self.rect.center)
        screen.blit(text_surface, text_rect)


class TextInput:
    """Editable text input field."""
    
    def __init__(self, x: int, y: int, width: int, height: int, 
                 initial_text: str = "", max_length: int = 20):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = initial_text
        self.max_length = max_length
        self.active = False
        self.cursor_visible = True
        self.cursor_timer = 0
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        """Handle keyboard/mouse events. Returns True if text changed."""
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.active = self.rect.collidepoint(event.pos)
        
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.active = False
                return True
            elif event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
                return True
            elif event.unicode.isprintable() and len(self.text) < self.max_length:
                self.text += event.unicode
                return True
        
        return False
    
    def update(self, dt: float):
        """Update cursor blink animation."""
        self.cursor_timer += dt
        if self.cursor_timer > 0.5:
            self.cursor_visible = not self.cursor_visible
            self.cursor_timer = 0
    
    def draw(self, screen: pygame.Surface):
        """Draw the text input field."""
        # Background
        color = (255, 255, 255) if self.active else (240, 240, 240)
        pygame.draw.rect(screen, color, self.rect, border_radius=5)
        pygame.draw.rect(screen, (0, 0, 0), self.rect, 2, border_radius=5)
        
        # Text
        font = pygame.font.Font(None, 32)
        text_surface = font.render(self.text, True, (0, 0, 0))
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 10))
        
        # Cursor
        if self.active and self.cursor_visible:
            cursor_x = self.rect.x + 10 + text_surface.get_width()
            pygame.draw.line(
                screen, (0, 0, 0),
                (cursor_x, self.rect.y + 8),
                (cursor_x, self.rect.y + self.rect.height - 8),
                2
            )


class CharacterPreview:
    """Visual preview of character with customization."""
    
    def __init__(self, x: int, y: int, size: int = 64):
        self.x = x
        self.y = y
        self.size = size
    
    def draw(self, screen: pygame.Surface, color: str, gear: List[str]):
        """Draw character with current customization."""
        # Color mapping
        color_map = {
            "red": (237, 41, 57),
            "blue": (31, 117, 254),
            "green": (28, 172, 120)
        }
        body_color = color_map.get(color, (237, 41, 57))
        
        # Draw body (circle)
        center = (self.x + self.size // 2, self.y + self.size // 2)
        pygame.draw.circle(screen, body_color, center, self.size // 2)
        pygame.draw.circle(screen, (0, 0, 0), center, self.size // 2, 3)
        
        # Draw eyes
        eye_y = center[1] - self.size // 6
        pygame.draw.circle(screen, (255, 255, 255), (center[0] - 10, eye_y), 6)
        pygame.draw.circle(screen, (255, 255, 255), (center[0] + 10, eye_y), 6)
        pygame.draw.circle(screen, (0, 0, 0), (center[0] - 10, eye_y), 3)
        pygame.draw.circle(screen, (0, 0, 0), (center[0] + 10, eye_y), 3)
        
        # Draw smile
        pygame.draw.arc(
            screen, (0, 0, 0),
            (center[0] - 15, center[1] - 5, 30, 20),
            3.14, 0, 3
        )
        
        # Draw gear
        if "glasses" in gear:
            # Glasses
            pygame.draw.circle(screen, (0, 0, 0), (center[0] - 10, eye_y), 8, 2)
            pygame.draw.circle(screen, (0, 0, 0), (center[0] + 10, eye_y), 8, 2)
            pygame.draw.line(screen, (0, 0, 0), (center[0] - 2, eye_y), (center[0] + 2, eye_y), 2)
        
        if "cap" in gear:
            # Graduation cap
            cap_y = center[1] - self.size // 2 - 10
            # Square top
            points = [
                (center[0] - 20, cap_y),
                (center[0] + 20, cap_y),
                (center[0] + 20, cap_y + 5),
                (center[0] - 20, cap_y + 5)
            ]
            pygame.draw.polygon(screen, (0, 0, 0), points)
            # Cap base
            pygame.draw.rect(screen, (0, 0, 0), (center[0] - 15, cap_y + 5, 30, 8))
            # Tassel
            pygame.draw.line(screen, (218, 165, 32), (center[0], cap_y), (center[0] + 15, cap_y - 8), 2)
            pygame.draw.circle(screen, (218, 165, 32), (center[0] + 15, cap_y - 8), 3)
        
        if "backpack" in gear:
            # Backpack (behind character)
            back_x = center[0] + self.size // 2 - 5
            back_rect = pygame.Rect(back_x - 15, center[1] - 10, 18, 25)
            pygame.draw.rect(screen, (139, 90, 43), back_rect, border_radius=3)
            pygame.draw.rect(screen, (0, 0, 0), back_rect, 2, border_radius=3)
            # Straps
            pygame.draw.line(screen, (101, 67, 33), 
                           (back_x - 12, center[1] - 8), 
                           (center[0] - 8, center[1]), 2)


class DeskWidget:
    """Display widget for a student desk in the lobby."""
    
    def __init__(self, x: int, y: int, width: int = 120, height: int = 140):
        self.rect = pygame.Rect(x, y, width, height)
    
    def draw(self, screen: pygame.Surface, player_data: dict):
        """Draw desk with player info."""
        # Draw desk background
        desk_color = (139, 90, 43)
        desk_rect = pygame.Rect(
            self.rect.x + 10, 
            self.rect.y + self.rect.height - 40,
            self.rect.width - 20, 
            35
        )
        pygame.draw.rect(screen, desk_color, desk_rect, border_radius=5)
        
        # Draw character above desk
        char_preview = CharacterPreview(
            self.rect.x + self.rect.width // 2 - 32,
            self.rect.y + 10,
            64
        )
        char_preview.draw(
            screen,
            player_data.get("color", "red"),
            player_data.get("gear", [])
        )
        
        # Draw username
        font = pygame.font.Font(None, 20)
        username = player_data.get("username", "Student")
        text_surface = font.render(username, True, (0, 0, 0))
        text_rect = text_surface.get_rect(
            centerx=self.rect.centerx,
            y=self.rect.y + 80
        )
        screen.blit(text_surface, text_rect)
        
        # Draw ready indicator
        if player_data.get("ready_status", False):
            # Green check mark
            pygame.draw.circle(
                screen, (0, 255, 0),
                (self.rect.right - 15, self.rect.y + 10),
                8
            )
            pygame.draw.circle(
                screen, (0, 0, 0),
                (self.rect.right - 15, self.rect.y + 10),
                8, 2
            )
