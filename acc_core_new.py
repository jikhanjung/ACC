"""
ACC Core - New implementation starting from first step
Focus on: finding the two areas with highest subordinate similarity
"""

import math
import logging
from collections import defaultdict
from itertools import combinations

# Configure logger
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('ACC_Iterative')


# ------------------------------------------------------------
# Utility functions
# ------------------------------------------------------------
def pol2cart(r, angle_deg):
    # Reference: (0,1) as 0 degrees (upward on y-axis)
    # Add 90 degrees to rotate from standard (1,0) reference
    rad = math.radians(angle_deg + 90)
    return (r * math.cos(rad), r * math.sin(rad))


def cart2pol(x, y):
    # Reference: (0,1) as 0 degrees (upward on y-axis)
    # Subtract 90 degrees to convert from standard (1,0) reference
    r = math.sqrt(x**2 + y**2)
    angle_rad = math.atan2(y, x)
    angle_deg = math.degrees(angle_rad) - 90
    return (r, angle_deg)


def cart_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


# ------------------------------------------------------------
# Step 1: Find two areas with highest local similarity
# ------------------------------------------------------------
def find_highest_similarity_pair(local_matrix):
    """
    Find the pair of areas with highest similarity in local matrix

    Args:
        local_matrix: dict of dict, e.g. {"J": {"T": 0.9, "Y": 0.8}, ...}

    Returns:
        tuple: (area1, area2, similarity)
    """
    best_pair = None
    best_sim = -1.0

    # Get all areas
    areas = list(local_matrix.keys())

    # Check all pairs
    for area1, area2 in combinations(areas, 2):
        sim = None

        # Try both directions
        if area1 in local_matrix and area2 in local_matrix[area1]:
            sim = local_matrix[area1][area2]
        elif area2 in local_matrix and area1 in local_matrix[area2]:
            sim = local_matrix[area2][area1]

        if sim is not None and sim > best_sim:
            best_sim = sim
            best_pair = (area1, area2)

    if best_pair:
        return (best_pair[0], best_pair[1], best_sim)
    else:
        return None


def get_similarity(matrix, area1, area2):
    """
    Get similarity between two areas from matrix

    Args:
        matrix: dict of dict
        area1, area2: area names

    Returns:
        float: similarity value, or None if not found
    """
    # Try both directions
    if area1 in matrix and area2 in matrix[area1]:
        return matrix[area1][area2]
    elif area2 in matrix and area1 in matrix[area2]:
        return matrix[area2][area1]
    else:
        return None


def average_pairwise_similarity(members, matrix):
    """
    Calculate average pairwise similarity for cluster members

    Args:
        members: set of member names
        matrix: similarity matrix (dict of dict)

    Returns:
        float: average similarity
    """
    ms = list(members)
    if len(ms) == 1:
        return 1.0

    total = 0.0
    cnt = 0
    for a, b in combinations(ms, 2):
        sim = get_similarity(matrix, a, b)
        if sim is not None:
            total += sim
            cnt += 1

    return total / cnt if cnt > 0 else 0.0


def format_cluster_structure(structure):
    """
    Format cluster structure for display

    Args:
        structure: nested dict/string representing hierarchical cluster structure

    Returns:
        str: formatted structure string
    """
    if isinstance(structure, str):
        return structure
    elif isinstance(structure, dict):
        # New format: {'children': [child1, child2], 'angle': float, 'radius': float}
        if 'children' in structure:
            parts = [format_cluster_structure(child) for child in structure['children']]
            return "[" + ", ".join(parts) + "]"
        else:
            return str(structure)
    elif isinstance(structure, list):
        # Legacy format: nested list
        if len(structure) == 0:
            return "[]"
        parts = [format_cluster_structure(item) for item in structure]
        return "[" + ", ".join(parts) + "]"
    else:
        return str(structure)


