"""Check package versions"""
import sys

print("Python version:", sys.version)
print()

try:
    import PyQt5
    from PyQt5.QtCore import PYQT_VERSION_STR, QT_VERSION_STR
    print("PyQt5 version:", PYQT_VERSION_STR)
    print("Qt version:", QT_VERSION_STR)
except Exception as e:
    print("PyQt5 error:", e)

print()

try:
    import matplotlib
    print("matplotlib version:", matplotlib.__version__)
except Exception as e:
    print("matplotlib error:", e)

print()

try:
    import numpy
    print("numpy version:", numpy.__version__)
except Exception as e:
    print("numpy error:", e)

print()

try:
    import scipy
    print("scipy version:", scipy.__version__)
except Exception as e:
    print("scipy error:", e)

print()

try:
    import pandas
    print("pandas version:", pandas.__version__)
except Exception as e:
    print("pandas error:", e)
