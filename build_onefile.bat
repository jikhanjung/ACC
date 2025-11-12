@echo off
echo Building OneFile version...
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --clean acc_gui.spec

if exist "dist\AACCViz_v0.0.1_20251112.exe" (
    echo.
    echo SUCCESS! File: dist\AACCViz_v0.0.1_20251112.exe
) else (
    echo.
    echo FAILED! Check errors above.
)

echo.
pause
