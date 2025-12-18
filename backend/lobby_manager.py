"""
OOP-based Lobby Management System with asyncio support.
Manages concurrent game lobbies with up to 50 players each.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Any
from dataclasses import dataclass, field
from fastapi import WebSocket
from fastapi import WebSocket


@dataclass
class Player:
    """Represents a connected player."""
    id: str
    username: str
    websocket: WebSocket
    lobby_id: str | None = None
    
    # Educational Mayhem: Character customization
    color: str = "red"  # red, blue, green
    shape: str = "circle"  # square, circle, triangle, star, hexagon
    gear: list[str] = field(default_factory=list)  # glasses, cap, backpack
    ready_status: bool = False
    
    # Game state
    position: dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    velocity: dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    rotation: float = 0.0
    state: str = "idle"  # idle, running, jumping, falling, eliminated
    
    def to_dict(self) -> dict[str, Any]:
        """Convert player to dictionary for broadcasting."""
        return {
            "id": self.id,
            "username": self.username,
            "color": self.color,
            "shape": self.shape,
            "gear": self.gear,
            "ready_status": self.ready_status,
            "position": self.position,
            "velocity": self.velocity,
            "rotation": self.rotation,
            "state": self.state
        }


class Lobby:
    """Represents a game lobby with up to 50 players."""
    
    MAX_PLAYERS = 50
    
    def __init__(self, lobby_id: str, host_id: str):
        self.id = lobby_id
        self.host_id = host_id
        self.players: dict[str, Player] = {}
        self.created_at = datetime.utcnow()
        self.status = "waiting"  # waiting, in_progress, finished
        
    def add_player(self, player: Player) -> bool:
        """Add a player to the lobby. Returns True if successful."""
        if self.is_full():
            return False
        
        self.players[player.id] = player
        player.lobby_id = self.id
        return True
    
    def remove_player(self, player_id: str) -> Player | None:
        """Remove and return a player from the lobby."""

    def remove_player(self, player_id: str) -> None:
        """Remove a player from the lobby."""
        if player_id in self.players:
            del self.players[player_id]

    def get_player(self, player_id: str) -> Player | None:
        return self.players.get(player_id)

    async def broadcast(self, message: dict, exclude_id: str | None = None) -> None:
        """Send a formatted JSON message to all connected players."""
        # Using list(values) to avoid runtime errors if dict changes during iteration
        for player in list(self.players.values()):
            if player.id == exclude_id or player.websocket is None:
                continue
            try:
                await player.websocket.send_json(message)
            except Exception as e:
                print(f"Error broadcasting to {player.username}: {e}")
                # Ideally, we might handle disconnection here
                pass

    def to_summary(self) -> dict:
        """Return a lightweight summary for the lobby list."""
        return {
            "id": self.id,
            "host_id": self.host_id,
            "player_count": len(self.players),
            "max_players": self.max_players,
            "status": "In Game" if self.is_game_started else "Waiting"
        }

class LobbyManager:
    """
    Singleton-style manager for handling all active lobbies.
    """
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LobbyManager, cls).__new__(cls)
            cls._instance.lobbies = {} # type: dict[str, Lobby]
            cls._instance.active_connections = {} # type: dict[str, Player] (Global lookup)
        return cls._instance

    def create_lobby(self, host_player: Player, capacity: int) -> Lobby:
        """Create a new lobby and return it."""
        # Generate a short 6-char ID for easier typing
        lobby_id = str(uuid.uuid4())[:6].upper()
        new_lobby = Lobby(lobby_id, host_player.id, capacity)
        self.lobbies[lobby_id] = new_lobby
        return new_lobby

    def get_lobby(self, lobby_id: str) -> Lobby | None:
        return self.lobbies.get(lobby_id)
    
        if lobby:
            lobby.remove_player(player_id)
            
            # Clean up empty lobbies
            if lobby.is_empty():
                del self.lobbies[lobby_id]
                return None
            
            return lobby
        return None
    
    def get_player_lobby(self, player_id: str) -> Lobby | None:
        """Get the lobby a player is currently in."""
        lobby_id = self.player_to_lobby.get(player_id)
        if lobby_id:
            return self.get_lobby(lobby_id)
        return None
    
    def list_lobbies(self) -> list[dict]:
        """List all active lobbies."""
        return [lobby.get_lobby_info() for lobby in self.lobbies.values()]
    
    async def broadcast_to_lobby(self, lobby_id: str, message: dict, exclude_player_id: str | None = None):
        """Broadcast a message to all players in a specific lobby."""
        lobby = self.get_lobby(lobby_id)
        if lobby:
            await lobby.broadcast_async(message, exclude_player_id)


# Global singleton instance
lobby_manager = LobbyManager()
