/**
 * EDU PARTY - Frontend JavaScript
 * Handles authentication, lobby management, and game launching
 */

// API Configuration
const API_BASE = window.location.origin;
const GODOT_GAME_URL = `${API_BASE}/game/index.html`; // Update with actual Godot web export path

// State Management
let currentToken = localStorage.getItem('token') || null;
let currentUsername = localStorage.getItem('username') || null;
let currentLobbyId = null;

// DOM Elements
const loginScreen = document.getElementById('loginScreen');
const registerScreen = document.getElementById('registerScreen');
const lobbyScreen = document.getElementById('lobbyScreen');
const gameLaunchScreen = document.getElementById('gameLaunchScreen');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');

// ============================================================================
// Screen Management
// ============================================================================

function showScreen(screenElement) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screenElement.classList.add('active');
}

function showLoading() {
    loadingOverlay.classList.add('active');
}

function hideLoading() {
    loadingOverlay.classList.remove('active');
}

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('active');
    setTimeout(() => {
        errorMessage.classList.remove('active');
    }, 3000);
}

// ============================================================================
// API Calls
// ============================================================================

async function apiCall(endpoint, method = 'GET', body = null) {
    const options = {
        method,
        headers: {
            'Content-Type': 'application/json'
        }
    };
    
    if (body) {
        options.body = JSON.stringify(body);
    }
    
    const response = await fetch(`${API_BASE}${endpoint}`, options);
    
    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Request failed');
    }
    
    return await response.json();
}

// ============================================================================
// Authentication
// ============================================================================

async function register(username, password) {
    showLoading();
    try {
        const data = await apiCall('/api/register', 'POST', { username, password });
        currentToken = data.access_token;
        currentUsername = data.username;
        localStorage.setItem('token', currentToken);
        localStorage.setItem('username', currentUsername);
        
        await loadProfile();
        showScreen(lobbyScreen);
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function login(username, password) {
    showLoading();
    try {
        const data = await apiCall('/api/login', 'POST', { username, password });
        currentToken = data.access_token;
        currentUsername = data.username;
        localStorage.setItem('token', currentToken);
        localStorage.setItem('username', currentUsername);
        
        await loadProfile();
        showScreen(lobbyScreen);
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

function logout() {
    currentToken = null;
    currentUsername = null;
    localStorage.removeItem('token');
    localStorage.removeItem('username');
    showScreen(loginScreen);
}

// ============================================================================
// Profile & Stats
// ============================================================================

async function loadProfile() {
    try {
        const data = await apiCall(`/api/profile?token=${currentToken}`);
        
        document.getElementById('welcomeText').textContent = `WELCOME ${data.username.toUpperCase()}!`;
        document.getElementById('winsValue').textContent = data.wins;
        document.getElementById('lossesValue').textContent = data.losses;
        document.getElementById('eloValue').textContent = Math.floor(data.elo_rating);
        
        await loadLobbies();
    } catch (error) {
        showError('Failed to load profile');
        logout();
    }
}

// ============================================================================
// Lobby Management
// ============================================================================

async function createLobby() {
    showLoading();
    try {
        const data = await apiCall(`/api/lobby/create?token=${currentToken}`, 'POST');
        currentLobbyId = data.lobby_id;
        
        document.getElementById('lobbyIdDisplay').textContent = currentLobbyId;
        showScreen(gameLaunchScreen);
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

async function loadLobbies() {
    try {
        const data = await apiCall('/api/lobby/list');
        const container = document.getElementById('lobbiesContainer');
        
        if (data.lobbies.length === 0) {
            container.innerHTML = '<p class="empty-message">No active lobbies. Create one!</p>';
            return;
        }
        
        container.innerHTML = data.lobbies.map(lobby => `
            <div class="lobby-item" onclick="joinLobby('${lobby.id}')">
                <div class="lobby-info">
                    <div class="lobby-id">Lobby: ${lobby.id}</div>
                    <div class="lobby-players">Players: ${lobby.player_count}/${lobby.max_players}</div>
                </div>
                <button class="lobby-join-btn" onclick="event.stopPropagation(); joinLobby('${lobby.id}')">
                    JOIN
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load lobbies:', error);
    }
}

function joinLobby(lobbyId) {
    currentLobbyId = lobbyId;
    document.getElementById('lobbyIdDisplay').textContent = currentLobbyId;
    showScreen(gameLaunchScreen);
}

// ============================================================================
// Game Launch
// ============================================================================

function launchGame() {
    if (!currentToken || !currentLobbyId) {
        showError('Missing token or lobby ID');
        return;
    }
    
    // Construct Godot game URL with parameters
    const gameUrl = `${GODOT_GAME_URL}?lobby_id=${currentLobbyId}&token=${currentToken}`;
    
    // Open game in new tab (or same tab depending on preference)
    window.location.href = gameUrl;
    // Alternative: window.open(gameUrl, '_blank');
}

// ============================================================================
// Event Listeners
// ============================================================================

// Login Form
document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('loginUsername').value;
    const password = document.getElementById('loginPassword').value;
    login(username, password);
});

// Register Form
document.getElementById('registerForm').addEventListener('submit', (e) => {
    e.preventDefault();
    const username = document.getElementById('registerUsername').value;
    const password = document.getElementById('registerPassword').value;
    register(username, password);
});

// Screen Switching
document.getElementById('showRegister').addEventListener('click', () => {
    showScreen(registerScreen);
});

document.getElementById('showLogin').addEventListener('click', () => {
    showScreen(loginScreen);
});

// Logout
document.getElementById('logoutBtn').addEventListener('click', logout);

// Lobby Actions
document.getElementById('createLobbyBtn').addEventListener('click', createLobby);
document.getElementById('refreshLobbiesBtn').addEventListener('click', loadLobbies);

// Game Launch
document.getElementById('playGameBtn').addEventListener('click', launchGame);
document.getElementById('backToLobbyBtn').addEventListener('click', () => {
    showScreen(lobbyScreen);
    loadLobbies();
});

// ============================================================================
// Initialization
// ============================================================================

window.addEventListener('DOMContentLoaded', () => {
    // Check if user is already logged in
    if (currentToken && currentUsername) {
        loadProfile();
        showScreen(lobbyScreen);
    } else {
        showScreen(loginScreen);
    }
    
    // Auto-refresh lobbies every 5 seconds when on lobby screen
    setInterval(() => {
        if (lobbyScreen.classList.contains('active')) {
            loadLobbies();
        }
    }, 5000);
});
