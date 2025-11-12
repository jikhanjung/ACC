@echo off
echo Building ACC Visualization executable with spec file...
echo.

REM Clean previous build
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

REM Build with spec file
pyinstaller --clean acc_gui.spec

echo.
echo Done! Executable is in the 'dist' folder.
echo.
pause
