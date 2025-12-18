"""
Login Scene for EDU-PARTY
Handles user authentication with chalkboard-style UI.
"""
import pygame
import asyncio
import aiohttp
from ui_widgets import Button, TextInput
from assets import create_chalkboard_panel, render_chalk_text, create_notebook_paper
from game_state import game_state


class LoginScene:
    """Login/Register screen."""
    
    def __init__(self, screen: pygame.Surface):
        self.screen = screen
        self.width, self.height = screen.get_size()
        
        # UI elements
        self.username_input = TextInput(
            self.width // 2 - 150, 300, 300, 40, "Student1"
        )
        self.password_input = TextInput(
            self.width // 2 - 150, 360, 300, 40, "password123"
        )
        
        self.login_button = Button(
            self.width // 2 - 100, 430, 95, 50, "Login",
            on_click=self.on_login_click
        )
        self.register_button = Button(
            self.width // 2 + 5, 430, 95, 50, "Register",
            on_click=self.on_register_click
        )
        
        # Background
        self.background = create_notebook_paper(self.width, self.height)
        self.panel = create_chalkboard_panel(500, 350)
        
        # Status message
        self.status_message = ""
        self.message_color = (255, 255, 255)
        
        # API base URL
        self.api_url = "http://localhost:8000"
    
    def on_login_click(self):
        """Handle login button click."""
        asyncio.create_task(self.attempt_login())
    
    def on_register_click(self):
        """Handle register button click."""
        asyncio.create_task(self.attempt_register())
    
    async def attempt_login(self):
        """Attempt to login with credentials."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/login",
                    json={
                        "username": self.username_input.text,
                        "password": self.password_input.text
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        game_state.profile.token = data["access_token"]
                        game_state.profile.username = data["username"]
                        self.status_message = "Login successful!"
                        self.message_color = (0, 255, 0)
                        
                        # Create lobby and transition
                        await self.create_and_join_lobby()
                    else:
                        error_data = await response.json()
                        self.status_message = error_data.get("detail", "Login failed")
                        self.message_color = (255, 0, 0)
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            self.message_color = (255, 0, 0)
    
    async def attempt_register(self):
        """Attempt to register new account."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/register",
                    json={
                        "username": self.username_input.text,
                        "password": self.password_input.text
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        game_state.profile.token = data["access_token"]
                        game_state.profile.username = data["username"]
                        self.status_message = "Registration successful!"
                        self.message_color = (0, 255, 0)
                        
                        # Create lobby and transition
                        await self.create_and_join_lobby()
                    else:
                        error_data = await response.json()
                        self.status_message = error_data.get("detail", "Registration failed")
                        self.message_color = (255, 0, 0)
        except Exception as e:
            self.status_message = f"Error: {str(e)}"
            self.message_color = (255, 0, 0)
    
    async def create_and_join_lobby(self):
        """Create a lobby after successful login."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/api/lobby/create",
                    params={"token": game_state.profile.token}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        lobby_id = data["lobby_id"]
                        
                        # Connect to WebSocket
                        from network import network
                        await network.connect(lobby_id, game_state.profile.token)
                        
                        # Transition to lobby
                        game_state.current_scene = "lobby"
                        game_state.is_host = True
        except Exception as e:
            self.status_message = f"Lobby error: {str(e)}"
            self.message_color = (255, 0, 0)
    
    def handle_event(self, event: pygame.event.Event):
        """Handle input events."""
        self.username_input.handle_event(event)
        self.password_input.handle_event(event)
        self.login_button.handle_event(event)
        self.register_button.handle_event(event)
    
    def update(self, dt: float):
        """Update scene state."""
        self.username_input.update(dt)
        self.password_input.update(dt)
    
    def draw(self):
        """Render the login scene."""
        # Background
        self.screen.blit(self.background, (0, 0))
        
        # Chalkboard panel
        panel_x = self.width // 2 - 250
        panel_y = 200
        self.screen.blit(self.panel, (panel_x, panel_y))
        
        # Title
        title = render_chalk_text("EDU-PARTY", 72)
        title_rect = title.get_rect(center=(self.width // 2, 150))
        self.screen.blit(title, title_rect)
        
        # Subtitle
        subtitle_font = pygame.font.Font(None, 28)
        subtitle = subtitle_font.render("Classroom Mayhem!", True, (0, 0, 0))
        subtitle_rect = subtitle.get_rect(center=(self.width // 2, 200))
        self.screen.blit(subtitle, subtitle_rect)
        
        # Labels
        label_font = pygame.font.Font(None, 24)
        username_label = label_font.render("Username:", True, (255, 255, 255))
        self.screen.blit(username_label, (self.width // 2 - 150, 275))
        
        password_label = label_font.render("Password:", True, (255, 255, 255))
        self.screen.blit(password_label, (self.width // 2 - 150, 335))
        
        # Input fields and buttons
        self.username_input.draw(self.screen)
        self.password_input.draw(self.screen)
        self.login_button.draw(self.screen)
        self.register_button.draw(self.screen)
        
        # Status message
        if self.status_message:
            status_font = pygame.font.Font(None, 24)
            status_surface = status_font.render(self.status_message, True, self.message_color)
            status_rect = status_surface.get_rect(center=(self.width // 2, 500))
            self.screen.blit(status_surface, status_rect)
