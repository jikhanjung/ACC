"""
ACC2 Algorithm Implementation

ACC2 maps dendrogram onto concentric circles with explicit hierarchy lines.

Key differences from ACC1:
1. Circle size: diameter = 1 + (1 - similarity)
2. All areas at r=0.5, angles from ACC1 final positions
3. Explicit hierarchy lines: radial lines + arcs
"""

import math
import numpy as np
from acc_core_new import build_acc_iterative, cart2pol, pol2cart


# ------------------------------------------------------------
# Phase 1: Dendrogram Analysis and Concentric Circle Creation
# ------------------------------------------------------------

def analyze_dendrogram_levels(sub_matrix, inc_matrix):
    """
    Analyze dendrogram and extract all merge levels

    Performs hierarchical clustering (average linkage) and calculates
    radius for each merge level using ACC2 formula: diameter = 1 + (1 - inc_sim)

    Args:
        sub_matrix: dict of dict, subordinate similarity matrix
        inc_matrix: dict of dict, inclusive similarity matrix

    Returns:
        levels: list of dicts, each containing:
            - level: int, merge order (1, 2, 3, ...)
            - cluster1: str or list, first child
            - cluster2: str or list, second child
            - members: set, all members in merged cluster
            - structure: list, nested structure
            - sub_sim: float, subordinate similarity
            - inc_sim: float, inclusive similarity
            - diameter: float, 1 + (1 - inc_sim)
            - radius: float, diameter / 2
    """
    # Initialize clusters (each area is a cluster)
    all_areas = set(sub_matrix.keys())
    clusters = {area: {'members': {area}, 'level': 0} for area in all_areas}

    levels = []
    level = 1

    def get_similarity(matrix, area1, area2):
        """Get similarity between two areas"""
        if area1 == area2:
            return 1.0
        try:
            return matrix[area1][area2]
        except:
            try:
                return matrix[area2][area1]
            except:
                return 0.0

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
    while len(clusters) > 1:
        # Find best merge based on subordinate similarity
        c1_id, c2_id, sub_sim = find_best_merge(clusters, sub_matrix)

        # Calculate inclusive similarity for this merge
        c1_members = clusters[c1_id]['members']
        c2_members = clusters[c2_id]['members']
        inc_sim = linkage_similarity(inc_matrix, c1_members, c2_members)

        # Create merged cluster ID and members
        merged_members = c1_members | c2_members

        # Calculate diameter and radius using ACC2 formula
        diameter = 1.0 + (1.0 - inc_sim)
        radius = diameter / 2.0

        # Store level info
        level_info = {
            'level': level,
            'cluster1': c1_id,
            'cluster2': c2_id,
            'members': sorted(merged_members),
            'structure': [c1_id, c2_id],
            'sub_sim': sub_sim,
            'inc_sim': inc_sim,
            'diameter': diameter,
            'radius': radius
        }
        levels.append(level_info)

        # Create merged cluster ID
        merged_id = f"[{c1_id}, {c2_id}]"

        # Update clusters
        del clusters[c1_id]
        del clusters[c2_id]
        clusters[merged_id] = {
            'members': merged_members,
            'level': level
        }

        level += 1

    return levels


# ------------------------------------------------------------
# Phase 2: Area Final Angle Calculation (Reuse ACC1)
# ------------------------------------------------------------

def calculate_final_positions(sub_matrix, inc_matrix, unit=1.0):
    """
    Run ACC1 algorithm to get final angle for each area

    Args:
        sub_matrix: dict of dict, subordinate similarity matrix
        inc_matrix: dict of dict, inclusive similarity matrix
        unit: float, unit parameter

    Returns:
        positions: dict, mapping area name to (x, y, radius, angle)
    """
    # Run ACC1 algorithm
    acc1_steps = build_acc_iterative(sub_matrix, inc_matrix, unit=unit)

    if not acc1_steps:
        return {}

    # Get final step
    final_step = acc1_steps[-1]
    final_cluster = final_step['clusters'][0]

    # Extract positions and calculate angles
    positions = {}
    for member, (x, y) in final_cluster['points'].items():
        # Calculate angle using cart2pol
        _, angle = cart2pol(x, y)

        # For ACC2, all areas are at r=0.5
        positions[member] = {
            'x': x,
            'y': y,
            'radius': 0.5,
            'angle': angle
        }

    return positions


# ------------------------------------------------------------
# Phase 3: Merge Point Position Calculation
# ------------------------------------------------------------

def calculate_merge_points(levels, final_positions):
    """
    Calculate merge point position for each level

    Merge point is at the midpoint (angle-wise) of the arc connecting two children

    Args:
        levels: list from analyze_dendrogram_levels
        final_positions: dict from calculate_final_positions

    Returns:
        merge_points: dict, mapping cluster_id to merge point info
            {
                'cluster_id': {
                    'radius': float,
                    'angle': float,  # midpoint of children angles
                    'children': [child1_id, child2_id],
                    'level': int
                }
            }
    """
    merge_points = {}

    for level_info in levels:
        cluster1 = level_info['cluster1']
        cluster2 = level_info['cluster2']
        merge_radius = level_info['radius']
        level = level_info['level']

        # Get angles of children
        # Child can be an area (in final_positions) or a cluster (in merge_points)
        def get_child_angle(child_id):
            if child_id in final_positions:
                # It's an area
                return final_positions[child_id]['angle']
            elif child_id in merge_points:
                # It's a cluster
                return merge_points[child_id]['angle']
            else:
                raise ValueError(f"Child {child_id} not found in positions or merge_points")

        angle1 = get_child_angle(cluster1)
        angle2 = get_child_angle(cluster2)

        # Merge point is at the midpoint of the two children angles
        merge_angle = (angle1 + angle2) / 2.0

        # Create cluster ID
        cluster_id = f"[{cluster1}, {cluster2}]"

        merge_points[cluster_id] = {
            'radius': merge_radius,
            'angle': merge_angle,
            'children': [cluster1, cluster2],
            'level': level
        }

    return merge_points


