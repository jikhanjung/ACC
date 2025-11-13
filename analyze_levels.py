"""
Analyze dendrogram levels and calculate radius for each level
"""

import pandas as pd
import numpy as np

# Load data
sub_df = pd.read_csv('/mnt/d/projects/ACC/data/sample_subordinate.csv', index_col=0)
inc_df = pd.read_csv('/mnt/d/projects/ACC/data/sample_inclusive.csv', index_col=0)

# Convert to dict for easier access
sub_matrix = {}
inc_matrix = {}

for i in sub_df.index:
    sub_matrix[i] = {}
    inc_matrix[i] = {}
    for j in sub_df.columns:
        if i != j:
            sub_matrix[i][j] = sub_df.loc[i, j]
            inc_matrix[i][j] = inc_df.loc[i, j]

print("=" * 80)
print("HIERARCHICAL CLUSTERING ANALYSIS (Average Linkage)")
print("=" * 80)
print()

# Track clusters and their similarities
clusters = {area: {'members': {area}, 'level': 0, 'sub_sim': 1.0, 'inc_sim': 1.0}
            for area in sub_df.index}

def get_similarity(matrix, area1, area2):
    """Get similarity between two areas"""
    if area1 == area2:
        return 1.0
    try:
        return matrix[area1][area2]
    except:
        return matrix[area2][area1]

def linkage_similarity(matrix, cluster1_members, cluster2_members):
    """Calculate average linkage similarity between two clusters"""
    sims = []
    for m1 in cluster1_members:
        for m2 in cluster2_members:
            sim = get_similarity(matrix, m1, m2)
            sims.append(sim)
    return np.mean(sims) if sims else 0.0

def find_best_merge(clusters, matrix):
    """Find the pair of clusters with highest similarity"""
    best_sim = -1
    best_pair = None

    cluster_ids = list(clusters.keys())
    for i in range(len(cluster_ids)):
        for j in range(i+1, len(cluster_ids)):
            c1_id = cluster_ids[i]
            c2_id = cluster_ids[j]
            c1_members = clusters[c1_id]['members']
            c2_members = clusters[c2_id]['members']

            sim = linkage_similarity(matrix, c1_members, c2_members)

            if sim > best_sim:
                best_sim = sim
                best_pair = (c1_id, c2_id, sim)

    return best_pair

# Perform hierarchical clustering
level = 1
merge_history = []

while len(clusters) > 1:
    # Find best merge based on subordinate similarity
    c1_id, c2_id, sub_sim = find_best_merge(clusters, sub_matrix)

    # Calculate inclusive similarity for this merge
    c1_members = clusters[c1_id]['members']
    c2_members = clusters[c2_id]['members']
    inc_sim = linkage_similarity(inc_matrix, c1_members, c2_members)

    # Create merged cluster ID
    merged_id = f"[{c1_id}, {c2_id}]"
    merged_members = c1_members | c2_members

    # Calculate radius and diameter
    diameter = 1.0 / inc_sim if inc_sim > 0 else 999
    radius = diameter / 2.0

    # Calculate angle
    angle = 180.0 * (1.0 - sub_sim)

    print(f"LEVEL {level}: Merge {c1_id} + {c2_id}")
    print(f"  Members: {sorted(merged_members)}")
    print(f"  Subordinate similarity (for angle): {sub_sim:.3f}")
    print(f"  Inclusive similarity (for radius): {inc_sim:.3f}")
    print(f"  Diameter = 1 / {inc_sim:.3f} = {diameter:.3f}")
    print(f"  Radius = {diameter:.3f} / 2 = {radius:.3f}")
    print(f"  Angle = 180° × (1 - {sub_sim:.3f}) = {angle:.1f}°")
    print()

    # Store merge info
    merge_history.append({
        'level': level,
        'cluster1': c1_id,
        'cluster2': c2_id,
        'members': sorted(merged_members),
        'sub_sim': sub_sim,
        'inc_sim': inc_sim,
        'diameter': diameter,
        'radius': radius,
        'angle': angle
    })

    # Update clusters
    del clusters[c1_id]
    del clusters[c2_id]
    clusters[merged_id] = {
        'members': merged_members,
        'level': level,
        'sub_sim': sub_sim,
        'inc_sim': inc_sim
    }

    level += 1

print("=" * 80)
print("CONCENTRIC CIRCLES SUMMARY")
print("=" * 80)
print()

# Sort by radius (innermost to outermost)
merge_history_sorted = sorted(merge_history, key=lambda x: x['radius'])

for i, merge in enumerate(merge_history_sorted, 1):
    print(f"Circle {i}: radius = {merge['radius']:.3f}")
    print(f"  Level: {merge['level']}")
    print(f"  Members: {merge['members']}")
    print(f"  Structure: {merge['cluster1']} + {merge['cluster2']}")
    print(f"  Inc similarity: {merge['inc_sim']:.3f}")
    print()

print("=" * 80)
print("KEY INSIGHT")
print("=" * 80)
print()
print("Each merge level creates a NEW concentric circle.")
print("Total levels:", len(merge_history))
print("Total concentric circles needed:", len(merge_history))
print()
print("Current algorithm problem:")
print("  - Calculates radius for each POINT individually")
print("  - Should calculate radius for each MERGE LEVEL")
print()
