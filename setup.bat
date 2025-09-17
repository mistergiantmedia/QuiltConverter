@echo off
echo ===============================================
echo Looking Glass Quilt Video Converter Setup
echo ===============================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python 3.7+ from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo ✓ Python found
python --version

REM Check if pip is available
pip --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: pip is not available
    pause
    exit /b 1
)

echo ✓ pip found

REM Create virtual environment if it doesn't exist
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if %errorlevel% neq 0 (
        echo ERROR: Failed to create virtual environment
        echo This might happen if Python was not installed with pip
        pause
        exit /b 1
    )
    echo ✓ Virtual environment created
) else (
    echo ✓ Virtual environment already exists
)

REM Activate virtual environment
call venv\Scripts\activate.bat
if %errorlevel% neq 0 (
    echo ERROR: Failed to activate virtual environment
    pause
    exit /b 1
)

echo ✓ Virtual environment activated

REM Upgrade pip first
echo Upgrading pip...
python -m pip install --upgrade pip

REM Install required packages one by one with error checking
echo Installing required packages...

echo Installing opencv-python...
pip install opencv-python
if %errorlevel% neq 0 (
    echo WARNING: opencv-python installation failed
)

echo Installing numpy...
pip install numpy
if %errorlevel% neq 0 (
    echo WARNING: numpy installation failed
)

echo Installing Pillow...
pip install Pillow  
if %errorlevel% neq 0 (
    echo WARNING: Pillow installation failed
)

echo ✓ Package installation completed

REM Test imports
echo Testing Python imports...
python -c "import cv2; print('✓ OpenCV OK')" 2>nul || echo "❌ OpenCV failed"
python -c "import numpy; print('✓ NumPy OK')" 2>nul || echo "❌ NumPy failed"  
python -c "import PIL; print('✓ Pillow OK')" 2>nul || echo "❌ Pillow failed"
python -c "import tkinter; print('✓ tkinter OK')" 2>nul || echo "❌ tkinter failed - GUI may not work"

REM Check for FFmpeg
ffmpeg -version >nul 2>&1
if %errorlevel% neq 0 (
    echo.
    echo WARNING: FFmpeg is not found in PATH
    echo Please download FFmpeg from https://ffmpeg.org/download.html
    echo and add it to your system PATH, or place ffmpeg.exe in this folder
    echo.
    echo FFmpeg is REQUIRED for:
    echo - H.265/HEVC encoding
    echo - ProRes 422 encoding
    echo - Better quality output
    echo.
    echo Without FFmpeg, only basic H.264 encoding is available
    echo.
) else (
    echo ✓ FFmpeg found
    ffmpeg -codecs 2>nul | findstr "libx265" >nul
    if %errorlevel% equ 0 (
        echo ✓ H.265/HEVC support available
    ) else (
        echo ⚠ H.265/HEVC support not available in this FFmpeg build
    )
    
    ffmpeg -codecs 2>nul | findstr "prores" >nul
    if %errorlevel% equ 0 (
        echo ✓ ProRes support available
    ) else (
        echo ⚠ ProRes support not available in this FFmpeg build
    )
)

echo.
echo ===============================================
echo Setup completed successfully!
echo ===============================================
echo.
echo To run the converter, double-click on quilt-converter-gui.py
echo or run: python quilt-converter-gui.py
echo.
pause