def position_structure_recursively(structure, parent_direction_atan2, radius_scale=1.0):
    """
    Recursively position all members in a hierarchical structure.

    Args:
        structure: hierarchical structure dict or string (area name)
            - String: single area
            - Dict: {'children': [left, right], 'angle': float, 'radius': float}
        parent_direction_atan2: direction from origin to this sub-cluster center (in atan2 convention)
            - 0° = north, positive = clockwise (east)
        radius_scale: multiplier for radius (default 1.0)

    Returns:
        dict: mapping of area names to (x, y) positions
    """
    if isinstance(structure, str):
        # Single area - position at parent direction
        angle_acc = -parent_direction_atan2  # Convert to ACC convention
        pos = pol2cart(radius_scale, angle_acc)
        return {structure: pos}

    if isinstance(structure, dict) and 'children' in structure:
        # Cluster node - has two children
        children = structure['children']
        node_angle = structure['angle']
        node_radius = structure.get('radius', radius_scale)

        half_angle = node_angle / 2.0

        # Left child at parent_direction - half_angle (counter-clockwise)
        # Right child at parent_direction + half_angle (clockwise)
        left_direction_atan2 = parent_direction_atan2 - half_angle
        right_direction_atan2 = parent_direction_atan2 + half_angle

        points = {}

        # Position left child (first in children list)
        left_child = children[0]
        if isinstance(left_child, str):
            # Single area
            left_child_radius = node_radius
        elif isinstance(left_child, dict):
            # Sub-cluster - use its stored radius
            left_child_radius = left_child.get('radius', node_radius)
        else:
            left_child_radius = node_radius

        left_points = position_structure_recursively(left_child, left_direction_atan2, left_child_radius)
        points.update(left_points)

        # Position right child (second in children list)
        right_child = children[1]
        if isinstance(right_child, str):
            right_child_radius = node_radius
        elif isinstance(right_child, dict):
            right_child_radius = right_child.get('radius', node_radius)
        else:
            right_child_radius = node_radius

        right_points = position_structure_recursively(right_child, right_direction_atan2, right_child_radius)
        points.update(right_points)

        return points

    # Fallback for legacy list format
    if isinstance(structure, list):
        # Convert legacy format to dict format and recurse
        if len(structure) == 2:
            # Assume 90 degree angle for legacy format
            converted = {'children': structure, 'angle': 90.0, 'radius': radius_scale}
            return position_structure_recursively(converted, parent_direction_atan2, radius_scale)
        else:
            # Multiple items - just position them evenly
            points = {}
            for i, item in enumerate(structure):
                if isinstance(item, str):
                    angle_offset = (i - (len(structure)-1)/2) * 30  # 30 degrees apart
                    angle_atan2 = parent_direction_atan2 + angle_offset
                    angle_acc = -angle_atan2
                    pos = pol2cart(radius_scale, angle_acc)
                    points[item] = pos
            return points

    return {}


def place_first_two_areas(area1, area2, local_sim, global_sim, unit=1.0):
    """
    Place the first two areas based on local and global similarities

    Args:
        area1, area2: names of the two areas
        local_sim: local similarity (determines angle - closest possible affinity)
        global_sim: global similarity (determines diameter - farthest possible affinity)
        unit: unit parameter for calculation (e.g., 1.0 cm)

    Returns:
        dict: cluster information with positioned areas
    """
    # Calculate diameter based on GLOBAL similarity (farthest possible affinity)
    # Formula from paper: d = unit / global_sim
    # Higher global similarity -> smaller diameter (tighter cluster overall)
    # If global_sim = 1.0 (perfect), diameter = unit
    # If global_sim = 0.5 (medium), diameter = 2 * unit
    # If global_sim = 0.0, diameter would be infinite (avoid division by zero)

    if global_sim > 0:
        diameter = unit / global_sim
    else:
        diameter = unit * 100  # Very large

    radius = diameter / 2.0

    # Calculate angle based on LOCAL similarity (closest possible affinity)
    # Formula from paper: θ = 180° × (1 - local_sim)
    # Higher local similarity -> smaller angle (closer together)
    # If local_sim = 1.0, angle = 0° (same position)
    # If local_sim = 0.5, angle = 90°
    # If local_sim = 0.0, angle = 180° (opposite sides)

    angle = 180.0 * (1.0 - local_sim)

    # Place areas on circle
    # Center at origin
    center = (0.0, 0.0)

    # Place area1 at -angle/2, area2 at +angle/2
    pos1 = pol2cart(radius, -angle / 2.0)
    pos2 = pol2cart(radius, angle / 2.0)

    # Create cluster dict with hierarchical structure
    # Structure stores the tree with angles at each level
    structure = {
        'children': [area1, area2],
        'angle': angle,
        'radius': radius
    }

    cluster = {
        "members": {area1, area2},
        "center": center,
        "radius": radius,
        "diameter": radius * 2.0,
        "angle": angle,
        "local_sim": local_sim,
        "global_sim": global_sim,
        "points": {
            area1: pos1,
            area2: pos2
        },
        "structure": structure
    }

    return cluster


def build_acc_step_1(local_matrix, global_matrix, unit=1.0):
    """
    Build ACC Step 1: Place first two areas

    Args:
        local_matrix: local similarity matrix (dict of dict)
        global_matrix: global similarity matrix (dict of dict)
        unit: unit parameter for radius calculation

    Returns:
        dict: step information
    """
    # Step 1: Find pair with highest local similarity
    result = find_highest_similarity_pair(local_matrix)

    if result is None:
        return None

    area1, area2, local_sim = result

    # Step 2: Get global similarity for same pair
    global_sim = get_similarity(global_matrix, area1, area2)

    if global_sim is None:
        # Fallback: use local similarity if not found in global
        global_sim = local_sim

    # Step 3: Place the two areas
    cluster = place_first_two_areas(area1, area2, local_sim, global_sim, unit)

    # Create step info
    step_info = {
        "step": 0,
        "action": "initial",
        "description": f"Initial: {area1} and {area2} (local_sim={local_sim:.3f}, global_sim={global_sim:.3f})",
        "cluster": cluster,
        "highlighted_members": {area1, area2}
    }

    return step_info


