@echo off
echo Building DEBUG version with console window...
echo This version will show error messages in console.
echo.

if exist build rmdir /s /q build
if exist dist rmdir /s /q dist

pyinstaller --clean acc_gui_debug.spec

if exist "dist\AACCViz_v0.0.1_20251112_DEBUG\AACCViz_v0.0.1_20251112_DEBUG.exe" (
    echo.
    echo SUCCESS! Debug version created.
    echo Folder: dist\AACCViz_v0.0.1_20251112_DEBUG\
    echo.
    echo This version will show a console window with error messages.
    echo Run it to see detailed error information.
) else (
    echo.
    echo FAILED! Check errors above.
)

echo.
pause
