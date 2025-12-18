"""
GameController Class - Master orchestrator for the game.
Manages main loop, event handling, and state transitions.
"""
import pygame
import asyncio
import aiohttp
from enum import Enum, auto
from typing import Any
from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, API_URL,
    CHALKBOARD_DARK, CHALK_WHITE, SCHOOL_BUS_YELLOW, GEAR_DATABASE
)
from student import Student
from network_manager import NetworkManager
from math_dash import MathDash


class GameState(Enum):
    """Game state enumeration."""
    MENU = auto()
    LOBBY = auto()
    MATH_MINIGAME = auto()


class GameController:
    """Master class that manages the entire game."""
    
    def __init__(self):
        """Initialize the game controller."""
        # Pygame setup
        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EDU-PARTY - OOP Edition")
        self._clock: pygame.time.Clock = pygame.time.Clock()
        self._running: bool = True
        
        # Game state
        self._state: GameState = GameState.MENU
        
        # Network
        self._network: NetworkManager = NetworkManager("ws://localhost:8000")
        
        # Students
        self._students: dict[str, Student] = {}
        self._local_student: Student | None = None
        self._is_host: bool = False
        
        # Auth data
        self._token: str = ""
        self._lobby_id: str = ""
        
        # Minigame
        self._math_dash: MathDash = MathDash(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # UI state
        self._username_input: str = "Student1"
        self._password_input: str = "password123"
        self._status_message: str = ""
        self._gear_index: int = 0  # For cycling through GEAR_DATABASE
    
    @property
    def state(self) -> GameState:
        """Get current game state."""
        return self._state
    
    @property
    def local_student(self) -> Student | None:
        """Get local student."""
        return self._local_student
    
    def switch_state(self, new_state: GameState) -> None:
        """Transition to a new game state.
        
        Args:
            new_state: The state to transition to
        """
        print(f"[GameController] State transition: {self._state} -> {new_state}")
        self._state = new_state
    
    # Event handling
    def handle_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            
            elif self._state == GameState.MENU:
                self._handle_menu_events(event)
            
            elif self._state == GameState.LOBBY:
                self._handle_lobby_events(event)
            
            elif self._state == GameState.MATH_MINIGAME:
                self._handle_game_events(event)
    
    def _handle_menu_events(self, event: pygame.event.Event) -> None:
        """Handle events in MENU state."""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                # Login
                asyncio.create_task(self._attempt_login())
            elif event.key == pygame.K_r:
                # Register
                asyncio.create_task(self._attempt_register())
    
    def _handle_lobby_events(self, event: pygame.event.Event) -> None:
        """Handle events in LOBBY state."""
        if event.type == pygame.KEYDOWN:
            # Gear cycling
            if event.key == pygame.K_g and self._local_student:
                self._cycle_gear()
            
            # Color changing
            elif event.key == pygame.K_1 and self._local_student:
                self._change_color("red")
            elif event.key == pygame.K_2 and self._local_student:
                self._change_color("blue")
            elif event.key == pygame.K_3 and self._local_student:
                self._change_color("green")
            
            # Ready toggle
            elif event.key == pygame.K_SPACE and self._local_student:
                new_ready = not self._local_student.ready
                self._local_student.ready = new_ready
                asyncio.create_task(self._network.toggle_ready(new_ready))
            
            # Start game (host only)
            elif event.key == pygame.K_s and self._is_host:
                asyncio.create_task(self._network.start_game())
    
    def _handle_game_events(self, event: pygame.event.Event) -> None:
        """Handle events in MATH_MINIGAME state."""
        if event.type == pygame.KEYDOWN and self._local_student:
            # Platform movement
            if event.key in (pygame.K_1, pygame.K_a, pygame.K_LEFT):
                self._move_to_platform(0)
            elif event.key in (pygame.K_2,):
                self._move_to_platform(1)
            elif event.key in (pygame.K_3, pygame.K_d, pygame.K_RIGHT):
                self._move_to_platform(2)
    
    # Update logic
    def update(self, dt: float) -> None:
        """Update game state.
        
        Args:
            dt: Delta time in seconds
        """
        # Process network messages
        self._process_network_messages()
        
        if self._state == GameState.MATH_MINIGAME:
            # Update minigame
            round_ended = self._math_dash.update(dt)
            
            # Generate new round if needed
            if round_ended and not self._math_dash.active and self._is_host:
                if self._math_dash._show_result == False:
                    asyncio.create_task(self._start_new_round())
    
    def _process_network_messages(self) -> None:
        """Process incoming network messages."""
        while True:
            message = self._network.get_message()
            if message is None:
                break
            
            msg_type = message.get("type", "")
            
            if msg_type == "connected":
                # Initial connection
                student_id = message.get("player_id", "")
                if self._local_student:
                    self._local_student._id = student_id
            
            elif msg_type == "player_joined":
                player_data = message.get("player", {})
                student_id = player_data.get("id", "")
                if student_id and student_id != (self._local_student.id if self._local_student else ""):
                    student = Student(student_id, player_data.get("username", "Student"))
                    student.from_dict(player_data)
                    self._students[student_id] = student
            
            elif msg_type == "player_left":
                player_id = message.get("player_id", "")
                self._students.pop(player_id, None)
            
            elif msg_type == "players_list":
                players = message.get("players", [])
                for player_data in players:
                    student_id = player_data.get("id", "")
                    if student_id and student_id != (self._local_student.id if self._local_student else ""):
                        student = Student(student_id, player_data.get("username", "Student"))
                        student.from_dict(player_data)
                        self._students[student_id] = student
            
            elif msg_type == "profile_update":
                player_data = message.get("player", {})
                student_id = player_data.get("id", "")
                if student_id in self._students:
                    self._students[student_id].from_dict(player_data)
            
            elif msg_type == "ready_update":
                player_id = message.get("player_id", "")
                ready = message.get("ready", False)
                if player_id in self._students:
                    self._students[player_id].ready = ready
            
            elif msg_type == "game_start":
                self.switch_state(GameState.MATH_MINIGAME)
                if self._is_host:
                    asyncio.create_task(self._start_new_round())
            
            elif msg_type == "game_action":
                self._handle_game_action(message)
    
    def _handle_game_action(self, message: dict[str, Any]) -> None:
        """Handle game action messages."""
        action = message.get("action", {})
        action_type = action.get("action_type", "")
        
        if action_type == "new_round":
            problem = action.get("problem", {})
            self._math_dash._setup_round(problem)
        
        elif action_type == "move":
            player_id = message.get("player_id", "")
            platform = action.get("platform", 0)
            self._math_dash.set_player_platform(player_id, platform)
            
            # Update student position
            if player_id in self._students and 0 <= platform < 3:
                student = self._students[player_id]
                platform_obj = self._math_dash._platforms[platform]
                student.update_position(
                    platform_obj.rect.centerx,
                    platform_obj.rect.top - 70
                )
    
    # Rendering
    def render(self) -> None:
        """Render the current game state."""
        self._screen.fill(CHALKBOARD_DARK)
        
        if self._state == GameState.MENU:
            self._render_menu()
        elif self._state == GameState.LOBBY:
            self._render_lobby()
        elif self._state == GameState.MATH_MINIGAME:
            self._render_game()
        
        pygame.display.flip()
    
    def _render_menu(self) -> None:
        """Render MENU state."""
        # Title
        font_title = pygame.font.Font(None, 72)
        title = font_title.render("EDU-PARTY", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self._screen.blit(title, title_rect)
        
        # Subtitle
        font_sub = pygame.font.Font(None, 32)
        subtitle = font_sub.render("OOP Game Engine Edition", True, CHALK_WHITE)
        subtitle_rect = subtitle.get_rect(center=(SCREEN_WIDTH // 2, 210))
        self._screen.blit(subtitle, subtitle_rect)
        
        # Instructions
        font = pygame.font.Font(None, 28)
        instructions = [
            f"Username: {self._username_input}",
            f"Password: {self._password_input}",
            "",
            "Press ENTER to Login",
            "Press R to Register"
        ]
        
        y = 300
        for line in instructions:
            text = font.render(line, True, CHALK_WHITE)
            text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, y))
            self._screen.blit(text, text_rect)
            y += 40
        
        # Status message
        if self._status_message:
            status = font.render(self._status_message, True, SCHOOL_BUS_YELLOW)
            status_rect = status.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self._screen.blit(status, status_rect)
    
    def _render_lobby(self) -> None:
        """Render LOBBY state (Homeroom)."""
        # Title
        font_title = pygame.font.Font(None, 56)
        title = font_title.render("The Homeroom", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self._screen.blit(title, title_rect)
        
        # Class size
        font = pygame.font.Font(None, 32)
        class_size = len(self._students) + (1 if self._local_student else 0)
        class_text = font.render(f"Class Size: {class_size}/15", True, CHALK_WHITE)
        self._screen.blit(class_text, (50, 100))
        
        # Student preview (local)
        if self._local_student:
            self._local_student.render(self._screen, 50, 150, 80)
            username_text = font.render(self._local_student.username, True, CHALK_WHITE)
            self._screen.blit(username_text, (50, 240))
            
            ready_text = "READY!" if self._local_student.ready else "Not Ready"
            ready_color = SCHOOL_BUS_YELLOW if self._local_student.ready else CHALK_WHITE
            ready = font.render(ready_text, True, ready_color)
            self._screen.blit(ready, (50, 270))
        
        # Controls
        controls = [
            "1/2/3: Change Color",
            "G: Cycle Gear",
            "SPACE: Toggle Ready",
        ]
        if self._is_host:
            controls.append("S: Start Game")
        
        y = 320
        small_font = pygame.font.Font(None, 24)
        for control in controls:
            text = small_font.render(control, True, CHALK_WHITE)
            self._screen.blit(text, (50, y))
            y += 30
        
        # Render other students in a grid
        desk_x = 300
        desk_y = 150
        desk_spacing_x = 150
        desk_spacing_y = 150
        col = 0
        row = 0
        
        for student in self._students.values():
            x = desk_x + col * desk_spacing_x
            y = desk_y + row * desk_spacing_y
            
            student.render(self._screen, x, y, 64)
            
            name_font = pygame.font.Font(None, 20)
            name_text = name_font.render(student.username, True, CHALK_WHITE)
            name_rect = name_text.get_rect(center=(x + 32, y + 75))
            self._screen.blit(name_text, name_rect)
            
            if student.ready:
                ready_indicator = name_font.render("✓", True, SCHOOL_BUS_YELLOW)
                self._screen.blit(ready_indicator, (x + 50, y - 5))
            
            col += 1
            if col >= 5:
                col = 0
                row += 1
    
    def _render_game(self) -> None:
        """Render MATH_MINIGAME state."""
        # Title
        font_title = pygame.font.Font(None, 56)
        title = font_title.render("Math Dash!", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self._screen.blit(title, title_rect)
        
        # Render minigame
        self._math_dash.render(self._screen)
        
        # Render students on platforms
        if self._local_student:
            platform_index = self._math_dash.get_player_platform(self._local_student.id)
            if 0 <= platform_index < 3:
                platform = self._math_dash._platforms[platform_index]
                self._local_student.render(
                    self._screen,
                    platform.rect.centerx - 32,
                    platform.rect.top - 70,
                    64
                )
        
        for student in self._students.values():
            platform_index = self._math_dash.get_player_platform(student.id)
            if 0 <= platform_index < 3:
                platform = self._math_dash._platforms[platform_index]
                student.render(
                    self._screen,
                    platform.rect.centerx - 32,
                    platform.rect.top - 70,
                    64
                )
        
        # Controls reminder
        font_small = pygame.font.Font(None, 24)
        controls = font_small.render("Use 1/2/3 or A/D or Arrow Keys to move", True, CHALK_WHITE)
        controls_rect = controls.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self._screen.blit(controls, controls_rect)
    
    # Helper methods
    async def _attempt_login(self) -> None:
        """Attempt to login."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/login",
                    json={
                        "username": self._username_input,
                        "password": self._password_input
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._token = data["access_token"]
                        await self._create_and_join_lobby(data["username"])
                    else:
                        self._status_message = "Login failed"
        except Exception as e:
            self._status_message = f"Error: {str(e)}"
    
    async def _attempt_register(self) -> None:
        """Attempt to register."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/register",
                    json={
                        "username": self._username_input,
                        "password": self._password_input
                    }
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._token = data["access_token"]
                        await self._create_and_join_lobby(data["username"])
                    else:
                        self._status_message = "Registration failed"
        except Exception as e:
            self._status_message = f"Error: {str(e)}"
    
    async def _create_and_join_lobby(self, username: str) -> None:
        """Create lobby and join."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/lobby/create",
                    params={"token": self._token}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._lobby_id = data["lobby_id"]
                        
                        # Create local student
                        self._local_student = Student("temp_id", username)
                        
                        # Connect to WebSocket
                        connected = await self._network.connect(self._lobby_id, self._token)
                        if connected:
                            self._is_host = True
                            self.switch_state(GameState.LOBBY)
        except Exception as e:
            self._status_message = f"Lobby error: {str(e)}"
    
    def _cycle_gear(self) -> None:
        """Cycle through gear items."""
        if not self._local_student:
            return
        
        # Get current gear item
        current_gear = GEAR_DATABASE[self._gear_index]
        
        # Toggle it
        self._local_student.toggle_gear(current_gear)
        
        # Move to next
        self._gear_index = (self._gear_index + 1) % len(GEAR_DATABASE)
        
        # Sync to server
        asyncio.create_task(self._network.update_profile(gear=self._local_student.gear))
    
    def _change_color(self, color: str) -> None:
        """Change student color."""
        if self._local_student:
            self._local_student.color = color
            asyncio.create_task(self._network.update_profile(color=color))
    
    def _move_to_platform(self, platform_index: int) -> None:
        """Move student to a platform."""
        if not self._local_student or not self._math_dash.active:
            return
        
        self._math_dash.set_player_platform(self._local_student.id, platform_index)
        
        # Update position
        if 0 <= platform_index < 3:
            platform = self._math_dash._platforms[platform_index]
            self._local_student.update_position(
                platform.rect.centerx,
                platform.rect.top - 70
            )
        
        # Send to server
        asyncio.create_task(self._network.send_game_action({
            "action_type": "move",
            "platform": platform_index
        }))
    
    async def _start_new_round(self) -> None:
        """Generate and broadcast new math problem."""
        problem_data = self._math_dash.generate_problem()
        await self._network.send_game_action({
            "action_type": "new_round",
            "problem": problem_data
        })
    
    # Main loop
    async def run(self) -> None:
        """Main async game loop (60 FPS)."""
        while self._running:
            dt = self._clock.tick(FPS) / 1000.0
            
            self.handle_events()
            self.update(dt)
            self.render()
            
            # Yield to async tasks
            await asyncio.sleep(0)
        
        # Cleanup
        if self._network.connected:
            await self._network.disconnect()
        
        pygame.quit()
