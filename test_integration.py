"""
Integration test for ACC algorithm with matrix input
Tests the complete pipeline from CSV to visualization
"""

import pandas as pd
from acc_utils import dict_matrix_from_dataframe, validate_similarity_matrix, build_acc_from_matrices


def test_sample_data():
    """Test with sample data files"""
    print("=" * 60)
    print("ACC Integration Test")
    print("=" * 60)

    # Load sample data
    print("\n1. Loading sample data...")
    sub_df = pd.read_csv("data/sample_subordinate.csv", index_col=0)
    inc_df = pd.read_csv("data/sample_inclusive.csv", index_col=0)
    print(f"   Subordinate matrix: {sub_df.shape}")
    print(f"   Inclusive matrix: {inc_df.shape}")

    # Convert to dict format
    print("\n2. Converting to dict format...")
    sub_matrix = dict_matrix_from_dataframe(sub_df)
    inc_matrix = dict_matrix_from_dataframe(inc_df)

    # Validate matrices
    print("\n3. Validating matrices...")
    valid, msg = validate_similarity_matrix(sub_matrix)
    print(f"   Subordinate: {msg}")
    if not valid:
        print("   ERROR: Validation failed!")
        return

    valid, msg = validate_similarity_matrix(inc_matrix)
    print(f"   Inclusive: {msg}")
    if not valid:
        print("   ERROR: Validation failed!")
        return

    # Run ACC algorithm (conversion happens inside)
    print("\n4. Running ACC algorithm (with automatic dendrogram conversion)...")
    result = build_acc_from_matrices(sub_matrix, inc_matrix, unit=1.0, method='average')

    # Display results (new structure with multiple clusters)
    print("\n5. Results:")
    print(f"   Total members: {result['all_members']}")
    print(f"   Number of clusters: {len(result['clusters'])}")

    print(f"\n   Cluster details:")
    for idx, cluster in enumerate(result['clusters'], 1):
        print(f"\n   Cluster {idx}:")
        print(f"      Members: {cluster['members']}")
        print(f"      Diameter: {cluster['diameter']:.4f}")
        print(f"      Theta: {cluster['theta']:.2f}°")
        print(f"      Center: {cluster['center']}")
        print(f"      Positions:")
        for member, (x, y) in sorted(cluster['points'].items()):
            print(f"         {member}: ({x:.4f}, {y:.4f})")

    print("\n" + "=" * 60)
    print("Test completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    test_sample_data()
