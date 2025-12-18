"""
Educational Mayhem Constants and Configuration
Updated with profile system colors and shape database.
"""

# Educational Mayhem Color Scheme (Synced with Web Client)
MAYHEM_PURPLE = (53, 28, 96)          # #351C60 - Deep intro background
CHALKBOARD_DARK = (42, 22, 75)        # #2A164B - Darker boxes
CHALK_WHITE = (236, 240, 241)         # #ECF0F1 - Text/UI
SCHOOL_BUS_YELLOW = (255, 210, 0)     # #FFD200 - Bright Title Yellow
ERASER_PINK = (255, 192, 203)         # Accent color

# Character Colors
STUDENT_RED = (231, 76, 60)           # #E74C3C
STUDENT_BLUE = (52, 152, 219)         # #3498DB
STUDENT_GREEN = (46, 204, 113)        # #2ECC71

# Shape Database for Educational Mayhem
SHAPE_DATABASE: list[str] = [
    "circle",
    "square",
    "triangle",
    "star",
    "hexagon"
]

# Gear Database
GEAR_DATABASE: list[str] = [
    "Graduation Cap",
    "Science Goggles",
    "Backpack",
    "Calculator Watch",
    "Pencil Case"
]

# Game Configuration
SCREEN_WIDTH: int = 1280
SCREEN_HEIGHT: int = 720
FPS: int = 60
MAX_STUDENTS: int = 15

# WebSocket Configuration
SERVER_URL: str = "ws://localhost:8000"
API_URL: str = "http://localhost:8000"
