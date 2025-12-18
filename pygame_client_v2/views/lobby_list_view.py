"""
Lobby List View
Displays available lobbies and allows creating or joining.
"""
import pygame
import asyncio
from views.base_view import BaseView
from ui_widgets import Button, TextInput
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CHALK_WHITE, SCHOOL_BUS_YELLOW, 
    CHALKBOARD_DARK, FONT_MAIN
)

class LobbyListView(BaseView):
    def __init__(self, screen, game_controller):
        super().__init__(screen, game_controller)
        
        # UI Elements
        self.create_btn = Button(
            SCREEN_WIDTH - 250, 50, 200, 50, 
            "Create Class", SCHOOL_BUS_YELLOW, 
            on_click=self._on_create_click
        )
        self.refresh_btn = Button(
            SCREEN_WIDTH - 250, 110, 200, 50,
            "Refresh List", CHALK_WHITE,
            on_click=self._on_refresh_click
        )
        
        self.lobbies = []
        self.refresh_timer = 0
        
    def on_enter(self):
        """Called when entering this view."""
        print("Entering Lobby List View")
        asyncio.create_task(self._fetch_lobbies())

    def _on_create_click(self):
        # Navigate to Settings Modal
        self.game_controller.switch_state("LOBBY_SETTINGS")

    def _on_refresh_click(self):
        asyncio.create_task(self._fetch_lobbies())

    async def _fetch_lobbies(self):
        # Fetch lobbies from backend via NetworkManager
        # This is a placeholder; actual impl depends on network manager
        self.lobbies = await self.game_controller.network_manager.get_lobbies()

    def handle_event(self, event):
        self.create_btn.handle_event(event)
        self.refresh_btn.handle_event(event)
        
        # Handle lobby clicks (rudimentary hit testing for list items)
        if event.type == pygame.MOUSEBUTTONDOWN:
            # Check list items...
            pass

    def update(self, dt):
        pass

    def render(self):
        # Draw Background (Chalkboard)
        # self.screen.blit(self.game_controller.assets["chalkboard"], (0,0))
        self.screen.fill(CHALKBOARD_DARK)

        # Title
        font = pygame.font.Font(None, 64)
        title = font.render("Class Procession", True, CHALK_WHITE)
        self.screen.blit(title, (50, 50))

        # Draw Buttons
        self.create_btn.draw(self.screen)
        self.refresh_btn.draw(self.screen)

        # Draw List
        y_offset = 180
        font_list = pygame.font.Font(None, 32)
        
        if not self.lobbies:
            text = font_list.render("No active classes found...", True, (150, 150, 150))
            self.game_controller.screen.blit(text, (50, y_offset))
        
        # Store rects for hit testing during render (a bit hacky but works for simple UI)
        self.lobby_rects = []
        for lobby in self.lobbies:
            text_str = f"Class {lobby['id']} - Host: {lobby['host']} ({lobby['count']}/{lobby['max']})"
            text = font_list.render(text_str, True, CHALK_WHITE)
            rect = self.game_controller.screen.blit(text, (50, y_offset))
            self.lobby_rects.append((rect, lobby['id']))
            
            # Draw join button next to it
            # (Simplified: clicking text joins)
            y_offset += 40

    def handle_event(self, event):
        self.create_btn.handle_event(event)
        self.refresh_btn.handle_event(event)
        
        if event.type == pygame.MOUSEBUTTONDOWN:
            if hasattr(self, 'lobby_rects'):
                for rect, lobby_id in self.lobby_rects:
                    if rect.collidepoint(event.pos):
                        self._join_lobby(lobby_id)
                        
    def _join_lobby(self, lobby_id):
        print(f"Joining lobby {lobby_id}...")
        asyncio.create_task(self._attempt_join(lobby_id))

    async def _attempt_join(self, lobby_id):
        connected = await self.game_controller.network_manager.connect(
            lobby_id, self.game_controller.token
        )
        if connected:
            self.game_controller._lobby_id = lobby_id
            self.game_controller.switch_state("IN_LOBBY")
        else:
            print("Failed to join lobby")

