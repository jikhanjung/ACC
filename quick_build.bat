@echo off
echo ========================================
echo ACC Visualization - Quick Build Script
echo ========================================
echo.
echo Choose build type:
echo [1] OneFile - Single .exe file (slower startup, easier distribution)
echo [2] OneDir  - Folder with .exe (faster startup, better for debugging)
echo.
set /p choice="Enter choice (1 or 2): "

if "%choice%"=="1" (
    set SPEC_FILE=acc_gui.spec
    set BUILD_TYPE=OneFile
    set CHECK_FILE=dist\AACCViz_v0.0.1_20251112.exe
) else if "%choice%"=="2" (
    set SPEC_FILE=acc_gui_onedir.spec
    set BUILD_TYPE=OneDir
    set CHECK_FILE=dist\AACCViz_v0.0.1_20251112\AACCViz_v0.0.1_20251112.exe
) else (
    echo Invalid choice!
    pause
    exit /b
)

echo.
echo Building with %BUILD_TYPE% mode...
echo.

REM Step 1: Clean previous builds
echo [1/3] Cleaning previous builds...
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
echo      Done!
echo.

REM Step 2: Build with spec file
echo [2/3] Building executable...
pyinstaller --clean %SPEC_FILE%
echo      Done!
echo.

REM Step 3: Check result
echo [3/3] Checking result...
if exist "%CHECK_FILE%" (
    echo.
    echo ========================================
    echo SUCCESS! Executable created:
    echo %CHECK_FILE%
    echo ========================================
    echo.
    dir "%CHECK_FILE%"
) else (
    echo.
    echo ========================================
    echo ERROR! Build failed.
    echo Check the messages above for errors.
    echo ========================================
)

echo.
pause
