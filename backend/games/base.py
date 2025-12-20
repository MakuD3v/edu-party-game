import asyncio
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseGame(ABC):
    """
    Abstract Base Class for all mini-games in Educational Mayhem.
    Enforces a standard interface for the Lobby to interact with.
    """
    def __init__(self, lobby):
        self.lobby = lobby
        self.is_active = False
        # Optional: metadata for UI
        self.game_id = 0 

    @abstractmethod
    async def run(self):
        """
        The main async entry point for the game.
        Should handle:
        - Initialization
        - Broadcasting Start Event
        - The Main Game Loop (timers, etc.)
        - Cleanup / End Event
        """
        pass

    @abstractmethod
    async def handle_input(self, player_id: str, data: Dict[str, Any]):
        """
        Handle incoming WebSocket messages from players.
        """
        pass
