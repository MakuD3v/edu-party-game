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
                const current = (this.state.typingWords && this.state.typingWords[this.state.currentWordIndex]) || "";
                if (typed.toLowerCase() === current.toLowerCase()) {
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
            // Only handle if in Game 3
            const game3Screen = document.getElementById('screen-game3');
            if (game3Screen && game3Screen.classList.contains('active')) {
                if (e.key === 'ArrowRight') {
                    e.preventDefault();
                    this.net.send('MAZE_MOVE', { direction: 'right' });
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

    initMazeGame(mazeData) {
        this.state.mazeLayout = mazeData.layout;
        this.state.mazePositions = mazeData.players || {};
        this.state.currentCheckpoint = null;
        this.state.checkpointLocked = false;

        // Initialize canvas
        const canvas = document.getElementById('maze-canvas');
        if (!canvas) return;

        // Set actual canvas dimensions
        canvas.width = canvas.offsetWidth;
        canvas.height = canvas.offsetHeight;

        this.renderMaze();
    }

    renderMaze() {
        const canvas = document.getElementById('maze-canvas');
        if (!canvas) return;

        const ctx = canvas.getContext('2d');
        const width = canvas.width;
        const height = canvas.height;

        // Clear canvas
        ctx.clearRect(0, 0, width, height);

        // Draw linear path (horizontal track)
        const mazeLength = this.state.mazeLayout?.length || 20;
        const stepWidth = width / (mazeLength + 1);
        const centerY = height / 2;

        // Draw track background
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, centerY - 40, width, 80);

        // Draw checkpoints
        const checkpoints = this.state.mazeLayout?.checkpoints || { 5: {}, 10: {}, 15: {} };
        Object.keys(checkpoints).forEach(step => {
            const x = stepWidth * (parseInt(step) + 0.5);

            // Draw checkpoint marker
            ctx.fillStyle = '#F39C12';
            ctx.beginPath();
            ctx.arc(x, centerY, 15, 0, Math.PI * 2);
            ctx.fill();

            // Draw checkpoint number
            ctx.fillStyle = '#fff';
            ctx.font = 'bold 14px Arial';
            ctx.textAlign = 'center';
            ctx.fillText('🔒', x, centerY + 5);
        });

        // Draw finish line
        const finishX = stepWidth * (mazeLength + 0.5);
        ctx.fillStyle = '#2ECC71';
        ctx.fillRect(finishX - 3, centerY - 50, 6, 100);
        ctx.font = 'bold 20px Arial';
        ctx.fillStyle = '#2ECC71';
        ctx.textAlign = 'center';
        ctx.fillText('🏁', finishX, centerY - 60);

        // Draw players
        if (this.state.mazePositions) {
            Object.entries(this.state.mazePositions).forEach(([playerId, position]) => {
                const player = this.getPlayerInfo(playerId);
                if (!player) return;

                const x = stepWidth * (position + 0.5);
                const y = centerY;

                // Draw player shape
                ctx.fillStyle = player.color || '#9B59B6';

                if (player.shape === 'circle') {
                    ctx.beginPath();
                    ctx.arc(x, y, 20, 0, Math.PI * 2);
                    ctx.fill();
                } else if (player.shape === 'square') {
                    ctx.fillRect(x - 20, y - 20, 40, 40);
                } else if (player.shape === 'triangle') {
                    ctx.beginPath();
                    ctx.moveTo(x, y - 20);
                    ctx.lineTo(x - 20, y + 20);
                    ctx.lineTo(x + 20, y + 20);
                    ctx.closePath();
                    ctx.fill();
                }

                // Draw player name
                ctx.fillStyle = '#fff';
                ctx.font = 'bold 12px Arial';
                ctx.textAlign = 'center';
                ctx.fillText(player.username, x, y + 40);
            });
        }

        // Draw step numbers
        ctx.fillStyle = '#666';
        ctx.font = '10px Arial';
        for (let i = 0; i <= mazeLength; i += 5) {
            const x = stepWidth * (i + 0.5);
            ctx.fillText(i.toString(), x, centerY + 60);
        }
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
                         You have <strong>60 seconds</strong>. Highest score wins! ⚡`
            },
            3: {
                title: "🧩 MAZE CHALLENGE",
                content: `Navigate the maze and solve code puzzles at checkpoints!<br><br>
                         Use <strong>Arrow Keys</strong> to move.<br><br>
                         <strong>FIRST</strong> player to reach the end wins the TOURNAMENT! 🎉`
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
                this.showTutorial(3);
                break; case 'NEW_QUESTION':
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

            case 'SCORE_UPDATE':
                this.renderLeaderboard(msg.payload);
                break;

            case 'ROUND_END':
                clearInterval(this.state.timerInterval);
                this.showIntermission(msg.payload);
                break;

            // === GAME 3 EVENTS ===

            case 'MAZE_START':
                console.log('MAZE_START received:', msg.payload);
                this.state.currentGame = 3;

                // Ensure game3 screen is visible
                this.ui.showScreen('game3');

                // Wait for DOM to be ready, then initialize
                setTimeout(() => {
                    console.log('Initializing maze game...');
                    this.initMazeGame(msg.payload);
                }, 100);
                break;

            case 'PLAYER_MOVED':
                // Another player moved, update their position
                if (this.state.mazePositions) {
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
                alert(`🏆 TOURNAMENT WINNER: ${msg.payload.winner}! 🏆`);
                setTimeout(() => location.reload(), 3000);
                break;

            case 'ERROR':
                alert(msg.msg);
                break;
        }
    }
}

// MAIN ENTRY POINT
const app = new AppController();
