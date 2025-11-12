@echo off
echo Building ACC Visualization executable...

pyinstaller --name "AACCViz_v0.0.1_20251112" ^
    --onefile ^
    --windowed ^
    --hidden-import PyQt6.QtCore ^
    --hidden-import PyQt6.QtGui ^
    --hidden-import PyQt6.QtWidgets ^
    --hidden-import matplotlib.backends.backend_qt5agg ^
    --hidden-import scipy.cluster.hierarchy ^
    --hidden-import scipy.spatial.distance ^
    --hidden-import scipy.special._cdflib ^
    --collect-all PyQt6 ^
    --collect-all matplotlib ^
    acc_gui.py

echo Done!
pause