# ------------------------------------------------------------
# Step 2: Merge areas into cluster and update matrix
# ------------------------------------------------------------
def merge_areas_in_matrix(matrix, area1, area2, method='average'):
    """
    Merge two areas into a cluster and update the similarity matrix

    Args:
        matrix: dict of dict similarity matrix
        area1, area2: areas to merge
        method: 'average', 'single' (max), or 'complete' (min)

    Returns:
        dict: updated matrix with merged cluster
        str: cluster name (e.g., "(J+T)")
    """
    # Create cluster name
    cluster_name = f"({area1}+{area2})"

    # Create new matrix
    new_matrix = {}

    # Get all areas except the two being merged
    all_areas = set(matrix.keys())
    other_areas = all_areas - {area1, area2}

    # Calculate similarities between cluster and other areas
    cluster_sims = {}
    for area in other_areas:
        # Get similarities
        sim1 = get_similarity(matrix, area1, area)
        sim2 = get_similarity(matrix, area2, area)

        # Calculate cluster similarity based on method
        if sim1 is not None and sim2 is not None:
            if method == 'average':
                cluster_sim = (sim1 + sim2) / 2.0
            elif method == 'single':  # max (single linkage)
                cluster_sim = max(sim1, sim2)
            elif method == 'complete':  # min (complete linkage)
                cluster_sim = min(sim1, sim2)
            else:
                cluster_sim = (sim1 + sim2) / 2.0
        elif sim1 is not None:
            cluster_sim = sim1
        elif sim2 is not None:
            cluster_sim = sim2
        else:
            cluster_sim = None

        if cluster_sim is not None:
            cluster_sims[area] = cluster_sim

    # Build new matrix
    # Add cluster row
    new_matrix[cluster_name] = dict(cluster_sims)

    # Add other areas
    for area in other_areas:
        new_matrix[area] = {}
        # Add similarity to cluster
        if area in cluster_sims:
            new_matrix[area][cluster_name] = cluster_sims[area]
        # Add similarities to other areas
        for other in other_areas:
            if other != area:
                sim = get_similarity(matrix, area, other)
                if sim is not None:
                    new_matrix[area][other] = sim

    return new_matrix, cluster_name


def find_next_highest_similarity(local_matrix, global_matrix, placed_areas, method='average'):
    """
    Find the next pair with highest similarity after merging placed areas

    Args:
        local_matrix: local similarity matrix
        global_matrix: global similarity matrix
        placed_areas: set of areas already placed
        method: linkage method for merging

    Returns:
        tuple: (item1, item2, local_sim, global_sim, updated_local_matrix, updated_global_matrix)
               where item1 or item2 might be a cluster
    """
    # If no areas placed yet, just find highest pair
    if len(placed_areas) == 0:
        result = find_highest_similarity_pair(local_matrix)
        if result:
            area1, area2, local_sim = result
            global_sim = get_similarity(global_matrix, area1, area2)
            if global_sim is None:
                global_sim = local_sim
            return (area1, area2, local_sim, global_sim, local_matrix, global_matrix)
        return None

    # Merge placed areas in both matrices
    placed_list = sorted(list(placed_areas))

    # For now, merge all placed areas into one cluster
    # Start with first two
    merged_local = dict(local_matrix)
    merged_global = dict(global_matrix)
    cluster_name = None

    if len(placed_list) >= 2:
        # Merge first two
        merged_local, cluster_name = merge_areas_in_matrix(merged_local, placed_list[0], placed_list[1], method)
        merged_global, _ = merge_areas_in_matrix(merged_global, placed_list[0], placed_list[1], method)

        # Merge remaining areas one by one into the cluster
        for i in range(2, len(placed_list)):
            area = placed_list[i]
            merged_local, cluster_name = merge_areas_in_matrix(merged_local, cluster_name, area, method)
            merged_global, _ = merge_areas_in_matrix(merged_global, cluster_name, area, method)

    # Now find highest similarity pair in merged matrix
    result = find_highest_similarity_pair(merged_local)

    if result:
        item1, item2, local_sim = result
        global_sim = get_similarity(merged_global, item1, item2)
        if global_sim is None:
            global_sim = local_sim
        return (item1, item2, local_sim, global_sim, merged_local, merged_global)

    return None


# ------------------------------------------------------------
# Step 3+: Handle multiple independent clusters
# ------------------------------------------------------------
def place_independent_pair(area1, area2, local_sim, global_sim, unit=1.0):
    """
    Place an independent pair of areas (same as place_first_two_areas)

    Args:
        area1, area2: names of the two areas
        local_sim: local similarity
        global_sim: global similarity
        unit: unit parameter

    Returns:
        dict: cluster information with positioned areas
    """
    return place_first_two_areas(area1, area2, local_sim, global_sim, unit)


