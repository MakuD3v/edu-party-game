"""
FastAPI WebSocket server with user authentication and lobby management.
main.py
The Application Entry Point.
Responsible for routing and HTTP/WebSocket separation.
Uses the ConnectionManager Singleton for state application.
"""
import asyncio
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from .models import (
    AuthResponse, CreateLobbyRequest, PlayerState, 
    LobbySummary, ShapeEnum, RegisterRequest
)
from .logic import manager
from .database import get_db, init_db
from .db_models import User

app = FastAPI(title="EDU PARTY: Educational Mayhem")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

import os
app.mount("/static", StaticFiles(directory=os.path.join(os.path.dirname(__file__), "../frontend")), name="static")

from fastapi.responses import FileResponse

@app.get("/")
async def get_index():
    return FileResponse(os.path.join(os.path.dirname(__file__), "../frontend/index.html"))

@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()

# Mock User Database (In-Memory for this lesson)
MOCK_DB = {
    "student": {"password": "123", "color": "#E74C3C", "shape": ShapeEnum.SQUARE},
    "teacher": {"password": "admin", "color": "#F1C40F", "shape": ShapeEnum.TRIANGLE},
    "maku": {"password": "123", "color": "#9B59B6", "shape": ShapeEnum.SQUARE}
}

# --- REST Endpoints (Stateless) ---

@app.post("/api/login", response_model=AuthResponse)
async def login(payload: dict, db: AsyncSession = Depends(get_db)):
    """
    Authenticates user and returns their persistent profile state.
    """
    username = payload.get("username")
    password = payload.get("password")
    
    # Try database first
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    
    if user and user.password == password:
        # Database user
        user_data = {"color": user.color, "shape": ShapeEnum(user.shape)}
    elif username in MOCK_DB:
        # Fallback to MOCK_DB for test users
        user_data = MOCK_DB[username]
        if user_data["password"] != password:
            raise HTTPException(status_code=401, detail="Invalid Credentials")
    else:
        raise HTTPException(status_code=401, detail="Invalid Credentials")
        
    # Construct state to return
    dummy_state = PlayerState(
        id="pending",
        username=username,
        color=user_data["color"],
        shape=user_data["shape"],
        is_ready=False,
        is_host=False
    )
    
    return AuthResponse(token=username, username=username, state=dummy_state)

