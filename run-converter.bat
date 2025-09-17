@echo off
echo ===============================================
echo Looking Glass Quilt Video Converter
echo ===============================================
echo.

REM Check if virtual environment exists and activate it
if exist "venv\Scripts\activate.bat" (
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
) else (
    echo Virtual environment not found. Please run setup.bat first.
    echo.
)

echo Starting converter...
echo.

REM Run the converter with error handling
python quilt-converter-gui.py

REM Check if there was an error
if %errorlevel% neq 0 (
    echo.
    echo ===============================================
    echo ERROR: The converter failed to start
    echo ===============================================
    echo Error code: %errorlevel%
    echo.
    echo Possible solutions:
    echo 1. Run setup.bat first to install dependencies
    echo 2. Make sure Python is installed
    echo 3. Check the error message above
    echo.
)

echo.
echo Press any key to close this window...
pause >nul