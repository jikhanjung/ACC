"""
Test clustering step manager
"""

import pandas as pd
import numpy as np
from clustering_steps import ClusteringStepManager


def test_clustering_steps():
    print("=" * 60)
    print("Testing Clustering Step Manager")
    print("=" * 60)

    # Load sample data
    df = pd.read_csv("data/sample_subordinate.csv", index_col=0)
    print(f"\n1. Loaded matrix: {df.shape[0]}x{df.shape[1]}")
    print(f"   Labels: {df.index.tolist()}")

    # Create step manager
    step_mgr = ClusteringStepManager(df.values, df.index.tolist())
    num_steps = step_mgr.get_num_steps()
    print(f"\n2. Number of steps: {num_steps}")

    # Display each step
    print(f"\n3. Step-by-step progression:")
    for i in range(min(num_steps, 7)):  # Show first 7 steps
        step = step_mgr.get_step(i)
        desc = step_mgr.get_step_description(i)
        print(f"\n   {desc}")
        print(f"   Matrix size: {step['matrix'].shape}")
        print(f"   Labels: {[str(l) if not isinstance(l, tuple) else '+'.join(l) for l in step['labels']]}")

        if i > 0:
            merged = step['merged_pair']
            print(f"   Merged: ({'+'.join(merged[0])}) + ({'+'.join(merged[1])})")
            print(f"   Similarity: {step.get('similarity', 0):.3f}")

    # Test partial linkage
    print(f"\n4. Testing partial linkage:")
    for step_num in [0, 1, 2, num_steps-1]:
        partial = step_mgr.get_partial_linkage(step_num)
        if partial is not None:
            print(f"   Step {step_num}: linkage shape = {partial.shape}")
        else:
            print(f"   Step {step_num}: no linkage (original matrix)")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_clustering_steps()
