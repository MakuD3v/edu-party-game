"""
Lobby Settings View
Modal screen for configuring a new lobby (Capacity, Game Mode).
"""
import pygame
import asyncio
from views.base_view import BaseView
from ui_widgets import Button
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CHALK_WHITE, SCHOOL_BUS_YELLOW, 
    CHALKBOARD_DARK, DELETE_RED
)

class LobbySettingsView(BaseView):
    def __init__(self, screen, game_controller):
        super().__init__(screen, game_controller)
        
        # State
        self.capacity = 10
        self.game_mode = "Math Dash"
        
        # UI
        center_x = SCREEN_WIDTH // 2
        
        self.btn_capacity_minus = Button(center_x - 100, 200, 40, 40, "-", CHALK_WHITE, self._cap_minus)
        self.btn_capacity_plus = Button(center_x + 60, 200, 40, 40, "+", CHALK_WHITE, self._cap_plus)
        
        self.btn_create = Button(center_x - 100, 400, 200, 50, "OPEN CLASS", SCHOOL_BUS_YELLOW, self._on_confirm)
        self.btn_cancel = Button(center_x - 100, 470, 200, 50, "CANCEL", DELETE_RED, self._on_cancel)
        
    def _cap_minus(self):
        if self.capacity > 10:
            self.capacity -= 5
            
    def _cap_plus(self):
        if self.capacity < 50:
            self.capacity += 5
            
    def _on_confirm(self):
        # Call GameController to create lobby
        asyncio.create_task(self.game_controller.create_lobby(self.capacity, self.game_mode))
        
    def _on_cancel(self):
        self.game_controller.switch_state("LOBBY_LIST")

    def handle_event(self, event):
        self.btn_capacity_minus.handle_event(event)
        self.btn_capacity_plus.handle_event(event)
        self.btn_create.handle_event(event)
        self.btn_cancel.handle_event(event)

    def update(self, dt):
        pass

    def render(self):
        # Semi-transparent overlay over the previous view (if we want a modal look)
        # For simple state machine, just fill background
        self.screen.fill(CHALKBOARD_DARK)
        
        center_x = SCREEN_WIDTH // 2
        
        # Title
        font_title = pygame.font.Font(None, 48)
        title = font_title.render("Classroom Settings", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(center_x, 100))
        self.screen.blit(title, title_rect)
        
        # Capacity
        font_label = pygame.font.Font(None, 36)
        label_cap = font_label.render("Class Capacity", True, CHALK_WHITE)
        label_rect = label_cap.get_rect(center=(center_x, 160))
        self.screen.blit(label_cap, label_rect)
        
        cap_val = font_label.render(str(self.capacity), True, SCHOOL_BUS_YELLOW)
        cap_rect = cap_val.get_rect(center=(center_x, 220))
        self.screen.blit(cap_val, cap_rect)
        
        # Game Mode (Static for now)
        label_mode = font_label.render(f"Subject: {self.game_mode}", True, CHALK_WHITE)
        mode_rect = label_mode.get_rect(center=(center_x, 300))
        self.screen.blit(label_mode, mode_rect)
        
        # Buttons
        self.btn_capacity_minus.draw(self.screen)
        self.btn_capacity_plus.draw(self.screen)
        self.btn_create.draw(self.screen)
        self.btn_cancel.draw(self.screen)