def add_area_to_cluster(cluster, new_area, local_matrix, global_matrix, unit=1.0):
    """
    Add a single area to an existing cluster

    Args:
        cluster: existing cluster dict
        new_area: name of area to add
        local_matrix: local similarity matrix (for angle calculation)
        global_matrix: global similarity matrix (for diameter calculation)
        unit: unit parameter for calculation

    Returns:
        dict: updated cluster with new area positioned
    """
    # Find which member has highest similarity to new area
    # Use LOCAL similarity (closest possible affinity) for positioning
    best_member = None
    best_local_sim = -1.0

    for member in cluster['members']:
        local_sim = get_similarity(local_matrix, member, new_area)
        if local_sim and local_sim > best_local_sim:
            best_local_sim = local_sim
            best_member = member

    if best_member is None:
        # Fallback: use first member
        best_member = list(cluster['members'])[0]
        best_local_sim = 0.5

    # Calculate linkage similarity between existing cluster and new area
    new_members = cluster['members'] | {new_area}

    # Collect similarities between each cluster member and new area
    sims_local = []
    sims_global = []

    for member in cluster['members']:
        local_sim = get_similarity(local_matrix, member, new_area)
        global_sim = get_similarity(global_matrix, member, new_area)

        if local_sim is not None:
            sims_local.append(local_sim)
        if global_sim is not None:
            sims_global.append(global_sim)

    # Calculate cluster-to-area similarity based on average linkage
    if sims_local:
        new_local_sim = sum(sims_local) / len(sims_local)
    else:
        new_local_sim = 0.5

    if sims_global:
        new_global_sim = sum(sims_global) / len(sims_global)
    else:
        new_global_sim = 0.5

    # Apply paper formulas to calculate new diameter and angle
    if new_global_sim > 0:
        new_diameter = unit / new_global_sim
    else:
        new_diameter = unit * 100

    new_angle = 180.0 * (1.0 - new_local_sim)
    new_radius = new_diameter / 2.0

    # HIERARCHICAL PLACEMENT using recursive structure positioning
    # Build new structure: [existing_cluster_structure, new_area]
    # The structure stores the tree topology with angles at each node

    old_structure = cluster.get('structure')

    # Create new structure node
    # Left child = existing cluster structure
    # Right child = new area
    new_structure = {
        'children': [old_structure, new_area],
        'angle': new_angle,
        'radius': new_radius
    }

    # Use recursive positioning function
    # Parent direction is 0° (north) since root is always at 12 o'clock
    parent_direction_atan2 = 0.0  # North in compass convention

    new_points = position_structure_recursively(new_structure, parent_direction_atan2, new_radius)

    # Create updated cluster
    new_cluster = {
        'members': new_members,
        'center': (0.0, 0.0),
        'radius': new_radius,
        'diameter': new_diameter,
        'angle': new_angle,
        'local_sim': new_local_sim,
        'global_sim': new_global_sim,
        'points': new_points,
        'midline_angle': 0.0,
        'structure': new_structure
    }

    return new_cluster


