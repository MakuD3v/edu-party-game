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
            lobby: document.getElementById('screen-lobby'),
            game1: document.getElementById('screen-game1'),
            game2: document.getElementById('screen-game2'),
            game3: document.getElementById('screen-game3'),
            intermission: document.getElementById('screen-intermission'),
            spectator: document.getElementById('screen-spectator')
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
            console.log('Connected to server');
            this.reconnectAttempts = 0;
            // Attempt to recover session if we have one
            // (For now clean slate or re-login logic would go here)
        };

        this.ws.onmessage = (event) => {
            try {
                const msg = JSON.parse(event.data);
                this.notify(msg); // Assuming handleMessage is meant to be notify
            } catch (e) {
                console.error('Invalid message:', event.data, e);
            }
        };

        this.ws.onclose = () => {
            console.log('Disconnected from server');
            this.showDisconnectOverlay();
        };

        this.ws.onerror = (error) => {
            console.error('WebSocket error:', error);
        };
    }

    showDisconnectOverlay() {
        const overlay = document.createElement('div');
        overlay.style.position = 'fixed';
        overlay.style.top = '0';
        overlay.style.left = '0';
        overlay.style.width = '100vw';
        overlay.style.height = '100vh';
        overlay.style.background = 'rgba(0,0,0,0.85)';
        overlay.style.zIndex = '9999';
        overlay.style.display = 'flex';
        overlay.style.flexDirection = 'column';
        overlay.style.alignItems = 'center';
        overlay.style.justifyContent = 'center';
        overlay.style.color = 'white';
        overlay.style.fontFamily = 'Arial, sans-serif';

        overlay.innerHTML = `
            <h1 style="color:#E74C3C; font-size:3rem; margin-bottom:20px;">⚠️ Connection Lost</h1>
            <p style="font-size:1.5rem; margin-bottom:30px;">The server has restarted or connection was lost.</p>
            <button onclick="window.location.reload()" style="
                padding: 15px 40px;
                font-size: 1.2rem;
                background: #3498DB;
                color: white;
                border: none;
                border-radius: 5px;
                cursor: pointer;
                box-shadow: 0 4px 0 #2980B9;
            ">REFRESH PAGE</button>
        `;

        document.body.appendChild(overlay);
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
            timerInterval: null, // Timer interval ID
            typingWords: [], // Game 2: List of words to type
            currentWordIndex: 0 // Game 2: Current word index
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

        // Typing Game Input
        const typeInput = document.getElementById('typing-input');
        if (typeInput) {
            typeInput.addEventListener('keydown', (e) => {
                if (e.key === 'Enter' || e.key === ' ') {
                    e.preventDefault();
                    const typed = typeInput.value.trim();
                    if (this.state.typingWords && this.state.typingWords[this.state.currentWordIndex]) {
                        this.net.send('SUBMIT_WORD', {
                            current_word: this.state.typingWords[this.state.currentWordIndex],
                            typed_word: typed
                        });
                    }
                }
            });

            // Also validate on input for instant feedback if they type it correctly without enter
            typeInput.addEventListener('input', (e) => {
                const typed = typeInput.value.trim();

                // Safety checks
                if (!this.state.typingWords || this.state.typingWords.length === 0) {
                    return; // No words loaded yet
                }

                const current = this.state.typingWords[this.state.currentWordIndex];
                if (!current) {
                    return; // No current word
                }

                console.log(`[Game2] Typed: '${typed}' vs Current: '${current}'`);

                // Only submit if typed matches completely AND has same length
                if (typed.length === current.length && typed.toLowerCase() === current.toLowerCase()) {
                    console.log(`[Game2] Match found! Sending SUBMIT_WORD...`);

                    // --- OPTIMISTIC UI ---
                    // 1. Clear Input Immediately
                    typeInput.value = '';

                    // 2. Advance Word Locally
                    this.state.currentWordIndex++;

                    // 3. Update UI (Visual Sync)
                    const wordDisplay = document.querySelector('#word-display');
                    if (wordDisplay && this.state.typingWords[this.state.currentWordIndex]) {
                        wordDisplay.innerText = this.state.typingWords[this.state.currentWordIndex];
                        document.getElementById('next-word-display').innerText =
                            `Next: ${this.state.typingWords[this.state.currentWordIndex + 1] || 'FINISH'}`;
                    } else if (wordDisplay) {
                        wordDisplay.innerText = "Done!";
                    }

                    // --- UPDATE SCORE & WPM LOCALLY ---
                    const scoreEl = document.getElementById('score-display-g2');
                    const wpmEl = document.getElementById('wpm-display');

                    if (scoreEl) {
                        const currentScore = parseInt(scoreEl.innerText) || 0;
                        scoreEl.innerText = currentScore + 10; // Assume +10 per word
                    }

                    // Simple WPM calc (Words / Minutes passed)
                    // We need start time. `this.state.gameStartTime` isn't tracked explicitly here but we can approximate or wait for server.
                    // Better: Just increment score for feedback. Server WPM is authoritative.
                    // Let's just do Score for now to feel responsive.

                    // 4. Send to Backend
                    this.net.send('SUBMIT_WORD', {
                        current_word: current,
                        typed_word: typed
                    });
                }
            });
        }

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

        // Game 3 Maze Controls (Arrow Keys)
        document.addEventListener('keydown', (e) => {
            // Debug log for ANY keydown to check focus
            console.log('[Input] Key:', e.key, 'Game:', this.state.currentGame);

            // Only handle if in Game 3
            if (this.state.currentGame === 3) {
                // Game 3: Maze Controls (Dynamic)
                // path can go up, down, right.
                // We send the KEY direction.
                let direction = null;
                if (e.key === 'ArrowRight' || e.key === 'd') direction = 'right';
                if (e.key === 'ArrowUp' || e.key === 'w') direction = 'up';
                if (e.key === 'ArrowDown' || e.key === 's') direction = 'down';
                // Note: 'down' usually moves Forward-Down in our visual logic.

                if (direction) {
                    e.preventDefault(); // Prevent default scrolling for arrow keys
                    console.log(`[Input] Direction: ${direction}`);
                    this.net.send('MAZE_MOVE', { direction: direction });

                    // Simple prediction/feedback log
                    console.log(`[Game3] Sent Move: ${direction}`);
                }
            }
        });

        // Game 3 Checkpoint Answer Submission
        const checkpointSubmit = document.getElementById('btn-submit-checkpoint');
        if (checkpointSubmit) {
            checkpointSubmit.addEventListener('click', () => {
                this.submitCheckpointAnswer();
            });
        }

        const checkpointInput = document.getElementById('checkpoint-input');
        if (checkpointInput) {
            checkpointInput.addEventListener('keypress', (e) => {
                if (e.key === 'Enter') {
                    this.submitCheckpointAnswer();
                }
            });
        }
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

    // === GAME 3: MAZE CHALLENGE METHODS ===

    initMazeGame(payload) {
        // Init state
        this.state.mazePath = payload.layout.path;
        this.state.mazePositions = payload.players;

        // Reset local current position
        this.state.currentMazePos = 0;
        this.state.totalMazeSteps = (payload.layout && payload.layout.length) ? payload.layout.length : 10;

        // Update UI
        const counter = document.getElementById('maze-position-counter');
        if (counter) {
            counter.innerText = `Step: 0 / ${this.state.totalMazeSteps}`;
        }

        // Render initial frame
        this.renderMaze();

        // Focus for input
        window.focus();
    }

    // === GAME 3: TECH QUIZ RACE METHODS ===

    initRaceGame(payload) {
        // payload = { questions: [...], total_steps: 10, duration: 90 }

        this.state.questions = payload.questions || [];
        this.state.currentQuestionIndex = 0;
        this.state.racePositions = {}; // playerId -> step (0-10)

        // Initialize my position
        this.state.myRaceStep = 0;

        // Render Track (Dots)
        const trackContainer = document.getElementById('track-steps');
        if (trackContainer) {
            trackContainer.innerHTML = '';
            for (let i = 0; i <= 10; i++) {
                const dot = document.createElement('div');
                dot.style.width = '15px';
                dot.style.height = '15px';
                dot.style.borderRadius = '50%';
                dot.style.background = i === 10 ? '#2ECC71' : '#777'; // Finish green
                dot.style.boxShadow = '0 0 5px rgba(0,0,0,0.5)';
                trackContainer.appendChild(dot);
            }
        }

        // Show First Question
        this.showRaceQuestion();

        // Initial Render
        this.renderRaceTrack();
    }

    showRaceQuestion() {
        if (!this.state.questions || this.state.questions.length === 0) return;

        const qData = this.state.questions[this.state.currentQuestionIndex];
        // If we ran out of questions, maybe loop or show "Wait"?
        // Data generation creates 50 questions, should be enough.
        if (!qData) {
            document.getElementById('quiz-question').innerText = "Race in progress...";
            document.getElementById('quiz-options').style.display = 'none';
            return;
        }

        document.getElementById('quiz-question').innerText = qData.q;

        const opts = document.querySelectorAll('.quiz-btn');
        if (opts.length >= 4 && qData.options) {
            opts.forEach((btn, i) => {
                btn.innerText = qData.options[i];
                btn.disabled = false;
                btn.style.background = '#3498DB'; // Reset color
                btn.style.cursor = 'pointer';
            });
        }

        document.getElementById('quiz-options').style.display = 'grid';
    }

    handleRaceOption(selectedIndex) {
        // Prevent double click
        const opts = document.querySelectorAll('.quiz-btn');
        opts.forEach(b => b.disabled = true);

        const qData = this.state.questions[this.state.currentQuestionIndex];
        const isCorrect = (selectedIndex === qData.a);

        // Instant Feedback
        const clickedBtn = opts[selectedIndex];
        clickedBtn.style.background = isCorrect ? '#2ECC71' : '#E74C3C';

        // Send to Backend
        this.net.send('SUBMIT_RACE_ANSWER', { is_correct: isCorrect });

        // Wait then Next Question
        setTimeout(() => {
            this.state.currentQuestionIndex++;
            this.showRaceQuestion();
        }, 1000);
    }

    renderRaceTrack() {
        const container = document.getElementById('track-players');
        if (!container) return;

        container.innerHTML = '';

        // Render all players (active + me)
        // Need list of players from Lobby... `this.state.racePositions`

        // Merge known positions
        const allPos = this.state.racePositions || {};

        // Add me if not in list yet (for local smoothness)
        if (this.state.user && this.state.user.id) {
            if (allPos[this.state.user.id] === undefined) {
                allPos[this.state.user.id] = this.state.myRaceStep;
            }
        }

        Object.keys(allPos).forEach(pid => {
            const step = allPos[pid]; // 0 to 10

            // Calculate % left
            const percent = (step / 10) * 100;

            const avatar = document.createElement('div');
            avatar.style.position = 'absolute';
            avatar.style.left = `${percent}%`;
            avatar.style.top = '50%';
            avatar.style.transform = 'translate(-50%, -50%)';
            avatar.style.transition = 'left 0.5s ease';

            // Style based on user
            // We need Color/Shape info. Might need to lookup from `this.roster` if available?
            // For now, generic or try to extract.

            // Try to find player info
            let color = '#fff';
            let shape = 'circle';
            // Simple mockup style
            avatar.style.width = '30px';
            avatar.style.height = '30px';
            avatar.style.background = this.getPlayerColor(pid) || '#F1C40F';
            avatar.style.borderRadius = '50%';
            avatar.style.border = '2px solid white';
            avatar.style.boxShadow = '0 2px 5px rgba(0,0,0,0.5)';
            avatar.style.zIndex = (pid === this.state.user.id) ? 100 : 1;

            // Add label
            const label = document.createElement('div');
            label.innerText = this.getPlayerName(pid);
            label.style.position = 'absolute';
            label.style.top = '-20px';
            label.style.left = '50%';
            label.style.transform = 'translateX(-50%)';
            label.style.fontSize = '10px';
            label.style.color = 'white';
            label.style.whiteSpace = 'nowrap';

            avatar.appendChild(label);
            container.appendChild(avatar);
        });

        // Update Step Counter
        if (this.state.user) {
            const myStep = allPos[this.state.user.id] || 0;
            const cnt = document.getElementById('race-step-counter');
            if (cnt) cnt.innerText = `Step: ${myStep} / 10`;
        }
    }

    // Helper to get player info from storage/state
    getPlayerName(pid) {
        if (pid === this.state.user.id) return "YOU";
        // Logic to lookup name from roster... 
        // We haven't stored full roster globally well, but let's try.
        return "Player";
    }

    getPlayerColor(pid) {
        if (pid === this.state.user.id) return this.state.user.color;
        return '#3498DB';
    }

    renderMaze() {
        const canvas = document.getElementById('maze-canvas');
        if (!canvas) return;
        const ctx = canvas.getContext('2d');

        // Resize canvas
        canvas.width = canvas.parentElement.clientWidth;
        canvas.height = 400;

        const w = canvas.width;
        const h = canvas.height;

        // Clear
        ctx.fillStyle = '#2C3E50';
        ctx.fillRect(0, 0, w, h);

        // --- 1. Calculate Path Nodes ---
        const startX = 50;
        const startY = h / 2;
        const stepSize = (w - 100) / 10; // 10 steps

        let currentX = startX;
        let currentY = startY;
        const nodes = [{ x: startX, y: startY }]; // Step 0

        if (this.state.mazePath) {
            for (let dir of this.state.mazePath) {
                let nextX = currentX;
                let nextY = currentY;

                if (dir === 'right') {
                    nextX = currentX + stepSize;
                } else if (dir === 'up') {
                    nextX = currentX + stepSize;
                    nextY = currentY - 50;
                } else if (dir === 'down') {
                    nextX = currentX + stepSize;
                    nextY = currentY + 50;
                }

                // Clamp Y
                if (nextY < 50) nextY = 50;
                if (nextY > h - 50) nextY = h - 50;

                nodes.push({ x: nextX, y: nextY });
                currentX = nextX;
                currentY = nextY;
            }
        }

        // --- 2. Draw Track Line ---
        ctx.beginPath();
        if (nodes.length > 0) {
            ctx.moveTo(nodes[0].x, nodes[0].y);
            for (let i = 1; i < nodes.length; i++) {
                ctx.lineTo(nodes[i].x, nodes[i].y);
            }
        }
        ctx.lineWidth = 10;
        ctx.strokeStyle = '#7F8C8D';
        ctx.stroke();

        // --- 3. Draw Nodes & Arrows ---
        nodes.forEach((node, index) => {
            ctx.beginPath();
            ctx.arc(node.x, node.y, 10, 0, Math.PI * 2);
            ctx.fillStyle = '#ECF0F1';
            ctx.fill();

            // Draw Arrow Hint
            if (index < this.state.mazePath?.length) {
                const dir = this.state.mazePath[index];
                ctx.fillStyle = '#F39C12';
                ctx.font = '20px Arial';
                let arrow = '➡';
                if (dir === 'up') arrow = '↗';
                if (dir === 'down') arrow = '↘';

                ctx.fillText(arrow, node.x + 10, node.y - 15);
            }
        });

        // Finish Line
        if (nodes.length > 0) {
            const last = nodes[nodes.length - 1];
            ctx.font = '30px Arial';
            ctx.fillText('🏁', last.x, last.y - 20);
        }

        // --- 4. Draw Players ---
        const players = this.state.mazePositions || {};

        Object.entries(players).forEach(([pid, pos]) => {
            if (pos >= nodes.length) pos = nodes.length - 1;
            const pNode = nodes[pos];

            // Offset slightly
            const offsetX = (Math.random() - 0.5) * 10;
            const offsetY = (Math.random() - 0.5) * 10;

            ctx.beginPath();
            ctx.arc(pNode.x + offsetX, pNode.y + offsetY, 15, 0, Math.PI * 2);

            // Check if it's ME (Use username match if id unavailable)
            let isMe = false;
            if (this.state.user && this.state.user.id === pid) isMe = true;
            // Also check legacy if id map not synced
            // For now default RED

            if (isMe) {
                ctx.fillStyle = '#F1C40F'; // Yellow (Me)
                ctx.shadowBlur = 10;
                ctx.shadowColor = '#F1C40F';
            } else {
                ctx.fillStyle = '#E74C3C'; // Red (Other)
                ctx.shadowBlur = 0;
            }

            ctx.fill();
            ctx.strokeStyle = '#fff';
            ctx.lineWidth = 2;
            ctx.stroke();
            ctx.shadowBlur = 0;
        });

        // Update Counter
        const counter = document.getElementById('maze-position-counter');
        // Find my pos
        if (counter && this.state.user) {
            const myPos = players[this.state.user.id] || 0;
            const total = this.state.totalMazeSteps || 10;
            counter.innerText = `Step: ${myPos} / ${total}`;

            // Check for Checkpoints (Steps 3, 6, 9)
            if ([3, 6, 9].includes(myPos)) {
                this.showCheckpointPuzzle(myPos);
            }
        }
    }

    showCheckpointPuzzle(step) {
        // Simple mock puzzles for now to satisfy requirement
        // In real app, these would come from backend
        const puzzles = {
            3: { q: "Fix syntax: print 'hello'", a: "print('hello')" },
            6: { q: "Fix syntax: if x = 5:", a: "if x == 5:" },
            9: { q: "Fix syntax: for i in range(5)", a: "for i in range(5):" }
        };

        const puzzle = puzzles[step];
        if (!puzzle) return;

        // Check if already solved this step (locally) to avoid spam
        if (this.state.lastSolvedStep === step) return;

        // Verify we haven't shown it recently
        const modalId = 'checkpoint-modal';
        if (document.getElementById(modalId)) return;

        // Create modal
        const modal = document.createElement('div');
        modal.id = modalId;
        modal.style.position = 'fixed';
        modal.style.top = '50%';
        modal.style.left = '50%';
        modal.style.transform = 'translate(-50%, -50%)';
        modal.style.background = '#2C3E50';
        modal.style.padding = '20px';
        modal.style.borderRadius = '10px';
        modal.style.border = '2px solid #F1C40F';
        modal.style.color = 'white';
        modal.style.zIndex = '1000';
        modal.style.textAlign = 'center';

        modal.innerHTML = `
            <h3 style="color:#F1C40F; margin-top:0;">🛑 CHECKPOINT!</h3>
            <p>${puzzle.q}</p>
            <input type="text" id="chk-answer" placeholder="Type correction..." style="padding:10px; border-radius:5px; border:none; width:80%;">
            <button id="chk-submit" style="margin-top:10px; padding:8px 20px; background:#27AE60; border:none; border-radius:5px; color:white; cursor:pointer;">SUBMIT</button>
        `;

        document.body.appendChild(modal);

        const input = document.getElementById('chk-answer');
        const btn = document.getElementById('chk-submit');

        input.focus();

        const submit = () => {
            const val = input.value.trim();
            if (val === puzzle.a) {
                // Correct!
                this.state.lastSolvedStep = step;
                document.body.removeChild(modal);
                // Maybe send a "bonus" score or just allow continue?
                // For now, it just parses as a "blocker" you must solve.
            } else {
                input.style.border = '2px solid red';
                setTimeout(() => input.style.border = 'none', 1000);
            }
        };

        btn.onclick = submit;
        input.onkeydown = (e) => { if (e.key === 'Enter') submit(); };
    }

    getPlayerInfo(playerId) {
        // Helper to get player info from lobby roster
        if (this.state.currentLobbyRoster) {
            return this.state.currentLobbyRoster.find(p => p.id === playerId);
        }
        return null;
    }

    showCheckpoint(checkpointData) {
        if (!checkpointData) return;

        this.state.currentCheckpoint = checkpointData;
        this.state.checkpointLocked = true;

        const popup = document.getElementById('checkpoint-popup');
        const questionEl = document.getElementById('checkpoint-q');
        const inputEl = document.getElementById('checkpoint-input');

        if (popup && questionEl && inputEl) {
            questionEl.textContent = checkpointData.q;
            inputEl.value = '';
            popup.classList.remove('hidden');
            inputEl.focus();
        }
    }

    submitCheckpointAnswer() {
        const inputEl = document.getElementById('checkpoint-input');
        const answer = inputEl.value.trim();

        if (!this.state.currentCheckpoint || !answer) return;

        // Simple client-side validation
        const correctAnswer = this.state.currentCheckpoint.a;
        const isCorrect = answer.toLowerCase() === correctAnswer.toLowerCase();

        if (isCorrect) {
            // Hide popup
            const popup = document.getElementById('checkpoint-popup');
            if (popup) popup.classList.add('hidden');

            // Unlock movement
            this.state.checkpointLocked = false;
            this.state.currentCheckpoint = null;
        } else {
            // Show error feedback
            const questionEl = document.getElementById('checkpoint-q');
            if (questionEl) {
                questionEl.style.color = '#E74C3C';
                setTimeout(() => {
                    questionEl.style.color = '';
                }, 500);
            }
        }
    }

    startGameTimer() {
        // Determine which timer element to use based on current game
        const timerElId = this.state.currentGame === 2 ? 'game2-timer' : 'game-timer';
        const timerEl = document.getElementById(timerElId);

        if (!timerEl) {
            console.error(`Timer element ${timerElId} not found`);
            return;
        }

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
            const advancingHtml = (data.advancing || []).map(p => `
                <div class="player-chip">
                    <span>${p.username}</span>
                    <span class="score">${p.score} pts</span>
                </div>
            `).join('');
            document.getElementById('advancing-list').innerHTML = advancingHtml || '<div class="no-players">None</div>';

            // Render eliminated players
            const eliminatedHtml = (data.eliminated || []).map(p => `
                <div class="player-chip">
                    <span>${p.username}</span>
                    <span class="score">${p.score} pts</span>
                </div>
            `).join('');
            document.getElementById('eliminated-list').innerHTML = eliminatedHtml || '<div class="no-players">None</div>';

            // Show next game info or winner
            if (data.next_game) {
                // Display next game info above countdown
                const nextGameInfo = document.getElementById('next-game-info');
                nextGameInfo.innerHTML = `
                    <div style="font-size:1.3rem; color:#aaa; margin-bottom:10px;">
                        Next Game: <span style="color:var(--school-bus-yellow); font-weight:bold;">${data.next_game.icon} ${data.next_game.name}</span>
                    </div>
                    <div id="next-game-countdown" style="font-size:3rem; color:var(--school-bus-yellow); font-weight:bold; margin:20px 0;">
                        <!-- Countdown appears here -->
                    </div>
                    <div style="color:#aaa;">Get ready...</div>
                `;

                // Start countdown for next game
                const countdownEl = document.getElementById('next-game-countdown');
                let countdown = 5; // 5 second countdown

                if (countdownEl) {
                    countdownEl.textContent = countdown;

                    const countdownInterval = setInterval(() => {
                        countdown--;
                        countdownEl.textContent = countdown;

                        if (countdown <= 0) {
                            clearInterval(countdownInterval);
                            countdownEl.textContent = 'Starting...';
                        }
                    }, 1000);
                }
            } else {
                // Tournament over, show winner
                if (data.advancing.length > 0) {
                    const winner = data.advancing[0];
                    const nextGameInfo = document.getElementById('next-game-info');
                    nextGameInfo.innerHTML = `
                        <h2 style="color:var(--school-bus-yellow);">🎉 WINNER: ${winner.username}! 🎉</h2>
                        <button class="btn-primary" onclick="location.reload()">RETURN TO MENU</button>
                    `;
                }
            }
        }
    }


    // === TUTORIAL & COUNTDOWN METHODS ===

    showTutorial(gameNumber) {
        const tutorials = {
            1: {
                title: "🧮 MATH QUIZ",
                content: `Answer as many math problems as you can in <strong>20 seconds</strong>!<br><br>
                         Type your answer and hit <strong>SUBMIT</strong> or press <strong>ENTER</strong>.<br><br>
                         Top half advance to the next round! 🏆`
            },
            2: {
                title: "⌨️ SPEED TYPING",
                content: `Type the words shown on screen as fast as possible!<br><br>
                         Press <strong>ENTER</strong> after each word.<br><br>
                         You have <strong>20 seconds</strong>. Highest score wins! ⚡`
            },
            3: {
                title: "🚀 TECH SPRINT",
                content: `Race to the finish line by answering tech questions!<br><br>
                         <strong>Correct Answer</strong> = Move forward (+1)<br>
                         <strong>Wrong Answer</strong> = Move backward (-1)<br><br>
                         First to reach the goal wins! 🏆`
            }
        };

        const tutorial = tutorials[gameNumber];
        if (!tutorial) return;

        document.getElementById('tutorial-title').textContent = tutorial.title;
        document.getElementById('tutorial-content').innerHTML = tutorial.content;
        document.getElementById('tutorial-modal').classList.remove('hidden');

        // Auto-dismiss countdown (5 seconds)
        let secondsLeft = 5;
        const countdownEl = document.getElementById('tutorial-countdown');
        countdownEl.textContent = secondsLeft;

        const interval = setInterval(() => {
            secondsLeft--;
            countdownEl.textContent = secondsLeft;

            if (secondsLeft <= 0) {
                clearInterval(interval);
                document.getElementById('tutorial-modal').classList.add('hidden');
                // After tutorial, show countdown then start game
                this.showCountdown().then(() => {
                    // Start the actual game after countdown - use currentGame to determine screen
                    const screenName = `game${this.state.currentGame}`;
                    this.ui.showScreen(screenName);
                    const timerEl = document.getElementById('game-timer');
                    if (timerEl) {
                        timerEl.textContent = this.state.gameTimer;
                    }
                    this.startGameTimer();
                    console.log(`Game ${this.state.currentGame} started after tutorial + countdown`);
                });
            }
        }, 1000);
    }

    async showCountdown() {
        const overlay = document.getElementById('countdown-overlay');
        const numberEl = document.getElementById('countdown-number');

        overlay.classList.remove('hidden');

        for (let i = 3; i > 0; i--) {
            numberEl.textContent = i;
            numberEl.style.animation = 'none';
            // Force reflow to restart animation
            void numberEl.offsetWidth;
            numberEl.style.animation = 'countdownPulse 1s ease-in-out';
            await new Promise(resolve => setTimeout(resolve, 1000));
        }

        overlay.classList.add('hidden');
    }

    showGamePreview(data) {
        const overlay = document.getElementById('game-preview-overlay');
        const icon = document.getElementById('preview-game-icon');
        const name = document.getElementById('preview-game-name');
        const description = document.getElementById('preview-game-description');
        const roundNumber = document.getElementById('preview-round-number');

        // Update content
        const gameInfo = data.game_info;
        icon.textContent = gameInfo.icon;
        name.textContent = gameInfo.name;
        description.textContent = gameInfo.description;
        roundNumber.textContent = data.round_number;

        // Dynamic background based on game color
        const colorMap = {
            '#E74C3C': 'linear-gradient(135deg, rgba(231, 76, 60, 0.95) 0%, rgba(192, 57, 43, 0.95) 100%)', // Red for Math
            '#3498DB': 'linear-gradient(135deg, rgba(52, 152, 219, 0.95) 0%, rgba(41, 128, 185, 0.95) 100%)', // Blue for Typing
            '#F39C12': 'linear-gradient(135deg, rgba(243, 156, 18, 0.95) 0%, rgba(211, 84, 0, 0.95) 100%)' // Orange for Maze
        };
        overlay.style.background = colorMap[gameInfo.color] || colorMap['#3498DB'];

        // Show overlay
        overlay.classList.remove('hidden');

        // Auto-hide after 3 seconds (backend waits 3 seconds)
        setTimeout(() => {
            overlay.classList.add('hidden');
        }, 3000);
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

                // Store roster for Game 3 player rendering
                this.state.currentLobbyRoster = msg.payload;

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

            // EDU PARTY Educational Mayhem game preview
            case 'GAME_PREVIEW':
                console.log('GAME_PREVIEW received:', msg.payload);
                this.showGamePreview(msg.payload);
                break;

            case 'GAME_1_START':
                console.log('GAME_1_START received:', msg.payload);

                // Store game state
                this.state.gameTimer = msg.payload.duration;
                this.state.currentGame = 1;

                // Show tutorial first
                this.showTutorial(1);
                break;


            case 'GAME_2_START':
                console.log('GAME_2_START received:', msg.payload);
                this.state.gameTimer = msg.payload.duration;
                this.state.currentGame = 2;
                this.showTutorial(2);
                break;

            case 'GAME_3_START':
                console.log('GAME_3_START received:', msg.payload);
                this.state.gameTimer = msg.payload.duration;
                this.state.currentGame = 3;

                // Initialize Game Data IMMEDIATELY
                this.initRaceGame(msg.payload);

                // Show Tutorial
                this.showTutorial(3);
                break;
            case 'NEW_QUESTION':
                console.log('Received NEW_QUESTION:', msg.payload);
                const question = msg.payload;
                const questionEl = document.getElementById('math-question');
                const answerEl = document.getElementById('math-answer');
                const feedbackEl = document.getElementById('answer-feedback');

                if (questionEl && question && question.text) {
                    questionEl.textContent = question.text + ' = ?';
                    console.log('Question displayed:', question.text);
                } else {
                    console.error('Failed to display question', { questionEl, question });
                }

                if (answerEl) {
                    answerEl.value = '';
                    answerEl.focus();
                }

                if (feedbackEl) {
                    feedbackEl.textContent = '';
                }
                break;

            case 'ANSWER_RESULT':
                console.log('Received ANSWER_RESULT:', msg.payload);
                const feedback = document.getElementById('answer-feedback');
                if (feedback) {
                    if (msg.payload.correct) {
                        feedback.innerHTML = '<strong style="font-size:1.5rem;">✅ CORRECT!</strong>';
                        feedback.style.color = '#2ECC71';
                    } else {
                        feedback.innerHTML = '<strong style="font-size:1.5rem;">❌ WRONG</strong>';
                        feedback.style.color = '#E74C3C';
                    }
                    // Clear feedback after 2 seconds (longer for visibility)
                    setTimeout(() => {
                        feedback.textContent = '';
                    }, 2000);
                } else {
                    console.error('Feedback element not found');
                }
                break;

            // === GAME 2 EVENTS ===

            case 'NEW_WORDS':
                console.log('Received NEW_WORDS:', msg.payload);
                this.state.typingWords = msg.payload.words || [];
                this.state.currentWordIndex = 0;

                // Display first word
                if (this.state.typingWords.length > 0) {
                    const wordDisplay = document.getElementById('word-display');
                    const nextWordDisplay = document.getElementById('next-word-display');
                    const typingInput = document.getElementById('typing-input');

                    if (wordDisplay) {
                        wordDisplay.textContent = this.state.typingWords[0];
                    }
                    if (nextWordDisplay && this.state.typingWords.length > 1) {
                        nextWordDisplay.textContent = `Next: ${this.state.typingWords[1]}`;
                    }
                    if (typingInput) {
                        typingInput.value = '';
                        typingInput.focus();
                    }
                }
                break;

            case 'WORD_RESULT':
                const wordResult = msg.payload;
                const typingInput = document.getElementById('typing-input');

                if (wordResult.correct) {
                    // Move to next word
                    this.state.currentWordIndex++;

                    if (this.state.currentWordIndex < this.state.typingWords.length) {
                        const wordDisplay = document.getElementById('word-display');
                        const nextWordDisplay = document.getElementById('next-word-display');

                        if (wordDisplay) {
                            wordDisplay.textContent = this.state.typingWords[this.state.currentWordIndex];
                        }
                        if (nextWordDisplay && this.state.currentWordIndex + 1 < this.state.typingWords.length) {
                            nextWordDisplay.textContent = `Next: ${this.state.typingWords[this.state.currentWordIndex + 1]}`;
                        } else if (nextWordDisplay) {
                            nextWordDisplay.textContent = '';
                        }
                    } else {
                        // Finished all words
                        const wordDisplay = document.getElementById('word-display');
                        if (wordDisplay) wordDisplay.textContent = 'FINISHED!';
                    }

                    // Clear input
                    if (typingInput) {
                        typingInput.value = '';
                        typingInput.style.borderColor = '#2ECC71'; // Green flash
                        setTimeout(() => {
                            typingInput.style.borderColor = '';
                        }, 300);
                    }
                } else {
                    // Wrong word - flash red
                    if (typingInput) {
                        typingInput.style.borderColor = '#E74C3C';
                        setTimeout(() => {
                            typingInput.style.borderColor = '';
                        }, 300);
                    }
                }
                break;

            case 'SCORE_UPDATE':
                // Update Leaderboard
                this.ui.updateLeaderboard(msg.payload);

                // Also update local HUD if I am in the list
                if (this.state.user) {
                    const myData = msg.payload.find(p => p.username === this.state.user.username);
                    if (myData) {
                        const scoreEl = document.getElementById('score-display-g2');
                        const wpmEl = document.getElementById('wpm-display');
                        if (scoreEl) scoreEl.innerText = myData.score;
                        // WPM might be in payload? Lobby.get_leaderboard usually just sends score.
                        // Logic.py: check_typed_word updates score.
                        // If we want WPM, backend needs to send it.
                        // For now, Score is key.
                    }
                }
                break;

            case 'ROUND_END':
                clearInterval(this.state.timerInterval);
                this.showIntermission(msg.payload);
                break;

            // === GAME 3 EVENTS ===



            case 'PLAYER_MOVED':
                // Another player moved, update their position
                if (this.state.currentGame === 3) {
                    // Game 3 Update
                    this.state.racePositions = this.state.racePositions || {};
                    this.state.racePositions[msg.payload.player_id] = msg.payload.new_pos;
                    this.renderRaceTrack();
                } else if (this.state.mazePositions) {
                    this.state.mazePositions[msg.payload.player_id] = msg.payload.new_pos;
                    this.renderMaze();
                }
                break;

            case 'MAZE_CHECKPOINT':
                // Show checkpoint puzzle
                this.showCheckpoint(msg.payload);
                break;

            case 'MAZE_STATE':
                // Periodic sync of all player positions
                this.state.mazePositions = msg.payload;
                this.renderMaze();
                break;

            case 'TOURNAMENT_WINNER':
                // Game 3 tournament winner
                clearInterval(this.state.timerInterval);
                const winnerOverlay = document.getElementById('winner-overlay');
                const winnerName = document.getElementById('winner-name');
                if (winnerOverlay && winnerName) {
                    winnerName.textContent = msg.payload.winner;
                    winnerOverlay.classList.remove('hidden');
                    // Add some confetti effect or animation here if desired in future
                } else {
                    alert(`🏆 TOURNAMENT WINNER: ${msg.payload.winner}! 🏆`);
                    setTimeout(() => location.reload(), 3000);
                }
                break;

            case 'ERROR':
                alert(msg.msg);
                break;
        }
    }
}

// MAIN ENTRY POINT
// MAIN ENTRY POINT
window.app = new AppController();
