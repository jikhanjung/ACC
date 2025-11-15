"""Test FigureCanvasQTAgg import with different approaches"""
import sys
import os

# Set environment variables BEFORE any imports
os.environ['QT_API'] = 'pyqt5'
os.environ['QT_DEBUG_PLUGINS'] = '1'  # Show Qt plugin loading debug info

# Get the Qt plugins path
from PyQt5.QtCore import QLibraryInfo
plugins_path = QLibraryInfo.location(QLibraryInfo.PluginsPath)
print(f"Qt plugins path: {plugins_path}")

# Make sure Qt can find its plugins
os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = plugins_path
print(f"Set QT_QPA_PLATFORM_PLUGIN_PATH to: {plugins_path}")

print("\nStep 1: Import PyQt5.QtWidgets...")
from PyQt5.QtWidgets import QApplication
print("✓ PyQt5.QtWidgets imported")

print("\nStep 2: Create QApplication...")
app = QApplication(sys.argv)
print(f"✓ QApplication created")
print(f"  Platform: {app.platformName()}")

print("\nStep 3: Import matplotlib...")
import matplotlib
matplotlib.use('Qt5Agg')
print(f"✓ matplotlib backend set to Qt5Agg")

print("\nStep 4: Import Figure...")
from matplotlib.figure import Figure
print("✓ Figure imported")

print("\nStep 5: Create Figure...")
fig = Figure(figsize=(5, 4))
print("✓ Figure created")

print("\nStep 6: Import FigureCanvasQTAgg (CRITICAL STEP)...")
print("If this crashes, the problem is Qt backend initialization")
print("Watch for Qt debug messages above...")

# Try to import with explicit error handling
import ctypes
import ctypes.wintypes

try:
    # First, try to load the Qt5 DLLs manually to see if they exist
    print("\nChecking Qt5 DLLs...")
    qt_path = os.path.join(os.path.dirname(plugins_path), 'bin')
    print(f"Looking for Qt DLLs in: {qt_path}")

    if os.path.exists(qt_path):
        print(f"✓ Qt bin directory exists")
        # List DLL files
        dlls = [f for f in os.listdir(qt_path) if f.endswith('.dll')]
        print(f"Found {len(dlls)} DLL files")
        for dll in sorted(dlls)[:10]:  # Show first 10
            print(f"  - {dll}")
    else:
        print(f"✗ Qt bin directory not found")

    print("\nAttempting FigureCanvasQTAgg import...")
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    print("✓✓✓ SUCCESS! FigureCanvasQTAgg imported!")

    print("\nStep 7: Create FigureCanvas...")
    canvas = FigureCanvasQTAgg(fig)
    print("✓✓✓ SUCCESS! FigureCanvas created!")

    print("\n" + "="*60)
    print("ALL TESTS PASSED!")
    print("="*60)

except Exception as e:
    print(f"\n✗ Error: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
