/**
 * EDU PARTY - Frontend JavaScript
 * Handles authentication, lobby management, and profile customization
 */

// API Configuration
const API_BASE = window.location.origin;
const GODOT_GAME_URL = `${API_BASE}/game/index.html`;

// State Management
let currentToken = localStorage.getItem('token') || null;
let currentUsername = localStorage.getItem('username') || null;
let currentLobbyId = null;

// Profile State
let selectedColor = 'red';
let selectedShape = 'circle';

// DOM Elements
const loginScreen = document.getElementById('loginScreen');
const registerScreen = document.getElementById('registerScreen');
const lobbyScreen = document.getElementById('lobbyScreen');
const gameLaunchScreen = document.getElementById('gameLaunchScreen');
const profileModal = document.getElementById('profileModal');
const loadingOverlay = document.getElementById('loadingOverlay');
const errorMessage = document.getElementById('errorMessage');

// ============================================================================
// Screen Management
// ============================================================================

function showScreen(screenElement) {
    document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
    screenElement.classList.add('active');
}

function showLoading() { loadingOverlay.classList.add('active'); }
function hideLoading() { loadingOverlay.classList.remove('active'); }

function showError(message) {
    errorMessage.textContent = message;
    errorMessage.classList.add('active');
    setTimeout(() => { errorMessage.classList.remove('active'); }, 3000);
}

function toggleProfileModal(show) {
    if (show) profileModal.classList.add('active');
    else profileModal.classList.remove('active');
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
    if (body) options.body = JSON.stringify(body);

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
        handleAuthSuccess(data);
    } catch (error) { showError(error.message); }
    finally { hideLoading(); }
}

async function login(username, password) {
    showLoading();
    try {
        const data = await apiCall('/api/login', 'POST', { username, password });
        handleAuthSuccess(data);
    } catch (error) { showError(error.message); }
    finally { hideLoading(); }
}

function handleAuthSuccess(data) {
    currentToken = data.access_token;
    currentUsername = data.username;
    localStorage.setItem('token', currentToken);
    localStorage.setItem('username', currentUsername);
    loadProfile();
    showScreen(lobbyScreen);
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

        // Init profile selection
        selectedColor = data.color || 'red';
        selectedShape = data.shape || 'circle';
        highlightSelection(); // Visual update

        loadLobbies();
    } catch (error) {
        console.error(error);
        logout();
    }
}

async function saveProfile() {
    showLoading();
    try {
        await apiCall(`/api/profile/update?token=${currentToken}`, 'POST', {
            username: currentUsername, // Keep same username
            color: selectedColor,
            shape: selectedShape
        });
        toggleProfileModal(false);
        showError("Profile Saved!"); // Reusing error box for success msg temporarily
    } catch (error) {
        showError(error.message);
    } finally {
        hideLoading();
    }
}

// Profile UI Selection Logic
window.selectColor = (color) => {
    selectedColor = color;
    highlightSelection();
}

window.selectShape = (shape) => {
    selectedShape = shape;
    highlightSelection();
}

function highlightSelection() {
    // Colors
    document.querySelectorAll('.color-selector .selector-option').forEach(el => {
        el.classList.remove('selected');
        if (el.dataset.color === selectedColor) el.classList.add('selected');
    });
    // Shapes handles visually? For now just log, implementation of shape visual selector in HTML was simplified text
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
            container.innerHTML = '<p class="empty-message">No active classes found. Create one!</p>';
            return;
        }

        container.innerHTML = data.lobbies.map(lobby => `
            <div class="lobby-item" onclick="joinLobby('${lobby.id}')">
                <div class="lobby-info">
                    <div class="lobby-id">CLASS: ${lobby.id}</div>
                    <div class="lobby-players">Students: ${lobby.player_count}/${lobby.max_players}</div>
                </div>
                <button class="join-btn" onclick="event.stopPropagation(); joinLobby('${lobby.id}')">
                    JOIN
                </button>
            </div>
        `).join('');
    } catch (error) {
        console.error('Failed to load lobbies:', error);
    }
}

window.joinLobby = (lobbyId) => {
    currentLobbyId = lobbyId;
    document.getElementById('lobbyIdDisplay').textContent = currentLobbyId;
    showScreen(gameLaunchScreen);
}

function launchGame() {
    if (!currentToken || !currentLobbyId) return;
    const gameUrl = `${GODOT_GAME_URL}?lobby_id=${currentLobbyId}&token=${currentToken}`;
    window.location.href = gameUrl;
}

// ============================================================================
// Event Listeners
// ============================================================================

document.getElementById('loginForm').addEventListener('submit', (e) => {
    e.preventDefault();
    login(document.getElementById('loginUsername').value, document.getElementById('loginPassword').value);
});

document.getElementById('registerForm').addEventListener('submit', (e) => {
    e.preventDefault();
    register(document.getElementById('registerUsername').value, document.getElementById('registerPassword').value);
});

document.getElementById('showRegister').addEventListener('click', () => showScreen(registerScreen));
document.getElementById('showLogin').addEventListener('click', () => showScreen(loginScreen));
document.getElementById('logoutBtn').addEventListener('click', logout);

document.getElementById('createLobbyBtn').addEventListener('click', createLobby);
document.getElementById('refreshLobbiesBtn').addEventListener('click', loadLobbies);

document.getElementById('editProfileBtn').addEventListener('click', () => toggleProfileModal(true));
document.getElementById('closeProfileBtn').addEventListener('click', () => toggleProfileModal(false));
document.getElementById('saveProfileBtn').addEventListener('click', saveProfile);

document.getElementById('playGameBtn').addEventListener('click', launchGame);
document.getElementById('backToLobbyBtn').addEventListener('click', () => {
    showScreen(lobbyScreen);
    loadLobbies();
});

// Initialization
window.addEventListener('DOMContentLoaded', () => {
    if (currentToken && currentUsername) {
        loadProfile();
        showScreen(lobbyScreen);
    } else {
        showScreen(loginScreen);
    }

    // Auto-refresh lobbies
    setInterval(() => {
        if (lobbyScreen.classList.contains('active')) loadLobbies();
    }, 5000);
});

