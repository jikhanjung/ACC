@echo off
echo ========================================
echo PyQt6 Version Fix Script
echo ========================================
echo.
echo This script will:
echo 1. Uninstall current PyQt6
echo 2. Install stable version (PyQt6 6.5.0)
echo.
echo Press Ctrl+C to cancel, or
pause

echo.
echo [1/2] Uninstalling PyQt6...
pip uninstall -y PyQt6 PyQt6-Qt6 PyQt6-sip

echo.
echo [2/2] Installing PyQt6 6.5.0...
pip install PyQt6==6.5.0

echo.
echo ========================================
echo Done! Now try building again:
echo   build_onedir.bat
echo ========================================
echo.
pause