def merge_two_clusters(c1, c2, local_matrix, global_matrix, unit=1.0):
    """
    Merge two independent clusters into one

    Args:
        c1, c2: cluster dicts to merge
        local_matrix: local similarity matrix (for angle calculation)
        global_matrix: global similarity matrix (for diameter calculation)
        unit: unit parameter

    Returns:
        dict: merged cluster
    """
    # Find the most similar pair between the two clusters
    # Use LOCAL similarity (closest possible affinity) for positioning
    best_local_sim = -1.0
    best_global_sim = -1.0
    best_pair = None

    for m1 in c1['members']:
        for m2 in c2['members']:
            local_sim = get_similarity(local_matrix, m1, m2)
            if local_sim and local_sim > best_local_sim:
                best_local_sim = local_sim
                best_pair = (m1, m2)
                # Also get global similarity for this pair
                global_sim = get_similarity(global_matrix, m1, m2)
                best_global_sim = global_sim if global_sim else local_sim

    if best_pair is None:
        # Fallback
        best_pair = (list(c1['members'])[0], list(c2['members'])[0])
        best_local_sim = 0.5
        best_global_sim = 0.5

    m1, m2 = best_pair

    # Calculate linkage similarity between two clusters
    # This follows hierarchical clustering approach:
    # similarity(cluster1, cluster2) based on linkage method (average, single, complete)
    # NOT the overall pairwise average of all members!

    # Collect similarities between all pairs from the two clusters
    sims_local = []
    sims_global = []

    for member1 in c1['members']:
        for member2 in c2['members']:
            local_sim = get_similarity(local_matrix, member1, member2)
            global_sim = get_similarity(global_matrix, member1, member2)

            if local_sim is not None:
                sims_local.append(local_sim)
            if global_sim is not None:
                sims_global.append(global_sim)

    # Calculate cluster-to-cluster similarity based on average linkage
    # This is the similarity value at which we merge the two clusters
    if sims_local:
        merged_local_sim = sum(sims_local) / len(sims_local)  # average linkage
    else:
        merged_local_sim = 0.5

    if sims_global:
        merged_global_sim = sum(sims_global) / len(sims_global)  # average linkage
    else:
        merged_global_sim = 0.5

    merged_members = c1['members'] | c2['members']

    # Apply paper formulas to calculate new diameter and angle
    # Formula: d = unit / global_sim (farthest possible affinity)
    if merged_global_sim > 0:
        new_diameter = unit / merged_global_sim
    else:
        new_diameter = unit * 100  # Very large

    # Formula: θ = 180° × (1 - local_sim) (closest possible affinity)
    new_angle = 180.0 * (1.0 - merged_local_sim)
    new_radius = new_diameter / 2.0

    # Calculate angle between the two alignment members based on LOCAL similarity
    # (closest possible affinity)
    alignment_angle = 180.0 * (1.0 - best_local_sim)

    # HIERARCHICAL PLACEMENT for merging two clusters using recursive positioning
    # Build new structure: [c1_structure, c2_structure]

    c1_structure = c1.get('structure')
    c2_structure = c2.get('structure')

    # Create new structure node
    new_structure = {
        'children': [c1_structure, c2_structure],
        'angle': new_angle,
        'radius': new_radius
    }

    # Use recursive positioning function
    # Parent direction is 0° (north) since root is always at 12 o'clock
    parent_direction_atan2 = 0.0  # North in compass convention

    new_points = position_structure_recursively(new_structure, parent_direction_atan2, new_radius)

    # Create merged cluster
    merged = {
        'members': merged_members,
        'center': (0.0, 0.0),
        'radius': new_radius,
        'diameter': new_diameter,
        'angle': new_angle,
        'local_sim': merged_local_sim,
        'global_sim': merged_global_sim,
        'points': new_points,
        'midline_angle': 0.0,  # Root always at 0° (north)
        'structure': new_structure
    }

    return merged


def find_highest_similarity_with_clusters(local_matrix, global_matrix, placed_areas, clusters):
    """
    Find highest similarity considering:
    1. Between two unplaced areas
    2. Between a cluster and an unplaced area
    3. Between two clusters

    Args:
        local_matrix: local similarity matrix
        global_matrix: global similarity matrix
        placed_areas: set of placed areas
        clusters: list of cluster dicts

    Returns:
        tuple: (type, item1, item2, local_sim, global_sim)
               type: 'new_pair', 'add_to_cluster', or 'merge_clusters'
    """
    all_areas = set(local_matrix.keys())
    unplaced_areas = all_areas - placed_areas

    best_sim = -1.0
    best_result = None

    # 1. Check pairs of unplaced areas
    for area1, area2 in combinations(unplaced_areas, 2):
        local_sim = get_similarity(local_matrix, area1, area2)
        if local_sim and local_sim > best_sim:
            global_sim = get_similarity(global_matrix, area1, area2) or local_sim
            best_sim = local_sim
            best_result = ('new_pair', area1, area2, local_sim, global_sim)

    # 2. Check between clusters and unplaced areas
    for cluster in clusters:
        for area in unplaced_areas:
            # Find max similarity between area and any member of cluster
            max_sim = -1.0
            for member in cluster['members']:
                sim = get_similarity(local_matrix, member, area)
                if sim and sim > max_sim:
                    max_sim = sim

            if max_sim > best_sim:
                global_sim = get_similarity(global_matrix, list(cluster['members'])[0], area) or max_sim
                best_sim = max_sim
                best_result = ('add_to_cluster', cluster, area, max_sim, global_sim)

    # 3. Check between pairs of clusters
    for c1, c2 in combinations(clusters, 2):
        # Find max similarity between any members of the two clusters
        max_sim = -1.0
        for m1 in c1['members']:
            for m2 in c2['members']:
                sim = get_similarity(local_matrix, m1, m2)
                if sim and sim > max_sim:
                    max_sim = sim

        if max_sim > best_sim:
            global_sim = get_similarity(global_matrix, list(c1['members'])[0], list(c2['members'])[0]) or max_sim
            best_sim = max_sim
            best_result = ('merge_clusters', c1, c2, max_sim, global_sim)

    return best_result


