/**
 * EDU PARTY - Client Logic (OOP)
 * Handles UI transitions, Networking, and Game State.
 */

// ============================================================================
// NetworkManager
// Handlles Fetch API calls and WebSocket events
// ============================================================================
class NetworkManager {
    constructor(uiManager) {
        this.ui = uiManager;
        this.ws = null;
        this.token = localStorage.getItem('token');
        this.username = localStorage.getItem('username');
        this.apiBase = window.location.origin + '/api';
    }

    // --- REST API Helpers ---
    async login(username, password) {
        try {
            const res = await fetch(`${this.apiBase}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ username, password })
            });
            if (!res.ok) throw new Error("Login failed");
            const data = await res.json();

            // Save Session
            this.token = data.access_token;
            this.username = data.username;
            localStorage.setItem('token', this.token);
            localStorage.setItem('username', this.username);

            // Connect Real-time
            this.connectWebSocket();
            return data;
        } catch (e) {
            console.error(e);
            alert("Login Failed: " + e.message);
        }
    }

    async createLobby(capacity) {
        const res = await fetch(`${this.apiBase}/lobby/create`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ capacity, token: this.token })
        });
        const data = await res.json();
        return data.lobby_id;
    }

    async getLobbies() {
        const res = await fetch(`${this.apiBase}/lobbies`);
        return await res.json();
    }

    // --- WebSocket ---
    connectWebSocket() {
        if (this.ws) return;

        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws`);

        this.ws.onopen = () => {
            console.log("Connected to Server");
            this.send({ type: 'IDENTIFY', token: this.token });
        };

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.handleMessage(msg);
        };

        this.ws.onclose = () => {
            console.log("Disconnected");
            this.ws = null;
            // Optional: Auto-reconnect logic could go here
        };
    }

    send(data) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify(data));
        }
    }

    handleMessage(msg) {
        console.log("Received:", msg);
        switch (msg.type) {
            case 'WELCOME':
                this.ui.showScreen('home-screen');
                this.ui.updateProfileInfo(msg.username);
                break;
            case 'LOBBY_JOINED':
                this.ui.showScreen('lobby-screen');
                this.ui.renderLobbyInfo(msg.lobby_data);
                break;
            case 'PLAYER_LIST_UPDATE':
                this.ui.updatePlayerList(msg.players);
                break;
            case 'PLAYER_JOINED':
                // Could toast notification here
                // But usually we wait for the full list update or append
                break;
            case 'CHAT_INCOMING':
                this.ui.appendChatMessage(msg.sender, msg.text);
                break;
            case 'ERROR':
                alert(msg.message);
                break;
        }
    }

    joinLobby(lobbyId) {
        this.send({ type: 'JOIN_LOBBY', lobby_id: lobbyId });
    }

    sendChat(text) {
        this.send({ type: 'CHAT_MESSAGE', message: text });
    }

    updateProfile(color, shape) {
        this.send({ type: 'UPDATE_PROFILE', color, shape });
    }
}

// ============================================================================
// UIManager
// Handles Screen Switching and DOM Updates
// ============================================================================
class UIManager {
    constructor() {
        this.screens = document.querySelectorAll('.screen');
        this.modal = document.getElementById('profile-modal');
        this.activeLobbyId = null;
    }

    showScreen(id) {
        this.screens.forEach(s => s.classList.remove('active'));
        const target = document.getElementById(id);
        if (target) target.classList.add('active');
    }

    toggleModal(show) {
        if (show) this.modal.classList.add('active');
        else this.modal.classList.remove('active');
    }

    updateProfileInfo(username) {
        document.getElementById('user-name-display').textContent = username;
    }

    renderLobbyInfo(data) {
        this.activeLobbyId = data.id;
        document.getElementById('lobby-code-display').textContent = data.id;
        document.getElementById('lobby-capacity-display').textContent = data.max_players;
        document.getElementById('chat-messages').innerHTML = ''; // Clear chat
    }

    updatePlayerList(players) {
        const list = document.getElementById('player-list');
        list.innerHTML = '';
        players.forEach(p => {
            const li = document.createElement('li');
            li.className = 'player-item';
            // Simple avatar shape logic
            const shapeIcon = this.getShapeIcon(p.shape);
            li.innerHTML = `
                <span class="avatar-small" style="background-color: var(--color-${p.color})">${shapeIcon}</span>
                <span class="player-name">${p.username} ${p.username === network.username ? '(You)' : ''}</span>
            `;
            list.appendChild(li);
        });
    }

    appendChatMessage(sender, text) {
        const box = document.getElementById('chat-messages');
        const div = document.createElement('div');
        div.className = 'chat-entry';
        div.innerHTML = `<strong>${sender}:</strong> ${text}`;
        box.appendChild(div);
        box.scrollTop = box.scrollHeight;
    }

    getShapeIcon(shape) {
        const map = { 'circle': '●', 'square': '■', 'triangle': '▲', 'star': '★' };
        return map[shape] || '●';
    }
}

// ============================================================================
// Initialization & Events
// ============================================================================
const ui = new UIManager();
const network = new NetworkManager(ui);

// Login Form
document.getElementById('login-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    const user = document.getElementById('username-input').value;
    const pass = document.getElementById('password-input').value;
    await network.login(user, pass);
});

// Profile Button
document.getElementById('profile-btn').addEventListener('click', () => ui.toggleModal(true));
document.getElementById('close-modal-btn').addEventListener('click', () => ui.toggleModal(false));

// Save Profile
document.getElementById('save-profile-btn').addEventListener('click', () => {
    const color = document.querySelector('input[name="color"]:checked').value;
    const shape = document.querySelector('input[name="shape"]:checked').value;
    network.updateProfile(color, shape);
    ui.toggleModal(false);
});

// Create Lobby
document.getElementById('create-lobby-btn').addEventListener('click', async () => {
    const capacity = parseInt(document.getElementById('capacity-range').value);
    const lobbyId = await network.createLobby(capacity);
    if (lobbyId) {
        network.joinLobby(lobbyId);
    }
});

// Refresh Lobby List
document.getElementById('refresh-btn').addEventListener('click', async () => {
    const data = await network.getLobbies();
    const list = document.getElementById('public-lobbies');
    list.innerHTML = '';
    data.lobbies.forEach(lobby => {
        const div = document.createElement('div');
        div.className = 'lobby-card';
        div.innerHTML = `
            <span>Lobby ${lobby.id}</span>
            <span>${lobby.player_count}/${lobby.max_players}</span>
            <button onclick="network.joinLobby('${lobby.id}')">JOIN</button>
        `;
        list.appendChild(div);
    });
});
// Initial load (if we want to auto-refresh)
// network.getLobbies(); // Call manually

// Chat
document.getElementById('chat-input').addEventListener('keypress', (e) => {
    if (e.key === 'Enter') {
        network.sendChat(e.target.value);
        e.target.value = '';
    }
});

// Capacity Slider Update
document.getElementById('capacity-range').addEventListener('input', (e) => {
    document.getElementById('capacity-val').textContent = e.target.value;
});
