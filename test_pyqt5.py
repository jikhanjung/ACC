"""
Simple PyQt5 test
"""
import sys
print("1. Importing PyQt5...")

try:
    from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
    from PyQt5.QtCore import Qt
    print("✓ PyQt5 imports OK")
except Exception as e:
    print(f"✗ Import error: {e}")
    sys.exit(1)

print("2. Creating QApplication...")
try:
    app = QApplication(sys.argv)
    print("✓ QApplication created")
except Exception as e:
    print(f"✗ QApplication error: {e}")
    sys.exit(1)

print("3. Creating QMainWindow...")
try:
    window = QMainWindow()
    window.setWindowTitle("PyQt5 Test")
    window.setGeometry(100, 100, 400, 300)

    label = QLabel("PyQt5 is working!", window)
    label.setAlignment(Qt.AlignCenter)
    window.setCentralWidget(label)
    print("✓ QMainWindow created")
except Exception as e:
    print(f"✗ Window creation error: {e}")
    sys.exit(1)

print("4. Showing window...")
try:
    window.show()
    print("✓ Window shown")
    print("5. Starting event loop...")
    sys.exit(app.exec_())
except Exception as e:
    print(f"✗ Execution error: {e}")
    sys.exit(1)
