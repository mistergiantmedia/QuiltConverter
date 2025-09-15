@echo off
echo Starting Looking Glass Quilt Video Converter...
python quilt_converter_gui.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to start the application
    echo Make sure you ran setup.bat first
    pause
)