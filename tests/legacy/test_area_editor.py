"""
Test script for Area List Editor functionality
"""

import pandas as pd
import numpy as np


def test_area_addition():
    """Test adding a new area to matrices"""
    # Create initial matrices
    labels = ['J', 'T', 'Y']
    data = np.array([
        [1.0, 0.9, 0.8],
        [0.9, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ])

    local_df = pd.DataFrame(data, index=labels, columns=labels)
    global_df = pd.DataFrame(data, index=labels, columns=labels)

    print("Initial matrices:")
    print("Local:")
    print(local_df)
    print("\nGlobal:")
    print(global_df)

    # Simulate adding a new area 'N'
    new_label = 'N'
    new_labels = labels + [new_label]
    n = len(new_labels)

    # Create new row/column data
    new_row_sub = pd.Series([0.5] * n, index=new_labels)
    new_row_sub[new_label] = 1.0  # Diagonal

    new_row_inc = pd.Series([0.5] * n, index=new_labels)
    new_row_inc[new_label] = 1.0  # Diagonal

    # Add to local matrix
    local_df = pd.concat([local_df, pd.DataFrame([new_row_sub], index=[new_label])])
    local_df[new_label] = new_row_sub

    # Add to global matrix
    global_df = pd.concat([global_df, pd.DataFrame([new_row_inc], index=[new_label])])
    global_df[new_label] = new_row_inc

    print("\n" + "="*50)
    print("After adding 'N':")
    print("Local:")
    print(local_df)
    print("\nGlobal:")
    print(global_df)

    # Verify
    assert local_df.shape == (4, 4), f"Expected (4,4), got {local_df.shape}"
    assert global_df.shape == (4, 4), f"Expected (4,4), got {global_df.shape}"
    assert local_df.loc[new_label, new_label] == 1.0, "Diagonal should be 1.0"
    assert global_df.loc[new_label, new_label] == 1.0, "Diagonal should be 1.0"

    print("\n✓ Addition test passed!")


def test_area_renaming():
    """Test renaming an area"""
    labels = ['J', 'T', 'Y']
    data = np.array([
        [1.0, 0.9, 0.8],
        [0.9, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ])

    local_df = pd.DataFrame(data, index=labels, columns=labels)
    global_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Initial matrices:")
    print("Local:")
    print(local_df)

    # Rename 'T' to 'K'
    old_name = 'T'
    new_name = 'K'

    local_df.rename(index={old_name: new_name}, columns={old_name: new_name}, inplace=True)
    global_df.rename(index={old_name: new_name}, columns={old_name: new_name}, inplace=True)

    print("\nAfter renaming 'T' to 'K':")
    print("Local:")
    print(local_df)

    # Verify
    assert new_name in local_df.index, f"'{new_name}' should be in index"
    assert old_name not in local_df.index, f"'{old_name}' should not be in index"
    assert local_df.loc[new_name, new_name] == 1.0, "Diagonal should be 1.0"

    print("\n✓ Renaming test passed!")


def test_area_deletion():
    """Test deleting an area"""
    labels = ['J', 'T', 'Y', 'N']
    data = np.array([
        [1.0, 0.9, 0.8, 0.4],
        [0.9, 1.0, 0.7, 0.3],
        [0.8, 0.7, 1.0, 0.35],
        [0.4, 0.3, 0.35, 1.0]
    ])

    local_df = pd.DataFrame(data, index=labels, columns=labels)
    global_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Initial matrices (4x4):")
    print("Local:")
    print(local_df)

    # Delete 'N'
    area_to_delete = 'N'

    local_df.drop(index=area_to_delete, columns=area_to_delete, inplace=True)
    global_df.drop(index=area_to_delete, columns=area_to_delete, inplace=True)

    print(f"\nAfter deleting '{area_to_delete}':")
    print("Local:")
    print(local_df)

    # Verify
    assert local_df.shape == (3, 3), f"Expected (3,3), got {local_df.shape}"
    assert global_df.shape == (3, 3), f"Expected (3,3), got {global_df.shape}"
    assert area_to_delete not in local_df.index, f"'{area_to_delete}' should not be in index"

    print("\n✓ Deletion test passed!")


def test_symmetry_preservation():
    """Test that matrices remain symmetric"""
    labels = ['J', 'T', 'Y']
    data = np.array([
        [1.0, 0.9, 0.8],
        [0.9, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ])

    local_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Testing symmetry preservation:")
    print("Initial matrix:")
    print(local_df)

    # Verify initial symmetry
    assert np.allclose(local_df.values, local_df.values.T), "Initial matrix should be symmetric"

    # Simulate editing upper triangle cell [0,1] (J,T)
    new_value = 0.95
    local_df.iloc[0, 1] = new_value
    local_df.iloc[1, 0] = new_value  # Mirror to lower triangle

    print(f"\nAfter editing [0,1] to {new_value}:")
    print(local_df)

    # Verify symmetry preserved
    assert np.allclose(local_df.values, local_df.values.T), "Matrix should remain symmetric"
    assert local_df.iloc[0, 1] == local_df.iloc[1, 0], "Upper and lower triangle should match"

    print("\n✓ Symmetry test passed!")


if __name__ == "__main__":
    print("Running Area List Editor Tests")
    print("="*50)

    test_area_addition()
    test_area_renaming()
    test_area_deletion()
    test_symmetry_preservation()

    print("\n" + "="*50)
    print("All tests passed! ✓")
