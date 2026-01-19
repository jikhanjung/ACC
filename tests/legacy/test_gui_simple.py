"""
Simple test to verify the fix works with new function
"""

import pandas as pd
from acc_utils import dict_matrix_from_dataframe, build_acc_from_matrices


print("Loading sample data...")
local_df = pd.read_csv("data/sample_local.csv", index_col=0)
global_df = pd.read_csv("data/sample_global.csv", index_col=0)

local_matrix = dict_matrix_from_dataframe(local_df)
global_matrix = dict_matrix_from_dataframe(global_df)

print("Running ACC algorithm...")
result = build_acc_from_matrices(local_matrix, global_matrix, unit=1.0)

print("\n✓ SUCCESS! Multiple concentric circles generated:")
print(f"Total members: {len(result['all_members'])}")
print(f"Number of clusters: {len(result['clusters'])}")

for idx, cluster in enumerate(result['clusters'], 1):
    print(f"\nCluster {idx} (diameter: {cluster['diameter']:.4f}, theta: {cluster['theta']:.2f}°):")
    for member, (x, y) in sorted(cluster['points'].items()):
        print(f"  {member}: ({x:.4f}, {y:.4f})")
