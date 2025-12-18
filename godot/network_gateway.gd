extends Node
## NetworkGateway - Godot 4 WebSocket Client for Fall Guys-Style Multiplayer
## Cross-platform support (Mobile & Desktop)

# Signals for game logic
signal connected_to_server(player_id: String, lobby_id: String)
signal player_joined(player_data: Dictionary)
signal player_left(player_id: String, username: String)
signal player_updated(player_data: Dictionary)
signal players_list_received(players: Array)
signal connection_error(message: String)

# WebSocket
var socket: WebSocketPeer
var is_connected: bool = false

# Connection info
var server_url: String = "ws://localhost:8000/ws"
var lobby_id: String = ""
var token: String = ""
var player_id: String = ""

# Player state for synchronization
var local_player_state = {
	"position": {"x": 0.0, "y": 0.0, "z": 0.0},
	"velocity": {"x": 0.0, "y": 0.0, "z": 0.0},
	"rotation": 0.0,
	"state": "idle"  # idle, running, jumping, falling, eliminated
}

# Update throttling
var update_interval: float = 0.05  # Send updates every 50ms (20 FPS)
var time_since_last_update: float = 0.0

# Touch detection
var is_touch_device: bool = false


func _ready():
	# Detect if running on mobile
	_detect_platform()
	
	# Parse URL parameters (only works in web build)
	if OS.has_feature("web"):
		_parse_url_parameters()
	else:
		# For testing in editor, use default values
		lobby_id = "test123"
		token = "test_token"
		print("Running in editor - using test credentials")
	
	# Connect to server
	_connect_to_server()


func _process(delta):
	if socket:
		socket.poll()
		var state = socket.get_ready_state()
		
		if state == WebSocketPeer.STATE_OPEN:
			if not is_connected:
				is_connected = true
				print("WebSocket connected!")
			
			# Receive messages
			while socket.get_available_packet_count():
				var packet = socket.get_packet()
				var json_string = packet.get_string_from_utf8()
				var json = JSON.new()
				var error = json.parse(json_string)
				
				if error == OK:
					_handle_message(json.data)
				else:
					print("JSON Parse Error: ", json.get_error_message())
			
			# Send updates at throttled rate
			time_since_last_update += delta
			if time_since_last_update >= update_interval:
				send_player_update()
				time_since_last_update = 0.0
		
		elif state == WebSocketPeer.STATE_CLOSING:
			pass
		
		elif state == WebSocketPeer.STATE_CLOSED:
			var code = socket.get_close_code()
			var reason = socket.get_close_reason()
			print("WebSocket closed with code: %d, reason: %s" % [code, reason])
			is_connected = false
			connection_error.emit("Connection closed")


# ============================================================================
# Connection Management
# ============================================================================

func _connect_to_server():
	"""Connect to the WebSocket server with lobby_id and token."""
	socket = WebSocketPeer.new()
	
	# Build full URL with query parameters
	var full_url = "%s?lobby_id=%s&token=%s" % [server_url, lobby_id, token]
	
	print("Connecting to: ", server_url)
	print("Lobby ID: ", lobby_id)
	
	var err = socket.connect_to_url(full_url)
	
	if err != OK:
		print("Unable to connect to server: ", err)
		connection_error.emit("Failed to connect to server")
	else:
		print("Connection initiated...")


func disconnect_from_server():
	"""Gracefully disconnect from the server."""
	if socket:
		socket.close(1000, "Client disconnect")
		is_connected = false


# ============================================================================
# URL Parameter Parsing (Web Build Only)
# ============================================================================

func _parse_url_parameters():
	"""Parse lobby_id and token from URL using JavaScriptBridge."""
	if not OS.has_feature("web"):
		return
	
	# Get URL parameters using JavaScript
	var js_code = """
	(function() {
		var params = new URLSearchParams(window.location.search);
		return {
			lobby_id: params.get('lobby_id') || '',
			token: params.get('token') || ''
		};
	})();
	"""
	
	var result = JavaScriptBridge.eval(js_code)
	
	if result:
		lobby_id = result.lobby_id if result.has("lobby_id") else ""
		token = result.token if result.has("token") else ""
		
		print("Parsed URL Parameters:")
		print("  Lobby ID: ", lobby_id)
		print("  Token: ", token[:20] + "..." if token.length() > 20 else token)
	else:
		print("Failed to parse URL parameters")
		connection_error.emit("Missing lobby_id or token in URL")


# ============================================================================
# Platform Detection
# ============================================================================

func _detect_platform():
	"""Detect if running on mobile or desktop."""
	if OS.has_feature("mobile") or OS.has_feature("web_android") or OS.has_feature("web_ios"):
		is_touch_device = true
		print("Platform: Mobile/Touch Device")
	else:
		is_touch_device = false
		print("Platform: Desktop")


func is_mobile() -> bool:
	"""Helper function for game logic to check if on mobile."""
	return is_touch_device


# ============================================================================
# Message Handling
# ============================================================================

func _handle_message(data: Dictionary):
	"""Handle incoming messages from server."""
	if not data.has("type"):
		return
	
	var msg_type = data["type"]
	
	match msg_type:
		"connected":
			player_id = data.get("player_id", "")
			var received_lobby_id = data.get("lobby_id", "")
			print("Connected! Player ID: ", player_id)
			connected_to_server.emit(player_id, received_lobby_id)
		
		"player_joined":
			var player_data = data.get("player", {})
			print("Player joined: ", player_data.get("username", "Unknown"))
			player_joined.emit(player_data)
		
		"player_left":
			var left_player_id = data.get("player_id", "")
			var username = data.get("username", "Unknown")
			print("Player left: ", username)
			player_left.emit(left_player_id, username)
		
		"player_update":
			var player_data = data.get("player", {})
			player_updated.emit(player_data)
		
		"players_list":
			var players = data.get("players", [])
			print("Received players list: ", players.size(), " players")
			players_list_received.emit(players)
		
		"error":
			var error_msg = data.get("message", "Unknown error")
			print("Server error: ", error_msg)
			connection_error.emit(error_msg)


# ============================================================================
# Sending Updates
# ============================================================================

func send_player_update():
	"""Send current player state to server."""
	if not is_connected:
		return
	
	var json = JSON.stringify(local_player_state)
	socket.send_text(json)


func update_player_position(pos: Vector3):
	"""Update player position for synchronization."""
	local_player_state["position"] = {
		"x": pos.x,
		"y": pos.y,
		"z": pos.z
	}


func update_player_velocity(vel: Vector3):
	"""Update player velocity for synchronization."""
	local_player_state["velocity"] = {
		"x": vel.x,
		"y": vel.y,
		"z": vel.z
	}


func update_player_rotation(rot: float):
	"""Update player rotation for synchronization."""
	local_player_state["rotation"] = rot


func update_player_state(state: String):
	"""Update player state (idle, running, jumping, falling, eliminated)."""
	local_player_state["state"] = state


func send_custom_data(data: Dictionary):
	"""Send custom data to the server (for future extensibility)."""
	if not is_connected:
		return
	
	var json = JSON.stringify(data)
	socket.send_text(json)


# ============================================================================
# Utility Functions
# ============================================================================

func set_server_url(url: String):
	"""Set custom server URL (useful for production deployment)."""
	server_url = url


func get_local_player_id() -> String:
	"""Get the local player's ID."""
	return player_id


func get_connection_status() -> bool:
	"""Check if connected to server."""
	return is_connected
