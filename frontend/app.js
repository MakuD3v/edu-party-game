/**
 * app.js
 * The Frontend Core Logic for Educational Mayhem.
 * Implements AppController (State Machine), NetworkService, and UIManager.
 */

// ========================================================
// 1. UI MANAGER
// Responsible for all DOM manipulations. No logic here.
// ========================================================
class UIManager {
    constructor() {
        this.screens = {
            auth: document.getElementById('screen-auth'),
            home: document.getElementById('screen-home'),
            lobby: document.getElementById('screen-lobby')
        };
        this.badge = document.getElementById('profile-badge');
        this.modal = document.getElementById('modal-profile');
    }

    showScreen(name) {
        Object.values(this.screens).forEach(el => el.classList.remove('active'));
        if (this.screens[name]) this.screens[name].classList.add('active');
    }

    toggleModal(isOpen) {
        if (isOpen) this.modal.classList.remove('hidden');
        else this.modal.classList.add('hidden');
    }

    toggleBadge(isVisible) {
        if (isVisible) this.badge.classList.remove('hidden');
        else this.badge.classList.add('hidden');
    }

    updateBadge(username, color, shape) {
        const nameEl = document.getElementById('badge-username');
        const iconEl = document.getElementById('badge-icon');

        nameEl.textContent = username;
        iconEl.style.backgroundColor = color;

        // Shape Reset
        iconEl.className = 'avatar-icon'; // Reset class
        iconEl.classList.add(`shape-${shape}`);

        // Triangle special case for CSS Hack
        if (shape === 'triangle') {
            iconEl.style.backgroundColor = 'transparent';
            iconEl.style.color = color; // For border-bottom color
        } else {
            iconEl.style.color = 'transparent';
        }
    }

    renderLobbyList(lobbies, joinCallback) {
        const container = document.getElementById('lobby-list');
        container.innerHTML = '';

        if (lobbies.length === 0) {
            container.innerHTML = '<div style="padding:20px; color:#aaa">No classes active. Be the first!</div>';
            return;
        }

        lobbies.forEach(lobby => {
            const row = document.createElement('div');
            row.className = 'lobby-row';

            const info = document.createElement('span');
            info.innerHTML = `<strong>Class #${lobby.id}</strong> (${lobby.host_name}) - ${lobby.player_count}/${lobby.max_players}`;

            const joinBtn = document.createElement('button');
            joinBtn.textContent = 'JOIN';
            joinBtn.style.backgroundColor = 'var(--chalk-green)';
            joinBtn.style.color = 'white';
            joinBtn.style.padding = '5px 15px';
            joinBtn.style.borderRadius = '20px';

            joinBtn.onclick = () => joinCallback(lobby.id);

            row.appendChild(info);
            row.appendChild(joinBtn);
            container.appendChild(row);
        });
    }

    renderRoster(players) {
        const container = document.getElementById('roster-grid');
        container.innerHTML = '';

        players.forEach(p => {
            const card = document.createElement('div');
            card.className = 'roster-card';

            // Icon Logic
            let iconDiv = document.createElement('div');
            iconDiv.className = `avatar-icon shape-${p.shape}`;
            iconDiv.style.margin = '0 auto 10px auto';

            if (p.shape === 'triangle') {
                iconDiv.style.backgroundColor = 'transparent';
                iconDiv.style.color = p.color; // CSS border color
            } else {
                iconDiv.style.backgroundColor = p.color;
            }

            const nameDiv = document.createElement('div');
            nameDiv.textContent = p.username;

            card.appendChild(iconDiv);
            card.appendChild(nameDiv);
            container.appendChild(card);
        });
    }
}

// ========================================================
// 2. NETWORK SERVICE
// Encapsulates WebSocket and Fetch logic. Observer Pattern.
// ========================================================
class NetworkService {
    constructor() {
        this.ws = null;
        this.listeners = []; // Observers
    }

    async login(username, password) {
        const res = await fetch('/api/login', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password })
        });
        if (!res.ok) throw new Error('Auth Failed');
        return await res.json();
    }

    async register(username, password, color, shape) {
        const res = await fetch('/api/register', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ username, password, color, shape })
        });
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Registration Failed');
        }
        return await res.json();
    }

    async getLobbies() {
        const res = await fetch('/api/lobbies');
        return await res.json();
    }

    connect(username) {
        const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
        this.ws = new WebSocket(`${protocol}//${window.location.host}/ws/${username}`);

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.notify(msg);
        };
    }

    send(type, payload = {}) {
        if (this.ws && this.ws.readyState === WebSocket.OPEN) {
            this.ws.send(JSON.stringify({ type, ...payload }));
        }
    }

    subscribe(callback) {
        this.listeners.push(callback);
    }

    notify(msg) {
        this.listeners.forEach(cb => cb(msg));
    }
}

// ========================================================
// 3. APP CONTROLLER
// The "Brain" / State Machine.
// ========================================================
class AppController {
    constructor() {
        this.ui = new UIManager();
        this.net = new NetworkService();
        this.state = {
            user: null, // {username, color, shape}
            connected: false,
            isRegisterMode: false // Track auth mode
        };

        // Bind UI Events
        this.bindEvents();

        // Network Listener
        this.net.subscribe(this.handleServerEvent.bind(this));
    }

