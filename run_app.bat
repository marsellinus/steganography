@echo off
echo ======================================================
echo Transform Domain Steganography - Web Application
echo ======================================================
echo.

REM Check if Python is installed
python --version > nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan! Pastikan Python telah diinstal dan terdaftar di PATH.
    goto end
)

REM Check if virtual environment exists
if exist venv (
    echo [INFO] Menggunakan virtual environment yang sudah ada...
    call venv\Scripts\activate
) else (
    echo [INFO] Membuat virtual environment baru...
    python -m venv venv
    call venv\Scripts\activate
    echo [INFO] Menginstal requirements...
    pip install -r requirements.txt
)

REM Check if requirements need to be updated
echo [INFO] Memeriksa dependensi yang diperlukan...
pip install -r requirements.txt --quiet

echo [INFO] Menjalankan aplikasi web...
echo [INFO] Buka browser dan akses http://127.0.0.1:5000/
echo [INFO] Tekan Ctrl+C untuk menghentikan server
echo.
python app.py

:end
pause