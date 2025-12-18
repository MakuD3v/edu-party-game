"""
Profile View - Character Customizer Screen
Educational Mayhem themed profile editing interface.
"""
import pygame
import asyncio
from typing import Any
from constants import (
    MAYHEM_PURPLE, CHALK_WHITE, SCHOOL_BUS_YELLOW, CHALKBOARD_DARK,
    SCREEN_WIDTH, SCREEN_HEIGHT, SHAPE_DATABASE, API_URL
)
from views.base_view import BaseView
from ui_widgets import Button, TextInput
from student import Student


class ProfileView(BaseView):
    """Character customizer screen for Educational Mayhem."""
    
    def __init__(self, screen: pygame.Surface, game_controller: Any):
        """Initialize profile view."""
        super().__init__(screen, game_controller)
        
        # Initialize with temporary defaults, will populate on_enter
        self._edit_username = "Student"
        self._edit_color = "red"
        self._edit_shape = "circle"
        
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
                ShapeButton(x, button_y, 100, 100, shape)
            )
        
        # Color buttons
        self._color_buttons: list[ColorButton] = []
        colors = ["red", "blue", "green"]
        color_y = 450
        for i, color in enumerate(colors):
            x = SCREEN_WIDTH // 2 - 150 + i * 100
            self._color_buttons.append(
                ColorButton(x, color_y, 80, 80, color)
            )
        
        # Action buttons
        self._save_button = Button(
            SCREEN_WIDTH // 2 - 110, SCREEN_HEIGHT - 100, 100, 50,
            "Save", SCHOOL_BUS_YELLOW, on_click=self._on_save
        )
        self._cancel_button = Button(
            SCREEN_WIDTH // 2 + 10, SCREEN_HEIGHT - 100, 100, 50,
            "Cancel", (150, 150, 150), on_click=self._on_cancel
        )
    
    def on_enter(self, *args, **kwargs) -> None:
        """Called when entering the view."""
        student = self.game_controller.local_student
        if student:
            self._edit_username = student.username
            self._edit_color = student.color
            self._edit_shape = student._shape
            
            # Update UI state
            self._username_input.text = self._edit_username
            
            for b in self._shape_buttons:
                b.selected = (b.shape == self._edit_shape)
            
            for b in self._color_buttons:
                b.selected = (b.color == self._edit_color)
    
    def _on_save(self) -> None:
        """Handle save button click."""
        asyncio.create_task(self._save_changes())
        
    def _on_cancel(self) -> None:
        """Navigate back."""
        # Typically return to LOBBY or previous state
        self.game_controller.switch_state("LOBBY")  # Or previous state

    async def _save_changes(self) -> None:
        """Save to backend."""
        # Update local student immediately for responsiveness
        student = self.game_controller.local_student
        if student:
            student.username = self._edit_username
            student.color = self._edit_color
            student._shape = self._edit_shape
            
            # Use network manager
            await self.game_controller.network_manager.update_profile(
                 username=self._edit_username,
                 color=self._edit_color,
                 shape=self._edit_shape,
                 token=self.game_controller.token
            )
            
            self.game_controller.switch_state("LOBBY")

    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle events."""
        # Username input
        if self._username_input.handle_event(event):
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
        self._save_button.handle_event(event)
        self._cancel_button.handle_event(event)
        
        # ESC key to cancel
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self._on_cancel()
    
    def update(self, dt: float) -> None:
        """Update animations."""
        self._username_input.update(dt)
    
    def render(self) -> None:
        """Render the profile customizer."""
        # Background
        self.screen.fill(MAYHEM_PURPLE)
        
        # Educational Mayhem title
        title_font = pygame.font.Font(None, 72)
        title = title_font.render("CHARACTER CUSTOMIZER", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 80))
        self.screen.blit(title, title_rect)
        
        # Username section
        label_font = pygame.font.Font(None, 32)
        username_label = label_font.render("Username:", True, CHALK_WHITE)
        self.screen.blit(username_label, (SCREEN_WIDTH // 2 - 150, 160))
        self._username_input.draw(self.screen)
        
        # Shape section
        shape_label = label_font.render("Choose Your Shape:", True, CHALK_WHITE)
        shape_rect = shape_label.get_rect(center=(SCREEN_WIDTH // 2, 260))
        self.screen.blit(shape_label, shape_rect)
        
        for button in self._shape_buttons:
            button.draw(self.screen)
        
        # Color section
        color_label = label_font.render("Choose Your Color:", True, CHALK_WHITE)
        color_rect = color_label.get_rect(center=(SCREEN_WIDTH // 2, 410))
        self.screen.blit(color_label, color_rect)
        
        for button in self._color_buttons:
            button.draw(self.screen)
        
        # Preview
        preview_label = label_font.render("Preview:", True, CHALK_WHITE)
        self.screen.blit(preview_label, (SCREEN_WIDTH // 2 - 100, 550))
        
        # Render preview character
        preview_student = Student("preview", self._edit_username)
        preview_student._shape = self._edit_shape
        preview_student.color = self._edit_color
        preview_student.render(self.screen, SCREEN_WIDTH // 2 - 40, 600, 80)
        
        # Action buttons
        self._save_button.draw(self.screen)
        self._cancel_button.draw(self.screen)


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
