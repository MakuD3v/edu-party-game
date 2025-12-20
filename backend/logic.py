"""
logic.py
The Core Logic Engine for Educational Mayhem.
Implements specific game rules and state management using strict OOP.
"""
import uuid
import asyncio
import random
import time
from typing import Dict, List, Optional
from fastapi import WebSocket

from .models import PlayerState, ShapeEnum, LobbySummary

class Player:
    """
    Player Class.
    Encapsulates all session-specific state and logic for a single user.
    """
    def __init__(self, player_id: str, username: str, websocket: WebSocket):
        self.id = player_id
        self.username = username
        self.websocket = websocket
        
        # State Data (Pedagogical Note: We keep defaults strict)
        self.color: str = "#4a148c" 
        self.shape: ShapeEnum = ShapeEnum.CIRCLE
        self.is_ready: bool = False
        self.is_host: bool = False
        self.lobby_id: str | None = None

    def update_profile(self, color: str, shape: ShapeEnum) -> None:
        """Mutates player profile state."""
        self.color = color
        self.shape = shape
    
    def to_state(self) -> PlayerState:
        """Returns a clean DTO representation of the player."""
        return PlayerState(
            id=self.id,
            username=self.username,
            color=self.color,
            shape=self.shape,
            is_ready=self.is_ready,
            is_host=self.is_host
        )