    bindEvents() {
        // Auth Mode Toggle
        document.getElementById('toggle-auth-mode').addEventListener('click', (e) => {
            e.preventDefault();
            this.state.isRegisterMode = !this.state.isRegisterMode;

            const registerFields = document.getElementById('register-fields');
            const modeLabel = document.getElementById('auth-mode-label');
            const submitBtn = document.getElementById('auth-submit-btn');
            const toggleLink = document.getElementById('toggle-auth-mode');

            if (this.state.isRegisterMode) {
                registerFields.classList.remove('hidden');
                modeLabel.textContent = 'Create Your Student ID';
                submitBtn.textContent = 'REGISTER';
                toggleLink.textContent = 'Already have an account? Sign in';
            } else {
                registerFields.classList.add('hidden');
                modeLabel.textContent = 'Please Sign In to Class';
                submitBtn.textContent = 'ENTER';
                toggleLink.textContent = 'Need access? Register here';
            }
        });

        // Auth Form Submit
        document.getElementById('auth-form').addEventListener('submit', async (e) => {
            e.preventDefault();
            const u = document.getElementById('auth-username').value;
            const p = document.getElementById('auth-password').value;

            try {
                let data;
                if (this.state.isRegisterMode) {
                    // Registration mode
                    const colorEl = document.querySelector('#register-fields .color-dot.selected');
                    const color = colorEl ? colorEl.getAttribute('data-color') : '#9B59B6';
                    const shape = document.getElementById('auth-shape').value;

                    data = await this.net.register(u, p, color, shape);
                } else {
                    // Login mode
                    data = await this.net.login(u, p);
                }
                this.handleLoginSuccess(data);
            } catch (err) {
                document.getElementById('auth-error').textContent = err.message;
            }
        });

        // Color selection for registration
        document.querySelectorAll('#register-fields .color-dot').forEach(d => {
            d.onclick = () => {
                document.querySelectorAll('#register-fields .color-dot').forEach(x => x.classList.remove('selected'));
                d.classList.add('selected');
            };
        });

        // Dashboard
        document.getElementById('capacity-input').addEventListener('input', (e) => {
            document.getElementById('capacity-val').textContent = e.target.value;
        });

        document.getElementById('btn-create').addEventListener('click', () => {
            const cap = document.getElementById('capacity-input').value;
            this.net.send('CREATE_LOBBY', { capacity: cap });
        });

        document.getElementById('btn-refresh').addEventListener('click', () => {
            this.refreshLobbyList();
        });

        // Profile
        document.getElementById('profile-badge').addEventListener('click', () => this.ui.toggleModal(true));
        document.getElementById('btn-cancel-profile').addEventListener('click', () => this.ui.toggleModal(false));

        document.querySelectorAll('.color-dot').forEach(d => {
            d.onclick = () => {
                document.querySelectorAll('.color-dot').forEach(x => x.classList.remove('selected'));
                d.classList.add('selected');
            };
        });

        document.getElementById('btn-save-profile').addEventListener('click', () => {
            const shape = document.getElementById('profile-shape').value;
            const colorEl = document.querySelector('.color-dot.selected');
            // Pedagogical check
            const color = colorEl ? colorEl.getAttribute('data-color') : '#E74C3C';

            this.net.send('UPDATE_PROFILE', { color, shape });
            this.ui.toggleModal(false);
        });

        // Lobby
        document.getElementById('btn-leave').addEventListener('click', () => {
            // We simplify: Reload page or just visual switch. 
            // For prototype, we reload to clear state cleanly.
            window.location.reload();
        });
    }

    handleLoginSuccess(data) {
        this.state.user = {
            username: data.username,
            color: data.state.color,
            shape: data.state.shape
        };

        // State Transition
        this.ui.updateBadge(this.state.user.username, this.state.user.color, this.state.user.shape);
        this.ui.toggleBadge(true);
        this.ui.showScreen('home');

        // Connect Real-time
        this.net.connect(this.state.user.username);
        this.refreshLobbyList();
    }

    async refreshLobbyList() {
        const lobbies = await this.net.getLobbies();
        this.ui.renderLobbyList(lobbies, (id) => {
            this.net.send('JOIN_LOBBY', { lobby_id: id });
        });
    }

    handleServerEvent(msg) {
        console.log('[Event]', msg);

        switch (msg.type) {
            case 'LOBBY_JOINED':
                this.ui.showScreen('lobby');
                document.getElementById('lobby-title-id').textContent = '#' + msg.payload.id;
                document.getElementById('lobby-host-name').textContent = 'Host: ' + msg.payload.host_name;
                break;

            case 'ROSTER_UPDATE':
                this.ui.renderRoster(msg.payload);
                break;

            case 'PROFILE_ACK':
                const p = msg.payload;
                this.state.user.color = p.color;
                this.state.user.shape = p.shape;
                this.ui.updateBadge(p.username, p.color, p.shape);
                break;

            case 'ERROR':
                alert(msg.msg);
                break;
        }
    }
}

// MAIN ENTRY POINT
const app = new AppController();
