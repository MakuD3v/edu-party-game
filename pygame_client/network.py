"""
Async WebSocket Network Layer for EDU-PARTY
Handles connection to backend, sends/receives messages without blocking Pygame.
"""
import asyncio
import websockets
import json
from typing import Callable, Optional
from game_state import game_state


class NetworkClient:
    """Async WebSocket client for multiplayer communication."""
    
    def __init__(self, server_url: str = "ws://localhost:8000"):
        self.server_url = server_url
        self.ws: Optional[websockets.WebSocketClientProtocol] = None
        self.running = False
        
        # Message queues
        self.outgoing_queue = asyncio.Queue()
        self.incoming_queue = asyncio.Queue()
        
        # Callbacks for different message types
        self.message_handlers = {}
    
    def on_message(self, message_type: str, callback: Callable):
        """Register a callback for a specific message type."""
        self.message_handlers[message_type] = callback
    
    async def connect(self, lobby_id: str, token: str):
        """Connect to the WebSocket server."""
        try:
            url = f"{self.server_url}/ws?lobby_id={lobby_id}&token={token}"
            self.ws = await websockets.connect(url)
            self.running = True
            game_state.connected = True
            game_state.lobby_id = lobby_id
            print(f"Connected to lobby {lobby_id}")
            
            # Start send/receive tasks
            asyncio.create_task(self._receive_loop())
            asyncio.create_task(self._send_loop())
            
        except Exception as e:
            print(f"Connection error: {e}")
            game_state.connected = False
    
    async def disconnect(self):
        """Disconnect from server."""
        self.running = False
        if self.ws:
            await self.ws.close()
        game_state.connected = False
    
    async def send(self, message: dict):
        """Queue a message to send."""
        await self.outgoing_queue.put(message)
    
    async def _send_loop(self):
        """Background task to send queued messages."""
        while self.running and self.ws:
            try:
                message = await asyncio.wait_for(
                    self.outgoing_queue.get(),
                    timeout=0.1
                )
                await self.ws.send(json.dumps(message))
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"Send error: {e}")
                break
    
    async def _receive_loop(self):
        """Background task to receive messages."""
        while self.running and self.ws:
            try:
                data = await self.ws.recv()
                message = json.loads(data)
                await self._handle_message(message)
            except websockets.ConnectionClosed:
                print("Connection closed")
                break
            except Exception as e:
                print(f"Receive error: {e}")
                break
    
    async def _handle_message(self, message: dict):
        """Process incoming message and update game state."""
        msg_type = message.get("type", "")
        
        # Update game state based on message
        if msg_type == "connected":
            game_state.profile.player_id = message.get("player_id", "")
        
        elif msg_type == "player_joined":
            player_data = message.get("player", {})
            game_state.add_or_update_player(player_data)
        
        elif msg_type == "player_left":
            player_id = message.get("player_id", "")
            game_state.remove_player(player_id)
        
        elif msg_type == "players_list":
            players = message.get("players", [])
            for player_data in players:
                game_state.add_or_update_player(player_data)
        
        elif msg_type == "profile_update":
            player_data = message.get("player", {})
            game_state.add_or_update_player(player_data)
        
        elif msg_type == "ready_update":
            player_id = message.get("player_id", "")
            ready = message.get("ready", False)
            if player_id in game_state.remote_players:
                game_state.remote_players[player_id].ready_status = ready
        
        elif msg_type == "game_start":
            game_state.lobby_status = "in_progress"
            game_state.current_scene = "game"
        
        elif msg_type == "player_update":
            player_data = message.get("player", {})
            game_state.add_or_update_player(player_data)
        
        # Call registered handler if exists
        if msg_type in self.message_handlers:
            self.message_handlers[msg_type](message)
        
        # Also queue for scene-specific processing
        await self.incoming_queue.put(message)
    
    # Convenience methods for common actions
    async def update_profile(self, **kwargs):
        """Send profile update (color, gear, username)."""
        message = {"type": "profile_update"}
        message.update(kwargs)
        await self.send(message)
    
    async def toggle_ready(self, ready: bool):
        """Toggle ready status."""
        await self.send({
            "type": "ready_toggle",
            "ready": ready
        })
    
    async def start_game(self):
        """Start the game (host only)."""
        await self.send({
            "type": "start_game"
        })
    
    async def send_game_action(self, action: dict):
        """Send a game action (movement, answer selection, etc.)."""
        await self.send({
            "type": "game_action",
            "action": action
        })


# Global singleton
network = NetworkClient()
