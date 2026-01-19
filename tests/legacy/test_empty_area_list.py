"""
Test creating area list from scratch (empty state)
"""

import pandas as pd
import numpy as np


def test_create_first_area():
    """Test creating the first area in an empty matrix"""
    print("Test 1: Creating first area from scratch")
    print("="*50)

    # Start with empty
    current_labels = []
    local_df = pd.DataFrame()
    global_df = pd.DataFrame()

    print(f"Initial state:")
    print(f"  Labels: {current_labels}")
    print(f"  Sub matrix shape: {local_df.shape}")
    print(f"  Inc matrix shape: {global_df.shape}")

    # Simulate adding first area 'J'
    text = 'J'
    current_labels.append(text)
    n = len(current_labels)

    if n == 1:
        # First area - create new 1x1 matrices
        local_df = pd.DataFrame([[1.0]], index=[text], columns=[text])
        global_df = pd.DataFrame([[1.0]], index=[text], columns=[text])

    print(f"\nAfter adding '{text}':")
    print(f"  Labels: {current_labels}")
    print(f"  Sub matrix shape: {local_df.shape}")
    print(f"  Sub matrix:\n{local_df}")

    # Verify
    assert local_df.shape == (1, 1), f"Expected (1,1), got {local_df.shape}"
    assert global_df.shape == (1, 1), f"Expected (1,1), got {global_df.shape}"
    assert local_df.loc[text, text] == 1.0, "Diagonal should be 1.0"

    print("\n✓ Test 1 passed!\n")
    return current_labels, local_df, global_df


def test_add_second_area(current_labels, local_df, global_df):
    """Test adding second area"""
    print("Test 2: Adding second area")
    print("="*50)

    print(f"Starting state:")
    print(f"  Labels: {current_labels}")
    print(f"  Sub matrix:\n{local_df}\n")

    # Add second area 'T'
    text = 'T'
    current_labels.append(text)
    n = len(current_labels)

    # Add to existing dataframes
    new_row_sub = pd.Series([0.5] * n, index=current_labels)
    new_row_sub[text] = 1.0  # Diagonal

    new_row_inc = pd.Series([0.5] * n, index=current_labels)
    new_row_inc[text] = 1.0  # Diagonal

    # Add to local matrix
    local_df = pd.concat([local_df, pd.DataFrame([new_row_sub], index=[text])])
    local_df[text] = new_row_sub

    # Add to global matrix
    global_df = pd.concat([global_df, pd.DataFrame([new_row_inc], index=[text])])
    global_df[text] = new_row_inc

    print(f"After adding '{text}':")
    print(f"  Labels: {current_labels}")
    print(f"  Sub matrix:\n{local_df}")

    # Verify
    assert local_df.shape == (2, 2), f"Expected (2,2), got {local_df.shape}"
    assert global_df.shape == (2, 2), f"Expected (2,2), got {global_df.shape}"
    assert local_df.loc[text, text] == 1.0, "Diagonal should be 1.0"
    assert local_df.loc['J', 'T'] == 0.5, "Off-diagonal default should be 0.5"
    assert local_df.loc['T', 'J'] == 0.5, "Matrix should be symmetric"

    # Check symmetry
    assert np.allclose(local_df.values, local_df.values.T), "Matrix should be symmetric"

    print("\n✓ Test 2 passed!\n")
    return current_labels, local_df, global_df


def test_add_multiple_areas(current_labels, local_df, global_df):
    """Test adding multiple areas"""
    print("Test 3: Adding multiple areas (Y, N, O)")
    print("="*50)

    print(f"Starting state: {len(current_labels)} areas")

    new_areas = ['Y', 'N', 'O']
    for text in new_areas:
        current_labels.append(text)
        n = len(current_labels)

        new_row_sub = pd.Series([0.5] * n, index=current_labels)
        new_row_sub[text] = 1.0

        new_row_inc = pd.Series([0.5] * n, index=current_labels)
        new_row_inc[text] = 1.0

        local_df = pd.concat([local_df, pd.DataFrame([new_row_sub], index=[text])])
        local_df[text] = new_row_sub

        global_df = pd.concat([global_df, pd.DataFrame([new_row_inc], index=[text])])
        global_df[text] = new_row_inc

        print(f"  Added '{text}' - now {n} areas")

    print(f"\nFinal state:")
    print(f"  Labels: {current_labels}")
    print(f"  Sub matrix shape: {local_df.shape}")
    print(f"  Sub matrix:\n{local_df}")

    # Verify
    assert local_df.shape == (5, 5), f"Expected (5,5), got {local_df.shape}"
    assert len(current_labels) == 5, f"Expected 5 labels, got {len(current_labels)}"

    # Check all diagonals are 1.0
    for label in current_labels:
        assert local_df.loc[label, label] == 1.0, f"Diagonal for {label} should be 1.0"

    # Check symmetry
    assert np.allclose(local_df.values, local_df.values.T), "Matrix should be symmetric"

    print("\n✓ Test 3 passed!\n")
    return current_labels, local_df, global_df


if __name__ == "__main__":
    print("Testing Area List Creation from Scratch")
    print("="*50 + "\n")

    # Test creating from empty
    labels, local_df, global_df = test_create_first_area()

    # Test adding second area
    labels, local_df, global_df = test_add_second_area(labels, local_df, global_df)

    # Test adding multiple areas
    labels, local_df, global_df = test_add_multiple_areas(labels, local_df, global_df)

    print("="*50)
    print("All tests passed! ✓")
    print("\nFinal matrix is ready for clustering:")
    print(f"  {len(labels)} areas: {', '.join(labels)}")
    print(f"  Matrix size: {local_df.shape[0]}×{local_df.shape[1]}")
