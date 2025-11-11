"""
Simple test to verify the fix works with new function
"""

import pandas as pd
from acc_utils import dict_matrix_from_dataframe, build_acc_from_matrices


print("Loading sample data...")
sub_df = pd.read_csv("data/sample_subordinate.csv", index_col=0)
inc_df = pd.read_csv("data/sample_inclusive.csv", index_col=0)

sub_matrix = dict_matrix_from_dataframe(sub_df)
inc_matrix = dict_matrix_from_dataframe(inc_df)

print("Running ACC algorithm...")
result = build_acc_from_matrices(sub_matrix, inc_matrix, unit=1.0)

print("\n✓ SUCCESS! Points are properly distributed:")
for member, (x, y) in sorted(result['points'].items()):
    print(f"  {member}: ({x:.4f}, {y:.4f})")

print(f"\nDiameter: {result['diameter']:.4f}")
print(f"Theta: {result['theta']:.2f}°")
print(f"Total members: {len(result['members'])}")
