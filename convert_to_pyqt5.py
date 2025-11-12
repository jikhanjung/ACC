"""
Convert acc_gui.py from PyQt6 to PyQt5
This script automatically replaces PyQt6 imports with PyQt5
"""

import os

def convert_pyqt6_to_pyqt5(file_path):
    """Convert PyQt6 imports to PyQt5 in a file"""

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Backup original file
    backup_path = file_path + '.pyqt6_backup'
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✓ Backup created: {backup_path}")

    # Replace PyQt6 with PyQt5
    original_content = content
    content = content.replace('from PyQt6.QtWidgets import', 'from PyQt5.QtWidgets import')
    content = content.replace('from PyQt6.QtCore import', 'from PyQt5.QtCore import')
    content = content.replace('from PyQt6.QtGui import', 'from PyQt5.QtGui import')
    content = content.replace('from PyQt6 import', 'from PyQt5 import')
    content = content.replace('import PyQt6', 'import PyQt5')

    # Check if any changes were made
    if content == original_content:
        print("⚠ No PyQt6 imports found in file")
        return False

    # Save modified file
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"✓ Converted to PyQt5: {file_path}")
    return True

def main():
    print("="*60)
    print("PyQt6 → PyQt5 Conversion Script")
    print("="*60)
    print()

    # Convert acc_gui.py
    if os.path.exists('acc_gui.py'):
        print("Converting acc_gui.py...")
        convert_pyqt6_to_pyqt5('acc_gui.py')
    else:
        print("✗ acc_gui.py not found!")

    print()
    print("="*60)
    print("Conversion complete!")
    print("="*60)
    print()
    print("Next steps:")
    print("1. Install PyQt5:")
    print("   pip uninstall PyQt6")
    print("   pip install PyQt5==5.15.9")
    print()
    print("2. Test the GUI:")
    print("   python acc_gui.py")
    print()
    print("3. Build executable:")
    print("   build_pyqt5.bat")
    print()
    print("To revert: Restore from acc_gui.py.pyqt6_backup")
    print("="*60)

if __name__ == "__main__":
    main()
