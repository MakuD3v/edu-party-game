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

            // Ready indicator (raised hand emoji)
            if (p.is_ready) {
                const readyDiv = document.createElement('div');
                readyDiv.textContent = '🙋';
                readyDiv.style.fontSize = '1.5rem';
                card.appendChild(readyDiv);
            }

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
        this.connected = false; // Track WebSocket state
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

        this.ws.onopen = () => {
            console.log('WebSocket connected');
            this.connected = true;
        };

        this.ws.onmessage = (event) => {
            const msg = JSON.parse(event.data);
            this.notify(msg);
        };

        this.ws.onclose = () => {
            console.log('WebSocket disconnected');
            this.connected = false;
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
            isRegisterMode: false, // Track auth mode
            isReady: false, // Track player ready state
            gameTimer: 0, // Game countdown timer
            timerInterval: null // Timer interval ID
        };

        // Bind UI Events
        this.bindEvents();

        // Network Listener
        this.net.subscribe(this.handleServerEvent.bind(this));

        // Check for existing session on page load
        this.checkExistingSession();
    }

    checkExistingSession() {
        const sessionData = localStorage.getItem('eduPartySession');
        if (sessionData) {
            try {
                const session = JSON.parse(sessionData);
                // Auto-login with stored session
                this.restoreSession(session);
            } catch (e) {
                localStorage.removeItem('eduPartySession');
            }
        }
    }

    async restoreSession(session) {
        // Restore user state
        this.state.user = session.user;

        // Update UI
        this.ui.updateBadge(session.user.username, session.user.color, session.user.shape);
        this.ui.toggleBadge(true);
        this.ui.showScreen('home');

        // Reconnect WebSocket
        this.net.connect(session.user.username);
        this.refreshLobbyList();
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
        document.getElementById('btn-ready').addEventListener('click', () => {
            this.toggleReadyState();
            this.net.send('TOGGLE_READY');
        });

        document.getElementById('btn-start').addEventListener('click', () => {
            this.net.send('START_GAME');
        });

        document.getElementById('btn-test-mode').addEventListener('click', () => {
            // Force start game in test mode (bypasses checks)
            this.net.send('START_GAME', { test_mode: true });
        });

        document.getElementById('btn-leave').addEventListener('click', () => {
            this.net.send('LEAVE_LOBBY');
        });

        // Game 1 Answer Submission
        document.getElementById('btn-submit-answer').addEventListener('click', () => {
            this.submitAnswer();
        });

        // Allow Enter key to submit answer
        document.getElementById('math-answer').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.submitAnswer();
            }
        });
    }

    handleLoginSuccess(data) {
        this.state.user = {
            username: data.username,
            color: data.state.color,
            shape: data.state.shape
        };

        // Save session to localStorage
        localStorage.setItem('eduPartySession', JSON.stringify({
            user: this.state.user,
            timestamp: Date.now()
        }));

        // State Transition
        this.ui.updateBadge(this.state.user.username, this.state.user.color, this.state.user.shape);
        this.ui.toggleBadge(true);
        this.ui.showScreen('home');

        // Connect Real-time
        this.net.connect(this.state.user.username);

        // Wait for WebSocket to be ready before allowing lobby operations
        const checkConnection = setInterval(() => {
            if (this.net.connected) {
                clearInterval(checkConnection);
                this.refreshLobbyList();
            }
        }, 100); // Check every 100ms

        // Timeout after 5 seconds
        setTimeout(() => {
            clearInterval(checkConnection);
            if (!this.net.connected) {
                console.warn('WebSocket connection timeout');
            }
        }, 5000);
    }

    async refreshLobbyList() {
        const lobbies = await this.net.getLobbies();
        this.ui.renderLobbyList(lobbies, (id) => {
            this.net.send('JOIN_LOBBY', { lobby_id: id });
        });
    }

    toggleReadyState() {
        this.state.isReady = !this.state.isReady;
        this.updateReadyButton();
    }

    updateReadyButton() {
        const readyBtn = document.getElementById('btn-ready');
        if (this.state.isReady) {
            readyBtn.style.background = '#2ECC71'; // Green
            readyBtn.textContent = 'READY ✓';
        } else {
            readyBtn.style.background = '#E74C3C'; // Red
            readyBtn.textContent = 'READY';
        }
    }

    // === GAME METHODS ===

    submitAnswer() {
        const answer = document.getElementById('math-answer').value;
        if (answer) {
            this.net.send('SUBMIT_ANSWER', { answer });
        }
    }

    startGameTimer() {
        const timerEl = document.getElementById('game-timer');

        this.state.timerInterval = setInterval(() => {
            this.state.gameTimer--;
            timerEl.textContent = this.state.gameTimer;

            if (this.state.gameTimer <= 0) {
                clearInterval(this.state.timerInterval);
            }
        }, 1000);
    }

    renderLeaderboard(leaderboard) {
        const container = document.getElementById('game-leaderboard');
        const spectatorContainer = document.getElementById('spectator-leaderboard');

        const html = leaderboard.map((player, index) => `
            <div class="leaderboard-row">
                <span class="rank">#${index + 1}</span>
                <span style="flex:1; text-align:left; padding-left:10px;">${player.username}</span>
                <span style="color:var(--school-bus-yellow); font-weight:bold; font-size:1.2rem;">${player.score}</span>
            </div>
        `).join('');

        container.innerHTML = html;
        if (spectatorContainer) {
            spectatorContainer.innerHTML = html;
        }
    }

    showIntermission(data) {
        // Check if current player was eliminated
        const isEliminated = data.eliminated.some(p => p.username === this.state.user.username);

        if (isEliminated) {
            // Show spectator mode
            this.ui.showScreen('spectator');
        } else {
            // Show intermission screen
            this.ui.showScreen('intermission');

            // Render advancing players
            const advancingHtml = data.advancing.map(p => `
                <div class="player-chip">
                    <span>${p.username}</span>
                    <span class="score">${p.score} pts</span>
                </div>
            `).join('');
            document.getElementById('advancing-list').innerHTML = advancingHtml;

            // Render eliminated players
            const eliminatedHtml = data.eliminated.map(p => `
                <div class="player-chip">
                    <span>${p.username}</span>
                    <span class="score">${p.score} pts</span>
                </div>
            `).join('');
            document.getElementById('eliminated-list').innerHTML = eliminatedHtml;

            // Show next game info or winner
            const nextGameInfo = document.getElementById('next-game-info');
            if (data.next_game) {
                nextGameInfo.innerHTML = '<p>Next round coming soon...</p>';
            } else {
                // Tournament over, show winner
                if (data.advancing.length > 0) {
                    const winner = data.advancing[0];
                    nextGameInfo.innerHTML = `
                        <h2 style="color:var(--school-bus-yellow);">🎉 WINNER: ${winner.username}! 🎉</h2>
                        <button class="btn-primary" onclick="location.reload()">RETURN TO MENU</button>
                    `;
                }
            }
        }
    }

    handleServerEvent(msg) {
        console.log('[Event]', msg);

        switch (msg.type) {
            case 'LOBBY_JOINED':
                // Reset ready state when joining a lobby
                this.state.isReady = false;
                this.updateReadyButton();

                this.ui.showScreen('lobby');
                document.getElementById('lobby-title-id').textContent = '#' + msg.payload.id;
                document.getElementById('lobby-host-name').textContent = 'Host: ' + msg.payload.host_name;

                // Show start button and test mode button if user is host
                const startBtn = document.getElementById('btn-start');
                const testBtn = document.getElementById('btn-test-mode');

                if (msg.payload.host_name === this.state.user.username) {
                    startBtn.style.display = 'inline-block';
                    testBtn.style.display = 'inline-block'; // Show test mode for host
                    // Initialize as disabled/grayed
                    startBtn.disabled = true;
                    startBtn.style.background = '#555';
                    startBtn.style.opacity = '0.5';
                    startBtn.style.cursor = 'not-allowed';
                } else {
                    startBtn.style.display = 'none';
                    testBtn.style.display = 'none';
                }
                break;

            case 'ROSTER_UPDATE':
                this.ui.renderRoster(msg.payload);

                // Update player's own ready state from roster
                const currentPlayer = msg.payload.find(p => p.username === this.state.user.username);
                if (currentPlayer) {
                    this.state.isReady = currentPlayer.is_ready;
                    this.updateReadyButton();
                }

                // Update start button state for host
                const startButton = document.getElementById('btn-start');
                if (startButton.style.display !== 'none') {
                    // Check if all players are ready
                    const allReady = msg.payload.every(p => p.is_ready);
                    const hasPlayers = msg.payload.length > 1;
                    const canStart = allReady && hasPlayers;
                    startButton.disabled = !canStart;

                    // Update visual state
                    if (canStart) {
                        startButton.style.background = '#F39C12'; // Orange - lit up
                        startButton.style.opacity = '1';
                        startButton.style.cursor = 'pointer';
                    } else {
                        startButton.style.background = '#555'; // Gray
                        startButton.style.opacity = '0.5';
                        startButton.style.cursor = 'not-allowed';
                    }
                }
                break;

            case 'LOBBY_LEFT':
                this.ui.showScreen('home');
                this.refreshLobbyList();
                break;

            case 'PROFILE_ACK':
                const p = msg.payload;
                this.state.user.color = p.color;
                this.state.user.shape = p.shape;
                this.ui.updateBadge(p.username, p.color, p.shape);
                break;

            // === GAME EVENTS ===
            case 'GAME_1_START':
                this.ui.showScreen('game1');
                this.state.gameTimer = msg.payload.duration;
                this.startGameTimer();
                // Question will arrive via NEW_QUESTION
                break;

            case 'NEW_QUESTION':
                const question = msg.payload;
                document.getElementById('math-question').textContent = question.text;
                document.getElementById('math-answer').value = '';
                document.getElementById('math-answer').focus();
                document.getElementById('answer-feedback').textContent = '';
                break;

            case 'ANSWER_RESULT':
                const feedback = document.getElementById('answer-feedback');
                if (msg.payload.correct) {
                    feedback.textContent = '✅ Correct!';
                    feedback.style.color = '#2ECC71';
                } else {
                    feedback.textContent = '❌ Wrong';
                    feedback.style.color = '#E74C3C';
                }
                // Clear feedback after 1 second
                setTimeout(() => {
                    feedback.textContent = '';
                }, 1000);
                break;

            case 'SCORE_UPDATE':
                this.renderLeaderboard(msg.payload);
                break;

            case 'ROUND_END':
                clearInterval(this.state.timerInterval);
                this.showIntermission(msg.payload);
                break;

            case 'ERROR':
                alert(msg.msg);
                break;
        }
    }
}

// MAIN ENTRY POINT
const app = new AppController();
