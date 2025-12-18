# 🚀 QUICK START: Deploy to Render in 5 Minutes

## What You Have Now

✅ **Complete multiplayer game system** with:
- Backend API (FastAPI + PostgreSQL + WebSockets)
- Mobile-responsive Brawl Stars-themed launcher
- Godot 4 network integration script
- Fall Guys-style multiplayer sync
- Git repository ready to push

## Deploy to Public Cloud (Render.com)

### Step 1: Create GitHub Repository

1. Go to **https://github.com/new**
2. Create a new repository (name it "edu-party-game")
3. **Don't** initialize with README (we already have code)
4. Copy the repository URL

### Step 2: Push Your Code

```powershell
# In PowerShell (already in EDU_PARTY_FINAL directory):
git remote add origin https://github.com/YOUR_USERNAME/edu-party-game.git
git branch -M main
git push -u origin main
```

### Step 3: Deploy to Render

1. Go to **https://render.com** (sign up if needed)
2. Click **"New +"** → **"Blueprint"**
3. **Connect your GitHub repo**: edu-party-game
4. Click **"Apply"**

Render will automatically:
- Create a web service
- Create a PostgreSQL database
- Set up environment variables
- Deploy your app!

### Step 4: Initialize Database

After deployment completes (~3-5 minutes):

1. Go to your service dashboard on Render
2. Click **"Shell"** tab
3. Run this command:
   ```bash
   python init_render_db.py
   ```

This creates the database tables.

### Step 5: Access Your Live App! 🎉

Your app will be at: `https://edu-party-game-XXXX.onrender.com`

Open it in:
- Your desktop browser
- Your mobile phone browser
- Share with friends!

---

## What to Test

1. **Register** a new user on your live app
2. **Create a lobby**
3. **Open the same URL on your phone** and join the lobby
4. Ready to integrate with your Godot game!

---

## Update Godot for Production

In your Godot project's `network_gateway.gd`, change line 20:

```gdscript
# OLD (local):
var server_url: String = "ws://localhost:8000/ws"

# NEW (production - use YOUR actual Render URL):
var server_url: String = "wss://edu-party-game-XXXX.onrender.com/ws"
```

Note: Use `wss://` (secure WebSocket) for production!

---

## Troubleshooting

**"Service failed to start"?**
- Check the Render logs for errors
- Verify DATABASE_URL is set in environment variables

**"Can't connect from mobile"?**
- Make sure you're using the HTTPS URL (not localhost)
- Check that CORS_ORIGINS is set to `*` in Render

**Need to update code?**
```powershell
git add .
git commit -m "Your update message"
git push
```
Render auto-deploys on push!

---

## 💰 Cost

**Render Free Tier:**
- Web Service: FREE (spins down after 15 min inactivity)
- PostgreSQL: FREE (90 days, then $7/month or use Neon.tech)
- Perfect for demos and testing!

---

## Alternative: Quick Local Test

If you want to test locally on Windows first:

```powershell
venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
```

Open: `http://localhost:8000`

But remember: **mobile devices can't access localhost!**

---

**You're ready to deploy! 🚀**
