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
    rad = math.radians(angle_deg)
    return (r * math.cos(rad), r * math.sin(rad))


def cart_add(a, b):
    return (a[0] + b[0], a[1] + b[1])


# ------------------------------------------------------------
# Step 1: Find two areas with highest subordinate similarity
# ------------------------------------------------------------
def find_highest_similarity_pair(sub_matrix):
    """
    Find the pair of areas with highest similarity in subordinate matrix

    Args:
        sub_matrix: dict of dict, e.g. {"J": {"T": 0.9, "Y": 0.8}, ...}

    Returns:
        tuple: (area1, area2, similarity)
    """
    best_pair = None
    best_sim = -1.0

    # Get all areas
    areas = list(sub_matrix.keys())

    # Check all pairs
    for area1, area2 in combinations(areas, 2):
        sim = None

        # Try both directions
        if area1 in sub_matrix and area2 in sub_matrix[area1]:
            sim = sub_matrix[area1][area2]
        elif area2 in sub_matrix and area1 in sub_matrix[area2]:
            sim = sub_matrix[area2][area1]

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
        structure: nested list/string representing hierarchical cluster structure

    Returns:
        str: formatted structure string
    """
    if isinstance(structure, str):
        return structure
    elif isinstance(structure, list):
        if len(structure) == 0:
            return "[]"
        # Format nested structure
        parts = [format_cluster_structure(item) for item in structure]
        return "[" + ", ".join(parts) + "]"
    else:
        return str(structure)


def place_first_two_areas(area1, area2, sub_sim, inc_sim, unit=1.0):
    """
    Place the first two areas based on subordinate and inclusive similarities

    Args:
        area1, area2: names of the two areas
        sub_sim: subordinate similarity (determines angle - closest possible affinity)
        inc_sim: inclusive similarity (determines diameter - farthest possible affinity)
        unit: unit parameter for calculation (e.g., 1.0 cm)

    Returns:
        dict: cluster information with positioned areas
    """
    # Calculate diameter based on INCLUSIVE similarity (farthest possible affinity)
    # Formula from paper: d = unit / inc_sim
    # Higher inclusive similarity -> smaller diameter (tighter cluster overall)
    # If inc_sim = 1.0 (perfect), diameter = unit
    # If inc_sim = 0.5 (medium), diameter = 2 * unit
    # If inc_sim = 0.0, diameter would be infinite (avoid division by zero)

    if inc_sim > 0:
        diameter = unit / inc_sim
    else:
        diameter = unit * 100  # Very large

    radius = diameter / 2.0

    # Calculate angle based on SUBORDINATE similarity (closest possible affinity)
    # Formula from paper: θ = 180° × (1 - sub_sim)
    # Higher subordinate similarity -> smaller angle (closer together)
    # If sub_sim = 1.0, angle = 0° (same position)
    # If sub_sim = 0.5, angle = 90°
    # If sub_sim = 0.0, angle = 180° (opposite sides)

    angle = 180.0 * (1.0 - sub_sim)

    # Place areas on circle
    # Center at origin
    center = (0.0, 0.0)

    # Place area1 at -angle/2, area2 at +angle/2
    pos1 = pol2cart(radius, -angle / 2.0)
    pos2 = pol2cart(radius, angle / 2.0)

    # Create cluster dict with hierarchical structure
    cluster = {
        "members": {area1, area2},
        "center": center,
        "radius": radius,
        "diameter": radius * 2.0,
        "angle": angle,
        "sub_sim": sub_sim,
        "inc_sim": inc_sim,
        "points": {
            area1: pos1,
            area2: pos2
        },
        "structure": [area1, area2]  # Initial pair structure
    }

    return cluster


def build_acc_step_1(sub_matrix, inc_matrix, unit=1.0):
    """
    Build ACC Step 1: Place first two areas

    Args:
        sub_matrix: subordinate similarity matrix (dict of dict)
        inc_matrix: inclusive similarity matrix (dict of dict)
        unit: unit parameter for radius calculation

    Returns:
        dict: step information
    """
    # Step 1: Find pair with highest subordinate similarity
    result = find_highest_similarity_pair(sub_matrix)

    if result is None:
        return None

    area1, area2, sub_sim = result

    # Step 2: Get inclusive similarity for same pair
    inc_sim = get_similarity(inc_matrix, area1, area2)

    if inc_sim is None:
        # Fallback: use subordinate similarity if not found in inclusive
        inc_sim = sub_sim

    # Step 3: Place the two areas
    cluster = place_first_two_areas(area1, area2, sub_sim, inc_sim, unit)

    # Create step info
    step_info = {
        "step": 0,
        "action": "initial",
        "description": f"Initial: {area1} and {area2} (sub_sim={sub_sim:.3f}, inc_sim={inc_sim:.3f})",
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


def find_next_highest_similarity(sub_matrix, inc_matrix, placed_areas, method='average'):
    """
    Find the next pair with highest similarity after merging placed areas

    Args:
        sub_matrix: subordinate similarity matrix
        inc_matrix: inclusive similarity matrix
        placed_areas: set of areas already placed
        method: linkage method for merging

    Returns:
        tuple: (item1, item2, sub_sim, inc_sim, updated_sub_matrix, updated_inc_matrix)
               where item1 or item2 might be a cluster
    """
    # If no areas placed yet, just find highest pair
    if len(placed_areas) == 0:
        result = find_highest_similarity_pair(sub_matrix)
        if result:
            area1, area2, sub_sim = result
            inc_sim = get_similarity(inc_matrix, area1, area2)
            if inc_sim is None:
                inc_sim = sub_sim
            return (area1, area2, sub_sim, inc_sim, sub_matrix, inc_matrix)
        return None

    # Merge placed areas in both matrices
    placed_list = sorted(list(placed_areas))

    # For now, merge all placed areas into one cluster
    # Start with first two
    merged_sub = dict(sub_matrix)
    merged_inc = dict(inc_matrix)
    cluster_name = None

    if len(placed_list) >= 2:
        # Merge first two
        merged_sub, cluster_name = merge_areas_in_matrix(merged_sub, placed_list[0], placed_list[1], method)
        merged_inc, _ = merge_areas_in_matrix(merged_inc, placed_list[0], placed_list[1], method)

        # Merge remaining areas one by one into the cluster
        for i in range(2, len(placed_list)):
            area = placed_list[i]
            merged_sub, cluster_name = merge_areas_in_matrix(merged_sub, cluster_name, area, method)
            merged_inc, _ = merge_areas_in_matrix(merged_inc, cluster_name, area, method)

    # Now find highest similarity pair in merged matrix
    result = find_highest_similarity_pair(merged_sub)

    if result:
        item1, item2, sub_sim = result
        inc_sim = get_similarity(merged_inc, item1, item2)
        if inc_sim is None:
            inc_sim = sub_sim
        return (item1, item2, sub_sim, inc_sim, merged_sub, merged_inc)

    return None


# ------------------------------------------------------------
# Step 3+: Handle multiple independent clusters
# ------------------------------------------------------------
def place_independent_pair(area1, area2, sub_sim, inc_sim, unit=1.0):
    """
    Place an independent pair of areas (same as place_first_two_areas)

    Args:
        area1, area2: names of the two areas
        sub_sim: subordinate similarity
        inc_sim: inclusive similarity
        unit: unit parameter

    Returns:
        dict: cluster information with positioned areas
    """
    return place_first_two_areas(area1, area2, sub_sim, inc_sim, unit)


def add_area_to_cluster(cluster, new_area, sub_matrix, inc_matrix, unit=1.0):
    """
    Add a single area to an existing cluster

    Args:
        cluster: existing cluster dict
        new_area: name of area to add
        sub_matrix: subordinate similarity matrix (for angle calculation)
        inc_matrix: inclusive similarity matrix (for diameter calculation)
        unit: unit parameter for calculation

    Returns:
        dict: updated cluster with new area positioned
    """
    # Find which member has highest similarity to new area
    # Use SUBORDINATE similarity (closest possible affinity) for positioning
    best_member = None
    best_sub_sim = -1.0

    for member in cluster['members']:
        sub_sim = get_similarity(sub_matrix, member, new_area)
        if sub_sim and sub_sim > best_sub_sim:
            best_sub_sim = sub_sim
            best_member = member

    if best_member is None:
        # Fallback: use first member
        best_member = list(cluster['members'])[0]
        best_sub_sim = 0.5

    # Calculate linkage similarity between existing cluster and new area
    # This follows hierarchical clustering approach:
    # similarity(cluster, new_area) based on linkage method (average, single, complete)
    # NOT the overall pairwise average of all members!

    new_members = cluster['members'] | {new_area}

    # Collect similarities between each cluster member and new area
    sims_sub = []
    sims_inc = []

    for member in cluster['members']:
        sub_sim = get_similarity(sub_matrix, member, new_area)
        inc_sim = get_similarity(inc_matrix, member, new_area)

        if sub_sim is not None:
            sims_sub.append(sub_sim)
        if inc_sim is not None:
            sims_inc.append(inc_sim)

    # Calculate cluster-to-area similarity based on average linkage
    # This is the similarity value at which we merge the cluster with the new area
    if sims_sub:
        new_sub_sim = sum(sims_sub) / len(sims_sub)  # average linkage
    else:
        new_sub_sim = 0.5

    if sims_inc:
        new_inc_sim = sum(sims_inc) / len(sims_inc)  # average linkage
    else:
        new_inc_sim = 0.5

    # Apply paper formulas to calculate new diameter and angle
    # Formula: d = unit / inc_sim (farthest possible affinity)
    if new_inc_sim > 0:
        new_diameter = unit / new_inc_sim
    else:
        new_diameter = unit * 100  # Very large

    # Formula: θ = 180° × (1 - sub_sim) (closest possible affinity)
    new_angle = 180.0 * (1.0 - new_sub_sim)
    new_radius = new_diameter / 2.0

    # IMPORTANT: Preserve concentric circles structure
    # DO NOT scale existing points - they stay on their original circles
    # Only the new area is placed on the new (outer) circle
    # This creates the concentric circles structure of ACC

    # Create updated cluster with NEW calculated values
    new_cluster = {
        'members': new_members,
        'center': cluster['center'],
        'radius': new_radius,  # This represents the outermost circle
        'diameter': new_diameter,
        'angle': new_angle,
        'sub_sim': new_sub_sim,
        'inc_sim': new_inc_sim,
        'points': dict(cluster['points']),  # Keep existing points as-is (inner circles)
        'midline_angle': cluster.get('midline_angle', 0.0),
        'structure': [cluster.get('structure', list(cluster['members'])), new_area]  # Nest structure
    }

    # Calculate position for new area
    # Place it based on SUBORDINATE similarity to best_member (closest possible affinity)
    # Angle from best_member is based on subordinate similarity
    angle_from_member = 180.0 * (1.0 - best_sub_sim)

    # Get position of best_member (already scaled)
    best_pos = new_cluster['points'][best_member]

    # Calculate angle of best_member from center
    member_angle = math.degrees(math.atan2(best_pos[1] - new_cluster['center'][1],
                                            best_pos[0] - new_cluster['center'][0]))

    # New area's angle
    new_pos_angle = member_angle + angle_from_member

    # Place new area on the circle with NEW radius
    new_pos = pol2cart(new_radius, new_pos_angle)
    new_pos = cart_add(new_pos, new_cluster['center'])

    new_cluster['points'][new_area] = new_pos

    return new_cluster


def merge_two_clusters(c1, c2, sub_matrix, inc_matrix, unit=1.0):
    """
    Merge two independent clusters into one

    Args:
        c1, c2: cluster dicts to merge
        sub_matrix: subordinate similarity matrix (for angle calculation)
        inc_matrix: inclusive similarity matrix (for diameter calculation)
        unit: unit parameter

    Returns:
        dict: merged cluster
    """
    # Find the most similar pair between the two clusters
    # Use SUBORDINATE similarity (closest possible affinity) for positioning
    best_sub_sim = -1.0
    best_inc_sim = -1.0
    best_pair = None

    for m1 in c1['members']:
        for m2 in c2['members']:
            sub_sim = get_similarity(sub_matrix, m1, m2)
            if sub_sim and sub_sim > best_sub_sim:
                best_sub_sim = sub_sim
                best_pair = (m1, m2)
                # Also get inclusive similarity for this pair
                inc_sim = get_similarity(inc_matrix, m1, m2)
                best_inc_sim = inc_sim if inc_sim else sub_sim

    if best_pair is None:
        # Fallback
        best_pair = (list(c1['members'])[0], list(c2['members'])[0])
        best_sub_sim = 0.5
        best_inc_sim = 0.5

    m1, m2 = best_pair

    # Calculate linkage similarity between two clusters
    # This follows hierarchical clustering approach:
    # similarity(cluster1, cluster2) based on linkage method (average, single, complete)
    # NOT the overall pairwise average of all members!

    # Collect similarities between all pairs from the two clusters
    sims_sub = []
    sims_inc = []

    for member1 in c1['members']:
        for member2 in c2['members']:
            sub_sim = get_similarity(sub_matrix, member1, member2)
            inc_sim = get_similarity(inc_matrix, member1, member2)

            if sub_sim is not None:
                sims_sub.append(sub_sim)
            if inc_sim is not None:
                sims_inc.append(inc_sim)

    # Calculate cluster-to-cluster similarity based on average linkage
    # This is the similarity value at which we merge the two clusters
    if sims_sub:
        merged_sub_sim = sum(sims_sub) / len(sims_sub)  # average linkage
    else:
        merged_sub_sim = 0.5

    if sims_inc:
        merged_inc_sim = sum(sims_inc) / len(sims_inc)  # average linkage
    else:
        merged_inc_sim = 0.5

    merged_members = c1['members'] | c2['members']

    # Apply paper formulas to calculate new diameter and angle
    # Formula: d = unit / inc_sim (farthest possible affinity)
    if merged_inc_sim > 0:
        new_diameter = unit / merged_inc_sim
    else:
        new_diameter = unit * 100  # Very large

    # Formula: θ = 180° × (1 - sub_sim) (closest possible affinity)
    new_angle = 180.0 * (1.0 - merged_sub_sim)
    new_radius = new_diameter / 2.0

    # Calculate angle between the two alignment members based on SUBORDINATE similarity
    # (closest possible affinity)
    alignment_angle = 180.0 * (1.0 - best_sub_sim)

    # Create merged cluster centered at origin
    merged = {
        'members': merged_members,
        'center': (0.0, 0.0),
        'radius': new_radius,  # This is the outermost radius (for reference)
        'diameter': new_diameter,
        'angle': new_angle,
        'sub_sim': merged_sub_sim,  # Subordinate pairwise average (closest affinity)
        'inc_sim': merged_inc_sim,  # Inclusive pairwise average (farthest affinity)
        'points': {},
        'midline_angle': 0.0,
        'structure': [c1.get('structure', list(c1['members'])),
                      c2.get('structure', list(c2['members']))]  # Merge structures
    }

    # CRITICAL: Preserve concentric circles structure
    # Each point keeps its original radius from origin
    # We only ROTATE the clusters to align m1 and m2

    # Calculate current angles of m1 and m2
    m1_pos = c1['points'][m1]
    m1_current_angle = math.degrees(math.atan2(m1_pos[1], m1_pos[0]))

    m2_pos = c2['points'][m2]
    m2_current_angle = math.degrees(math.atan2(m2_pos[1], m2_pos[0]))

    # Target angles: m1 at -alignment_angle/2, m2 at +alignment_angle/2
    m1_target_angle = -alignment_angle / 2.0
    m2_target_angle = alignment_angle / 2.0

    # Calculate rotation needed for each cluster
    rotation1 = m1_target_angle - m1_current_angle
    rotation2 = m2_target_angle - m2_current_angle

    # Rotate all members of c1 around origin
    for member in c1['members']:
        old_pos = c1['points'][member]
        old_angle = math.degrees(math.atan2(old_pos[1], old_pos[0]))
        old_radius = math.sqrt(old_pos[0]**2 + old_pos[1]**2)

        # Apply rotation, keep radius unchanged
        new_angle = old_angle + rotation1
        merged['points'][member] = pol2cart(old_radius, new_angle)

    # Rotate all members of c2 around origin
    for member in c2['members']:
        old_pos = c2['points'][member]
        old_angle = math.degrees(math.atan2(old_pos[1], old_pos[0]))
        old_radius = math.sqrt(old_pos[0]**2 + old_pos[1]**2)

        # Apply rotation, keep radius unchanged
        new_angle = old_angle + rotation2
        merged['points'][member] = pol2cart(old_radius, new_angle)

    return merged


def find_highest_similarity_with_clusters(sub_matrix, inc_matrix, placed_areas, clusters):
    """
    Find highest similarity considering:
    1. Between two unplaced areas
    2. Between a cluster and an unplaced area
    3. Between two clusters

    Args:
        sub_matrix: subordinate similarity matrix
        inc_matrix: inclusive similarity matrix
        placed_areas: set of placed areas
        clusters: list of cluster dicts

    Returns:
        tuple: (type, item1, item2, sub_sim, inc_sim)
               type: 'new_pair', 'add_to_cluster', or 'merge_clusters'
    """
    all_areas = set(sub_matrix.keys())
    unplaced_areas = all_areas - placed_areas

    best_sim = -1.0
    best_result = None

    # 1. Check pairs of unplaced areas
    for area1, area2 in combinations(unplaced_areas, 2):
        sub_sim = get_similarity(sub_matrix, area1, area2)
        if sub_sim and sub_sim > best_sim:
            inc_sim = get_similarity(inc_matrix, area1, area2) or sub_sim
            best_sim = sub_sim
            best_result = ('new_pair', area1, area2, sub_sim, inc_sim)

    # 2. Check between clusters and unplaced areas
    for cluster in clusters:
        for area in unplaced_areas:
            # Find max similarity between area and any member of cluster
            max_sim = -1.0
            for member in cluster['members']:
                sim = get_similarity(sub_matrix, member, area)
                if sim and sim > max_sim:
                    max_sim = sim

            if max_sim > best_sim:
                inc_sim = get_similarity(inc_matrix, list(cluster['members'])[0], area) or max_sim
                best_sim = max_sim
                best_result = ('add_to_cluster', cluster, area, max_sim, inc_sim)

    # 3. Check between pairs of clusters
    for c1, c2 in combinations(clusters, 2):
        # Find max similarity between any members of the two clusters
        max_sim = -1.0
        for m1 in c1['members']:
            for m2 in c2['members']:
                sim = get_similarity(sub_matrix, m1, m2)
                if sim and sim > max_sim:
                    max_sim = sim

        if max_sim > best_sim:
            inc_sim = get_similarity(inc_matrix, list(c1['members'])[0], list(c2['members'])[0]) or max_sim
            best_sim = max_sim
            best_result = ('merge_clusters', c1, c2, max_sim, inc_sim)

    return best_result


def build_acc_iterative(sub_matrix, inc_matrix, unit=1.0, method='average'):
    """
    Build ACC iteratively following Option 1 approach:
    Always select the globally highest similarity pair at each step

    Args:
        sub_matrix: subordinate similarity matrix
        inc_matrix: inclusive similarity matrix
        unit: unit parameter
        method: linkage method for merging

    Returns:
        list: list of step information dicts
    """
    logger.info("="*60)
    logger.info("Starting ACC Iterative Algorithm (Option 1)")
    logger.info("="*60)
    logger.info(f"Total areas: {len(sub_matrix)}")
    logger.info(f"Areas: {sorted(sub_matrix.keys())}")
    logger.info(f"Unit parameter: {unit}")
    logger.info(f"Linkage method: {method}")

    steps = []
    placed_areas = set()
    active_clusters = []  # List of independent clusters

    # Working copies of matrices
    current_sub = dict(sub_matrix)
    current_inc = dict(inc_matrix)

    step_num = 0

    # Step 0: Find and place first pair
    logger.info("\n" + "-"*60)
    logger.info("STEP 0: Finding initial pair")
    logger.info("-"*60)

    result = find_highest_similarity_pair(current_sub)
    if result is None:
        logger.error("No valid pair found in matrix!")
        return steps

    area1, area2, sub_sim = result
    inc_sim = get_similarity(current_inc, area1, area2)
    if inc_sim is None:
        inc_sim = sub_sim
        logger.warning(f"No inclusive similarity found for {area1}-{area2}, using subordinate: {sub_sim:.3f}")

    logger.info(f"Selected pair: {area1} - {area2}")
    logger.info(f"  Subordinate similarity: {sub_sim:.3f}")
    logger.info(f"  Inclusive similarity: {inc_sim:.3f}")

    cluster = place_first_two_areas(area1, area2, sub_sim, inc_sim, unit)
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
        "description": f"Initial: {area1} and {area2} (sub={sub_sim:.3f}, inc={inc_sim:.3f})",
        "clusters": [dict(cluster)],  # Copy for snapshot
        "highlighted_members": {area1, area2},
        "placed_areas": set(placed_areas)
    })

    step_num += 1

    # Continue until all areas are placed
    all_areas = set(sub_matrix.keys())

    while len(placed_areas) < len(all_areas) or len(active_clusters) > 1:
        logger.info("\n" + "-"*60)
        logger.info(f"STEP {step_num}: Finding next action")
        logger.info("-"*60)
        logger.info(f"Placed areas: {sorted(placed_areas)} ({len(placed_areas)}/{len(all_areas)})")
        logger.info(f"Active clusters: {len(active_clusters)}")

        # Find next highest similarity
        result = find_highest_similarity_with_clusters(
            current_sub, current_inc, placed_areas, active_clusters
        )

        if result is None:
            logger.warning("No more valid actions found. Stopping.")
            break

        action_type = result[0]
        logger.info(f"Selected action: {action_type}")

        if action_type == 'new_pair':
            _, area1, area2, sub_sim, inc_sim = result
            logger.info(f"Creating new independent cluster:")
            logger.info(f"  Pair: {area1} - {area2}")
            logger.info(f"  Subordinate similarity: {sub_sim:.3f}")
            logger.info(f"  Inclusive similarity: {inc_sim:.3f}")

            # Both are new areas - create independent cluster
            new_cluster = place_independent_pair(area1, area2, sub_sim, inc_sim, unit)
            logger.info(f"  Radius: {new_cluster['radius']:.3f}")
            logger.info(f"  Angle: {new_cluster['angle']:.2f}°")

            active_clusters.append(new_cluster)
            placed_areas.update([area1, area2])

            logger.info(f"✓ New cluster created. Total clusters: {len(active_clusters)}")

            steps.append({
                "step": step_num,
                "action": "new_pair",
                "description": f"New pair: {area1} and {area2} (sub={sub_sim:.3f}, inc={inc_sim:.3f})",
                "clusters": [dict(c) for c in active_clusters],
                "highlighted_members": {area1, area2},
                "placed_areas": set(placed_areas)
            })

        elif action_type == 'add_to_cluster':
            _, cluster, area, sub_sim, inc_sim = result
            logger.info(f"Adding area to existing cluster:")
            logger.info(f"  Area: {area}")
            target_structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
            logger.info(f"  Target cluster: {target_structure}")
            logger.info(f"  Best member similarity: {sub_sim:.3f}")

            # Add single area to existing cluster
            # Find which cluster in active_clusters matches
            cluster_idx = None
            for idx, c in enumerate(active_clusters):
                if c['members'] == cluster['members']:
                    cluster_idx = idx
                    break

            if cluster_idx is not None:
                # Update the cluster
                updated_cluster = add_area_to_cluster(cluster, area, current_sub, current_inc, unit)

                # Log new cluster calculations
                logger.info(f"  ")
                cluster_structure = format_cluster_structure(updated_cluster.get('structure', sorted(updated_cluster['members'])))
                logger.info(f"  New cluster {cluster_structure} calculations:")
                logger.info(f"    Subordinate linkage similarity: {updated_cluster['sub_sim']:.3f} (cluster-to-area)")
                logger.info(f"    Inclusive linkage similarity: {updated_cluster['inc_sim']:.3f} (cluster-to-area)")
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
                    "description": f"Add {area} to cluster {cluster_str} (sim={sub_sim:.3f})",
                    "clusters": [dict(c) for c in active_clusters],
                    "highlighted_members": {area},
                    "placed_areas": set(placed_areas)
                })
            else:
                logger.error(f"Cluster not found in active_clusters! This shouldn't happen.")
                break

        elif action_type == 'merge_clusters':
            _, c1, c2, sub_sim, inc_sim = result
            c1_structure = format_cluster_structure(c1.get('structure', sorted(c1['members'])))
            c2_structure = format_cluster_structure(c2.get('structure', sorted(c2['members'])))
            logger.info(f"Merging two clusters:")
            logger.info(f"  Cluster 1: {c1_structure}")
            logger.info(f"  Cluster 2: {c2_structure}")
            logger.info(f"  Max similarity between clusters: {sub_sim:.3f}")

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
                merged_cluster = merge_two_clusters(c1, c2, current_sub, current_inc, unit)

                # Log merged cluster calculations
                logger.info(f"  ")
                cluster_structure = format_cluster_structure(merged_cluster.get('structure', sorted(merged_cluster['members'])))
                logger.info(f"  Merged cluster {cluster_structure} calculations:")
                logger.info(f"    Subordinate linkage similarity: {merged_cluster['sub_sim']:.3f} (cluster-to-cluster)")
                logger.info(f"    Inclusive linkage similarity: {merged_cluster['inc_sim']:.3f} (cluster-to-cluster)")
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
                    "description": f"Merge clusters {c1_structure} and {c2_structure} (sim={sub_sim:.3f})",
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
    sub_matrix = {
        "J": {"T": 0.9, "Y": 0.8, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.9, "Y": 0.8, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.8, "T": 0.8, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.75, "Q": 0.75},
        "O": {"Q": 0.85},
        "Q": {}
    }

    inc_matrix = {
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
    result = find_highest_similarity_pair(sub_matrix)
    if result:
        area1, area2, sim = result
        print(f"\nHighest subordinate similarity pair:")
        print(f"  {area1} - {area2}: {sim:.3f}")

    # Build step 1
    step = build_acc_step_1(sub_matrix, inc_matrix, unit=1.0)

    if step:
        print(f"\n{step['description']}")
        cluster = step['cluster']

        print(f"\nCluster properties:")
        cluster_structure = format_cluster_structure(cluster.get('structure', sorted(cluster['members'])))
        print(f"  Structure: {cluster_structure}")
        print(f"  Radius: {cluster['radius']:.3f}")
        print(f"  Diameter: {cluster['diameter']:.3f}")
        print(f"  Angle: {cluster['angle']:.2f}°")
        print(f"  Subordinate similarity: {cluster['sub_sim']:.3f}")
        print(f"  Inclusive similarity: {cluster['inc_sim']:.3f}")

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
    result = find_next_highest_similarity(sub_matrix, inc_matrix, placed_areas, method='average')

    if result:
        item1, item2, sub_sim, inc_sim, merged_sub, merged_inc = result

        print(f"\nMerged matrix (Subordinate):")
        print(f"  Areas/Clusters: {sorted(merged_sub.keys())}")

        print(f"\nNext highest subordinate similarity pair:")
        print(f"  {item1} - {item2}: {sub_sim:.3f}")
        print(f"  Inclusive similarity: {inc_sim:.3f}")

        print(f"\nDetailed similarities in merged subordinate matrix:")
        for area in sorted(merged_sub.keys()):
            sims = merged_sub[area]
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

    steps = build_acc_iterative(sub_matrix, inc_matrix, unit=1.0, method='average')

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