def build_acc_iterative(local_matrix, global_matrix, unit=1.0, method='average'):
    """
    Build ACC iteratively following Option 1 approach:
    Always select the globally highest similarity pair at each step

    Args:
        local_matrix: local similarity matrix
        global_matrix: global similarity matrix
        unit: unit parameter
        method: linkage method for merging

    Returns:
        list: list of step information dicts
    """
    logger.info("="*60)
    logger.info("Starting ACC Iterative Algorithm (Option 1)")
    logger.info("="*60)
    logger.info(f"Total areas: {len(local_matrix)}")
    logger.info(f"Areas: {sorted(local_matrix.keys())}")
    logger.info(f"Unit parameter: {unit}")
    logger.info(f"Linkage method: {method}")

    steps = []
    placed_areas = set()
    active_clusters = []  # List of independent clusters

    # Working copies of matrices
    current_local = dict(local_matrix)
    current_global = dict(global_matrix)

    step_num = 0

    # Step 0: Find and place first pair
    logger.info("\n" + "-"*60)
    logger.info("STEP 0: Finding initial pair")
    logger.info("-"*60)

    result = find_highest_similarity_pair(current_local)
    if result is None:
        logger.error("No valid pair found in matrix!")
        return steps

    area1, area2, local_sim = result
    global_sim = get_similarity(current_global, area1, area2)
    if global_sim is None:
        global_sim = local_sim
        logger.warning(f"No global similarity found for {area1}-{area2}, using local: {local_sim:.3f}")

    logger.info(f"Selected pair: {area1} - {area2}")
    logger.info(f"  Local similarity: {local_sim:.3f}")
    logger.info(f"  Global similarity: {global_sim:.3f}")

    cluster = place_first_two_areas(area1, area2, local_sim, global_sim, unit)
    logger.info(f"  Calculated radius: {cluster['radius']:.3f}")
    logger.info(f"  Calculated angle: {cluster['angle']:.2f}°")
    logger.info(f"  {area1} position: ({cluster['points'][area1][0]:.3f}, {cluster['points'][area1][1]:.3f})")
    logger.info(f"  {area2} position: ({cluster['points'][area2][0]:.3f}, {cluster['points'][area2][1]:.3f})")

    active_clusters.append(cluster)
    placed_areas.update([area1, area2])

    logger.info(f"✓ Initial cluster created with {len(placed_areas)} members")

    steps.append({
        "step": step_num,
        "action": "initial",
        "description": f"Initial: {area1} and {area2} (local={local_sim:.3f}, global={global_sim:.3f})",
        "clusters": [dict(cluster)],  # Copy for snapshot
        "highlighted_members": {area1, area2},
        "placed_areas": set(placed_areas)
    })

    step_num += 1

    # Continue until all areas are placed
    all_areas = set(local_matrix.keys())

    while len(placed_areas) < len(all_areas) or len(active_clusters) > 1:
        logger.info("\n" + "-"*60)
        logger.info(f"STEP {step_num}: Finding next action")
        logger.info("-"*60)
        logger.info(f"Placed areas: {sorted(placed_areas)} ({len(placed_areas)}/{len(all_areas)})")
        logger.info(f"Active clusters: {len(active_clusters)}")

        # Find next highest similarity
        result = find_highest_similarity_with_clusters(
            current_local, current_global, placed_areas, active_clusters
        )

        if result is None:
            logger.warning("No more valid actions found. Stopping.")
            break

        action_type = result[0]
        logger.info(f"Selected action: {action_type}")

        if action_type == 'new_pair':
            _, area1, area2, local_sim, global_sim = result
            logger.info(f"Creating new independent cluster:")
            logger.info(f"  Pair: {area1} - {area2}")
            logger.info(f"  Local similarity: {local_sim:.3f}")
            logger.info(f"  Global similarity: {global_sim:.3f}")

            # Both are new areas - create independent cluster
            new_cluster = place_independent_pair(area1, area2, local_sim, global_sim, unit)
            logger.info(f"  Radius: {new_cluster['radius']:.3f}")
            logger.info(f"  Angle: {new_cluster['angle']:.2f}°")

            active_clusters.append(new_cluster)
            placed_areas.update([area1, area2])

            logger.info(f"✓ New cluster created. Total clusters: {len(active_clusters)}")

            steps.append({
                "step": step_num,
                "action": "new_pair",
                "description": f"New pair: {area1} and {area2} (local={local_sim:.3f}, global={global_sim:.3f})",
                "clusters": [dict(c) for c in active_clusters],
                "highlighted_members": {area1, area2},
                "placed_areas": set(placed_areas)
            })

        elif action_type == 'add_to_cluster':
            _, cluster, area, local_sim, global_sim = result
            logger.info(f"Adding area to existing cluster:")
            logger.info(f"  Area: {area}")
            target_structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
            logger.info(f"  Target cluster: {target_structure}")
            logger.info(f"  Best member similarity: {local_sim:.3f}")

            # Add single area to existing cluster
            # Find which cluster in active_clusters matches
            cluster_idx = None
            for idx, c in enumerate(active_clusters):
                if c['members'] == cluster['members']:
                    cluster_idx = idx
                    break

            if cluster_idx is not None:
                # Update the cluster
                updated_cluster = add_area_to_cluster(cluster, area, current_local, current_global, unit)

                # Log new cluster calculations
                logger.info(f"  ")
                cluster_structure = format_cluster_structure(updated_cluster.get('structure', sorted(updated_cluster['members'])))
                logger.info(f"  New cluster {cluster_structure} calculations:")
                logger.info(f"    Local linkage similarity: {updated_cluster['local_sim']:.3f} (cluster-to-area)")
                logger.info(f"    Global linkage similarity: {updated_cluster['global_sim']:.3f} (cluster-to-area)")
                logger.info(f"    New diameter: {updated_cluster['diameter']:.3f} (was {cluster['diameter']:.3f})")
                logger.info(f"    New angle: {updated_cluster['angle']:.2f}° (was {cluster['angle']:.2f}°)")
                logger.info(f"  ")
                logger.info(f"  New position for {area}: ({updated_cluster['points'][area][0]:.3f}, {updated_cluster['points'][area][1]:.3f})")

                active_clusters[cluster_idx] = updated_cluster
                placed_areas.add(area)

                logger.info(f"✓ Area added. Cluster now has {len(updated_cluster['members'])} members")

                cluster_str = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
                steps.append({
                    "step": step_num,
                    "action": "add_area",
                    "description": f"Add {area} to cluster {cluster_str} (sim={local_sim:.3f})",
                    "clusters": [dict(c) for c in active_clusters],
                    "highlighted_members": {area},
                    "placed_areas": set(placed_areas)
                })
            else:
                logger.error(f"Cluster not found in active_clusters! This shouldn't happen.")
                break

        elif action_type == 'merge_clusters':
            _, c1, c2, local_sim, global_sim = result
            c1_structure = format_cluster_structure(c1.get('structure', sorted(c1['members'])))
            c2_structure = format_cluster_structure(c2.get('structure', sorted(c2['members'])))
            logger.info(f"Merging two clusters:")
            logger.info(f"  Cluster 1: {c1_structure}")
            logger.info(f"  Cluster 2: {c2_structure}")
            logger.info(f"  Max similarity between clusters: {local_sim:.3f}")

            # Merge two clusters
            # Find indices of both clusters
            idx1 = None
            idx2 = None
            for idx, c in enumerate(active_clusters):
                if c['members'] == c1['members']:
                    idx1 = idx
                if c['members'] == c2['members']:
                    idx2 = idx

            if idx1 is not None and idx2 is not None:
                # Merge the clusters
                merged_cluster = merge_two_clusters(c1, c2, current_local, current_global, unit)

                # Log merged cluster calculations
                logger.info(f"  ")
                cluster_structure = format_cluster_structure(merged_cluster.get('structure', sorted(merged_cluster['members'])))
                logger.info(f"  Merged cluster {cluster_structure} calculations:")
                logger.info(f"    Local linkage similarity: {merged_cluster['local_sim']:.3f} (cluster-to-cluster)")
                logger.info(f"    Global linkage similarity: {merged_cluster['global_sim']:.3f} (cluster-to-cluster)")
                logger.info(f"    New diameter: {merged_cluster['diameter']:.3f}")
                logger.info(f"    New angle: {merged_cluster['angle']:.2f}°")
                logger.info(f"    Total members: {len(merged_cluster['members'])}")

                # Remove both clusters and add merged one
                # Remove higher index first to avoid index shifting issues
                if idx1 > idx2:
                    del active_clusters[idx1]
                    del active_clusters[idx2]
                else:
                    del active_clusters[idx2]
                    del active_clusters[idx1]

                active_clusters.append(merged_cluster)

                logger.info(f"✓ Clusters merged. Active clusters: {len(active_clusters)}")

                steps.append({
                    "step": step_num,
                    "action": "merge_clusters",
                    "description": f"Merge clusters {c1_structure} and {c2_structure} (sim={local_sim:.3f})",
                    "clusters": [dict(c) for c in active_clusters],
                    "highlighted_members": set(),
                    "placed_areas": set(placed_areas)
                })
            else:
                logger.error(f"One or both clusters not found! idx1={idx1}, idx2={idx2}")
                break

        step_num += 1

    logger.info("\n" + "="*60)
    logger.info("ACC Iterative Algorithm Completed")
    logger.info("="*60)
    logger.info(f"Total steps: {len(steps)}")
    logger.info(f"Final clusters: {len(active_clusters)}")
    if active_clusters:
        logger.info(f"Final members: {sorted(active_clusters[0]['members'])}")
    logger.info("="*60 + "\n")

    return steps


