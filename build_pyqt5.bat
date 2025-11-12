@echo off
echo ========================================
echo Building with PyQt5 (Stable Version)
echo ========================================
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

echo Building OneDir version (recommended)...
echo.

pyinstaller --clean acc_gui_pyqt5.spec

if exist "dist\AACCViz_v0.0.1_20251112\AACCViz_v0.0.1_20251112.exe" (
    echo.
    echo ========================================
    echo SUCCESS! PyQt5 version built.
    echo ========================================
    echo.
    echo Folder: dist\AACCViz_v0.0.1_20251112\
    echo.
    echo PyQt5 is more stable with PyInstaller!
    echo This build should work without DLL errors.
) else (
    echo.
    echo FAILED! Check errors above.
)

echo.
pause
