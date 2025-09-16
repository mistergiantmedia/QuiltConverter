@echo off
echo Installing Looking Glass Quilt Video Converter...
echo.

REM Check if Python is installed
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://www.python.org/downloads/
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found! Installing required packages...
python -m pip install --upgrade pip
python -m pip install opencv-python numpy pillow

echo.
echo Installation complete!
echo You can now run the converter using run_converter.bat
echo.
pause