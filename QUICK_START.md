# EDU-PARTY Quick Start Guide

## Running the Complete System

### 1. Start the Backend Server

```bash
# From EDU_PARTY_FINAL directory
start_server.bat
```

The backend will start on `http://localhost:8000`

### 2. Launch the Pygame Client

**Terminal 1 (Player 1):**
```bash
start_client.bat
```

**Terminal 2 (Player 2 - Optional):**
```bash
start_client.bat
```

### 3. Play the Game

1. **Login Screen:**
   - Enter username and password
   - Click "Login" or "Register"
   - Server auto-creates a lobby

2. **The Homeroom (Lobby):**
   - Click your username to edit it
   - Choose character color (Red/Blue/Green)
   - Toggle school gear (Glasses, Grad Cap, Backpack)
   - Click "Raise Hand" when ready
   - Host clicks "Start Class!" to begin

3. **Math Dash Game:**
   - Read the math problem at the top
   - Use **A/D** or **Arrow Keys** or **1/2/3** to move between platforms
   - Stand on the correct answer platform before time runs out!
   - Get +10 points for correct answers
   - Multiple rounds automatically cycle

## Controls

### Lobby:
- **Click** on username to edit
- **Click** color/gear buttons to customize
- **Click** "Raise Hand" to toggle ready

### Math Dash:
- **A** or **Left Arrow** or **1**: Move to left platform
- **D** or **Right Arrow** or **3**: Move to right platform
- **2**: Move to middle platform

## Features Implemented

✅ **Profile Customization:**
- Editable username (syncs to all players)
- 3 color choices (Red, Blue, Green)
- 3 gear items (Glasses, Cap, Backpack)
- Real-time updates across all clients

✅ **Homeroom Lobby:**
- Student desk display for all players
- Class size counter (up to 15 students)
- Ready status with "Raise Hand" button
- Host can start the game

✅ **Math Dash Minigame:**
- Auto-generated math problems (+, -, ×)
- 3 platform jumping system
- 15-second countdown timer
- Score tracking
- Multiple rounds
- Full multiplayer synchronization

## Technical Details

- **Backend:** FastAPI + WebSockets (Python)
- **Client:** Pygame with asyncio integration
- **Architecture:** Non-blocking 60 FPS render loop
- **Theme:** School Supplies aesthetic (notebook paper, chalkboard, crayon fonts)

## Troubleshooting

**Connection Error:**
- Ensure backend server is running first
- Check that port 8000 is not in use

**Import Errors:**
- Run `pip install -r requirements.txt` in pygame_client directory

**WebSocket Disconnect:**
- Backend may have restarted - restart client

Enjoy the Classroom Mayhem! 🎓✏️📚
