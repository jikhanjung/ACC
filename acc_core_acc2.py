"""
ACC2 Algorithm Implementation

ACC2 maps dendrogram onto concentric circles with explicit hierarchy lines.

Key differences from ACC1:
1. Circle size: diameter = 1 + (1 - similarity)
2. All areas at r=0.5, angles from ACC1 final positions
3. Explicit hierarchy lines: radial lines + arcs
"""

import numpy as np

import math
from acc_core_new import build_acc_iterative, cart2pol, pol2cart


def compass_angle(x, y):
    """Calculate compass-style angle where 0° = north, positive = clockwise (east)"""
    return math.degrees(math.atan2(x, y))

# ------------------------------------------------------------
# Phase 1: Dendrogram Analysis and Concentric Circle Creation
# ------------------------------------------------------------


def analyze_dendrogram_levels(local_matrix, global_matrix):
    """
    Analyze dendrogram and extract all merge levels

    Performs hierarchical clustering (average linkage) and calculates
    radius for each merge level using ACC2 formula: diameter = 1 + (1 - global_sim)

    Args:
        local_matrix: dict of dict, local similarity matrix
        global_matrix: dict of dict, global similarity matrix

    Returns:
        levels: list of dicts, each containing:
            - level: int, merge order (1, 2, 3, ...)
            - cluster1: str or list, first child
            - cluster2: str or list, second child
            - members: set, all members in merged cluster
            - structure: list, nested structure
            - local_sim: float, local similarity
            - global_sim: float, global similarity
            - diameter: float, 1 + (1 - global_sim)
            - radius: float, diameter / 2
    """
    # Initialize clusters (each area is a cluster)
    all_areas = set(local_matrix.keys())
    clusters = {area: {"members": {area}, "level": 0} for area in all_areas}

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
            for j in range(i + 1, len(cluster_ids)):
                c1_id = cluster_ids[i]
                c2_id = cluster_ids[j]
                c1_members = clusters[c1_id]["members"]
                c2_members = clusters[c2_id]["members"]

                sim = linkage_similarity(matrix, c1_members, c2_members)

                if sim > best_sim:
                    best_sim = sim
                    best_pair = (c1_id, c2_id, sim)

        return best_pair

    # Perform hierarchical clustering
    while len(clusters) > 1:
        # Find best merge based on local similarity
        c1_id, c2_id, local_sim = find_best_merge(clusters, local_matrix)

        # Calculate global similarity for this merge
        c1_members = clusters[c1_id]["members"]
        c2_members = clusters[c2_id]["members"]
        global_sim = linkage_similarity(global_matrix, c1_members, c2_members)

        # Create merged cluster ID and members
        merged_members = c1_members | c2_members

        # Calculate diameter and radius using ACC2 formula
        diameter = 1.0 + (1.0 - global_sim)
        radius = diameter / 2.0

        # Store level info
        level_info = {
            "level": level,
            "cluster1": c1_id,
            "cluster2": c2_id,
            "members": sorted(merged_members),
            "structure": [c1_id, c2_id],
            "local_sim": local_sim,
            "global_sim": global_sim,
            "diameter": diameter,
            "radius": radius,
        }
        levels.append(level_info)

        # Create merged cluster ID
        merged_id = f"[{c1_id}, {c2_id}]"

        # Update clusters
        del clusters[c1_id]
        del clusters[c2_id]
        clusters[merged_id] = {"members": merged_members, "level": level}

        level += 1

    return levels


# ------------------------------------------------------------
# Phase 2: Area Final Angle Calculation (Reuse ACC1)
# ------------------------------------------------------------


