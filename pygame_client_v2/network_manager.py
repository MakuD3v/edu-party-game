"""
NetworkManager Class - Handles WebSocket communication lifecycle.
Manages connection, listening, sending, and disconnection asynchronously.
"""
import asyncio
import json
from typing import Any
import websockets
from websockets.client import WebSocketClientProtocol


class NetworkManager:
    """Dedicated WebSocket handler for multiplayer communication."""
    
    def __init__(self, server_url: str):
        """Initialize network manager.
        
        Args:
            server_url: WebSocket server URL (e.g., "ws://localhost:8000")
        """
        self._server_url: str = server_url
        self._ws: WebSocketClientProtocol | None = None
        self._send_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._recv_queue: asyncio.Queue[dict[str, Any]] = asyncio.Queue()
        self._running: bool = False
        self._listen_task: asyncio.Task[None] | None = None
        self._send_task: asyncio.Task[None] | None = None
    
    @property
    def connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self._ws is not None and not self._ws.closed
    
    async def connect(self, lobby_id: str, token: str) -> bool:
        """Connect to the WebSocket server.
        
        Args:
            lobby_id: Lobby ID to join
            token: Authentication token
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            url = f"{self._server_url}/ws?lobby_id={lobby_id}&token={token}"
            self._ws = await websockets.connect(url)
            self._running = True
            
            # Start background tasks
            self._listen_task = asyncio.create_task(self._listen_loop())
            self._send_task = asyncio.create_task(self._send_loop())
            
            print(f"[NetworkManager] Connected to {url}")
            return True
            
        except Exception as e:
            print(f"[NetworkManager] Connection failed: {e}")
            self._ws = None
            return False
    
    async def disconnect(self) -> None:
        """Clean disconnect from server."""
        self._running = False
        
        # Cancel background tasks
        if self._listen_task:
            self._listen_task.cancel()
            try:
                await self._listen_task
            except asyncio.CancelledError:
                pass
        
        if self._send_task:
            self._send_task.cancel()
            try:
                await self._send_task
            except asyncio.CancelledError:
                pass
        
        # Close WebSocket
        if self._ws:
            await self._ws.close()
            self._ws = None
        
        print("[NetworkManager] Disconnected")
    
    async def send(self, message: dict[str, Any]) -> None:
        """Queue a message for sending.
        
        Args:
            message: Dictionary to send as JSON
        """
        await self._send_queue.put(message)
    
    def get_message(self) -> dict[str, Any] | None:
        """Non-blocking retrieval of received message.
        
        Returns:
            Message dictionary or None if queue is empty
        """
        try:
            return self._recv_queue.get_nowait()
        except asyncio.QueueEmpty:
            return None
    
    async def _listen_loop(self) -> None:
        """Background task to receive messages from server."""
        while self._running and self._ws:
            try:
                raw_data = await self._ws.recv()
                message = json.loads(raw_data)
                await self._recv_queue.put(message)
                
            except websockets.ConnectionClosed:
                print("[NetworkManager] Connection closed by server")
                self._running = False
                break
            except Exception as e:
                print(f"[NetworkManager] Listen error: {e}")
                break
    
    async def _send_loop(self) -> None:
        """Background task to send queued messages to server."""
        while self._running and self._ws:
            try:
                message = await asyncio.wait_for(
                    self._send_queue.get(),
                    timeout=0.1
                )
                await self._ws.send(json.dumps(message))
                
            except asyncio.TimeoutError:
                continue
            except Exception as e:
                print(f"[NetworkManager] Send error: {e}")
                break
    
    # Convenience methods for common actions

    async def get_lobbies(self) -> list[dict[str, Any]]:
        """Fetch active lobbies from the server."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{API_URL}/api/lobby/list") as response:
                    if response.status == 200:
                        data = await response.json()
                        return data.get("lobbies", [])
        except Exception as e:
            print(f"Error fetching lobbies: {e}")
        return []

    async def create_lobby(self, token: str, capacity: int, game_mode: str) -> dict[str, Any] | None:
        """Create a new lobby."""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{API_URL}/api/lobby/create",
                    params={"token": token},
                    json={"capacity": capacity, "game_mode": game_mode}  # Note: Backend might need update to accept these
                ) as response:
                    if response.status == 200:
                        return await response.json()
        except Exception as e:
            print(f"Error creating lobby: {e}")
        return None

    async def update_profile(self, **kwargs: Any) -> None:
        """Send profile update message.
        
        Args:
            **kwargs: Profile fields to update (color, gear, username, etc.)
        """
        if self.connected:
            message = {"type": "profile_update"}
            message.update(kwargs)
            await self.send(message)
    
    async def toggle_ready(self, ready: bool) -> None:
        """Send ready status toggle.
        
        Args:
            ready: Ready status
        """
        await self.send({
            "type": "ready_toggle",
            "ready": ready
        })
    
    async def start_game(self) -> None:
        """Send game start command (host only)."""
        await self.send({
            "type": "start_game"
        })
    
    async def send_game_action(self, action: dict[str, Any]) -> None:
        """Send a game action.
        
        Args:
            action: Action data dictionary
        """
        await self.send({
            "type": "game_action",
            "action": action
        })
    
    def __repr__(self) -> str:
        """String representation for debugging."""
        status = "connected" if self.connected else "disconnected"
        return f"NetworkManager(url={self._server_url}, status={status})"
