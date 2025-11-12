@echo off
echo ============================================================
echo Fix matplotlib + PyQt5 using conda
echo ============================================================
echo.

echo Current versions:
python -c "import matplotlib; print('matplotlib:', matplotlib.__version__)"
python -c "from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR; print('PyQt5:', PYQT_VERSION_STR); print('Qt5:', QT_VERSION_STR)"
echo.

echo ============================================================
echo Uninstalling pip-installed matplotlib...
echo ============================================================
pip uninstall -y matplotlib

echo.
echo ============================================================
echo Installing matplotlib via conda (ensures binary compatibility)
echo ============================================================
conda install -y matplotlib=3.7.1

echo.
echo ============================================================
echo Testing...
echo ============================================================
python test_canvas_import.py

echo.
echo ============================================================
if errorlevel 1 (
    echo FAILED - Still crashing
    echo.
    echo Alternative: Try matplotlib 3.5.3 which is more stable with PyQt5
    echo conda install -y matplotlib=3.5.3
) else (
    echo SUCCESS!
)
echo ============================================================
