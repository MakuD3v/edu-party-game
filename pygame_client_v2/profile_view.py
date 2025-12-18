"""
Profile View - Character Customizer Screen
Educational Mayhem themed profile editing interface.
"""
import pygame
import aiohttp
from typing import Any
from constants import (
    MAYHEM_PURPLE, CHALK_WHITE, SCHOOL_BUS_YELLOW, CHALKBOARD_DARK,
    SCREEN_WIDTH, SCREEN_HEIGHT, SHAPE_DATABASE, API_URL
)
from ui_widgets import Button, TextInput
from student import Student


class ProfileView:
    """Character customizer screen for Educational Mayhem."""
    
    def __init__(self, screen: pygame.Surface, student: Student, token: str):
        """Initialize profile view.
        
        Args:
            screen: Pygame display surface
            student: Local student to edit
            token: Auth token for API calls
        """
        self._screen = screen
        self._student = student
        self._token = token
        
        # Temporary editing values
        self._edit_username = student.username
        self._edit_color = student.color
        self._edit_shape = student._shape
        
        # UI components
        self._username_input = TextInput(
            SCREEN_WIDTH // 2 - 150, 200, 300, 40,
            self._edit_username
        )
        
        # Shape selection buttons
        self._shape_buttons: list[ShapeButton] = []
        button_y = 300
        button_spacing = 130
        for i, shape in enumerate(SHAPE_DATABASE):
            x = SCREEN_WIDTH // 2 - (len(SHAPE_DATABASE) * button_spacing) // 2 + i * button_spacing
            self._shape_buttons.append(
                ShapeButton(x, button_y, 100, 100, shape, shape == self._edit_shape)
            )
        
        # Color buttons
        self._color_buttons: list[ColorButton] = []
        colors = ["red", "blue", "green"]
        color_y = 450
        for i, color in enumerate(colors):
            x = SCREEN_WIDTH // 2 - 150 + i * 100
            self._color_buttons.append(
                ColorButton(x, color_y, 80, 80, color, color == self._edit_color)
            )
        
        # Action buttons
        self._save_button = Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 100, 100, 50,
            "Save", SCHOOL_BUS_YELLOW, on_click=self._on_save
        )
        self._cancel_button = Button(
            SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT - 100, 100, 50,
            "Cancel", (150, 150, 150), on_click=lambda: None
        )
        
        self._cancel_requested = False
    
    def handle_event(self, event: pygame.event.Event) -> str | None:
        """Handle events.
        
        Args:
            event: Pygame event
            
        Returns:
            "cancel" if user canceled, "save" if saved, None otherwise
        """
        # Username input
        self._username_input.handle_event(event)
        self._edit_username = self._username_input.text
        
        # Shape buttons
        for button in self._shape_buttons:
            if button.handle_event(event):
                self._edit_shape = button.shape
                # Update all button states
                for b in self._shape_buttons:
                    b.selected = (b.shape == self._edit_shape)
        
        # Color buttons
        for button in self._color_buttons:
            if button.handle_event(event):
                self._edit_color = button.color
                for b in self._color_buttons:
                    b.selected = (b.color == self._edit_color)
        
        # Action buttons
        if self._save_button.handle_event(event):
            return "save"
        if self._cancel_button.handle_event(event):
            return "cancel"
        
        # ESC key to cancel
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            return "cancel"
        
        return None
    
    def update(self, dt: float) -> None:
        """Update animations."""
        self._username_input.update(dt)
    
    def render(self) -> None:
        """Render the profile customizer."""
        # Background
        self._screen.fill(MAYHEM_PURPLE)
        
        # Educational Mayhem title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("CHARACTER CUSTOMIZER", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self._screen.blit(title, title_rect)
        
        # Username section
        label_font = pygame.font.Font(None, 32)
        username_label = label_font.render("Username:", True, CHALK_WHITE)
        self._screen.blit(username_label, (SCREEN_WIDTH // 2 - 150, 160))
        self._username_input.draw(self._screen)
        
        # Shape section
        shape_label = label_font.render("Choose Your Shape:", True, CHALK_WHITE)
        shape_rect = shape_label.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self._screen.blit(shape_label, shape_rect)
        
        for button in self._shape_buttons:
            button.draw(self._screen)
        
        # Color section
        color_label = label_font.render("Choose Your Color:", True, CHALK_WHITE)
        color_rect = color_label.get_rect(center=(SCREEN_WIDTH // 2, 410))
        self._screen.blit(color_label, color_rect)
        
        for button in self._color_buttons:
            button.draw(self._screen)
        
        # Preview
        preview_label = label_font.render("Preview:", True, CHALK_WHITE)
        self._screen.blit(preview_label, (SCREEN_WIDTH // 2 - 100, 550))
        
        # Render preview character
        preview_student = Student("preview", self._edit_username)
        preview_student._shape = self._edit_shape
        preview_student.color = self._edit_color
        preview_student.render(self._screen, SCREEN_WIDTH // 2 - 40, 600, 80)
        
        # Action buttons
        self._save_button.draw(self._screen)
        self._cancel_button.draw(self._screen)
    
    def _on_save(self) -> None:
        """Handle save button click."""
        pass  # Handled by parent controller
    
    async def save_changes(self, network_manager: Any) -> bool:
        """Save profile changes to server.
        
        Args:
            network_manager: NetworkManager instance
            
        Returns:
            True if successful
        """
        try:
            # Update local student
            self._student.username = self._edit_username
            self._student.color = self._edit_color
            self._student._shape = self._edit_shape
            
            # POST to API
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/profile/update",
                    params={"token": self._token},
                    json={
                        "username": self._edit_username,
                        "color": self._edit_color,
                        "shape": self._edit_shape
                    }
                ) as response:
                    if response.status == 200:
                        # Send via WebSocket for real-time sync
                        await network_manager.update_profile(
                            username=self._edit_username,
                            color=self._edit_color,
                            shape=self._edit_shape
                        )
                        return True
            return False
        except Exception as e:
            print(f"Error saving profile: {e}")
            return False


class ShapeButton:
    """Button for shape selection."""
    
    def __init__(self, x: int, y: int, width: int, height: int, shape: str, selected: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.shape = shape
        self.selected = selected
        self.hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                return True
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        # Background
        bg_color = SCHOOL_BUS_YELLOW if self.selected else CHALK_WHITE
        if self.hovered and not self.selected:
            bg_color = (255, 255, 200)
        
        pygame.draw.rect(surface, bg_color, self.rect, border_radius=10)
        pygame.draw.rect(surface, CHALKBOARD_DARK, self.rect, 3, border_radius=10)
        
        # Shape preview (simplified)
        center_x = self.rect.centerx
        center_y = self.rect.centery - 10
        size = 40
        
        import math
        if self.shape == "circle":
            pygame.draw.circle(surface, CHALKBOARD_DARK, (center_x, center_y), size // 2, 3)
        elif self.shape == "square":
            r = pygame.Rect(center_x - size//2, center_y - size//2, size, size)
            pygame.draw.rect(surface, CHALKBOARD_DARK, r, 3)
        elif self.shape == "triangle":
            points = [(center_x, center_y - size//2), 
                     (center_x - size//2, center_y + size//2),
                     (center_x + size//2, center_y + size//2)]
            pygame.draw.polygon(surface, CHALKBOARD_DARK, points, 3)
        elif self.shape == "star":
            # Simple star outline
            points = []
            for i in range(10):
                angle = math.pi / 2 + (2 * math.pi * i / 10)
                radius = (size // 2) if i % 2 == 0 else (size // 4)
                px = center_x + radius * math.cos(angle)
                py = center_y - radius * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, CHALKBOARD_DARK, points, 3)
        elif self.shape == "hexagon":
            points = []
            for i in range(6):
                angle = math.pi / 3 * i
                px = center_x + (size // 2) * math.cos(angle)
                py = center_y + (size // 2) * math.sin(angle)
                points.append((px, py))
            pygame.draw.polygon(surface, CHALKBOARD_DARK, points, 3)
        
        # Label
        font = pygame.font.Font(None, 20)
        label = font.render(self.shape.capitalize(), True, CHALKBOARD_DARK)
        label_rect = label.get_rect(center=(center_x, self.rect.bottom - 15))
        surface.blit(label, label_rect)


class ColorButton:
    """Button for color selection."""
    
    COLOR_MAP = {
        "red": (231, 76, 60),
        "blue": (52, 152, 219),
        "green": (46, 204, 113)
    }
    
    def __init__(self, x: int, y: int, width: int, height: int, color: str, selected: bool = False):
        self.rect = pygame.Rect(x, y, width, height)
        self.color = color
        self.selected = selected
        self.hovered = False
    
    def handle_event(self, event: pygame.event.Event) -> bool:
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.hovered:
                return True
        return False
    
    def draw(self, surface: pygame.Surface) -> None:
        fill_color = self.COLOR_MAP[self.color]
        
        pygame.draw.rect(surface, fill_color, self.rect, border_radius=10)
        
        border_color = SCHOOL_BUS_YELLOW if self.selected else CHALK_WHITE
        border_width = 5 if self.selected else 3
        pygame.draw.rect(surface, border_color, self.rect, border_width, border_radius=10)