# ------------------------------------------------------------
# Phase 4: Connection Line Generation
# ------------------------------------------------------------

def generate_connection_lines(levels, final_positions, merge_points):
    """
    Generate radial lines and arcs for hierarchy visualization

    Args:
        levels: list from analyze_dendrogram_levels
        final_positions: dict from calculate_final_positions
        merge_points: dict from calculate_merge_points

    Returns:
        lines: list of dicts, each containing:
            - type: 'radial' or 'arc'
            - for radial: 'from' (r1, angle), 'to' (r2, angle)
            - for arc: 'radius', 'angle_start', 'angle_end'
    """
    lines = []

    for level_info in levels:
        cluster1 = level_info['cluster1']
        cluster2 = level_info['cluster2']
        merge_radius = level_info['radius']

        # Get child info (radius and angle)
        def get_child_info(child_id):
            if child_id in final_positions:
                # It's an area at r=0.5
                return (0.5, final_positions[child_id]['angle'])
            elif child_id in merge_points:
                # It's a cluster at its merge radius
                mp = merge_points[child_id]
                return (mp['radius'], mp['angle'])
            else:
                raise ValueError(f"Child {child_id} not found")

        r1, angle1 = get_child_info(cluster1)
        r2, angle2 = get_child_info(cluster2)

        # Radial line from child1 to merge radius
        lines.append({
            'type': 'radial',
            'from': (r1, angle1),
            'to': (merge_radius, angle1)
        })

        # Radial line from child2 to merge radius
        lines.append({
            'type': 'radial',
            'from': (r2, angle2),
            'to': (merge_radius, angle2)
        })

        # Arc connecting the two radial lines at merge radius
        lines.append({
            'type': 'arc',
            'radius': merge_radius,
            'angle_start': min(angle1, angle2),
            'angle_end': max(angle1, angle2)
        })

    return lines


# ------------------------------------------------------------
# Main ACC2 Algorithm
# ------------------------------------------------------------

def build_acc2(sub_matrix, inc_matrix, unit=1.0):
    """
    Build ACC2 visualization data

    Args:
        sub_matrix: dict of dict, subordinate similarity matrix
        inc_matrix: dict of dict, inclusive similarity matrix
        unit: float, unit parameter (default 1.0)

    Returns:
        acc2_data: dict containing:
            - levels: list of merge levels
            - positions: dict of area positions (all at r=0.5)
            - merge_points: dict of merge point positions
            - lines: list of connection lines (radial + arc)
            - circles: list of circle radii to draw
    """
    # Phase 1: Analyze dendrogram
    levels = analyze_dendrogram_levels(sub_matrix, inc_matrix)

    # Phase 2: Calculate final positions (from ACC1)
    positions = calculate_final_positions(sub_matrix, inc_matrix, unit)

    # Phase 3: Calculate merge points
    merge_points = calculate_merge_points(levels, positions)

    # Phase 4: Generate connection lines
    lines = generate_connection_lines(levels, positions, merge_points)

    # Collect all circle radii
    circles = [0.5]  # Area circle (innermost)
    for level_info in levels:
        circles.append(level_info['radius'])

    return {
        'levels': levels,
        'positions': positions,
        'merge_points': merge_points,
        'lines': lines,
        'circles': sorted(set(circles))  # Unique, sorted
    }


# ------------------------------------------------------------
# Helper function for matrix conversion
# ------------------------------------------------------------

def dict_matrix_from_dataframe(df):
    """Convert pandas DataFrame to dict matrix"""
    matrix = {}
    for i in df.index:
        matrix[i] = {}
        for j in df.columns:
            if i != j:
                matrix[i][j] = df.loc[i, j]
    return matrix


if __name__ == "__main__":
    # Test with sample data
    import pandas as pd

    # Load sample data
    sub_df = pd.read_csv('data/sample_subordinate.csv', index_col=0)
    inc_df = pd.read_csv('data/sample_inclusive.csv', index_col=0)

    sub_matrix = dict_matrix_from_dataframe(sub_df)
    inc_matrix = dict_matrix_from_dataframe(inc_df)

    # Build ACC2
    acc2_data = build_acc2(sub_matrix, inc_matrix)

    print("=" * 70)
    print("ACC2 Data Summary")
    print("=" * 70)
    print(f"\nNumber of levels: {len(acc2_data['levels'])}")
    print(f"Number of circles: {len(acc2_data['circles'])}")
    print(f"Number of areas: {len(acc2_data['positions'])}")
    print(f"Number of merge points: {len(acc2_data['merge_points'])}")
    print(f"Number of connection lines: {len(acc2_data['lines'])}")

    print("\n" + "=" * 70)
    print("Circles (radii)")
    print("=" * 70)
    for i, r in enumerate(acc2_data['circles'], 1):
        print(f"Circle {i}: r = {r:.3f}")

    print("\n" + "=" * 70)
    print("Area Positions (all at r=0.5)")
    print("=" * 70)
    for area, pos in sorted(acc2_data['positions'].items()):
        print(f"{area}: angle = {pos['angle']:.1f}°")

    print("\n" + "=" * 70)
    print("Merge Levels")
    print("=" * 70)
    for level in acc2_data['levels']:
        print(f"\nLevel {level['level']}: {level['cluster1']} + {level['cluster2']}")
        print(f"  Inc similarity: {level['inc_sim']:.3f}")
        print(f"  Diameter: {level['diameter']:.3f}")
        print(f"  Radius: {level['radius']:.3f}")
