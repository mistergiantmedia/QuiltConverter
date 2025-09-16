@echo off
echo Looking Glass Quilt Video Converter - Setup and Run
echo ===================================================
echo.

REM Check if Python is installed
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python from https://python.org
    echo Make sure to check "Add Python to PATH" during installation
    pause
    exit /b 1
)

echo Python found. Checking/installing required packages...
echo.

REM Install required packages
pip install opencv-python numpy tqdm tkinter pillow --quiet

if %errorlevel% neq 0 (
    echo Warning: Some packages may not have installed correctly
    echo You may need to run this as administrator
    echo.
)

echo Starting Looking Glass Quilt Video Converter...
echo.

REM Run the GUI application
python quilt_converter_gui.py

if %errorlevel% neq 0 (
    echo.
    echo Error running the converter. Please check the error messages above.
    pause
)

echo.
echo Converter finished. Press any key to exit.
pause