"""
lobby_system.py
The Core Logic of the Multiplayer System.
Uses Strict Object-Oriented Programming (OOP) principles.
"""
import uuid
from typing import Dict, List, Optional
from fastapi import WebSocket

# Import our Pydantic models for structure
from .models import PlayerData, LobbyData

class Player:
    """
    Encapsulates all data and state for a single connected user.
    """
    def __init__(self, start_id: str, username: str, websocket: WebSocket):
        self.id = start_id
        self.username = username
        self.websocket = websocket
        
        # Profile Data (Default values)
        self.color: str = "#4a148c"  # Default Purple
        self.shape: str = "circle"
        
        # State
        self.is_ready: bool = False
        self.is_host: bool = False
        self.lobby_id: Optional[str] = None

    def to_model(self) -> PlayerData:
        """Converts internal state to a transferable Pydantic model."""
        return PlayerData(
            id=self.id,
            username=self.username,
            color=self.color,
            shape=self.shape,
            is_ready=self.is_ready,
            is_host=self.is_host
        )


class Lobby:
    """
    Represents a game room/session.
    Manages the list of players and enforces rules (e.g., max capacity).
    """
    def __init__(self, lobby_id: str, host: Player, capacity: int):
        self.id = lobby_id
        self.host_id = host.id
        self.capacity = max(5, min(capacity, 50)) # Enforce 5-50 range
        self.players: Dict[str, Player] = {}
        
        # Add the host immediately
        self.add_player(host)

    def add_player(self, player: Player) -> bool:
        """Adds a player if space is available."""
        if len(self.players) >= self.capacity:
            return False
        
        self.players[player.id] = player
        player.lobby_id = self.id
        return True

    def remove_player(self, player_id: str) -> None:
        """Removes a player from the roster."""
        if player_id in self.players:
            player = self.players[player_id]
            player.lobby_id = None
            del self.players[player_id]

    async def broadcast(self, message: dict, exclude_id: Optional[str] = None):
        """Sends a message to all players in this lobby."""
        for pid, player in self.players.items():
            if pid == exclude_id:
                continue
            try:
                await player.websocket.send_json(message)
            except Exception:
                # Handle disconnect logic in ConnectionManager, not here ideally
                pass
    
    def to_model(self) -> LobbyData:
        return LobbyData(
            id=self.id,
            host_id=self.host_id,
            capacity=self.capacity,
            players=[p.to_model() for p in self.players.values()]
        )


class ConnectionManager:
    """
    Singleton Class to manage all active WebSocket connections and Lobbies.
    """
    def __init__(self):
        self.active_connections: Dict[str, Player] = {}
        self.lobbies: Dict[str, Lobby] = {}

    async def connect(self, websocket: WebSocket, player_id: str, username: str) -> Player:
        """Register a new connection."""
        await websocket.accept()
        player = Player(player_id, username, websocket)
        self.active_connections[player_id] = player
        return player

    def disconnect(self, player_id: str):
        """Clean up connection."""
        if player_id in self.active_connections:
            del self.active_connections[player_id]
        # Note: Handling remove from lobby happens in the main loop or here
        
    def create_lobby(self, host: Player, capacity: int) -> Lobby:
        """Creates a new lobby and registers it."""
        lobby_id = str(uuid.uuid4())[:6].upper()
        lobby = Lobby(lobby_id, host, capacity)
        self.lobbies[lobby_id] = lobby
        host.is_host = True
        return lobby

    def get_lobby(self, lobby_id: str) -> Optional[Lobby]:
        return self.lobbies.get(lobby_id)
    
    def get_all_lobbies_summary(self) -> list:
        # Returning a simplified list/dict for the frontend browser
        return [
            {
                "id": l.id, 
                "host": l.players[l.host_id].username if l.host_id in l.players else "Unknown",
                "count": len(l.players), 
                "capacity": l.capacity
            }
            for l in self.lobbies.values()
        ]

# Instantiate the Singleton
manager = ConnectionManager()
