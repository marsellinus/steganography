@echo off
REM filepath: d:\Tugas\KI\stegano\run_app.bat
echo Transform Domain Steganography Application
echo ========================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo Python is not installed or not in PATH.
    echo Please install Python from https://www.python.org/downloads/
    echo Ensure you check "Add Python to PATH" during installation.
    pause
    exit /b 1
)

echo Installing required packages...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo.
echo Creating required directories...
if not exist "uploads" mkdir uploads
if not exist "outputs" mkdir outputs
if not exist "temp" mkdir temp
if not exist "static" mkdir static
if not exist "templates" mkdir templates

echo.
echo Checking environment...
python check_env.py

echo.
echo Starting Flask application...
echo.
echo Access the application at http://127.0.0.1:5000/
echo.
echo Press Ctrl+C to stop the server when done.
echo.
python app.py