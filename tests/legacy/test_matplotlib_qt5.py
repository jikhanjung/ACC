"""
Test matplotlib with PyQt5 backend
"""
import sys

print("Step 1: Import PyQt5...")
try:
    from PyQt5.QtWidgets import QApplication
    print("✓ PyQt5.QtWidgets imported")
except Exception as e:
    print(f"✗ PyQt5 import failed: {e}")
    sys.exit(1)

print("\nStep 2: Set QT_API...")
import os
os.environ['QT_API'] = 'pyqt5'
print("✓ QT_API set to pyqt5")

print("\nStep 3: Import matplotlib...")
try:
    import matplotlib
    print(f"✓ matplotlib imported (version {matplotlib.__version__})")
except Exception as e:
    print(f"✗ matplotlib import failed: {e}")
    sys.exit(1)

print("\nStep 4: Set backend to Qt5Agg...")
try:
    matplotlib.use('Qt5Agg')
    print("✓ Backend set to Qt5Agg")
except Exception as e:
    print(f"✗ Backend setup failed: {e}")
    sys.exit(1)

print("\nStep 5: Import matplotlib.figure.Figure...")
try:
    from matplotlib.figure import Figure
    print("✓ Figure imported")
except Exception as e:
    print(f"✗ Figure import failed: {e}")
    sys.exit(1)

print("\nStep 6: Import matplotlib.pyplot...")
try:
    import matplotlib.pyplot as plt
    print("✓ pyplot imported")
except Exception as e:
    print(f"✗ pyplot import failed: {e}")
    sys.exit(1)

print("\nStep 7: Import FigureCanvasQTAgg...")
try:
    from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
    print("✓ FigureCanvasQTAgg imported")
except Exception as e:
    print(f"✗ FigureCanvasQTAgg import failed: {e}")
    sys.exit(1)

print("\nStep 8: Create QApplication...")
try:
    app = QApplication(sys.argv)
    print("✓ QApplication created")
except Exception as e:
    print(f"✗ QApplication creation failed: {e}")
    sys.exit(1)

print("\nStep 9: Create Figure...")
try:
    fig = Figure(figsize=(5, 4))
    print("✓ Figure created")
except Exception as e:
    print(f"✗ Figure creation failed: {e}")
    sys.exit(1)

print("\nStep 10: Create FigureCanvas...")
try:
    canvas = FigureCanvasQTAgg(fig)
    print("✓ FigureCanvas created")
except Exception as e:
    print(f"✗ FigureCanvas creation failed: {e}")
    sys.exit(1)

print("\n" + "="*50)
print("SUCCESS! All matplotlib + PyQt5 components work!")
print("="*50)
