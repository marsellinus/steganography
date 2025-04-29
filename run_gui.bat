@echo off
echo ======================================================
echo Transform Domain Steganography - Desktop Application
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

echo [INFO] Memilih aplikasi GUI untuk dijalankan:
echo [1] GUI Lama (Tkinter)
echo [2] GUI Baru (PySimpleGUI)
echo.

set /p choice="Pilih GUI [1/2]: "

if "%choice%"=="1" (
    echo [INFO] Menjalankan GUI lama (Tkinter)...
    python main.py
) else if "%choice%"=="2" (
    echo [INFO] Menjalankan GUI baru (PySimpleGUI)...
    python modern_gui.py
) else (
    echo [ERROR] Pilihan tidak valid!
)

:end
pause