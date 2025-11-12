# Matplotlib + PyQt5 Import Issue

## Problem
acc_gui.py crashes when importing matplotlib with PyQt5 backend, specifically at:
```python
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
```

## What Works
- PyQt5 5.15.9 imports correctly
- Simple PyQt5 test window (test_pyqt5.py) works
- All other imports (numpy, pandas, scipy) work
- matplotlib 3.7.1 is installed

## What Fails
- matplotlib.backends.backend_qt5agg import causes silent crash
- Application exits without error message after setting Qt5Agg backend

## Diagnosis Steps

### Step 1: Run matplotlib diagnostic
```powershell
# Windows PowerShell
cd D:\projects\ACC
python test_matplotlib_qt5.py
```

This will show exactly which step fails.

### Step 2: Check for missing dependencies

matplotlib with Qt5Agg backend may need additional packages:

```powershell
pip install pyqt5 matplotlib scipy numpy pandas
```

Or specifically:
```powershell
pip install PyQt5-sip PyQt5-Qt5
```

### Step 3: Check for conflicting backends

Check if multiple Qt backends are installed:
```powershell
python -c "import sys; print(sys.path)"
pip list | findstr -i qt
pip list | findstr -i pyqt
```

### Step 4: Try alternative import order

The current import order in acc_gui.py (after fix):
1. Set os.environ['QT_API'] = 'pyqt5'
2. Import matplotlib
3. matplotlib.use('Qt5Agg')
4. Import Figure from matplotlib.figure
5. Import pyplot
6. Import FigureCanvasQTAgg

### Step 5: Check for DLL issues (Windows)

matplotlib backend may have DLL loading issues:
```powershell
# Check if Visual C++ Redistributable is installed
# Download from: https://aka.ms/vs/17/release/vc_redist.x64.exe
```

## Potential Solutions

### Solution 1: Reinstall matplotlib with dependencies
```powershell
pip uninstall matplotlib
pip install matplotlib==3.7.1 --no-cache-dir
```

### Solution 2: Use conda (if available)
```powershell
conda install matplotlib=3.7.1 pyqt=5.15.9
```

### Solution 3: Check backend availability
```powershell
python -c "import matplotlib.backends; print(dir(matplotlib.backends))"
```

### Solution 4: Try without backend setup
Comment out `matplotlib.use('Qt5Agg')` and let matplotlib auto-detect.

## Known Issues

1. **WSL vs Windows**: Must run in Windows native Python, not WSL
2. **PyQt5 vs PyQt6**: Backend names differ (Qt5Agg vs QtAgg)
3. **matplotlib 3.10.0**: May have compatibility issues with older PyQt5

## Current Status

- ✓ PyQt5 conversion complete
- ✓ All imports work except matplotlib backend
- ✗ FigureCanvasQTAgg import crashes
- ⏳ Need to diagnose with test_matplotlib_qt5.py

## Next Steps

1. Run `python test_matplotlib_qt5.py` in Windows PowerShell
2. Report which step fails
3. Apply appropriate solution based on failure point