class Lobby:
    """
    Lobby Class.
    Manages the lifecycle of a game session: Joining, Leaving, and Limits.
    """
    def __init__(self, lobby_id: str, host: Player, max_capacity: int):
        self.id = lobby_id
        self.host_id = host.id
        self.max_capacity = max(5, min(max_capacity, 50)) # Clamp 5-50
        self.players: Dict[str, Player] = {}
        self.player_map: Dict[str, str] = {} # Username -> PlayerID (Persists even if disconnected)
        
        # Tournament State
        self.active_players: List[str] = [] # Player IDs still competing
        self.spectators: List[str] = [] # Eliminated player IDs
        self.current_game: int = 0      # 0=None, 1=Math, 2=Typing, 3=Maze
        self.game_round: int = 0
        
        # Game State
        self.current_question: Dict = None
        self.player_scores: Dict[str, int] = {} # player_id -> score
        self.last_score_update: Dict[str, float] = {} # player_id -> timestamp (for tie-breaking)
        self.game_history: List[int] = [] # Track played games
        self.available_games: List[int] = [1, 2, 3]

        # Immediately add host
        self.add_player(host)
        host.is_host = True
    
    @staticmethod
    def get_game_info(game_number: int) -> Dict:
        """
        Returns metadata for a specific game for UI display.
        EDU PARTY Educational Mayhem game information.
        """
        game_data = {
            1: {
                "name": "MATH QUIZ",
                "description": "Answer math problems as fast as you can!",
                "icon": "🧮",
                "color": "#E74C3C",  # Red
                "duration": 20
            },
            2: {
                "name": "SPEED TYPING",
                "description": "Type words at lightning speed!",
                "icon": "⌨️",
                "color": "#3498DB",  # Blue
                "duration": 60
            },
            3: {
                "name": "TECH SPRINT",
                "description": "Race to the finish by answering tech questions!",
                "icon": "🧩",
                "color": "#F39C12",  # Orange
                "duration": 90
            }
        }
        return game_data.get(game_number, {
            "name": "UNKNOWN",
            "description": "Mystery game!",
            "icon": "❓",
            "color": "#95A5A6",
            "duration": 30
        })

    def select_next_game(self) -> int:
        """
        Select a random game avoiding repeats from last 2 rounds.
        Implements EDU PARTY Educational Mayhem weighted randomization for variety.
        """
        # Build exclusion set from recent history
        if len(self.game_history) >= 2:
            excluded = set(self.game_history[-2:])
        elif len(self.game_history) == 1:
            excluded = {self.game_history[-1]}
        else:
            excluded = set()
            
        # Get possible games (exclude recent ones)
        possible = [g for g in self.available_games if g not in excluded]
        
        # Fallback: if somehow all are excluded (shouldn't happen with 3 games + logic)
        # Just avoid the very last game
        if not possible:
            possible = [g for g in self.available_games if g != self.game_history[-1]]
        
        # Ultimate fallback
        if not possible:
            possible = self.available_games.copy()
        
        # Weighted selection: Games played less recently get higher weights
        weights = []
        for game in possible:
            # Base weight
            weight = 1.0
            
            # Increase weight if game hasn't been played in a while
            if game not in self.game_history:
                weight = 2.0  # Never played yet
            elif len(self.game_history) >= 3 and game not in self.game_history[-3:]:
                weight = 1.5  # Not in last 3 rounds
            
            weights.append(weight)
        
        # Weighted random choice
        selected = random.choices(possible, weights=weights, k=1)[0]
        self.game_history.append(selected)
        
        return selected

    @property
    def is_full(self) -> bool:
        return len(self.players) >= self.max_capacity

    def add_player(self, player: Player) -> bool:
        """Attempts to add a player to the lobby. Handles Reconnection."""
        if self.is_full:
            return False
        
        # RECONNECTION LOGIC:
        # Check if this username was already playing
        if player.username in self.player_map:
            old_id = self.player_map[player.username]
            # If the old ID is still in players, wait, that's a duplicate login? 
            # Or valid reconnection if connection died.
            
            if old_id in self.players:
                # Duplicate login? Or socket zombie?
                # We should probably kick the old one or reject the new one.
                # For now, let's assume it's a replacement.
                pass
            
            # SWAP ID in game state to the NEW ID
            new_id = player.id
            
            # 1. Update Active Players
            if old_id in self.active_players:
                self.active_players = [new_id if pid == old_id else pid for pid in self.active_players]
                
            # 2. Update Spectators
            if old_id in self.spectators:
                self.spectators = [new_id if pid == old_id else pid for pid in self.spectators]
                
            # 3. Update Scores
            if old_id in self.player_scores:
                self.player_scores[new_id] = self.player_scores.pop(old_id)
                
            # 4. Update Maze State (Game 3)
            if hasattr(self, 'maze_state') and old_id in self.maze_state:
                self.maze_state[new_id] = self.maze_state.pop(old_id)
                
            print(f"[LOBBY] Reconnected {player.username}: Swapped {old_id} -> {new_id}")
            
        # Add to current players
        self.players[player.id] = player
        self.player_map[player.username] = player.id # Update map to new ID
        player.lobby_id = self.id
        return True

    async def broadcast(self, message: dict, exclude_id: str | None = None) -> None:
        """Thread-safe(ish) broadcast to all active websockets in lobby."""
        for pid, player in self.players.items():
            if pid == exclude_id:
                continue
            try:
                await player.websocket.send_json(message)
            except Exception:
                # Connection might be dead; Manager handles cleanup
                pass

    def get_summary(self) -> LobbySummary:
        """Returns lightweight info for the directory."""
        host_name = self.players[self.host_id].username if self.host_id in self.players else "Unknown"
        return LobbySummary(
            id=self.id,
            host_name=host_name,
            player_count=len(self.players),
            max_players=self.max_capacity,
            is_full=self.is_full
        )
    
    # === TOURNAMENT GAME METHODS ===
    
    def start_tournament(self) -> None:
        """Initialize tournament with all ready players as active."""
        self.current_game = 1
        self.active_players = [pid for pid, p in self.players.items() if p.is_ready]
        self.spectators = []
        self.player_scores = {pid: 0 for pid in self.active_players}
        self.game_start_time = time.time()
    
    def generate_math_question(self) -> Dict:
        """Generate a primary-grade math question (1-20 range)."""
        num1 = random.randint(1, 20)
        num2 = random.randint(1, 20)
        operation = random.choice(['+', '-'])
        
        if operation == '+':
            answer = num1 + num2
            question = f"{num1} + {num2}"
        else:
            # Ensure no negative results
            if num1 < num2:
                num1, num2 = num2, num1
            answer = num1 - num2
            question = f"{num1} - {num2}"
        
        question_id = str(uuid.uuid4())[:8]
        self.current_question = {
            'id': question_id,
            'text': question,
            'answer': answer
        }
        return self.current_question
    
    def check_answer(self, player_id: str, answer: int) -> bool:
        """Check math answer for Game 1."""
        if not self.current_question:
            return False
        
        correct = (self.current_question["answer"] == answer)
        if correct:
            self.player_scores[player_id] = self.player_scores.get(player_id, 0) + 1
            self.last_score_update[player_id] = time.time()
        return correct
        
    # --- GAME 2: SPEED TYPING ---
    def generate_typing_words(self, count=50) -> List[str]:
        """Generate a list of random words for typing game."""
        words = [
            "apple", "banana", "cherry", "date", "elderberry", "fig", "grape",
            "house", "island", "jungle", "kite", "lemon", "mango", "nest",
            "ocean", "piano", "queen", "river", "sun", "tiger", "umbrella",
            "violet", "water", "xylophone", "yellow", "zebra", "cloud",
            "dream", "energy", "flower", "garden", "happy", "image", "juice",
            "king", "lion", "mouse", "night", "orange", "pencil", "quiet",
            "radio", "snake", "tree", "unicorn", "vision", "whale", "xray"
        ]
        import random
        return [random.choice(words) for _ in range(count)]

    def check_typed_word(self, player_id: str, current_word: str, typed_word: str) -> bool:
        """Check typed word for Game 2."""
        correct = (current_word.lower().strip() == typed_word.lower().strip())
        if correct:
            # +1 score for each correct word
            self.player_scores[player_id] = self.player_scores.get(player_id, 0) + 1
            self.last_score_update[player_id] = time.time()
        return correct

    # --- GAME 3: MAZE CHALLENGE ---
    def generate_maze(self) -> Dict:
        """Generate a simple linear maze with checkpoints."""
        # Simple linear track with 20 steps
        # Checkpoints at steps 5, 10, 15
    # --- GAME 3: TECH QUIZ RACE ---
    def generate_tech_questions(self) -> List[Dict]:
        """Generate a list of 50 randomized tech questions for the race."""
        pool = [
            {"q": "What does CPU stand for?", "options": ["Central Processing Unit", "Computer Power Unit", "Central Power Unit", "Core Processing Unit"], "a": 0},
            {"q": "Which is a Python loop?", "options": ["circle", "for", "spin", "repeat"], "a": 1},
            {"q": "What is HTML used for?", "options": ["Database", "Styling", "Structure", "Programming"], "a": 2},
            {"q": "Which symbol is for comments in Python?", "options": ["//", "/*", "#", "--"], "a": 2},
            {"q": "What is 2 ** 3 in Python?", "options": ["5", "6", "8", "9"], "a": 2},
            {"q": "What does RAM stand for?", "options": ["Read Access Memory", "Random Access Memory", "Run All Memory", "Real Authorization Mode"], "a": 1},
            {"q": "Which is NOT a programming language?", "options": ["Java", "Python", "HTML", "C++"], "a": 2},
            {"q": "What does 'def' do in Python?", "options": ["Define function", "Defeat enemy", "Default value", "Defer execution"], "a": 0},
            {"q": "Which data type is 'Hello'?", "options": ["Integer", "Boolean", "String", "Float"], "a": 2},
            {"q": "What is the output of: print(10 % 3)?", "options": ["1", "3", "0", "10"], "a": 0},
            {"q": "Which key closes a full screen window?", "options": ["Shift", "Esc", "Ctrl", "Alt"], "a": 1},
            {"q": "What does CSS stand for?", "options": ["Computer Style Sheets", "Creative Style System", "Cascading Style Sheets", "Colorful Sheet Style"], "a": 2},
            {"q": "Which corresponds to 'True' in binary?", "options": ["0", "1", "2", "-1"], "a": 1},
            {"q": "What is the brains of the computer?", "options": ["Monitor", "Keyboard", "CPU", "Mouse"], "a": 2},
            {"q": "Which lists are immutable in Python?", "options": ["List", "Dictionary", "Tuple", "Set"], "a": 2},
            {"q": "How do you start a variable in PHP?", "options": ["$", "@", "#", "%"], "a": 0},
            {"q": "What does HTTP start with?", "options": ["www", "http", "ftp", "com"], "a": 1}, # Trick question? No, simplified.
            {"q": "What is the port for Web (HTTP)?", "options": ["21", "22", "80", "443"], "a": 2},
            {"q": "Which is a float?", "options": ["1", "1.0", "'1'", "One"], "a": 1},
            {"q": "What ends a line in Python?", "options": [";", "Newline", ".", "}"], "a": 1},
        ] * 4 # Duplicate to ensure enough questions
        
        random.shuffle(pool)
        return pool[:50]
        
    def init_race_state(self):
        """Initialize player positions for race (0 to 10)."""
        self.maze_state = {pid: 0 for pid in self.active_players}
        
    def handle_race_answer(self, player_id: str, is_correct: bool) -> Dict:
        """
        Update player position based on answer.
        Correct: +1
        Wrong: -1
        Bounds: 0 to 10.
        """
        if player_id not in self.maze_state:
            return {"moved": False}
            
        current_pos = self.maze_state[player_id]
        
        # Already finished?
        if current_pos >= 10:
            return {"moved": False, "finished": True}
        
        new_pos = current_pos
        if is_correct:
            new_pos += 1
        else:
            new_pos -= 1
            
        # Clamp
        if new_pos < 0: new_pos = 0
        if new_pos > 10: new_pos = 10
        
        self.maze_state[player_id] = new_pos
        self.last_score_update[player_id] = time.time() # Update for tie-breaking
        
        return {
            "moved": True,
            "new_pos": new_pos,
            "finished": (new_pos >= 10),
            "correct": is_correct
        }

    def get_leaderboard(self) -> List[Dict]:
        """Return sorted leaderboard with player info."""
        leaderboard = []
        for pid, player in self.players.items():
            if pid in self.active_players or pid in self.spectators:
                # Score depends on game?
                # Game 1 & 2: use player_scores
                # Game 3: use maze_state (progress)
                score = 0
                if self.current_game == 3 and hasattr(self, 'maze_state'):
                    score = self.maze_state.get(pid, 0)
                else:
                    score = self.player_scores.get(pid, 0)
                    
                leaderboard.append({
                    "id": pid,
                    "username": player.username,
                    "color": player.color,
                    "shape": player.shape.value, # Enum to value
                    "score": score,
                    "last_update": self.last_score_update.get(pid, float('inf'))
                })
        
        # Sort desc by score, then asc by last_update (earlier is better)
        return sorted(leaderboard, key=lambda x: (-x["score"], x["last_update"]))
    
    def advance_players(self) -> tuple[List[str], List[str]]:
        """Calculate top 50% to advance, rest become spectators."""
        leaderboard = self.get_leaderboard()
        total_active = len(self.active_players)
        
        if total_active <= 1:
            # Edge case: only 1 player, they win
            return self.active_players, []
        
        # Calculate how many advance (round up for odd numbers)
        num_advancing = max(1, (total_active + 1) // 2)
        
        advancing = [p['id'] for p in leaderboard[:num_advancing]]
        eliminated = [p['id'] for p in leaderboard[num_advancing:]]
        
        # Update state
        self.active_players = advancing
        self.spectators.extend(eliminated)
        
        return advancing, eliminated


class ConnectionManager:
    """
    Singleton Class.
    Registry for all active connections and lobbies.
    Prevents memory leaks by centralizing connection tracking.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConnectionManager, cls).__new__(cls)
            cls._instance.active_connections: Dict[str, Player] = {}
            cls._instance.lobbies: Dict[str, Lobby] = {}
        return cls._instance

    async def register(self, websocket: WebSocket, username: str) -> Player:
        """Accepts connection and mints a new Player object."""
        await websocket.accept()
        player_id = str(uuid.uuid4())
        player = Player(player_id, username, websocket)
        self.active_connections[player_id] = player
        return player

    def unregister(self, player_id: str) -> None:
        """Cleans up player reference."""
        if player_id in self.active_connections:
            del self.active_connections[player_id]

    def create_lobby(self, host: Player, capacity: int) -> Lobby:
        """Factory method for Lobbies."""
        lobby_id = str(uuid.uuid4())[:6].upper()
        lobby = Lobby(lobby_id, host, capacity)
        self.lobbies[lobby_id] = lobby
        return lobby

    def get_lobby(self, lobby_id: str) -> Lobby | None:
        return self.lobbies.get(lobby_id)
    
    def remove_lobby(self, lobby_id: str) -> None:
        if lobby_id in self.lobbies:
            del self.lobbies[lobby_id]
    
    def get_all_summaries(self) -> List[LobbySummary]:
        return [l.get_summary() for l in self.lobbies.values()]

# Global Singleton Accessor
manager = ConnectionManager()
