"""
models.py
Data Transfer Objects (DTOs) for the Educational Mayhem system.
Uses Pydantic V2 and Python 3.13 typing features.
"""
from pydantic import BaseModel, ConfigDict
from enum import Enum

# --- Enums for strict type safety ---

class ShapeEnum(str, Enum):
    CIRCLE = "circle"
    SQUARE = "square"
    TRIANGLE = "triangle"

# --- Shared Models ---

class PlayerState(BaseModel):
    """Encapsulates the visible state of a player."""
    id: str
    username: str
    color: str
    shape: ShapeEnum
    is_ready: bool = False
    is_host: bool = False
    
    # Pydantic V2 Config
    model_config = ConfigDict(from_attributes=True)

class LobbySummary(BaseModel):
    """Lightweight lobby info for the list view."""
    id: str
    host_name: str
    player_count: int
    max_players: int
    is_full: bool

# --- WebSocket / API Payloads ---

class AuthResponse(BaseModel):
    token: str
    username: str
    state: PlayerState

class CreateLobbyRequest(BaseModel):
    capacity: int

class ProfileUpdateRequest(BaseModel):
    color: str
    shape: ShapeEnum

class RegisterRequest(BaseModel):
    username: str
    password: str
    color: str
    shape: ShapeEnum
