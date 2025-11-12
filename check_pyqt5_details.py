"""Check PyQt5 installation details"""
import sys
import subprocess

print("="*60)
print("PyQt5 Installation Check")
print("="*60)

# Check Python version
print(f"\nPython: {sys.version}")
print(f"Python executable: {sys.executable}")

# Check installed packages
print("\n" + "="*60)
print("Installed Qt-related packages:")
print("="*60)

result = subprocess.run([sys.executable, "-m", "pip", "list"],
                       capture_output=True, text=True)
for line in result.stdout.split('\n'):
    line_lower = line.lower()
    if 'pyqt' in line_lower or 'qt' in line_lower or 'sip' in line_lower:
        print(line)

print("\n" + "="*60)
print("PyQt5 import test:")
print("="*60)

try:
    import PyQt5
    print(f"✓ PyQt5 location: {PyQt5.__file__}")

    from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR, QLibraryInfo
    print(f"✓ PyQt5 version: {PYQT_VERSION_STR}")
    print(f"✓ Qt version: {QT_VERSION_STR}")

    # Check for plugins path
    try:
        plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
        print(f"✓ Qt plugins path: {plugins_path}")
    except:
        print("✗ Could not get Qt plugins path")

    # Check sip
    try:
        import PyQt5.sip
        print(f"✓ PyQt5.sip available")
    except Exception as e:
        print(f"✗ PyQt5.sip error: {e}")

except Exception as e:
    print(f"✗ PyQt5 error: {e}")

print("\n" + "="*60)
print("Matplotlib backend test:")
print("="*60)

try:
    import matplotlib
    print(f"✓ matplotlib version: {matplotlib.__version__}")
    print(f"✓ matplotlib location: {matplotlib.__file__}")

    # Check available backends
    import matplotlib.backends
    print(f"✓ Available backends: {dir(matplotlib.backends)}")

    # Try to get backend info
    matplotlib.use('Qt5Agg')
    print(f"✓ Backend set to Qt5Agg")

except Exception as e:
    print(f"✗ matplotlib error: {e}")

print("\n" + "="*60)
print("Attempting FigureCanvasQTAgg import with error catching:")
print("="*60)

try:
    import os
    os.environ['QT_API'] = 'pyqt5'

    # Try with verbose error reporting
    import sys
    import traceback

    try:
        from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
        print("✓ FigureCanvasQTAgg imported successfully!")
    except Exception as e:
        print(f"✗ FigureCanvasQTAgg import failed!")
        print(f"Error type: {type(e).__name__}")
        print(f"Error message: {e}")
        print("\nFull traceback:")
        traceback.print_exc()

except Exception as e:
    print(f"✗ Outer error: {e}")
    import traceback
    traceback.print_exc()
