#!/bin/bash
echo "Installing Looking Glass Quilt Video Converter..."
echo

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3 from https://www.python.org/downloads/"
    exit 1
fi

echo "Python found! Installing required packages..."
python3 -m pip install --upgrade pip
python3 -m pip install opencv-python numpy pillow

echo
echo "Installation complete!"
echo "You can now run the converter using: ./run_converter.sh"
echo "Or: python3 quilt_converter_gui.py"
echo