def calculate_final_positions(local_matrix, global_matrix, unit=1.0):
    """
    Run ACC1 algorithm to get final angle for each area

    Args:
        local_matrix: dict of dict, local similarity matrix
        global_matrix: dict of dict, global similarity matrix
        unit: float, unit parameter

    Returns:
        positions: dict, mapping area name to (x, y, radius, angle)
    """
    # Run ACC1 algorithm
    acc1_steps = build_acc_iterative(local_matrix, global_matrix, unit=unit)

    if not acc1_steps:
        return {}

    # Get final step
    final_step = acc1_steps[-1]
    final_cluster = final_step["clusters"][0]

    # Extract positions and calculate angles
    positions = {}
    for member, (x, y) in final_cluster["points"].items():
        # Calculate angle using compass style (0° = north, positive = clockwise)
        angle = compass_angle(x, y)

        # For ACC2, all areas are at r=0.5
        positions[member] = {"x": x, "y": y, "radius": 0.5, "angle": angle}

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
        cluster1 = level_info["cluster1"]
        cluster2 = level_info["cluster2"]
        merge_radius = level_info["radius"]
        level = level_info["level"]

        # Get angles of children
        # Child can be an area (in final_positions) or a cluster (in merge_points)
        def get_child_angle(child_id):
            if child_id in final_positions:
                # It's an area
                return final_positions[child_id]["angle"]
            if child_id in merge_points:
                # It's a cluster
                return merge_points[child_id]["angle"]
            raise ValueError(f"Child {child_id} not found in positions or merge_points")

        angle1 = get_child_angle(cluster1)
        angle2 = get_child_angle(cluster2)

        # Merge point is at the midpoint of the two children angles (handling wrap-around)
        diff = angle2 - angle1
        # Normalize difference to [-180, 180]
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360
        # Midpoint is halfway along the shorter arc
        merge_angle = angle1 + diff / 2.0
        # Normalize the result to [-180, 180]
        while merge_angle > 180:
            merge_angle -= 360
        while merge_angle < -180:
            merge_angle += 360

        # Create cluster ID
        cluster_id = f"[{cluster1}, {cluster2}]"

        merge_points[cluster_id] = {
            "radius": merge_radius,
            "angle": merge_angle,
            "children": [cluster1, cluster2],
            "level": level,
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
        cluster1 = level_info["cluster1"]
        cluster2 = level_info["cluster2"]
        merge_radius = level_info["radius"]

        # Get child info (radius and angle)
        def get_child_info(child_id):
            if child_id in final_positions:
                # It's an area - use its actual radius (may not be 0.5 in ACC1 style)
                pos = final_positions[child_id]
                return (pos["radius"], pos["angle"])
            if child_id in merge_points:
                # It's a cluster at its merge radius
                mp = merge_points[child_id]
                return (mp["radius"], mp["angle"])
            raise ValueError(f"Child {child_id} not found")

        r1, angle1 = get_child_info(cluster1)
        r2, angle2 = get_child_info(cluster2)

        # Radial line from child1 to merge radius
        lines.append({"type": "radial", "from": (r1, angle1), "to": (merge_radius, angle1)})

        # Radial line from child2 to merge radius
        lines.append({"type": "radial", "from": (r2, angle2), "to": (merge_radius, angle2)})

        # Arc connecting the two radial lines at merge radius
        # Always take the shorter arc (< 180°)
        diff = angle2 - angle1
        # Normalize difference to [-180, 180]
        while diff > 180:
            diff -= 360
        while diff < -180:
            diff += 360

        # If diff is positive, angle2 is clockwise from angle1 (short path)
        # If diff is negative, angle1 is clockwise from angle2 (short path)
        if diff >= 0:
            arc_start = angle1
            arc_end = angle1 + diff  # = angle2 normalized
        else:
            arc_start = angle2
            arc_end = angle2 - diff  # = angle1 normalized

        lines.append({
            "type": "arc",
            "radius": merge_radius,
            "angle_start": arc_start,
            "angle_end": arc_end,
        })

    return lines


# ------------------------------------------------------------
# Main ACC2 Algorithm
# ------------------------------------------------------------


def build_acc2(local_matrix, global_matrix, unit=1.0, max_angle=None):
    """
    Build ACC2 visualization data

    Args:
        local_matrix: dict of dict, local similarity matrix
        global_matrix: dict of dict, global similarity matrix
        unit: float, unit parameter (default 1.0)
        max_angle: float or None, if specified, scale angles to fit within this limit

    Returns:
        acc2_data: dict containing:
            - levels: list of merge levels
            - positions: dict of area positions (all at r=0.5)
            - merge_points: dict of merge point positions
            - lines: list of connection lines (radial + arc)
            - circles: list of circle radii to draw
    """
    # Use ACC1's build_acc_iterative to get consistent hierarchical structure
    acc1_steps = build_acc_iterative(local_matrix, global_matrix, unit=unit)

    if not acc1_steps:
        return {"levels": [], "positions": {}, "merge_points": {}, "lines": [], "circles": [0.5]}

    # Get final cluster
    final_step = acc1_steps[-1]
    final_cluster = final_step["clusters"][0]

    # Extract area positions and angles from ACC1
    positions = {}
    for member, (x, y) in final_cluster["points"].items():
        # Use compass-style angle (0° = north, positive = clockwise)
        angle = compass_angle(x, y)
        positions[member] = {"x": x, "y": y, "radius": 0.5, "angle": angle}

    # Apply max angle scaling if specified
    if max_angle is not None and len(positions) > 1:
        angles = [pos["angle"] for pos in positions.values()]
        min_ang = min(angles)
        max_ang = max(angles)
        span = max_ang - min_ang

        if span > max_angle:
            # Scale all angles to fit within max_angle
            scale = max_angle / span
            center = (min_ang + max_ang) / 2.0

            for area in positions:
                old_angle = positions[area]["angle"]
                new_angle = (old_angle - center) * scale + center
                positions[area]["angle"] = new_angle

                # Update x, y based on new angle (at radius 0.5)
                # compass_angle: 0° = north, positive = clockwise
                # x = r * sin(angle), y = r * cos(angle)
                r = 0.5
                rad = math.radians(new_angle)
                positions[area]["x"] = r * math.sin(rad)
                positions[area]["y"] = r * math.cos(rad)

    # Parse the hierarchical structure to build levels and merge points
    # The structure is a dict: {'children': [left, right], 'angle': float, 'radius': float}
    structure = final_cluster.get("structure")

    levels = []
    merge_points = {}

    def get_cluster_id(node):
        """Get a string ID for a structure node"""
        if isinstance(node, str):
            return node
        elif isinstance(node, dict) and 'children' in node:
            left_id = get_cluster_id(node['children'][0])
            right_id = get_cluster_id(node['children'][1])
            return f"[{left_id}, {right_id}]"
        return str(node)

    def get_all_members(node):
        """Get all member areas from a structure node"""
        if isinstance(node, str):
            return {node}
        elif isinstance(node, dict) and 'children' in node:
            members = set()
            for child in node['children']:
                members |= get_all_members(child)
            return members
        return set()

    def get_node_angle(node):
        """Get the angle for a structure node (midpoint of children angles, handling wrap-around)"""
        if isinstance(node, str):
            return positions[node]["angle"]
        elif isinstance(node, dict) and 'children' in node:
            # Merge point angle = midpoint of children angles
            left_angle = get_node_angle(node['children'][0])
            right_angle = get_node_angle(node['children'][1])

            # Handle wrap-around: find the midpoint of the shorter arc
            diff = right_angle - left_angle
            # Normalize difference to [-180, 180]
            while diff > 180:
                diff -= 360
            while diff < -180:
                diff += 360

            # Midpoint is halfway along the shorter arc
            merge_angle = left_angle + diff / 2.0

            # Normalize the result to [-180, 180]
            while merge_angle > 180:
                merge_angle -= 360
            while merge_angle < -180:
                merge_angle += 360

            return merge_angle
        return 0.0

    def parse_structure(node, level_num):
        """Recursively parse structure to extract levels and merge points"""
        if isinstance(node, str):
            # Leaf node (single area) - no merge point to create
            return

        if isinstance(node, dict) and 'children' in node:
            left_child = node['children'][0]
            right_child = node['children'][1]

            # First, recursively process children
            parse_structure(left_child, level_num)
            parse_structure(right_child, level_num + 1 if isinstance(left_child, dict) else level_num)

            # Get cluster info
            node_angle = node.get('angle', 90.0)
            node_radius = node.get('radius', 0.5)

            # ACC2 formula: diameter = 1 + (1 - global_sim)
            # So global_sim = 1 - (diameter - 1) = 2 - diameter
            # But we use radius, so diameter = 2 * radius
            # Actually, for ACC2 we recalculate based on the angle
            # local_sim = 1 - (angle / 180)
            local_sim = 1.0 - (node_angle / 180.0)
            # For global_sim, we use the radius: radius = diameter/2 = (1 + (1-global_sim))/2
            # So 2*radius = 1 + (1-global_sim) => global_sim = 2 - 2*radius
            # But this can go negative. Let's just use a reasonable estimate.
            global_sim = max(0.1, 1.0 / (2 * node_radius)) if node_radius > 0 else 0.5

            # Get IDs
            left_id = get_cluster_id(left_child)
            right_id = get_cluster_id(right_child)
            cluster_id = f"[{left_id}, {right_id}]"

            # Get members
            members = sorted(get_all_members(node))

            # Calculate merge point angle (using get_node_angle for this node handles wrap-around)
            merge_angle = get_node_angle(node)

            # Calculate ACC2 radius: diameter = 1 + (1 - global_sim)
            acc2_diameter = 1.0 + (1.0 - global_sim)
            acc2_radius = acc2_diameter / 2.0

            # Create level info
            level_info = {
                "level": len(levels) + 1,
                "cluster1": left_id,
                "cluster2": right_id,
                "members": members,
                "local_sim": local_sim,
                "global_sim": global_sim,
                "diameter": acc2_diameter,
                "radius": acc2_radius,
            }
            levels.append(level_info)

            # Create merge point
            merge_points[cluster_id] = {
                "radius": acc2_radius,
                "angle": merge_angle,
                "children": [left_id, right_id],
                "level": len(levels),
            }

    # Parse the structure
    parse_structure(structure, 1)

    # Generate connection lines
    lines = generate_connection_lines(levels, positions, merge_points)

    # Collect all circle radii
    circles = [0.5]  # Area circle (innermost)
    for level_info in levels:
        circles.append(level_info["radius"])

    return {
        "levels": levels,
        "positions": positions,
        "merge_points": merge_points,
        "lines": lines,
        "circles": sorted(set(circles)),
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
    local_df = pd.read_csv("data/sample_local.csv", index_col=0)
    global_df = pd.read_csv("data/sample_global.csv", index_col=0)

    local_matrix = dict_matrix_from_dataframe(local_df)
    global_matrix = dict_matrix_from_dataframe(global_df)

    # Build ACC2
    acc2_data = build_acc2(local_matrix, global_matrix)

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
    for i, r in enumerate(acc2_data["circles"], 1):
        print(f"Circle {i}: r = {r:.3f}")

    print("\n" + "=" * 70)
    print("Area Positions (all at r=0.5)")
    print("=" * 70)
    for area, pos in sorted(acc2_data["positions"].items()):
        print(f"{area}: angle = {pos['angle']:.1f}°")

    print("\n" + "=" * 70)
    print("Merge Levels")
    print("=" * 70)
    for level in acc2_data["levels"]:
        print(f"\nLevel {level['level']}: {level['cluster1']} + {level['cluster2']}")
        print(f"  Global similarity: {level['global_sim']:.3f}")
        print(f"  Diameter: {level['diameter']:.3f}")
        print(f"  Radius: {level['radius']:.3f}")