# ------------------------------------------------------------
# Test
# ------------------------------------------------------------
if __name__ == "__main__":
    # Example matrices
    local_matrix = {
        "J": {"T": 0.9, "Y": 0.8, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.9, "Y": 0.8, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.8, "T": 0.8, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.75, "Q": 0.75},
        "O": {"Q": 0.85},
        "Q": {}
    }

    global_matrix = {
        "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.7, "Q": 0.68},
        "O": {"Q": 0.83},
        "Q": {}
    }

    print("Testing ACC Step 1")
    print("="*60)

    # Find highest similarity pair
    result = find_highest_similarity_pair(local_matrix)
    if result:
        area1, area2, sim = result
        print(f"\nHighest local similarity pair:")
        print(f"  {area1} - {area2}: {sim:.3f}")

    # Build step 1
    step = build_acc_step_1(local_matrix, global_matrix, unit=1.0)

    if step:
        print(f"\n{step['description']}")
        cluster = step['cluster']

        print(f"\nCluster properties:")
        cluster_structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
        print(f"  Structure: {cluster_structure}")
        print(f"  Radius: {cluster['radius']:.3f}")
        print(f"  Diameter: {cluster['diameter']:.3f}")
        print(f"  Angle: {cluster['angle']:.2f}°")
        print(f"  Local similarity: {cluster['local_sim']:.3f}")
        print(f"  Global similarity: {cluster['global_sim']:.3f}")

        print(f"\nArea positions:")
        for area in sorted(cluster['points'].keys()):
            x, y = cluster['points'][area]
            print(f"  {area}: ({x:7.3f}, {y:7.3f})")

        # Calculate actual distance and angle between points
        pos1 = list(cluster['points'].values())[0]
        pos2 = list(cluster['points'].values())[1]
        dist = math.sqrt((pos2[0]-pos1[0])**2 + (pos2[1]-pos1[1])**2)
        actual_angle = math.degrees(math.acos((pos1[0]*pos2[0] + pos1[1]*pos2[1]) / (cluster['radius']**2)))

        print(f"\nVerification:")
        print(f"  Distance between areas: {dist:.3f}")
        print(f"  Actual angle: {actual_angle:.2f}° (should match {cluster['angle']:.2f}°)")

    # Step 2: Find next highest similarity after merging J and T
    print(f"\n\n{'='*60}")
    print("STEP 2: After merging J and T")
    print('='*60)

    placed_areas = {area1, area2}
    result = find_next_highest_similarity(local_matrix, global_matrix, placed_areas, method='average')

    if result:
        item1, item2, local_sim, global_sim, merged_local, merged_global = result

        print(f"\nMerged matrix (Local):")
        print(f"  Areas/Clusters: {sorted(merged_local.keys())}")

        print(f"\nNext highest local similarity pair:")
        print(f"  {item1} - {item2}: {local_sim:.3f}")
        print(f"  Global similarity: {global_sim:.3f}")

        print(f"\nDetailed similarities in merged local matrix:")
        for area in sorted(merged_local.keys()):
            sims = merged_local[area]
            if sims:
                for other in sorted(sims.keys()):
                    print(f"  {area} - {other}: {sims[other]:.3f}")

    # Step 3: If we merge the next pair, what happens?
    if result and item2 not in placed_areas and item1 not in placed_areas:
        # Both are new areas - we'd need to handle merging them with the existing cluster
        print(f"\n\n{'='*60}")
        print("STEP 3: Preview - if we merge the next pair")
        print('='*60)
        print(f"  We would be merging {item1} and {item2}")
        print(f"  Then we need to decide how to integrate with existing cluster ({area1}+{area2})")
    elif result:
        # One is the cluster, one is a new area
        new_area = item2 if item1.startswith('(') else item1
        cluster = item1 if item1.startswith('(') else item2

        print(f"\n\n{'='*60}")
        print("STEP 3: Preview - if we add next area")
        print('='*60)
        print(f"  Adding area '{new_area}' to cluster '{cluster}'")
        print(f"  This follows the ACC pattern of incrementally building the cluster")

    # Test the new iterative algorithm
    print(f"\n\n{'='*60}")
    print("TESTING NEW ITERATIVE ALGORITHM (Option 1)")
    print('='*60)

    steps = build_acc_iterative(local_matrix, global_matrix, unit=1.0, method='average')

    print(f"\nTotal steps: {len(steps)}\n")

    for step_info in steps:
        print(f"\n{'='*60}")
        print(f"Step {step_info['step']}: {step_info['action'].upper()}")
        print(f"{'='*60}")
        print(f"{step_info['description']}")
        print(f"Placed areas so far: {sorted(step_info['placed_areas'])}")
        print(f"Number of active clusters: {len(step_info['clusters'])}")

        if step_info['highlighted_members']:
            print(f"Highlighted (new) members: {sorted(step_info['highlighted_members'])}")

        print(f"\nCluster details:")
        for idx, cluster in enumerate(step_info['clusters']):
            cluster_structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
            print(f"  Cluster {idx + 1}: {cluster_structure}")
            print(f"    Radius: {cluster['radius']:.3f}")
            print(f"    Diameter: {cluster['diameter']:.3f}")
            print(f"    Angle: {cluster['angle']:.2f}°")
            print(f"    Positions:")
            for member in sorted(cluster['points'].keys()):
                x, y = cluster['points'][member]
                marker = " <-- NEW" if member in step_info['highlighted_members'] else ""
                print(f"      {member}: ({x:7.3f}, {y:7.3f}){marker}")
