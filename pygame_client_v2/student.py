"""
Student Class - Encapsulates player state and rendering.
Manages username, position, gear, and visual representation.
"""
import pygame
from typing import Any
from constants import STUDENT_RED, STUDENT_BLUE, STUDENT_GREEN, CHALK_WHITE


class Student:
    """Represents a student (player) in the game."""
    
    # Color mapping
    COLOR_MAP: dict[str, tuple[int, int, int]] = {
        "red": STUDENT_RED,
        "blue": STUDENT_BLUE,
        "green": STUDENT_GREEN
    }
    
    def __init__(self, student_id: str, username: str):
        """Initialize a new student.
        
        Args:
            student_id: Unique identifier for this student
            username: Display name
        """
        self._id: str = student_id
        self._username: str = username
        self._position: dict[str, float] = {"x": 0.0, "y": 0.0}
        self._color: str = "red"
        self._gear: list[str] = []
        self._ready: bool = False
    
    # Public properties with encapsulation
    @property
    def id(self) -> str:
        """Get student ID."""
        return self._id
    
    @property
    def username(self) -> str:
        """Get username."""
        return self._username
    
    @username.setter
    def username(self, value: str) -> None:
        """Set username."""
        self._username = value
    
    @property
    def position(self) -> dict[str, float]:
        """Get position."""
        return self._position.copy()
    
    @property
    def color(self) -> str:
        """Get color."""
        return self._color
    
    @color.setter
    def color(self, value: str) -> None:
        """Set color (validates against COLOR_MAP)."""
        if value in self.COLOR_MAP:
            self._color = value
    
    @property
    def gear(self) -> list[str]:
        """Get gear list (copy for safety)."""
        return self._gear.copy()
    
    @property
    def ready(self) -> bool:
        """Get ready status."""
        return self._ready
    
    @ready.setter
    def ready(self, value: bool) -> None:
        """Set ready status."""
        self._ready = value
    
    # State management methods
    def update_position(self, x: float, y: float) -> None:
        """Update student position.
        
        Args:
            x: X coordinate
            y: Y coordinate
        """
        self._position["x"] = x
        self._position["y"] = y
    
    def update_gear(self, gear_list: list[str]) -> None:
        """Update gear from GEAR_DATABASE.
        
        Args:
            gear_list: List of gear item names
        """
        self._gear = gear_list.copy()
    
    def add_gear(self, gear_item: str) -> None:
        """Add a gear item if not already equipped.
        
        Args:
            gear_item: Name of gear item
        """
        if gear_item not in self._gear:
            self._gear.append(gear_item)
    
    def remove_gear(self, gear_item: str) -> None:
        """Remove a gear item.
        
        Args:
            gear_item: Name of gear item
        """
        if gear_item in self._gear:
            self._gear.remove(gear_item)
    
    def toggle_gear(self, gear_item: str) -> None:
        """Toggle a gear item on/off.
        
        Args:
            gear_item: Name of gear item
        """
        if gear_item in self._gear:
            self._gear.remove(gear_item)
        else:
            self._gear.append(gear_item)
    
    # Rendering methods
    def render(self, surface: pygame.Surface, x: int, y: int, size: int = 64) -> None:
        """Render student character at specified position.
        
        Args:
            surface: Pygame surface to draw on
            x: X coordinate (top-left)
            y: Y coordinate (top-left)
            size: Character size in pixels
        """
        body_color = self.COLOR_MAP.get(self._color, STUDENT_RED)
        center = (x + size // 2, y + size // 2)
        
        # Draw body (circle)
        pygame.draw.circle(surface, body_color, center, size // 2)
        pygame.draw.circle(surface, CHALK_WHITE, center, size // 2, 3)
        
        # Draw eyes
        eye_y = center[1] - size // 6
        pygame.draw.circle(surface, CHALK_WHITE, (center[0] - size//6, eye_y), size//12)
        pygame.draw.circle(surface, CHALK_WHITE, (center[0] + size//6, eye_y), size//12)
        pygame.draw.circle(surface, (0, 0, 0), (center[0] - size//6, eye_y), size//18)
        pygame.draw.circle(surface, (0, 0, 0), (center[0] + size//6, eye_y), size//18)
        
        # Draw smile
        pygame.draw.arc(
            surface, CHALK_WHITE,
            (center[0] - size//4, center[1] - size//12, size//2, size//3),
            3.14, 0, 3
        )
        
        # Draw gear
        self._render_gear(surface, center, size)
    
    def _render_gear(self, surface: pygame.Surface, center: tuple[int, int], size: int) -> None:
        """Render equipped gear on character.
        
        Args:
            surface: Pygame surface to draw on
            center: Center point of character
            size: Character size
        """
        if "Graduation Cap" in self._gear:
            cap_y = center[1] - size // 2 - 10
            # Square top
            points = [
                (center[0] - size//3, cap_y),
                (center[0] + size//3, cap_y),
                (center[0] + size//3, cap_y + 5),
                (center[0] - size//3, cap_y + 5)
            ]
            pygame.draw.polygon(surface, CHALK_WHITE, points)
            # Cap base
            pygame.draw.rect(surface, CHALK_WHITE, 
                           (center[0] - size//4, cap_y + 5, size//2, 8))
            # Tassel
            pygame.draw.line(surface, SCHOOL_BUS_YELLOW,
                           (center[0], cap_y), (center[0] + size//4, cap_y - 8), 2)
            pygame.draw.circle(surface, SCHOOL_BUS_YELLOW, 
                             (center[0] + size//4, cap_y - 8), 3)
        
        if "Science Goggles" in self._gear:
            eye_y = center[1] - size // 6
            # Goggles
            pygame.draw.circle(surface, CHALK_WHITE, (center[0] - size//6, eye_y), size//8, 2)
            pygame.draw.circle(surface, CHALK_WHITE, (center[0] + size//6, eye_y), size//8, 2)
            pygame.draw.line(surface, CHALK_WHITE,
                           (center[0] - size//24, eye_y), (center[0] + size//24, eye_y), 2)
        
        if "Backpack" in self._gear:
            back_x = center[0] + size // 2 - 5
            back_rect = pygame.Rect(back_x - 15, center[1] - 10, 18, 25)
            pygame.draw.rect(surface, (139, 90, 43), back_rect, border_radius=3)
            pygame.draw.rect(surface, CHALK_WHITE, back_rect, 2, border_radius=3)
        
        if "Calculator Watch" in self._gear:
            # Watch on wrist (bottom right)
            watch_x = center[0] + size // 3
            watch_y = center[1] + size // 4
            pygame.draw.rect(surface, (50, 50, 50), 
                           (watch_x - 8, watch_y - 4, 16, 8), border_radius=2)
            pygame.draw.rect(surface, (100, 200, 100),
                           (watch_x - 6, watch_y - 2, 12, 4))
        
        if "Pencil Case" in self._gear:
            # Pencil case at hip
            case_x = center[0] - size // 3
            case_y = center[1] + size // 4
            pygame.draw.rect(surface, SCHOOL_BUS_YELLOW,
                           (case_x - 10, case_y - 5, 20, 10), border_radius=2)
            pygame.draw.rect(surface, CHALK_WHITE,
                           (case_x - 10, case_y - 5, 20, 10), 2, border_radius=2)
    
    # Serialization
    def to_dict(self) -> dict[str, Any]:
        """Serialize student state for network transmission.
        
        Returns:
            Dictionary representation of student state
        """
        return {
            "id": self._id,
            "username": self._username,
            "position": self._position.copy(),
            "color": self._color,
            "gear": self._gear.copy(),
            "ready": self._ready
        }
    
    def from_dict(self, data: dict[str, Any]) -> None:
        """Update student state from dictionary.
        
        Args:
            data: Dictionary with student state
        """
        if "username" in data:
            self._username = data["username"]
        if "position" in data:
            self._position = data["position"].copy()
        if "color" in data and data["color"] in self.COLOR_MAP:
            self._color = data["color"]
        if "gear" in data:
            self._gear = data["gear"].copy()
        if "ready" in data:
            self._ready = data["ready"]
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"Student(id={self._id}, username={self._username}, color={self._color}, gear={len(self._gear)})"
