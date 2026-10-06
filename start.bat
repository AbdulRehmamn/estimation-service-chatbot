@echo off
title Estimation Service Chat Bot
color 0B

echo ======================================================================
echo             ESTIMATION SERVICE CHAT BOT
echo ======================================================================
echo.
echo [1/3] Checking Python installation...
python --version >nul 2>&1
if errorlevel 1 (
    echo.
    echo [ERROR] Python is not found in your system PATH!
    echo Please install Python 3.9+ from https://www.python.org/
    echo and ensure "Add Python to PATH" is checked during installation.
    echo.
    pause
    exit /b 1
)

echo Python is detected successfully.
echo.
echo [2/3] Installing and verifying required dependencies...
python -m pip install -r "%~dp0requirements.txt"
if errorlevel 1 (
    echo.
    echo [WARNING] There was an issue installing some dependencies.
    echo Attempting to launch the server anyway...
    echo.
)

echo.
echo [3/3] Launching Web Chat Application...
echo The web browser will open automatically in a moment.
echo Server Address: http://127.0.0.1:5000
echo.
echo ======================================================================
echo  Chatbot server is now running! 
echo  Keep this window open while chatting. Press CTRL+C to stop the server.
echo ======================================================================
echo.

:: Launch browser after a 2-second delay so Flask has time to bind to port 5000
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://127.0.0.1:5000"

:: Start the Flask app
cd /d "%~dp0"
python app.py

pause
