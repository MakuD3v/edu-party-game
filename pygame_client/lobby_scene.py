"""
Lobby Scene - "The Homeroom"
Shows connected students with customization options and ready status.
"""
import pygame
from typing import List
from ui_widgets import Button, TextInput, CharacterPreview, DeskWidget
from assets import create_notebook_paper, render_crayon_text, PENCIL_YELLOW, CRAYON_RED, CRAYON_BLUE, CRAYON_GREEN
from game_state import game_state
from network import network
import asyncio


class LobbyScene:
    """Homeroom lobby with student desks and customization."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # Background
        self.background = create_notebook_paper(self.width, self.height)
        
        # Username editing
        self.username_input = TextInput(100, 50, 250, 40, game_state.profile.username)
        self.username_editing = False
        
        # Character customization
        self.character_preview = CharacterPreview(100, 120, 80)
        
        # Color buttons
        self.color_buttons = [
            Button(220, 130, 60, 40, "Red", CRAYON_RED, on_click=lambda: self.set_color("red")),
            Button(220, 175, 60, 40, "Blue", CRAYON_BLUE, on_click=lambda: self.set_color("blue")),
            Button(290, 130, 70, 40, "Green", CRAYON_GREEN, on_click=lambda: self.set_color("green")),
        ]
        
        # Gear toggle buttons
        self.gear_buttons = [
            Button(220, 230, 120, 35, "Glasses", PENCIL_YELLOW, on_click=lambda: self.toggle_gear("glasses")),
            Button(220, 270, 120, 35, "Grad Cap", PENCIL_YELLOW, on_click=lambda: self.toggle_gear("cap")),
            Button(220, 310, 120, 35, "Backpack", PENCIL_YELLOW, on_click=lambda: self.toggle_gear("backpack")),
        ]
        
        # Ready button
        self.ready_button = Button(
            100, 360, 240, 50, "Raise Hand",
            color=(150, 150, 150),
            on_click=self.toggle_ready
        )
        self.is_ready = False
        
        # Start game button (host only)
        self.start_button = Button(
            self.width // 2 - 100, self.height - 80, 200, 60,
            "Start Class!", (0, 255, 0),
            on_click=self.start_game
        )
        
        # Desk widgets for showing players
        self.desk_widgets: List[DeskWidget] = []
        self.setup_desks()
    
    def setup_desks(self):
        """Set up desk positions in grid."""
        self.desk_widgets.clear()
        desk_width = 120
        desk_height = 140
        padding = 20
        start_x = 400
        start_y = 100
        cols = 5
        
        for i in range(15):  # Max 15 students
            row = i // cols
            col = i % cols
            x = start_x + col * (desk_width + padding)
            y = start_y + row * (desk_height + padding)
            self.desk_widgets.append(DeskWidget(x, y, desk_width, desk_height))
    
    def set_color(self, color: str):
        """Change character color and sync."""
        game_state.profile.color = color
        asyncio.create_task(network.update_profile(color=color))
    
    def toggle_gear(self, gear_name: str):
        """Toggle gear item and sync."""
        if gear_name in game_state.profile.gear:
            game_state.profile.gear.remove(gear_name)
        else:
            game_state.profile.gear.append(gear_name)
        asyncio.create_task(network.update_profile(gear=game_state.profile.gear))
    
    def toggle_ready(self):
        """Toggle ready status."""
        self.is_ready = not self.is_ready
        self.ready_button.color = (0, 255, 0) if self.is_ready else (150, 150, 150)
        self.ready_button.text = "Ready!" if self.is_ready else "Raise Hand"
        asyncio.create_task(network.toggle_ready(self.is_ready))
    
    def start_game(self):
        """Start the game (host only)."""
        if game_state.is_host:
            asyncio.create_task(network.start_game())
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        # Username editing
        if event.type == pygame.MOUSEBUTTONDOWN:
            username_rect = pygame.Rect(100, 50, 250, 40)
            if username_rect.collidepoint(event.pos):
                self.username_editing = True
                self.username_input.active = True
        
        if self.username_editing:
            changed = self.username_input.handle_event(event)
            if changed and event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Submit username change
                game_state.profile.username = self.username_input.text
                asyncio.create_task(network.update_profile(username=self.username_input.text))
                self.username_editing = False
        
        # Customization buttons
        for btn in self.color_buttons + self.gear_buttons:
            btn.handle_event(event)
        
        self.ready_button.handle_event(event)
        
        if game_state.is_host:
            self.start_button.handle_event(event)
    
    def update(self, dt: float):
        """Update scene state."""
        self.username_input.update(dt)
    
    def draw(self):
        """Render the lobby scene."""
        # Background
        self.screen.blit(self.background, (0, 0))
        
        # Title
        title = render_crayon_text("The Homeroom", 48, (0, 0, 0))
        title_rect = title.get_rect(center=(self.width // 2, 30))
        self.screen.blit(title, title_rect)
        
        # Customization panel
        panel_title = render_crayon_text("Your Character", 32, (0, 0, 0))
        self.screen.blit(panel_title, (100, 15))
        
        # Username (clickable)
        if not self.username_editing:
            font = pygame.font.Font(None, 32)
            username_surface = font.render(game_state.profile.username, True, (0, 0, 255))
            username_surface_underline = font.render(game_state.profile.username, True, (0, 0, 255))
            pygame.draw.line(
                self.screen, (0, 0, 255),
                (100, 85), (100 + username_surface.get_width(), 85), 1
            )
            self.screen.blit(username_surface, (100, 55))
        else:
            self.username_input.draw(self.screen)
        
        # Character preview
        self.character_preview.draw(
            self.screen,
            game_state.profile.color,
            game_state.profile.gear
        )
        
        # Customization buttons
        colors_label = pygame.font.Font(None, 24).render("Colors:", True, (0, 0, 0))
        self.screen.blit(colors_label, (220, 105))
        for btn in self.color_buttons:
            btn.draw(self.screen)
        
        gear_label = pygame.font.Font(None, 24).render("School Gear:", True, (0, 0, 0))
        self.screen.blit(gear_label, (220, 205))
        for btn in self.gear_buttons:
            # Highlight if equipped
            gear_name = btn.text.lower().replace(" ", "")
            if gear_name == "gradcap":
                gear_name = "cap"
            if gear_name in game_state.profile.gear:
                btn.color = (255, 215, 0)  # Gold for equipped
            else:
                btn.color = PENCIL_YELLOW
            btn.draw(self.screen)
        
        # Ready button
        self.ready_button.draw(self.screen)
        
        # Class size counter
        total_students = len(game_state.remote_players) + 1  # +1 for self
        class_size_text = f"Class Size: {total_students}/15"
        class_font = pygame.font.Font(None, 36)
        class_surface = class_font.render(class_size_text, True, (0, 0, 0))
        self.screen.blit(class_surface, (self.width // 2 - 100, 60))
        
        # Draw student desks
        all_players = [
            {
                "username": game_state.profile.username,
                "color": game_state.profile.color,
                "gear": game_state.profile.gear,
                "ready_status": self.is_ready
            }
        ]
        for player in game_state.get_all_players():
            all_players.append({
                "username": player.username,
                "color": player.color,
                "gear": player.gear,
                "ready_status": player.ready_status
            })
        
        for i, player_data in enumerate(all_players):
            if i < len(self.desk_widgets):
                self.desk_widgets[i].draw(self.screen, player_data)
        
        # Start button (host only)
        if game_state.is_host:
            self.start_button.draw(self.screen)
            
            # Show host indicator
            host_label = pygame.font.Font(None, 28).render("(You are the Teacher)", True, (255, 0, 0))
            self.screen.blit(host_label, (450, 30))
