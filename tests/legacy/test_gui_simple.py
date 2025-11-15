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

print("\n✓ SUCCESS! Multiple concentric circles generated:")
print(f"Total members: {len(result['all_members'])}")
print(f"Number of clusters: {len(result['clusters'])}")

for idx, cluster in enumerate(result['clusters'], 1):
    print(f"\nCluster {idx} (diameter: {cluster['diameter']:.4f}, theta: {cluster['theta']:.2f}°):")
    for member, (x, y) in sorted(cluster['points'].items()):
        print(f"  {member}: ({x:.4f}, {y:.4f})")
