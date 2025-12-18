@echo off
REM Quick launcher script for EDU Party server

echo ============================================================
echo EDU PARTY - Starting Server
echo ============================================================
echo.

REM Check if venv exists
if not exist "venv\Scripts\activate.bat" (
    echo Error: Virtual environment not found!
    echo Please run: python -m venv venv
    pause
    exit /b 1
)

REM Check if .env exists
if not exist ".env" (
    echo .env file not found. Running setup script...
    echo.
    call venv\Scripts\python.exe setup.py
    if errorlevel 1 (
        echo.
        echo Setup failed. Please check your configuration.
        pause
        exit /b 1
    )
)

echo Starting FastAPI server...
echo Server will be available at: http://localhost:8000
echo Press Ctrl+C to stop the server
echo.

call venv\Scripts\python.exe -m uvicorn backend.main:app --reload --host 0.0.0.0 --port 8000
