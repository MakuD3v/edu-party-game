"""
Lobby List View
Displays available lobbies and allows creating or joining.
Matches "Digital/Mobile" aesthetic with Purple theme.
"""
import pygame
import asyncio
from views.base_view import BaseView
from ui_widgets import Button, TextInput
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, CHALK_WHITE, SCHOOL_BUS_YELLOW, 
    MAYHEM_PURPLE, DELETE_RED
)

# Color Palette based on image
BG_PURPLE = MAYHEM_PURPLE
PANEL_PURPLE = (80, 50, 140)  # Lighter purple for main box
BOX_DARK_PURPLE = (40, 20, 80) # Dark for stats/list
BUTTON_ORANGE = (255, 120, 0)
BUTTON_PURPLE = (150, 50, 200)
BUTTON_GREEN = (46, 204, 113)

class LobbyListView(BaseView):
    def __init__(self, screen, game_controller):
        super().__init__(screen, game_controller)
        
        # UI Elements
        center_x = SCREEN_WIDTH // 2
        
        # Main Actions
        self.btn_create = Button(
            center_x - 220, 450, 200, 60, 
            "CREATE LOBBY", BUTTON_ORANGE, 
            on_click=self._on_create_click,
            border_radius=15
        )
        self.btn_refresh = Button(
            center_x + 20, 450, 200, 60,
            "REFRESH LOBBIES", BUTTON_PURPLE,
            on_click=self._on_refresh_click,
            border_radius=15
        )
        
        self.btn_logout = Button(
            SCREEN_WIDTH - 120, 50, 100, 40,
            "LOGOUT", (100, 100, 100),
            on_click=self._on_logout,
            text_color=(200, 200, 200),
            border_radius=10
        )
        
        self.lobbies = []
        self.lobby_join_buttons = [] # Store (rect, lobby_id) tuples or Button objects
        
    def on_enter(self):
        """Called when entering this view."""
        asyncio.create_task(self._fetch_lobbies())

    def _on_create_click(self):
        self.game_controller.switch_state("LOBBY_SETTINGS")

    def _on_refresh_click(self):
        asyncio.create_task(self._fetch_lobbies())
        
    def _on_logout(self):
        # Implementation for logout could go here
        print("Logout clicked")
        # For now, just go back to menu
        self.game_controller.switch_state("MENU")

    async def _fetch_lobbies(self):
        self.lobbies = await self.game_controller.network_manager.get_lobbies()

    def _join_lobby(self, lobby_id):
        asyncio.create_task(self._attempt_join(lobby_id))

    async def _attempt_join(self, lobby_id):
        connected = await self.game_controller.network_manager.connect(
            lobby_id, self.game_controller.token
        )
        if connected:
            self.game_controller._lobby_id = lobby_id
            self.game_controller.switch_state("IN_LOBBY")

    def handle_event(self, event):
        self.btn_create.handle_event(event)
        self.btn_refresh.handle_event(event)
        self.btn_logout.handle_event(event)
        
        # Handle dynamic join buttons
        if event.type == pygame.MOUSEBUTTONDOWN:
             for btn, lobby_id in self.lobby_join_buttons:
                 if btn.handle_event(event):
                     self._join_lobby(lobby_id)

    def update(self, dt):
        pass

    def render(self):
        self.screen.fill(BG_PURPLE)
        
        center_x = SCREEN_WIDTH // 2
        
        # Header
        font_main = pygame.font.Font(None, 80)
        title = font_main.render("EDU PARTY", True, SCHOOL_BUS_YELLOW)
        # Shadow
        title_shadow = font_main.render("EDU PARTY", True, (0,0,0))
        self.screen.blit(title_shadow, (center_x - title.get_width()//2 + 4, 34))
        self.screen.blit(title, (center_x - title.get_width()//2, 30))
        
        font_sub = pygame.font.Font(None, 32)
        subtitle = font_sub.render("EDUCATIONAL MAYHEM!", True, CHALK_WHITE)
        self.screen.blit(subtitle, (center_x - subtitle.get_width()//2, 90))
        
        # Main Panel
        panel_rect = pygame.Rect(center_x - 300, 130, 600, 600)
        pygame.draw.rect(self.screen, PANEL_PURPLE, panel_rect, border_radius=20)
        
        # Welcome Text
        username = self.game_controller.local_student.username if self.game_controller.local_student else "Guest"
        welcome_text = font_main.render(f"WELCOME {username.upper()}!", True, SCHOOL_BUS_YELLOW)
        # Scale down if too long
        if welcome_text.get_width() > 350:
             scale = 350 / welcome_text.get_width()
             welcome_text = pygame.transform.rotozoom(welcome_text, 0, scale)
             
        self.screen.blit(welcome_text, (panel_rect.x + 30, panel_rect.y + 30))
        
        # Logout Button
        self.btn_logout.rect.topright = (panel_rect.right - 30, panel_rect.y + 30)
        self.btn_logout.draw(self.screen)
        
        # Stats Row
        self._render_stats(panel_rect.x + 30, panel_rect.y + 100)
        
        # Action Buttons
        self.btn_create.draw(self.screen)
        self.btn_refresh.draw(self.screen)
        
        # Lobby List Panel
        list_rect = pygame.Rect(panel_rect.x + 30, 530, 540, 180)
        pygame.draw.rect(self.screen, BOX_DARK_PURPLE, list_rect, border_radius=15)
        
        label_active = font_sub.render("ACTIVE LOBBIES", True, SCHOOL_BUS_YELLOW)
        self.screen.blit(label_active, (list_rect.centerx - label_active.get_width()//2, list_rect.y + 15))
        
        self._render_lobby_list(list_rect.x, list_rect.y + 50, list_rect.width)

    def _render_stats(self, x, y):
        # 3 Boxes: Wins, Losses, Elo
        box_w = 170
        box_h = 100
        gap = 15
        
        stats = [
            ("WINS", "0"),
            ("LOSSES", "0"),
            ("ELO", "1000")
        ]
        
        for i, (label, value) in enumerate(stats):
            bx = x + i * (box_w + gap)
            rect = pygame.Rect(bx, y, box_w, box_h)
            pygame.draw.rect(self.screen, BOX_DARK_PURPLE, rect, border_radius=15)
            
            font_label = pygame.font.Font(None, 24)
            lbl_surf = font_label.render(label, True, SCHOOL_BUS_YELLOW)
            self.screen.blit(lbl_surf, (bx + box_w//2 - lbl_surf.get_width()//2, y + 20))
            
            font_val = pygame.font.Font(None, 48)
            val_surf = font_val.render(value, True, CHALK_WHITE)
            self.screen.blit(val_surf, (bx + box_w//2 - val_surf.get_width()//2, y + 50))

    def _render_lobby_list(self, x, y, width):
        # Re-generate join buttons every frame is inefficient but works for simple GUI
        self.lobby_join_buttons = []
        
        font_item = pygame.font.Font(None, 28)
        
        if not self.lobbies:
            txt = font_item.render("No active lobbies found.", True, (150, 150, 150))
            self.screen.blit(txt, (x + 20, y))
            return

        current_y = y
        for lobby in self.lobbies[:2]: # Show max 2-3 for this layout space
            # Lobby Item container
            pygame.draw.rect(self.screen, (60, 40, 100), (x + 10, current_y, width - 20, 50), border_radius=10)
            
            # Text
            info = f"LOBBY: {lobby['id'][:8]}...   PLAYERS: {lobby['count']}/{lobby['max']}"
            txt = font_item.render(info, True, CHALK_WHITE)
            self.screen.blit(txt, (x + 30, current_y + 15))
            
            # Join Button
            btn_join = Button(x + width - 100, current_y + 8, 80, 34, "JOIN", BUTTON_GREEN, border_radius=8)
            btn_join.font = pygame.font.Font(None, 24)
            btn_join.draw(self.screen)
            
            self.lobby_join_buttons.append((btn_join, lobby['id']))
            current_y += 60
