@echo off
echo Building OneDir version (recommended for debugging)...
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --clean acc_gui_onedir.spec

if exist "dist\AACCViz_v0.0.1_20251112\AACCViz_v0.0.1_20251112.exe" (
    echo.
    echo SUCCESS! Folder: dist\AACCViz_v0.0.1_20251112\
    echo.
    echo To run: dist\AACCViz_v0.0.1_20251112\AACCViz_v0.0.1_20251112.exe
) else (
    echo.
    echo FAILED! Check errors above.
)

echo.
pause
