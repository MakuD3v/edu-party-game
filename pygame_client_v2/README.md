# EDU-PARTY OOP Game Engine - Quick Start

## Running the OOP Edition

### 1. Start Backend Server
```bash
# From EDU_PARTY_FINAL directory
start_server.bat
```

### 2. Launch OOP Client
```bash
cd pygame_client_v2
python main.py
```

OR use the launcher:
```bash
start_client_v2.bat
```

## Controls

### Menu (Login Screen):
- **ENTER**: Login with default credentials
- **R**: Register new account

### Lobby (Homeroom):
- **1/2/3**: Change color (Red/Blue/Green)
- **G**: Cycle through gear items (Graduation Cap, Science Goggles, etc.)
- **SPACE**: Toggle ready status
- **S**: Start game (host only)

### Math Dash Game:
- **1** or **A** or **←**: Move to left platform
- **2**: Move to middle platform
- **3** or **D** or **→**: Move to right platform

## OOP Architecture

### Core Classes

**Student** (`student.py`)
- Encapsulates player state (username, position, color, gear)
- Properties with getters/setters
- Rendering with gear visualization
- Serialization methods

**NetworkManager** (`network_manager.py`)
- WebSocket lifecycle management
- Async message queues (send/receive)
- Connection handling with auto-cleanup

**GameController** (`game_controller.py`)
- Master orchestrator
- State machine: MENU → LOBBY → MATH_MINIGAME
- Event handling per state
- 60 FPS async game loop

**MathDash** (`math_dash.py`)
- Problem generation (+, -, ×)
- AnswerPlatform management
- Collision detection
- Round timing

### Design Principles

✅ **Encapsulation**: Private attributes (`_variable`), public properties
✅ **Single Responsibility**: Each class has one clear purpose
✅ **Python 3.13**: Modern type hints (`list[str]`, `dict[str, Any]`, `| None`)
✅ **Async Integration**: Non-blocking WebSockets + 60 FPS rendering

### Color Scheme

- **Background**: `#2C3E50` (Chalkboard Dark)
- **Text**: `#ECF0F1` (Chalk White)
- **Accent**: `#F1C40F` (School Bus Yellow)

### Gear Database

5 gear items available via cycling (G key):
1. Graduation Cap
2. Science Goggles
3. Backpack
4. Calculator Watch
5. Pencil Case

## Features

- **OOP Design**: Proper encapsulation and state management
- **Type Safety**: Full Python 3.13 type hints (no deprecated imports)
- **Async Multiplayer**: Non-blocking WebSocket communication
- **Visual Feedback**: Character customization with real-time rendering
- **Educational Content**: Auto-generated math problems

## Troubleshooting

**TypeError with typing**:
- Ensure Python 3.9+ is installed
- Modern type hints used throughout (no `typing.List`)

**Connection Issues**:
- Start backend first with `start_server.bat`
- Check port 8000 is available
