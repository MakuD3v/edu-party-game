"""
Base View Class
Abstract base class for all game views (screens).
"""
import pygame
from typing import Optional, Any
from abc import ABC, abstractmethod


class BaseView(ABC):
    """Abstract base class for all game views."""

    def __init__(self, screen: pygame.Surface, game_controller: Any):
        """
        Initialize the view.
        
        Args:
            screen: The main game screen surface.
            game_controller: Reference to the main GameController.
        """
        self.screen = screen
        self.game_controller = game_controller

    @abstractmethod
    def handle_event(self, event: pygame.event.Event) -> None:
        """Handle pygame events (clicks, keys, etc)."""
        pass

    @abstractmethod
    def update(self, dt: float) -> None:
        """Update view state (animations, logic)."""
        pass

    @abstractmethod
    def render(self) -> None:
        """Render the view to the screen."""
        pass
    
    def on_enter(self, *args, **kwargs) -> None:
        """Called when this view becomes active."""
        pass
    
    def on_leave(self) -> None:
        """Called when this view is no longer active."""
        pass
