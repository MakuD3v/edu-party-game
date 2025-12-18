# EDU PARTY - Fall Guys Style Multiplayer Game

A web-based multiplayer game prototype with Fall Guys-style gameplay mechanics, built with FastAPI backend, PostgreSQL database, and Godot 4 game client.

## 🚀 Quick Deploy to Render (Recommended!)

[![Deploy to Render](https://render.com/images/deploy-to-render-button.svg)](https://render.com/deploy)

**5-Minute Deployment:**

1. **Push this repo to GitHub**
2. **Go to Render.com** → New → Blueprint
3. **Connect your repo** and deploy!
4. **Your app will be live** at `https://your-app-name.onrender.com`

📖 **Detailed deployment guide**: See [DEPLOY.md](DEPLOY.md)

---

## 🎮 Features

- **Mobile-First Design**: Optimized for both mobile and desktop play
- **Brawl Stars Aesthetic**: Bold, cartoony UI with vibrant colors
- **Real-Time Multiplayer**: WebSocket-based synchronization supporting up to 50 players per lobby
- **Cross-Platform**: Play on mobile browsers and desktop
- **OOP Lobby System**: Clean, modular lobby management

## 🏗️ Tech Stack

**Backend:**
- Python 3.10+ with FastAPI
- PostgreSQL with SQLAlchemy (async)
- WebSockets for real-time communication
- JWT authentication

**Frontend:**
- HTML5/CSS3/JavaScript
- Mobile-responsive design
- Google Fonts (Luckiest Guy)

**Game Client:**
- Godot 4.x (Web Export)
- GDScript networking

## 📋 Prerequisites

- Python 3.10+
- PostgreSQL 12+
- Godot 4.x (for game development)
- Modern web browser

## 🚀 Quick Start

### 1. Database Setup

```bash
# Create PostgreSQL database
createdb eduparty

# Or using psql
psql -U postgres
CREATE DATABASE eduparty;
```

### 2. Backend Setup

```bash
# Navigate to project root
cd EDU_PARTY_FINAL

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Windows:
venv\Scripts\activate
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r backend/requirements.txt
```

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
DATABASE_URL=postgresql+asyncpg://username:password@localhost:5432/eduparty
SECRET_KEY=your-secret-key-here-change-in-production
```

### 4. Run the Server

```bash
# From project root
python -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### 5. Access the Launcher

Open your browser to:
```
http://localhost:8000
```

## 🎯 Godot Integration

### Setup Your Godot Project

1. Copy `godot/network_gateway.gd` to your Godot project
2. Attach it to an AutoLoad singleton:
   - Project → Project Settings → AutoLoad
   - Add `network_gateway.gd` with name `Network`

### Configure Web Export

1. Export your Godot project as HTML5
2. Place the exported files in `frontend/game/`
3. Update `app.js` with the correct game URL:
   ```javascript
   const GODOT_GAME_URL = `${API_BASE}/static/game/index.html`;
   ```

### Using the Network Gateway in Your Game

```gdscript
extends Node3D

var player_position: Vector3

func _ready():
	# Connect signals
	Network.connected_to_server.connect(_on_connected)
	Network.player_updated.connect(_on_player_updated)
	Network.players_list_received.connect(_on_players_list)

func _physics_process(delta):
	# Update local player state
	Network.update_player_position(player_position)
	Network.update_player_velocity(velocity)
	Network.update_player_state("running")

func _on_connected(player_id, lobby_id):
	print("Connected! My ID: ", player_id)

func _on_player_updated(player_data):
	# Sync other players
	var pos = player_data.position
	update_remote_player(player_data.id, Vector3(pos.x, pos.y, pos.z))
```

## 🔌 API Endpoints

### Authentication
- `POST /api/register` - Register new user
- `POST /api/login` - Login and get token
- `GET /api/profile?token=XXX` - Get user profile

### Lobby Management
- `POST /api/lobby/create?token=XXX` - Create new lobby
- `GET /api/lobby/list` - List all active lobbies

### WebSocket
- `WS /ws?lobby_id=XXX&token=YYY` - Game connection

## 📱 Mobile Optimization

The launcher is optimized for mobile devices:
- Touch-friendly buttons (min 44px)
- Responsive flexbox layouts
- Media queries for tablet/desktop
- No hover effects on touch devices
- Prevents zoom on input focus

## 🎨 Brawl Stars Aesthetic

The UI features:
- Heavy black borders (5px)
- Bright yellow/orange gradient buttons
- Slanted shapes using CSS transforms
- "Luckiest Guy" font
- Cartoony, high-contrast colors

## 🔧 Development

### Project Structure
```
EDU_PARTY_FINAL/
├── backend/
│   ├── __init__.py
│   ├── main.py              # FastAPI server
│   ├── models.py            # SQLAlchemy models
│   ├── database.py          # Database config
│   ├── lobby_manager.py     # Lobby system
│   └── requirements.txt
├── frontend/
│   ├── index.html           # Launcher page
│   ├── style.css            # Brawl Stars styling
│   └── app.js               # Frontend logic
├── godot/
│   └── network_gateway.gd   # Godot WebSocket client
└── README.md
```

### Database Models

**User:**
- id, username, password_hash, created_at

**Profile:**
- id, user_id, wins, losses, total_games, elo_rating

## 🚢 Deployment

### Backend Deployment (Render/Heroku)

1. Set environment variables:
   - `DATABASE_URL`
   - `SECRET_KEY`

2. Deploy using:
   ```bash
   uvicorn backend.main:app --host 0.0.0.0 --port $PORT
   ```

### Frontend Deployment

The frontend is served automatically by FastAPI from the `/static` route.

### Godot Web Export

1. Export your Godot project for Web (HTML5)
2. Upload to `frontend/game/` directory
3. Update `GODOT_GAME_URL` in `app.js`

## 🔒 Security Notes

- Change `SECRET_KEY` in production
- Use HTTPS for production deployment
- Restrict CORS origins in `main.py`
- Use strong passwords
- Never commit `.env` files

## 📝 License

This project is for educational purposes.

## 🙋 Support

For issues or questions, please refer to the implementation plan and code comments.

---

**Built with ❤️ for multiplayer Fall Guys-style chaos!**
