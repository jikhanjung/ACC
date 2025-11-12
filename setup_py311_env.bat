@echo off
echo ============================================================
echo Create Python 3.11 Environment for ACC
echo ============================================================
echo.

echo Creating new conda environment 'ACC_py311' with Python 3.11...
conda create -n ACC_py311 python=3.11 -y

echo.
echo Activating environment...
call conda activate ACC_py311

echo.
echo Installing packages via conda...
conda install -y pyqt=5.15 scipy pandas "numpy>=2.0"

echo.
echo Installing packages via pip...
pip install PyQt5-sip==12.12.2 "matplotlib>=3.9.0" pyinstaller==5.13.0

echo.
echo ============================================================
echo Environment setup complete!
echo ============================================================
echo.
echo To use this environment:
echo   conda activate ACC_py311
echo.
echo To test the application:
echo   cd D:\projects\ACC
echo   python test_canvas_import.py
echo   python acc_gui.py
echo.
echo ============================================================
