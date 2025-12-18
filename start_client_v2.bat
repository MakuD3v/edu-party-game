@echo off
echo Starting EDU-PARTY OOP Game Engine...
echo.

cd pygame_client_v2

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
echo Launching OOP Edition...
python main.py

pause
