"""
logic.py
The Core Logic Engine for Educational Mayhem.
Implements specific game rules and state management using strict OOP.
"""
import uuid
import asyncio
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
        
        # Immediately add host
        self.add_player(host)
        host.is_host = True

    @property
    def is_full(self) -> bool:
        return len(self.players) >= self.max_capacity

    def add_player(self, player: Player) -> bool:
        """Attempts to add a player to the lobby. Returns False if full."""
        if self.is_full:
            return False
        
        self.players[player.id] = player
        player.lobby_id = self.id
        return True

    def remove_player(self, player_id: str) -> bool:
        """Removes a player. Returns True if lobby is now empty."""
        if player_id in self.players:
            player = self.players[player_id]
            player.lobby_id = None
            player.is_host = False # Reset host status
            del self.players[player_id]
            
        return len(self.players) == 0

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
