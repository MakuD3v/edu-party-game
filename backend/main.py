"""
FastAPI WebSocket server with user authentication and lobby management.
Serves static files and provides REST + WebSocket endpoints.
"""
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from passlib.context import CryptContext
from jose import JWTError, jwt
from datetime import datetime, timedelta
from pydantic import BaseModel
from typing import Any
import uuid
import os

from database import get_db, init_db
from models import User, Profile
from lobby_manager import lobby_manager, Player

# Configuration
SECRET_KEY = os.getenv("SECRET_KEY", "your-secret-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24  # 24 hours

# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# FastAPI app
app = FastAPI(title="EDU Party Game Server")

# CORS middleware for cross-platform support
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Pydantic Models
# ============================================================================

class UserRegister(BaseModel):
    username: str
    password: str


class UserLogin(BaseModel):
    username: str
    password: str


class Token(BaseModel):
    access_token: str
    token_type: str
    username: str


class ProfileResponse(BaseModel):
    username: str
    wins: int
    losses: int
    total_games: int
    elo_rating: float


class ProfileUpdate(BaseModel):
    """Profile update model with Python 3.13 strict typing."""
    username: str | None = None
    color: str | None = None
    shape: str | None = None  # square, circle, triangle, star, hexagon
    gear: list[str] | None = None
    
    model_config = {"from_attributes": True}  # Pydantic v2


class LobbyCreate(BaseModel):
    pass  # No fields needed, will use token to identify host


# ============================================================================
# Authentication Utilities
# ============================================================================

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=15)
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> Optional[str]:
    """Decode JWT token and return username."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        return username
    except JWTError:
        return None


# ============================================================================
# REST API Endpoints
# ============================================================================

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    print("Database initialized!")


@app.post("/api/register", response_model=Token)
async def register(user_data: UserRegister, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username exists
    result = await db.execute(select(User).where(User.username == user_data.username))
    existing_user = result.scalar_one_or_none()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already exists"
        )
    
    # Create user
    hashed_password = get_password_hash(user_data.password)
    new_user = User(username=user_data.username, password_hash=hashed_password)
    db.add(new_user)
    await db.flush()  # Get the user ID
    
    # Create profile
    new_profile = Profile(user_id=new_user.id)
    db.add(new_profile)
    await db.commit()
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user_data.username
    }


@app.post("/api/login", response_model=Token)
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    # Find user
    result = await db.execute(select(User).where(User.username == user_data.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password"
        )
    
    # Create access token
    access_token = create_access_token(
        data={"sub": user_data.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "username": user_data.username
    }


@app.get("/api/profile", response_model=ProfileResponse)
async def get_profile(token: str, db: AsyncSession = Depends(get_db)):
    """Get user profile statistics."""
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Get user and profile
    result = await db.execute(
        select(User, Profile)
        .join(Profile)
        .where(User.username == username)
    )
    row = result.one_or_none()
    
    if not row:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    user, profile = row
    return {
        "username": user.username,
        "wins": profile.wins,
        "losses": profile.losses,
        "total_games": profile.total_games,
        "elo_rating": profile.elo_rating
    }


@app.post("/api/profile/update")
async def update_profile(profile_data: ProfileUpdate, token: str, db: AsyncSession = Depends(get_db)):
    """Update user profile (username, color, shape, and character customization)."""
    # Valid shapes for Educational Mayhem
    VALID_SHAPES = ["square", "circle", "triangle", "star", "hexagon"]
    
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Get user
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    
    # Validate shape if provided
    if profile_data.shape and profile_data.shape.lower() not in VALID_SHAPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid shape. Must be one of: {', '.join(VALID_SHAPES)}"
        )
    
    # Update username if provided
    if profile_data.username and profile_data.username != username:
        # Check if new username already exists
        check_result = await db.execute(select(User).where(User.username == profile_data.username))
        existing = check_result.scalar_one_or_none()
        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        user.username = profile_data.username
        await db.commit()
    
    return {
        "message": "Profile updated successfully",
        "username": user.username
    }


@app.post("/api/lobby/create")
async def create_lobby(token: str):
    """Create a new lobby."""
    username = decode_token(token)
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    
    # Create lobby with user as host
    host_id = username
    lobby = lobby_manager.create_lobby(host_id)
    
    return {
        "lobby_id": lobby.id,
        "message": "Lobby created successfully"
    }


@app.get("/api/lobby/list")
async def list_lobbies():
    """List all active lobbies."""
    lobbies = lobby_manager.list_lobbies()
    return {"lobbies": lobbies}


# ============================================================================
# WebSocket Endpoint (Multiplayer Game Connection)
# ============================================================================

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket, lobby_id: str, token: str):
    """
    Main WebSocket endpoint for game connections.
    Expects lobby_id and token as query parameters.
    """
    await websocket.accept()
    
    # Verify token
    username = decode_token(token)
    if not username:
        await websocket.send_json({"type": "error", "message": "Invalid token"})
        await websocket.close()
        return
    
    # Verify lobby exists
    lobby = lobby_manager.get_lobby(lobby_id)
    if not lobby:
        await websocket.send_json({"type": "error", "message": "Lobby not found"})
        await websocket.close()
        return
    
    # Create player object
    player_id = str(uuid.uuid4())
    player = Player(id=player_id, username=username, websocket=websocket)
    
    # Join lobby
    if not lobby_manager.join_lobby(lobby_id, player):
        await websocket.send_json({"type": "error", "message": "Lobby is full"})
        await websocket.close()
        return
    
    # Send success message
    await websocket.send_json({
        "type": "connected",
        "player_id": player_id,
        "lobby_id": lobby_id,
        "message": f"Welcome {username}!"
    })
    
    # Broadcast player joined to others
    await lobby.broadcast_async({
        "type": "player_joined",
        "player": player.to_dict()
    }, exclude_player_id=player_id)
    
    # Send current players list
    current_players = [p.to_dict() for p in lobby.players.values() if p.id != player_id]
    await websocket.send_json({
        "type": "players_list",
        "players": current_players
    })
    
    try:
        # Main message loop
        while True:
            data = await websocket.receive_json()
            message_type = data.get("type", "")
            
            # Handle profile updates (color, gear, username)
            if message_type == "profile_update":
                if "color" in data:
                    player.color = data["color"]
                if "gear" in data:
                    player.gear = data["gear"]
                if "username" in data:
                    player.username = data["username"]
                
                # Broadcast to all players
                await lobby.broadcast_async({
                    "type": "profile_update",
                    "player": player.to_dict()
                })
            
            # Handle ready toggle
            elif message_type == "ready_toggle":
                player.ready_status = data.get("ready", False)
                await lobby.broadcast_async({
                    "type": "ready_update",
                    "player_id": player_id,
                    "ready": player.ready_status
                })
            
            # Handle game start (host only)
            elif message_type == "start_game":
                if player_id == lobby.host_id or player.username == lobby.host_id:
                    lobby.status = "in_progress"
                    await lobby.broadcast_async({
                        "type": "game_start",
                        "game_type": "math_dash"
                    })
            
            # Handle game actions (movement, answers, etc.)
            elif message_type == "game_action":
                action_data = data.get("action", {})
                # Broadcast game action to all players
                await lobby.broadcast_async({
                    "type": "game_action",
                    "player_id": player_id,
                    "action": action_data
                })
            
            # Update player state from received data
            if "position" in data:
                player.position = data["position"]
            if "velocity" in data:
                player.velocity = data["velocity"]
            if "rotation" in data:
                player.rotation = data["rotation"]
            if "state" in data:
                player.state = data["state"]
            
            # Broadcast updated state to all other players (legacy support)
            if message_type == "player_update" or not message_type:
                await lobby.broadcast_async({
                    "type": "player_update",
                    "player": player.to_dict()
                }, exclude_player_id=player_id)
    
    except WebSocketDisconnect:
        # Player disconnected
        lobby_manager.leave_lobby(player_id)
        
        # Notify others
        if lobby:
            await lobby.broadcast_async({
                "type": "player_left",
                "player_id": player_id,
                "username": username
            })
        
        print(f"Player {username} disconnected from lobby {lobby_id}")


# ============================================================================
# Static File Serving (Frontend)
# ============================================================================

# Serve static files from frontend directory
frontend_path = os.path.join(os.path.dirname(__file__), "..", "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")
    
    @app.get("/")
    async def serve_index():
        """Serve the main HTML page."""
        index_path = os.path.join(frontend_path, "index.html")
        return FileResponse(index_path)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
