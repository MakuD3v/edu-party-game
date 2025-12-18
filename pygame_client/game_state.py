"""
Game State Manager for EDU-PARTY
Centralizes all game state including player profile, lobby info, and game data.
"""
from typing import Dict, List, Optional
from dataclasses import dataclass, field


@dataclass
class PlayerProfile:
    """Local player profile."""
    username: str = "Student"
    color: str = "red"  # red, blue, green
    gear: List[str] = field(default_factory=list)  # glasses, cap, backpack
    token: str = ""
    player_id: str = ""


@dataclass
class RemotePlayer:
    """Remote player in the lobby/game."""
    id: str
    username: str
    color: str = "red"
    gear: List[str] = field(default_factory=list)
    ready_status: bool = False
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0})
    state: str = "idle"


class GameState:
    """Global game state singleton."""
    
    def __init__(self):
        # Connection state
        self.connected = False
        self.lobby_id: Optional[str] = None
        
        # Player data
        self.profile = PlayerProfile()
        self.remote_players: Dict[str, RemotePlayer] = {}
        
        # Lobby state
        self.is_host = False
        self.lobby_status = "waiting"  # waiting, in_progress
        
        # Game state (Math Dash)
        self.current_problem: Optional[Dict] = None
        self.player_scores: Dict[str, int] = {}
        self.game_round = 0
        
        # Current scene
        self.current_scene = "login"  # login, lobby, game
    
    def update_profile(self, **kwargs):
        """Update local player profile."""
        for key, value in kwargs.items():
            if hasattr(self.profile, key):
                setattr(self.profile, key, value)
    
    def add_or_update_player(self, player_data: dict):
        """Add or update a remote player."""
        player_id = player_data["id"]
        if player_id in self.remote_players:
            # Update existing
            player = self.remote_players[player_id]
            for key, value in player_data.items():
                if hasattr(player, key):
                    setattr(player, key, value)
        else:
            # Create new
            self.remote_players[player_id] = RemotePlayer(**player_data)
    
    def remove_player(self, player_id: str):
        """Remove a remote player."""
        self.remote_players.pop(player_id, None)
    
    def get_all_players(self) -> List[RemotePlayer]:
        """Get list of all remote players."""
        return list(self.remote_players.values())
    
    def reset_game(self):
        """Reset game state for new game."""
        self.current_problem = None
        self.player_scores.clear()
        self.game_round = 0
        for player in self.remote_players.values():
            player.state = "idle"


# Global singleton
game_state = GameState()
