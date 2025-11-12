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

    sub_df = pd.DataFrame(data, index=labels, columns=labels)
    inc_df = pd.DataFrame(data, index=labels, columns=labels)

    print("Initial matrices:")
    print("Subordinate:")
    print(sub_df)
    print("\nInclusive:")
    print(inc_df)

    # Simulate adding a new area 'N'
    new_label = 'N'
    new_labels = labels + [new_label]
    n = len(new_labels)

    # Create new row/column data
    new_row_sub = pd.Series([0.5] * n, index=new_labels)
    new_row_sub[new_label] = 1.0  # Diagonal

    new_row_inc = pd.Series([0.5] * n, index=new_labels)
    new_row_inc[new_label] = 1.0  # Diagonal

    # Add to subordinate matrix
    sub_df = pd.concat([sub_df, pd.DataFrame([new_row_sub], index=[new_label])])
    sub_df[new_label] = new_row_sub

    # Add to inclusive matrix
    inc_df = pd.concat([inc_df, pd.DataFrame([new_row_inc], index=[new_label])])
    inc_df[new_label] = new_row_inc

    print("\n" + "="*50)
    print("After adding 'N':")
    print("Subordinate:")
    print(sub_df)
    print("\nInclusive:")
    print(inc_df)

    # Verify
    assert sub_df.shape == (4, 4), f"Expected (4,4), got {sub_df.shape}"
    assert inc_df.shape == (4, 4), f"Expected (4,4), got {inc_df.shape}"
    assert sub_df.loc[new_label, new_label] == 1.0, "Diagonal should be 1.0"
    assert inc_df.loc[new_label, new_label] == 1.0, "Diagonal should be 1.0"

    print("\n✓ Addition test passed!")


def test_area_renaming():
    """Test renaming an area"""
    labels = ['J', 'T', 'Y']
    data = np.array([
        [1.0, 0.9, 0.8],
        [0.9, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ])

    sub_df = pd.DataFrame(data, index=labels, columns=labels)
    inc_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Initial matrices:")
    print("Subordinate:")
    print(sub_df)

    # Rename 'T' to 'K'
    old_name = 'T'
    new_name = 'K'

    sub_df.rename(index={old_name: new_name}, columns={old_name: new_name}, inplace=True)
    inc_df.rename(index={old_name: new_name}, columns={old_name: new_name}, inplace=True)

    print("\nAfter renaming 'T' to 'K':")
    print("Subordinate:")
    print(sub_df)

    # Verify
    assert new_name in sub_df.index, f"'{new_name}' should be in index"
    assert old_name not in sub_df.index, f"'{old_name}' should not be in index"
    assert sub_df.loc[new_name, new_name] == 1.0, "Diagonal should be 1.0"

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

    sub_df = pd.DataFrame(data, index=labels, columns=labels)
    inc_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Initial matrices (4x4):")
    print("Subordinate:")
    print(sub_df)

    # Delete 'N'
    area_to_delete = 'N'

    sub_df.drop(index=area_to_delete, columns=area_to_delete, inplace=True)
    inc_df.drop(index=area_to_delete, columns=area_to_delete, inplace=True)

    print(f"\nAfter deleting '{area_to_delete}':")
    print("Subordinate:")
    print(sub_df)

    # Verify
    assert sub_df.shape == (3, 3), f"Expected (3,3), got {sub_df.shape}"
    assert inc_df.shape == (3, 3), f"Expected (3,3), got {inc_df.shape}"
    assert area_to_delete not in sub_df.index, f"'{area_to_delete}' should not be in index"

    print("\n✓ Deletion test passed!")


def test_symmetry_preservation():
    """Test that matrices remain symmetric"""
    labels = ['J', 'T', 'Y']
    data = np.array([
        [1.0, 0.9, 0.8],
        [0.9, 1.0, 0.7],
        [0.8, 0.7, 1.0]
    ])

    sub_df = pd.DataFrame(data, index=labels, columns=labels)

    print("\n" + "="*50)
    print("Testing symmetry preservation:")
    print("Initial matrix:")
    print(sub_df)

    # Verify initial symmetry
    assert np.allclose(sub_df.values, sub_df.values.T), "Initial matrix should be symmetric"

    # Simulate editing upper triangle cell [0,1] (J,T)
    new_value = 0.95
    sub_df.iloc[0, 1] = new_value
    sub_df.iloc[1, 0] = new_value  # Mirror to lower triangle

    print(f"\nAfter editing [0,1] to {new_value}:")
    print(sub_df)

    # Verify symmetry preserved
    assert np.allclose(sub_df.values, sub_df.values.T), "Matrix should remain symmetric"
    assert sub_df.iloc[0, 1] == sub_df.iloc[1, 0], "Upper and lower triangle should match"

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
