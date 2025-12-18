"""
GameController Class - Master orchestrator for the game.
Manages main loop, event handling, and state transitions using the View System.
"""
import pygame
import asyncio
import aiohttp
from enum import Enum, auto
from typing import Any, Optional

from constants import (
    SCREEN_WIDTH, SCREEN_HEIGHT, FPS, API_URL,
    CHALKBOARD_DARK, CHALK_WHITE, SCHOOL_BUS_YELLOW, MAYHEM_PURPLE, GEAR_DATABASE
)
from student import Student
from network_manager import NetworkManager
from math_dash import MathDash
from profile_badge import ProfileBadge

# Views
from views.base_view import BaseView
from views.lobby_list_view import LobbyListView
from views.lobby_settings_view import LobbySettingsView
from views.in_lobby_view import InLobbyView
from profile_view import ProfileView  # Renamed/Refactored existing


class GameState(Enum):
    """Game state enumeration for Educational Mayhem."""
    MENU = auto()           # Login screen (keep legacy for now or refactor later)
    LOBBY_LIST = auto()     # New: List of lobbies
    LOBBY_SETTINGS = auto() # New: Create lobby modal
    IN_LOBBY = auto()       # New: Waiting room
    PROFILE_VIEW = auto()   # Character customizer
    MATH_MINIGAME = auto()  # Gameplay


