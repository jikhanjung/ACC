"""
Test step-by-step dendrogram visualization
"""

import matplotlib.pyplot as plt
import pandas as pd
from scipy.cluster.hierarchy import dendrogram, linkage
from scipy.spatial.distance import squareform
import numpy as np

# Load sample data
df = pd.read_csv("data/sample_subordinate.csv", index_col=0)
print(f"Loaded matrix: {df.shape}")
print(f"Labels: {df.index.tolist()}")

# Convert to distance
sim_array = df.values
max_sim = np.max(sim_array)
distance_matrix = max_sim - sim_array
condensed_dist = squareform(distance_matrix, checks=False)

# Perform clustering
linkage_matrix = linkage(condensed_dist, method='average')
print(f"\nLinkage matrix shape: {linkage_matrix.shape}")
print(f"Number of merges: {len(linkage_matrix)}")

# Test coloring for different steps
n = len(df)
print(f"\nNumber of original items: {n}")
print(f"Cluster IDs: {n} to {2*n-2}")

for step in [1, 2, 3]:
    print(f"\n=== Testing Step {step} ===")

    def link_color_func(k):
        cluster_step = k - n + 1
        if cluster_step <= step:
            return 'blue'
        else:
            return 'lightgray'

    # Check which clusters would be colored
    for i in range(len(linkage_matrix)):
        cluster_id = n + i
        cluster_step = cluster_id - n + 1
        color = link_color_func(cluster_id)
        print(f"  Cluster {cluster_id} (step {cluster_step}): {color}")

print("\n=== Creating test plot ===")

# Create figure with subplots for different steps
fig, axes = plt.subplots(2, 2, figsize=(12, 10))
axes = axes.flatten()

for idx, step in enumerate([0, 1, 2, 5]):
    ax = axes[idx]

    if step == 0:
        ax.text(0.5, 0.5, 'Original Matrix\n(No clustering)',
               ha='center', va='center', fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')
        ax.set_title('Step 0')
    else:
        def link_color_func(k):
            cluster_step = k - n + 1
            if cluster_step <= step:
                return 'blue'
            else:
                return 'lightgray'

        dendrogram(
            linkage_matrix,
            labels=df.index.tolist(),
            ax=ax,
            orientation='right',
            link_color_func=link_color_func,
            leaf_font_size=8
        )

        # Add vertical line
        if step <= len(linkage_matrix):
            current_height = linkage_matrix[step - 1, 2]
            ax.axvline(x=current_height, color='red', linestyle='--',
                      linewidth=2, alpha=0.7)

        ax.set_title(f'Step {step}')
        ax.set_xlabel('Distance', fontsize=8)

plt.tight_layout()
plt.savefig('test_step_dendro.png', dpi=100)
print("\nSaved test plot to test_step_dendro.png")
print("Check if blue lines show completed steps and gray lines show future steps")