@app.post("/api/register", response_model=AuthResponse)
async def register(payload: RegisterRequest, db: AsyncSession = Depends(get_db)):
    """
    Registers a new user and returns their profile state.
    """
    username = payload.username
    
    # Check if username already exists in database
    result = await db.execute(select(User).where(User.username == username))
    existing_user = result.scalar_one_or_none()
    
    if existing_user or username in MOCK_DB:
        raise HTTPException(status_code=400, detail="Username already exists")
    
    # Create new user in database
    new_user = User(
        username=username,
        password=payload.password,
        color=payload.color,
        shape=payload.shape.value
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    
    # Return auth response (auto-login after registration)
    dummy_state = PlayerState(
        id="pending",
        username=username,
        color=payload.color,
        shape=payload.shape,
        is_ready=False,
        is_host=False
    )
    
    return AuthResponse(token=username, username=username, state=dummy_state)

# === GAME TIMER FUNCTIONS ===

async def run_game_1(lobby):
    """Run Game 1 (Math Quiz) for 20 seconds."""
    import asyncio
    import time
    
    # Send first question to all active players
    question = lobby.generate_math_question()
    print(f"[GAME1] Generated question: {question}")
    print(f"[GAME1] Active players: {lobby.active_players}")
    
    for player_id in lobby.active_players:
        if player_id in lobby.players:
            player = lobby.players[player_id]
            try:
                await player.websocket.send_json({
                    "type": "NEW_QUESTION",
                    "payload": question
                })
                print(f"[GAME1] Sent question to {player.username}")
            except Exception as e:
                print(f"[GAME1] Failed to send question to {player.username}: {e}")
                pass
    
    # Wait for 20 seconds
    await asyncio.sleep(20)
    
    # Game Over - Calculate results
    leaderboard = lobby.get_leaderboard()
    advancing, eliminated = lobby.advance_players()
    
    # Get player info for results
    advancing_players = []
    eliminated_players = []
    
    for pid in advancing:
        if pid in lobby.players:
            p = lobby.players[pid]
            advancing_players.append({
                'username': p.username,
                'score': lobby.player_scores.get(pid, 0),
                'color': p.color,
                'shape': p.shape.value
            })
    
    for pid in eliminated:
        if pid in lobby.players:
            p = lobby.players[pid]
            eliminated_players.append({
                'username': p.username,
                'score': lobby.player_scores.get(pid, 0),
                'color': p.color,
                'shape': p.shape.value
            })
    
    # Broadcast round end results
    await lobby.broadcast({
        "type": "ROUND_END",
        "payload": {
            "game": 1,
            "advancing": advancing_players,
            "eliminated": eliminated_players,
            "next_game": 2 if len(advancing) > 1 else None
        }
    })

@app.get("/api/lobbies", response_model=List[LobbySummary])
async def list_lobbies():
    """Returns a real-time list of active lobbies."""
    return manager.get_all_summaries()

# --- WebSocket Endpoint (Stateful) ---

@app.websocket("/ws/{username}")
async def websocket_endpoint(websocket: WebSocket, username: str):
    """
    The main game loop.
    All state mutations happen here via event messages.
    """
    # 1. Connection Phase
    player = await manager.register(websocket, username)
    
    # Restore mock profile data
    if username in MOCK_DB:
        player.update_profile(MOCK_DB[username]["color"], MOCK_DB[username]["shape"])

    try:
        # 2. Event Loop
        while True:
            data = await websocket.receive_json()
            event_type = data.get("type")
            
            # --- LOBBY CREATION ---
            if event_type == "CREATE_LOBBY":
                capacity = int(data.get("capacity", 15))
                lobby = manager.create_lobby(player, capacity)
                
                # Notify Client
                await websocket.send_json({
                    "type": "LOBBY_JOINED", 
                    "payload": lobby.get_summary().model_dump()
                })
                # Send Initial Roster (Just Host)
                await websocket.send_json({
                    "type": "ROSTER_UPDATE",
                    "payload": [player.to_state().model_dump()]
                })

            # --- JOIN LOBBY ---
            elif event_type == "JOIN_LOBBY":
                lobby_id = data.get("lobby_id")
                lobby = manager.get_lobby(lobby_id)
                
                if lobby and lobby.add_player(player):
                    # Notify Self
                    await websocket.send_json({
                        "type": "LOBBY_JOINED", 
                        "payload": lobby.get_summary().model_dump()
                    })
                    
                    # Notify Lobby (Broadcast)
                    roster_data = [p.to_state().model_dump() for p in lobby.players.values()]
                    broadcast_msg = {
                        "type": "ROSTER_UPDATE",
                        "payload": roster_data
                    }
                    
                    # Send to everyone including self (easier sync)
                    await lobby.broadcast(broadcast_msg)
                    # Also explicit send to self just in case broadcast excludes or fails
                    await websocket.send_json(broadcast_msg)

                else:
                    await websocket.send_json({"type": "ERROR", "msg": "Lobby Full or Not Found"})

            # --- PROFILE UPDATES ---
            elif event_type == "UPDATE_PROFILE":
                player.update_profile(data.get("color"), data.get("shape"))
                
                # Update DB (Mock)
                if username in MOCK_DB:
                    MOCK_DB[username]["color"] = player.color
                    MOCK_DB[username]["shape"] = player.shape
                
                # Broadcast if in lobby
                if player.lobby_id:
                    lobby = manager.get_lobby(player.lobby_id)
                    if lobby:
                         # Send full roster update to ensure consistency
                        roster_data = [p.to_state().model_dump() for p in lobby.players.values()]
                        await lobby.broadcast({
                            "type": "ROSTER_UPDATE",
                            "payload": roster_data
                        })
                
                # Acknowledge to self (for UI update if not in lobby)
                await websocket.send_json({
                    "type": "PROFILE_ACK",
                    "payload": player.to_state().model_dump()
                })
            
            # --- LEAVE LOBBY ---
            elif event_type == "LEAVE_LOBBY":
                if player.lobby_id:
                    lobby = manager.get_lobby(player.lobby_id)
                    if lobby:
                        if lobby.remove_player(player.id):
                            # Lobby is empty
                            manager.remove_lobby(lobby.id)
                        else:
                            # Notify remaining players
                            roster_data = [p.to_state().model_dump() for p in lobby.players.values()]
                            await lobby.broadcast({
                                "type": "ROSTER_UPDATE",
                                "payload": roster_data
                            })
                
                # Notify client they left
                await websocket.send_json({
                    "type": "LOBBY_LEFT"
                })
            
            # --- TOGGLE READY ---
            elif event_type == "TOGGLE_READY":
                player.is_ready = not player.is_ready
                
                # Broadcast if in lobby
                if player.lobby_id:
                    lobby = manager.get_lobby(player.lobby_id)
                    if lobby:
                        roster_data = [p.to_state().model_dump() for p in lobby.players.values()]
                        await lobby.broadcast({
                            "type": "ROSTER_UPDATE",
                            "payload": roster_data
                        })
            
            # --- START GAME ---
            elif event_type == "START_GAME":
                if not player.is_host or not player.lobby_id:
                    await websocket.send_json({"type": "ERROR", "msg": "Only host can start game"})
                    continue
                
                lobby = manager.get_lobby(player.lobby_id)
                if not lobby:
                    continue
                
                # Check for test mode (bypasses validations)
                test_mode = data.get("test_mode", False)
                
                if not test_mode:
                    # Normal mode: Validate all players are ready
                    all_ready = all(p.is_ready for p in lobby.players.values())
                    if not all_ready:
                        await websocket.send_json({"type": "ERROR", "msg": "Not all players are ready"})
                        continue
                else:
                    # Test mode: Force all players to be ready BEFORE starting tournament
                    print(f"[TEST_MODE] Forcing all players to ready status")
                    for p in lobby.players.values():
                        p.is_ready = True
                
                # Start tournament (after players are set to ready)
                lobby.start_tournament()
                print(f"[GAME1] Tournament started with {len(lobby.active_players)} active players")
                
                # Broadcast game start to all players
                await lobby.broadcast({
                    "type": "GAME_1_START",
                    "payload": {
                        "duration": 20,
                        "active_players": lobby.active_players
                    }
                })
                
                # Start sending questions for 20 seconds
                asyncio.create_task(run_game_1(lobby))
            
            # --- SUBMIT ANSWER ---
            elif event_type == "SUBMIT_ANSWER":
                if not player.lobby_id:
                    continue
                
                lobby = manager.get_lobby(player.lobby_id)
                if not lobby or lobby.current_game != 1:
                    continue
                
                answer = data.get("answer")
                try:
                    answer_int = int(answer)
                except (ValueError, TypeError):
                    await websocket.send_json({"type": "ERROR", "msg": "Invalid answer"})
                    continue
                
                # Check answer and update score
                is_correct = lobby.check_answer(player.id, answer_int)
                
                # Send immediate feedback to player
                await websocket.send_json({
                    "type": "ANSWER_RESULT",
                    "payload": {"correct": is_correct}
                })
                
                # Send new question immediately (continuous flow)
                question = lobby.generate_math_question()
                await websocket.send_json({
                    "type": "NEW_QUESTION",
                    "payload": question
                })
                
                # Broadcast updated leaderboard
                leaderboard = lobby.get_leaderboard()
                await lobby.broadcast({
                    "type": "SCORE_UPDATE",
                    "payload": leaderboard
                })

    except WebSocketDisconnect:
        # 3. Cleanup Phase
        manager.unregister(player.id)
        if player.lobby_id:
            lobby = manager.get_lobby(player.lobby_id)
            if lobby:
                if lobby.remove_player(player.id):
                    # Lobby is empty
                    manager.remove_lobby(lobby.id)
                else:
                    # Notify remaining players
                    roster_data = [p.to_state().model_dump() for p in lobby.players.values()]
                    await lobby.broadcast({
                        "type": "ROSTER_UPDATE",
                        "payload": roster_data
                    })