class GameController:
    """Master class that manages the entire game."""
    
    def __init__(self):
        """Initialize the game controller."""
        # Pygame setup
        pygame.init()
        self._screen: pygame.Surface = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption("EDU-PARTY: Educational Mayhem")
        self._clock: pygame.time.Clock = pygame.time.Clock()
        self._running: bool = True
        
        # Audio/Assets (Placeholder)
        self.assets = {}
        
        # Network
        self._network: NetworkManager = NetworkManager(API_URL.replace("http", "ws"))
        self._token: str = ""
        
        # Game Data
        self._students: dict[str, Student] = {}
        self._local_student: Student | None = None
        self._lobby_id: str = ""
        self._is_host: bool = False
        
        # Legacy UI State (Menu)
        self._username_input: str = "Student1"
        self._password_input: str = "password123"
        self._status_message: str = ""
        
        # Minigame
        self._math_dash: MathDash = MathDash(SCREEN_WIDTH, SCREEN_HEIGHT)
        
        # View Management
        self.views: dict[str, BaseView] = {}
        self._active_view: BaseView | None = None
        self._state: GameState = GameState.MENU
        
        # Profile Badge (Overlay)
        self._profile_badge: ProfileBadge = ProfileBadge()

        # Initialize Views
        self._init_views()
    
    def _init_views(self):
        """Initialize all view instances."""
        self.views["LOBBY_LIST"] = LobbyListView(self._screen, self)
        self.views["LOBBY_SETTINGS"] = LobbySettingsView(self._screen, self)
        self.views["IN_LOBBY"] = InLobbyView(self._screen, self)
        self.views["PROFILE"] = ProfileView(self._screen, self)
        
        # Note: MENU and GAME are currently handled inline or legacy, 
        # but could be moved to views later.
    
    # Properties for Views to access
    @property
    def screen(self) -> pygame.Surface:
        return self._screen
        
    @property
    def network_manager(self) -> NetworkManager:
        return self._network

    @property
    def network(self) -> NetworkManager: # Alias
        return self._network
        
    @property
    def local_student(self) -> Student | None:
        return self._local_student
        
    @property
    def students(self) -> dict[str, Student]:
        return self._students
        
    @property
    def is_host(self) -> bool:
        return self._is_host
        
    @property
    def token(self) -> str:
        return self._token
        
    @property
    def lobby_id(self) -> str:
        return self._lobby_id

    # State Management
    def switch_state(self, new_state_name: str | GameState) -> None:
        """Transition to a new game state."""
        # Convert string to enum if needed
        if isinstance(new_state_name, str):
            try:
                # Map string names to Enum
                mapping = {
                    "LOBBY": GameState.LOBBY_LIST, # Default 'LOBBY' goes to list now
                    "LOBBY_LIST": GameState.LOBBY_LIST,
                    "LOBBY_SETTINGS": GameState.LOBBY_SETTINGS,
                    "IN_LOBBY": GameState.IN_LOBBY,
                    "PROFILE": GameState.PROFILE_VIEW,
                    "GAME": GameState.MATH_MINIGAME,
                    "MENU": GameState.MENU
                }
                new_state = mapping.get(new_state_name.upper(), GameState.MENU)
            except:
                print(f"Invalid state name: {new_state_name}")
                return
        else:
            new_state = new_state_name
            
        print(f"[GameController] Switch State: {self._state} -> {new_state}")
        
        # Exit current view
        if self._active_view:
            self._active_view.on_leave()
            
        self._state = new_state
        
        # Set new active view
        if new_state == GameState.LOBBY_LIST:
            self._active_view = self.views["LOBBY_LIST"]
        elif new_state == GameState.LOBBY_SETTINGS:
            self._active_view = self.views["LOBBY_SETTINGS"]
        elif new_state == GameState.IN_LOBBY:
            self._active_view = self.views["IN_LOBBY"]
        elif new_state == GameState.PROFILE_VIEW:
            self._active_view = self.views["PROFILE"]
        else:
            self._active_view = None # Handled by legacy methods (Menu/Game)
            
        # Enter new view
        if self._active_view:
            self._active_view.on_enter()

    async def create_lobby(self, capacity: int, game_mode: str) -> None:
        """Create a lobby via NetworkManager."""
        result = await self._network.create_lobby(self._token, capacity, game_mode)
        if result:
            self._lobby_id = result.get("lobby_id", "")
            # Connect to it
            connected = await self._network.connect(self._lobby_id, self._token)
            if connected:
                self._is_host = True
                self.switch_state(GameState.IN_LOBBY)
            else:
                print("Failed to connect to created lobby")
        else:
            print("Failed to create lobby")

    # Main Loop Methods
    def handle_events(self) -> None:
        """Process pygame events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self._running = False
            
            # Profile Badge Click (Global if logged in)
            if self._local_student and self._state != GameState.PROFILE_VIEW:
                if self._profile_badge.handle_event(event):
                    self.switch_state(GameState.PROFILE_VIEW)
                    return

            # Delegate to active view
            if self._active_view:
                self._active_view.handle_event(event)
            else:
                # Fallback to legacy handlers
                if self._state == GameState.MENU:
                    self._handle_menu_events(event)
                elif self._state == GameState.MATH_MINIGAME:
                    self._handle_game_events(event)

    def update(self, dt: float) -> None:
        """Update game state."""
        self._process_network_messages()
        
        if self._active_view:
            self._active_view.update(dt)
        else:
            if self._state == GameState.MATH_MINIGAME:
                round_ended = self._math_dash.update(dt)
                if round_ended and not self._math_dash.active and self._is_host:
                    if self._math_dash._show_result == False:
                        asyncio.create_task(self._start_new_round())

    def render(self) -> None:
        """Render the current state."""
        if self._active_view:
            self._active_view.render()
            
            # Draw Profile Badge on top of most views (except Profile itself)
            if self._state != GameState.PROFILE_VIEW and self._local_student:
                self._profile_badge.render(
                    self._screen,
                    self._local_student.username,
                    self._local_student.color,
                    self._local_student._shape
                )
        else:
            if self._state == GameState.MENU:
                self._render_menu()
            elif self._state == GameState.MATH_MINIGAME:
                self._render_game()
        
        pygame.display.flip()

    # Legacy/Inline Handlers (for Menu and Game)
    def _handle_menu_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                asyncio.create_task(self._attempt_login())
            elif event.key == pygame.K_r:
                asyncio.create_task(self._attempt_register())

    def _handle_game_events(self, event: pygame.event.Event) -> None:
        if event.type == pygame.KEYDOWN and self._local_student:
            if event.key in (pygame.K_1, pygame.K_a, pygame.K_LEFT):
                self._move_to_platform(0)
            elif event.key in (pygame.K_2,):
                self._move_to_platform(1)
            elif event.key in (pygame.K_3, pygame.K_d, pygame.K_RIGHT):
                self._move_to_platform(2)

    def _render_menu(self) -> None:
        self._screen.fill(CHALKBOARD_DARK)
        # Title
        font_title = pygame.font.Font(None, 72)
        title = font_title.render("EDU-PARTY", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 150))
        self._screen.blit(title, title_rect)
        
        # Subtitle
        font_sub = pygame.font.Font(None, 32)
        subtitle = font_sub.render("Educational Mayhem Edition", True, CHALK_WHITE)
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
            
        if self._status_message:
            status = font.render(self._status_message, True, SCHOOL_BUS_YELLOW)
            status_rect = status.get_rect(center=(SCREEN_WIDTH // 2, 550))
            self._screen.blit(status, status_rect)

    def _render_game(self) -> None:
        # Title
        self._screen.fill(CHALKBOARD_DARK)
        font_title = pygame.font.Font(None, 56)
        title = font_title.render("Math Dash!", True, SCHOOL_BUS_YELLOW)
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 40))
        self._screen.blit(title, title_rect)
        
        self._math_dash.render(self._screen)
        
        # Render students
        if self._local_student:
            self._render_student_on_platform(self._local_student)
        
        for student in self._students.values():
            self._render_student_on_platform(student)
            
        # Controls reminder
        font_small = pygame.font.Font(None, 24)
        controls = font_small.render("Use 1/2/3 or A/D or Arrow Keys to move", True, CHALK_WHITE)
        controls_rect = controls.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
        self._screen.blit(controls, controls_rect)

    def _render_student_on_platform(self, student):
        platform_index = self._math_dash.get_player_platform(student.id)
        if 0 <= platform_index < 3:
            platform = self._math_dash._platforms[platform_index]
            student.render(self._screen, platform.rect.centerx - 32, platform.rect.top - 70, 64)

    # Network Logic
    async def _attempt_login(self) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/login",
                    json={"username": self._username_input, "password": self._password_input}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._token = data["access_token"]
                        self._local_student = Student("temp_id", data["username"])
                        # Success - Go to Lobby List
                        self.switch_state(GameState.LOBBY_LIST)
                    else:
                        self._status_message = "Login failed"
        except Exception as e:
            self._status_message = f"Error: {str(e)}"

    async def _attempt_register(self) -> None:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/register",
                    json={"username": self._username_input, "password": self._password_input}
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        self._token = data["access_token"]
                        self._local_student = Student("temp_id", data["username"])
                        self.switch_state(GameState.LOBBY_LIST)
                    else:
                        self._status_message = "Registration failed"
        except Exception as e:
            self._status_message = f"Error: {str(e)}"

    def _process_network_messages(self) -> None:
        """Process incoming network messages."""
        while True:
            message = self._network.get_message()
            if message is None:
                break
            
            msg_type = message.get("type", "")
            
            if msg_type == "connected":
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
                for p_data in players:
                    sid = p_data.get("id")
                    if sid and sid != (self._local_student.id if self._local_student else ""):
                         s = Student(sid, p_data.get("username", "Student"))
                         s.from_dict(p_data)
                         self._students[sid] = s

            elif msg_type == "profile_update":
                p_data = message.get("player", {})
                sid = p_data.get("id")
                if sid in self._students:
                    self._students[sid].from_dict(p_data)
                elif self._local_student and sid == self._local_student.id:
                    self._local_student.from_dict(p_data)

            elif msg_type == "ready_update":
                pid = message.get("player_id")
                r = message.get("ready")
                if pid in self._students:
                    self._students[pid].ready = r
                elif self._local_student and pid == self._local_student.id:
                    self._local_student.ready = r
                    
            elif msg_type == "game_start":
                self.switch_state(GameState.MATH_MINIGAME)
                if self._is_host:
                    asyncio.create_task(self._start_new_round())
                    
            elif msg_type == "game_action":
                self._handle_game_action(message)

    def _handle_game_action(self, message):
         action = message.get("action", {})
         action_type = action.get("action_type", "")
         
         if action_type == "new_round":
             problem = action.get("problem", {})
             self._math_dash._setup_round(problem)
             
         elif action_type == "move":
             player_id = message.get("player_id", "")
             platform = action.get("platform", 0)
             self._math_dash.set_player_platform(player_id, platform)

    def _move_to_platform(self, platform_index):
        if not self._local_student or not self._math_dash.active:
            return
        self._math_dash.set_player_platform(self._local_student.id, platform_index)
        asyncio.create_task(self._network.send_game_action({
            "action_type": "move", "platform": platform_index
        }))

    async def _start_new_round(self):
        problem_data = self._math_dash.generate_problem()
        await self._network.send_game_action({
            "action_type": "new_round", "problem": problem_data
        })

    async def run(self) -> None:
        """Main async game loop (60 FPS)."""
        while self._running:
            dt = self._clock.tick(FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()
            await asyncio.sleep(0)
        
        if self._network.connected:
            await self._network.disconnect()
        pygame.quit()
