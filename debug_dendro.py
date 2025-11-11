"""
Debug script to investigate dendrogram conversion
"""

import pandas as pd
from acc_utils import matrix_to_dendrogram, dict_matrix_from_dataframe
from acc_core import build_acc, DendroNode


def print_dendro_structure(node, indent=0):
    """Recursively print dendrogram structure"""
    prefix = "  " * indent
    print(f"{prefix}Node: members={node.members}, sim={node.sim:.3f}")
    if node.left:
        print(f"{prefix}  LEFT:")
        print_dendro_structure(node.left, indent + 2)
    if node.right:
        print(f"{prefix}  RIGHT:")
        print_dendro_structure(node.right, indent + 2)


def test_original_example():
    """Test with the original example from acc_core.py"""
    print("=" * 60)
    print("Testing ORIGINAL example from acc_core.py")
    print("=" * 60)

    # Original example dendrograms
    jt = DendroNode(["J", "T"], sim=0.9)
    jty = DendroNode(["J", "T", "Y"], sim=0.8, left=jt, right=DendroNode(["Y"], sim=1.0))
    oq = DendroNode(["O", "Q"], sim=0.85)
    noq = DendroNode(["N", "O", "Q"], sim=0.75, left=DendroNode(["N"], sim=1.0), right=oq)
    sub_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.6, left=jty, right=noq)

    jt_inc = DendroNode(["J", "T"], sim=0.88)
    jy_inc = DendroNode(["J", "Y"], sim=0.82)
    jty_inc = DendroNode(["J", "T", "Y"], sim=0.78, left=jt_inc, right=jy_inc)
    oq_inc = DendroNode(["O", "Q"], sim=0.83)
    n_inc = DendroNode(["N"], sim=1.0)
    noq_inc = DendroNode(["N", "O", "Q"], sim=0.7, left=n_inc, right=oq_inc)
    inc_root = DendroNode(["J", "T", "Y", "N", "O", "Q"], sim=0.55, left=jty_inc, right=noq_inc)

    inc_matrix = {
        "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.7, "Q": 0.68, "J": 0.4},
        "O": {"Q": 0.83, "N": 0.7},
        "Q": {"O": 0.83, "N": 0.68},
    }

    print("\nOriginal Subordinate Dendrogram:")
    print_dendro_structure(sub_root)

    result = build_acc(sub_root, inc_root, inc_matrix, unit=1.0)

    print("\nOriginal Results:")
    print(f"Members: {result['members']}")
    print(f"Diameter: {result['diameter']:.4f}")
    print(f"Theta: {result['theta']:.2f}°")
    print("\nMember positions:")
    for member, (x, y) in sorted(result['points'].items()):
        print(f"  {member}: ({x:.4f}, {y:.4f})")


def test_converted_example():
    """Test with converted matrices"""
    print("\n\n" + "=" * 60)
    print("Testing CONVERTED matrices")
    print("=" * 60)

    # Load sample data
    sub_df = pd.read_csv("data/sample_subordinate.csv", index_col=0)
    inc_df = pd.read_csv("data/sample_inclusive.csv", index_col=0)

    sub_matrix = dict_matrix_from_dataframe(sub_df)
    inc_matrix = dict_matrix_from_dataframe(inc_df)

    # Convert to dendrograms
    sub_dendro, sub_labels = matrix_to_dendrogram(sub_matrix, method='average')
    inc_dendro, inc_labels = matrix_to_dendrogram(inc_matrix, method='average')

    print("\nConverted Subordinate Dendrogram:")
    print_dendro_structure(sub_dendro)

    print("\nConverted Inclusive Dendrogram:")
    print_dendro_structure(inc_dendro)

    # Run ACC
    result = build_acc(sub_dendro, inc_dendro, inc_matrix, unit=1.0)

    print("\nConverted Results:")
    print(f"Members: {result['members']}")
    print(f"Diameter: {result['diameter']:.4f}")
    print(f"Theta: {result['theta']:.2f}°")
    print("\nMember positions:")
    for member, (x, y) in sorted(result['points'].items()):
        print(f"  {member}: ({x:.4f}, {y:.4f})")


if __name__ == "__main__":
    test_original_example()
    test_converted_example()
