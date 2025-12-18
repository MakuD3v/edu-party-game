# Educational Mayhem - Quick Start Guide

## What's New

**Educational Mayhem** is the rebranded evolution of EDU-PARTY with a professional profile system!

### New Features:
- 🎭 **Profile Badge** - Top-right corner shows your character + name
- ✏️ **Character Customizer** - Click badge to edit username, shape, and color
- 🔷 **5 Shapes Available** - Circle, Square, Triangle, Star, Hexagon
- 🎨 **New Theme** - Purple Mayhem background (#663399) with School Bus Yellow (#F1C40F)
- 🔐 **Python 3.13 Compliant** - No deprecated typing imports

---

## Running Educational Mayhem

### 1. Start Backend
```bash
start_server.bat
```

### 2. Launch OOP Client
```bash
start_client_v2.bat
```

---

## Controls

### Menu (Login):
- **ENTER**: Login
- **R**: Register

### Lobby (Homeroom):
- **Click Profile Badge**: Open character customizer
- **1/2/3**: Quick color change (Red/Blue/Green)
- **G**: Cycle gear
- **SPACE**: Toggle ready
- **S**: Start game (host only)

### Profile Customizer:
- **Click Shape Buttons**: Choose your shape
- **Click Color Buttons**: Choose your color
- **Type in Username Field**: Edit name
- **Save Button**: Apply changes
- **Cancel or ESC**: Return to lobby

### Math Dash:
- **1/2/3** or **A/D** or **Arrows**: Move between platforms

---

## Educational Mayhem Features

### Profile System
- **Profile Badge**: Always visible in top-right corner
- **Edit Anytime**: Click badge to customize without leaving lobby
- **Real-time Sync**: Changes broadcast instantly to all players
- **WebSocket Persistence**: Connection maintained during customization

### Shape System
5 distinct character shapes:
1. **Circle** - Classic round shape
2. **Square** - Angular and bold
3. **Triangle** - Sharp and dynamic
4. **Star** - Stand out with 5 points
5. **Hexagon** - Modern geometric look

### Theme Updates
- **Background**: Mayhem Purple (#663399)
- **Primary Accent**: School Bus Yellow (#F1C40F)
- **Text**: Chalk White (#ECF0F1)
- **Title**: "EDUCATIONAL MAYHEM"

---

## Technical Details

### Backend Updates
- `ProfileUpdate` model with `shape` field
- Shape validation: `square|circle|triangle|star|hexagon`
- Strict Python 3.13 typing (`str | None`, `list[str]`)

### Frontend Architecture
- **PROFILE_VIEW** state added to GameController
- **ProfileBadge** component for top-right UI
- **ProfileView** full-screen customizer
- **Student** class with shape-based rendering

---

## File Structure

```
pygame_client_v2/
├── main.py                    # Entry point
├── game_controller.py         # Master class with PROFILE_VIEW ✨
├── student.py                 # Shape rendering support ✨
├── profile_badge.py           # Top-right badge ✨ NEW
├── profile_view.py            # Customizer screen ✨ NEW
├── constants.py               # Updated colors ✨
├── network_manager.py         # WebSocket handler
├── math_dash.py               # Minigame logic
├── ui_widgets.py              # Reusable components
└── requirements.txt
```

---

## Troubleshooting

**Profile badge not clickable?**
- Make sure you're in the lobby state
- Profile badge only appears when logged in

**Shapes not rendering?**
- Check that Python 3.9+ is installed
- Verify `pygame >= 2.5.0`

**Connection issues?**
- Start backend first (`start_server.bat`)
- Check port 8000 is available

---

## API Endpoints

### Profile Update
```http
POST /api/profile/update?token={token}
Content-Type: application/json

{
  "username": "NewName",
  "color": "blue",
  "shape": "star",
  "gear": ["Graduation Cap"]
}
```

**Shape Validation**: Must be one of `square`, `circle`, `triangle`, `star`, `hexagon`

---

## What's Next?

Try customizing your character and see your changes appear instantly in the lobby! The WebSocket connection stays alive, so you can edit your profile without disconnecting from your friends.

Enjoy Educational Mayhem! 🎓✏️🎮
