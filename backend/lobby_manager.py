"""
OOP-based Lobby Management System with asyncio support.
Manages concurrent game lobbies with up to 50 players each.
"""
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Optional, List
from dataclasses import dataclass, field
from fastapi import WebSocket


@dataclass
class Player:
    """Represents a connected player."""
    id: str
    username: str
    websocket: WebSocket
    lobby_id: Optional[str] = None
    
    # Fall Guys-style game state
    position: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    velocity: Dict[str, float] = field(default_factory=lambda: {"x": 0, "y": 0, "z": 0})
    rotation: float = 0.0
    state: str = "idle"  # idle, running, jumping, falling, eliminated
    
    def to_dict(self):
        """Convert player to dictionary for broadcasting."""
        return {
            "id": self.id,
            "username": self.username,
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
        self.players: Dict[str, Player] = {}
        self.created_at = datetime.utcnow()
        self.status = "waiting"  # waiting, in_progress, finished
        
    def add_player(self, player: Player) -> bool:
        """Add a player to the lobby. Returns True if successful."""
        if self.is_full():
            return False
        
        self.players[player.id] = player
        player.lobby_id = self.id
        return True
    
    def remove_player(self, player_id: str) -> Optional[Player]:
        """Remove and return a player from the lobby."""
        return self.players.pop(player_id, None)
    
    def get_player(self, player_id: str) -> Optional[Player]:
        """Get a player by ID."""
        return self.players.get(player_id)
    
    def is_full(self) -> bool:
        """Check if lobby is at max capacity."""
        return len(self.players) >= self.MAX_PLAYERS
    
    def is_empty(self) -> bool:
        """Check if lobby has no players."""
        return len(self.players) == 0
    
    async def broadcast_async(self, message: dict, exclude_player_id: Optional[str] = None):
        """
        Broadcast a message to all players in the lobby asynchronously.
        Optionally exclude a specific player (useful for echoing back sender's data).
        """
        tasks = []
        for player_id, player in self.players.items():
            if exclude_player_id and player_id == exclude_player_id:
                continue
            
            # Create async task for each send
            tasks.append(self._send_to_player(player.websocket, message))
        
        # Execute all sends concurrently
        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)
    
    @staticmethod
    async def _send_to_player(websocket: WebSocket, message: dict):
        """Helper to send message to a single player."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            # Log error but don't crash (player might have disconnected)
            print(f"Error sending to player: {e}")
    
    def get_lobby_info(self) -> dict:
        """Get lobby information for display."""
        return {
            "id": self.id,
            "host_id": self.host_id,
            "player_count": len(self.players),
            "max_players": self.MAX_PLAYERS,
            "status": self.status,
            "created_at": self.created_at.isoformat()
        }


class LobbyManager:
    """Global manager for all lobbies."""
    
    def __init__(self):
        self.lobbies: Dict[str, Lobby] = {}
        self.player_to_lobby: Dict[str, str] = {}  # player_id -> lobby_id mapping
    
    def create_lobby(self, host_id: str) -> Lobby:
        """Create a new lobby and return it."""
        lobby_id = str(uuid.uuid4())[:8]  # Short lobby ID
        lobby = Lobby(lobby_id, host_id)
        self.lobbies[lobby_id] = lobby
        return lobby
    
    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        """Get a lobby by ID."""
        return self.lobbies.get(lobby_id)
    
    def join_lobby(self, lobby_id: str, player: Player) -> bool:
        """Join a player to a specific lobby."""
        lobby = self.get_lobby(lobby_id)
        if not lobby:
            return False
        
        if lobby.add_player(player):
            self.player_to_lobby[player.id] = lobby_id
            return True
        return False
    
    def leave_lobby(self, player_id: str) -> Optional[Lobby]:
        """Remove player from their current lobby. Returns the lobby (or None)."""
        lobby_id = self.player_to_lobby.pop(player_id, None)
        if not lobby_id:
            return None
        
        lobby = self.get_lobby(lobby_id)
        if lobby:
            lobby.remove_player(player_id)
            
            # Clean up empty lobbies
            if lobby.is_empty():
                del self.lobbies[lobby_id]
                return None
            
            return lobby
        return None
    
    def get_player_lobby(self, player_id: str) -> Optional[Lobby]:
        """Get the lobby a player is currently in."""
        lobby_id = self.player_to_lobby.get(player_id)
        if lobby_id:
            return self.get_lobby(lobby_id)
        return None
    
    def list_lobbies(self) -> List[dict]:
        """List all active lobbies."""
        return [lobby.get_lobby_info() for lobby in self.lobbies.values()]
    
    async def broadcast_to_lobby(self, lobby_id: str, message: dict, exclude_player_id: Optional[str] = None):
        """Broadcast a message to all players in a specific lobby."""
        lobby = self.get_lobby(lobby_id)
        if lobby:
            await lobby.broadcast_async(message, exclude_player_id)


# Global singleton instance
lobby_manager = LobbyManager()
