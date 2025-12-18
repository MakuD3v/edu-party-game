@echo off
echo Starting EDU-PARTY Pygame Client...
echo.

cd pygame_client

REM Check if venv exists
if not exist "venv\" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Activate venv
call venv\Scripts\activate.bat

REM Install requirements
echo Installing dependencies...
pip install -q -r requirements.txt

REM Run the game
echo.
echo Starting game...
python main.py

pause
