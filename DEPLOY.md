# Deployment Guide - Render.com

## 🚀 Quick Deploy to Render

### Step 1: Set Up Cloud Database (Neon.tech - Free)

1. Go to **https://neon.tech** and sign up (free tier)
2. Create a new project called "EDU Party"
3. Copy your **connection string** (looks like):
   ```
   postgresql://user:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```
4. **IMPORTANT**: Convert it to async format by changing `postgresql://` to `postgresql+asyncpg://`:
   ```
   postgresql+asyncpg://user:password@ep-xxxxx.us-east-2.aws.neon.tech/neondb?sslmode=require
   ```

### Step 2: Deploy to Render

1. **Push code to GitHub**:
   ```bash
   git init
   git add .
   git commit -m "Initial commit - EDU Party multiplayer game"
   git remote add origin YOUR_GITHUB_REPO_URL
   git push -u origin main
   ```

2. **Go to Render**: https://render.com
3. Click **"New +"** → **"Web Service"**
4. Connect your GitHub repository
5. Configure the service:
   - **Name**: `edu-party-game`
   - **Environment**: `Python 3`
   - **Build Command**: `bash build.sh`
   - **Start Command**: `uvicorn backend.main:app --host 0.0.0.0 --port $PORT`
   - **Instance Type**: Free

6. **Add Environment Variables**:
   - Click "Environment" tab
   - Add these variables:
     ```
     DATABASE_URL = postgresql+asyncpg://YOUR_NEON_CONNECTION_STRING_HERE
     SECRET_KEY = your-random-64-character-secret-key-here
     CORS_ORIGINS = *
     ```

7. Click **"Create Web Service"**

Your app will deploy at: `https://edu-party-game.onrender.com`

### Step 3: Initialize Database

After deployment, run this command in Render's Shell (found in the dashboard):
```bash
python -c "import asyncio; from backend.database import init_db; asyncio.run(init_db())"
```

### Step 4: Update Godot Game URL

In your Godot project, update the WebSocket URL in `network_gateway.gd`:
```gdscript
var server_url: String = "wss://edu-party-game.onrender.com/ws"
```

Note: Use `wss://` (secure WebSocket) for HTTPS deployments.

### Step 5: Test Your Live App!

1. Open `https://edu-party-game.onrender.com` in your browser
2. Register a user
3. Create a lobby
4. Test on your mobile device at the same URL!

---

## 🔧 Alternative: Quick Local Test (Windows)

If you want to test locally first:

**Cancel the running setup.py** (press Ctrl+C in terminal)

Then run:
```powershell
venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open browser to: `http://localhost:8000`

---

## 📱 Mobile Testing on Render

Once deployed, your app is automatically accessible from any mobile device:
- Just open the Render URL on your phone's browser
- The responsive design will adapt automatically
- Touch controls work out of the box!

---

## ⚡ Performance Notes

**Render Free Tier**:
- ✅ Perfect for prototyping and demos
- ✅ HTTPS/WSS enabled automatically
- ⚠️ Spins down after 15 minutes of inactivity
- ⚠️ First request after sleep takes ~30 seconds

**For Production**:
- Upgrade to Render's paid tier ($7/month)
- Or use Railway, Fly.io, or DigitalOcean
