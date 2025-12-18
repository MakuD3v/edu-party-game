"""
In-Lobby View
Displays the player list (Roster) and ready status.
"""
import pygame
import asyncio
from views.base_view import BaseView
from ui_widgets import Button, TextInput
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CHALK_WHITE, SCHOOL_BUS_YELLOW, 
    CHALKBOARD_DARK, MAYHEM_PURPLE
)

class InLobbyView(BaseView):
    def __init__(self, screen, game_controller):
        super().__init__(screen, game_controller)
        
        # UI
        self.btn_ready = Button(
            SCREEN_WIDTH - 220, SCREEN_HEIGHT - 80, 200, 50, 
            "READY UP", SCHOOL_BUS_YELLOW, self._on_ready_toggle
        )
        self.btn_start = Button(
            SCREEN_WIDTH - 220, SCREEN_HEIGHT - 150, 200, 50,
            "START CLASS", (100, 255, 100), self._on_start_game
        )
        
        # Chat
        self.chat_input = TextInput(50, SCREEN_HEIGHT - 60, 400, 40)
        self.chat_messages = []
        
    def _on_ready_toggle(self):
        current_status = self.game_controller.local_student.ready
        self.game_controller.local_student.ready = not current_status
        asyncio.create_task(self.game_controller.network.toggle_ready(not current_status))
        
        # Update button text
        self.btn_ready.text = "NOT READY" if not current_status else "READY UP"
        self.btn_ready.color = (255, 100, 100) if not current_status else SCHOOL_BUS_YELLOW

    def _on_start_game(self):
        # Host only
        asyncio.create_task(self.game_controller.network.start_game())

    def handle_event(self, event):
        self.btn_ready.handle_event(event)
        if self.game_controller.is_host:
            self.btn_start.handle_event(event)
        
        if self.chat_input.handle_event(event):
            # Send chat message (Not implemented in backend yet, but UI is ready)
            pass

    def update(self, dt):
        self.chat_input.update(dt)

    def render(self):
        self.screen.fill(CHALKBOARD_DARK)
        
        # Header
        font_header = pygame.font.Font(None, 56)
        lobby_label = f"Classroom: {self.game_controller.lobby_id}"
        header = font_header.render(lobby_label, True, SCHOOL_BUS_YELLOW)
        self.screen.blit(header, (50, 30))
        
        # Player Roster (Clipboard style)
        roster_x = 50
        roster_y = 100
        roster_w = 400
        roster_h = 400
        pygame.draw.rect(self.screen, (240, 230, 200), (roster_x, roster_y, roster_w, roster_h)) # Paper color
        pygame.draw.rect(self.screen, (80, 50, 20), (roster_x, roster_y-20, roster_w, 30)) # Clipboard clip
        
        font_list = pygame.font.Font(None, 32)
        title = font_list.render("ATTENDANCE", True, (0,0,0))
        self.screen.blit(title, (roster_x + 120, roster_y + 20))
        
        # List Players
        y = roster_y + 60
        for pid, student in self.game_controller.students.items():
            color = (0, 150, 0) if student.ready else (150, 0, 0)
            status_Text = "✔" if student.ready else "x"
            
            text = font_list.render(f"{student.username} [{status_Text}]", True, (0,0,0))
            self.screen.blit(text, (roster_x + 20, y))
            y += 35
            
        # Draw Local Player separately if not in dict
        if self.game_controller.local_student:
             s = self.game_controller.local_student
             color = (0, 150, 0) if s.ready else (150, 0, 0)
             t = font_list.render(f"{s.username} (YOU)", True, (0,0,200))
             self.screen.blit(t, (roster_x + 20, y))
        
        # Buttons
        self.btn_ready.draw(self.screen)
        if self.game_controller.is_host:
            self.btn_start.draw(self.screen)
            
        # Chat
        self.chat_input.draw(self.screen)
