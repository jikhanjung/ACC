"""
Test Area List Editor Dialog independently
"""

import sys
import pandas as pd
import numpy as np
from PyQt6.QtWidgets import QApplication
from acc_gui import AreaListEditorDialog

def main():
    app = QApplication(sys.argv)

    # Create sample data
    labels = ['J', 'T', 'Y', 'N', 'O', 'Q']
    n = len(labels)

    # Create random symmetric matrices
    data_sub = np.random.rand(n, n)
    data_sub = (data_sub + data_sub.T) / 2  # Make symmetric
    np.fill_diagonal(data_sub, 1.0)  # Diagonal is 1.0

    data_inc = np.random.rand(n, n)
    data_inc = (data_inc + data_inc.T) / 2  # Make symmetric
    np.fill_diagonal(data_inc, 1.0)  # Diagonal is 1.0

    sub_df = pd.DataFrame(data_sub, index=labels, columns=labels)
    inc_df = pd.DataFrame(data_inc, index=labels, columns=labels)

    print("Creating dialog...")
    dialog = AreaListEditorDialog(labels, sub_df, inc_df)

    print("Showing dialog...")
    result = dialog.exec()

    print(f"\nDialog result: {result}")

    if result:
        data = dialog.get_result()
        print(f"Modified: {data['modified']}")
        print(f"Labels: {data['labels']}")
        print(f"Sub matrix shape: {data['sub_matrix'].shape}")
        print(f"Inc matrix shape: {data['inc_matrix'].shape}")

    sys.exit(0)

if __name__ == "__main__":
    main()
