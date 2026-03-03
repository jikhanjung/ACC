"""
ACC Render Paper — Paper algorithm (4-step incremental procedure) for ACC rendering.

Implements the ACC procedure described in the reference paper:
  - Section 2.3.1: Add area to cluster (clockwise)
  - Section 2.3.2: Merge two clusters
  - Section 2.3.3: Area sequence (α-diversity based)

Takes the same tree (root, merge_log) built by build_acc_tree() and produces
coordinates using the paper's incremental angular/diameter logic instead of the
tree-based recursive angle splitting.
"""

import logging
import math
from dataclasses import dataclass, field

from acc_core_tree import (
    _collect_leaf_diversity,
    _subtree_for_step,
    get_similarity,
    pol2cart,
)

logger = logging.getLogger("ACC_Paper")

THETA_MAX_DEGREES = 180.0


# ────────────────────────────────────────────────────────────
# Data structure
# ────────────────────────────────────────────────────────────
@dataclass
class ClusterState:
    """Incremental cluster state during paper algorithm rendering."""

    sequence: list          # ordered area names, e.g. ['A', 'B', 'D', 'C']
    sub_angles: list        # angles between adjacent pairs, len = len(sequence)-1
    area_radius: dict       # area → radius from centre
    total_angle: float      # θ of this cluster
    total_diameter: float   # d of this cluster
    local_sim: float        # local similarity score


@dataclass
class CachedStep:
    """Cached rendering decisions for re-render (sequence preserved)."""

    sequence: list
    sub_angles: list        # after all adjustments
    area_radius: dict
    total_angle: float
    total_diameter: float
    local_sim: float
    # ratio info for proportional re-render
    angle_ratios: list = field(default_factory=list)   # sub_angle / total_angle
    radius_ratios: dict = field(default_factory=dict)  # area → radius / max_radius


# ────────────────────────────────────────────────────────────
# Pairwise distance on a circle
# ────────────────────────────────────────────────────────────
def _pairwise_distance_on_circle(angle_deg, radius1, radius2):
    """Chord distance between two points on (possibly different) circles.

    Points are separated by angle_deg, at radii radius1 and radius2 from centre.
    Uses law of cosines: d² = r1² + r2² - 2*r1*r2*cos(θ)
    """
    rad = math.radians(angle_deg)
    d2 = radius1**2 + radius2**2 - 2 * radius1 * radius2 * math.cos(rad)
    return math.sqrt(max(0.0, d2))


def _angular_separation(sequence, sub_angles, area1, area2):
    """Total angle between two areas in a sequence."""
    try:
        i1 = sequence.index(area1)
        i2 = sequence.index(area2)
    except ValueError:
        return float("inf")
    lo, hi = min(i1, i2), max(i1, i2)
    return sum(sub_angles[lo:hi])


# ────────────────────────────────────────────────────────────
# Core algorithm functions
# ────────────────────────────────────────────────────────────
def _create_pair(left_node, right_node, merged_node, radius_fn,
                 local_matrix, global_matrix, diversity):
    """Create initial 2-area cluster.

    α-diversity determines sequence order: higher diversity → first.
    """
    left_name = next(iter(left_node.members))
    right_name = next(iter(right_node.members))

    div_left = diversity.get(left_name, 0)
    div_right = diversity.get(right_name, 0)

    # Higher diversity first; tie-break alphabetical
    if div_left > div_right:
        first, second = left_name, right_name
    elif div_right > div_left:
        first, second = right_name, left_name
    else:
        first, second = sorted([left_name, right_name])

    radius = radius_fn(merged_node.global_sim)

    return ClusterState(
        sequence=[first, second],
        sub_angles=[merged_node.angle],
        area_radius={first: radius, second: radius},
        total_angle=merged_node.angle,
        total_diameter=merged_node.diameter,
        local_sim=merged_node.local_sim,
    )


def _add_area(existing_state, new_area_name, merged_node, radius_fn,
              local_matrix):
    """Paper Section 2.3.1 — Add area to cluster.

    existing_state: ClusterState of cluster 1 (the less inclusive, higher-sim cluster)
    new_area_name: the area being added
    merged_node: ACCNode of cluster 2 (the more inclusive cluster)

    The new area is placed on the merged cluster's circle, whose radius is
    determined by merged_node.global_sim — the average pairwise global similarity
    across the cluster boundary, computed by build_acc_tree following the LOCAL
    topology.  We do NOT look up pairwise values from the global matrix directly,
    because that would follow the global dendrogram's topology instead.

    Returns updated ClusterState.
    """
    # θ₁ = existing cluster angle, θ₂ = merged (more inclusive) cluster angle
    theta1 = existing_state.total_angle
    theta2 = merged_node.angle

    # Step 2: θ_btw = θ₂ - θ₁/2
    theta_btw = theta2 - theta1 / 2.0

    # Find closest pair: compare local scores of (existing_area, new_area)
    # against cluster 1's local score
    cluster1_score = existing_state.local_sim
    best_pair_area = None
    best_diff = float("inf")
    for area in existing_state.sequence:
        sim = get_similarity(local_matrix, area, new_area_name)
        if sim is None:
            sim = 0.0
        diff = abs(sim - cluster1_score)
        if diff < best_diff:
            best_diff = diff
            best_pair_area = area
            best_pair_sim = sim

    # Two candidate sequences: append or prepend
    seq_append = list(existing_state.sequence) + [new_area_name]
    seq_prepend = [new_area_name] + list(existing_state.sequence)

    # Sub-angles for each candidate
    angles_append = list(existing_state.sub_angles) + [theta_btw]
    angles_prepend = [theta_btw] + list(existing_state.sub_angles)

    # Calculate angular separation of closest pair in each sequence
    sep_append = _angular_separation(seq_append, angles_append, best_pair_area, new_area_name)
    sep_prepend = _angular_separation(seq_prepend, angles_prepend, best_pair_area, new_area_name)

    # Select sequence with shorter angular separation for the closest pair
    if sep_append <= sep_prepend:
        chosen_seq = seq_append
        chosen_angles = angles_append
    else:
        chosen_seq = seq_prepend
        chosen_angles = angles_prepend

    # Step 3: Revert θ_btw to original pairwise value
    theta_original = THETA_MAX_DEGREES * (1.0 - best_pair_sim)
    # Find the index of theta_btw in chosen_angles and replace it
    btw_idx = _find_btw_index(chosen_seq, chosen_angles, best_pair_area, new_area_name, theta_btw)
    chosen_angles[btw_idx] = theta_original

    total_after_reversion = sum(chosen_angles)

    # Step 4: Proportional θ adjustment
    if total_after_reversion > theta2:
        scale = theta2 / total_after_reversion
        chosen_angles = [a * scale for a in chosen_angles]

    # Radius for new area: use the merged cluster's global_sim (local-topology-based).
    # merged_node.global_sim = avg pairwise global similarity across the cluster
    # boundary, computed by build_acc_tree following LOCAL topology — NOT the
    # global UPGMA tree value.
    new_radius = radius_fn(merged_node.global_sim)

    # Build updated area_radius
    area_radius = dict(existing_state.area_radius)
    area_radius[new_area_name] = new_radius
    # d is maintained for existing areas (no scaling)

    return ClusterState(
        sequence=chosen_seq,
        sub_angles=chosen_angles,
        area_radius=area_radius,
        total_angle=theta2,
        total_diameter=merged_node.diameter,
        local_sim=merged_node.local_sim,
    )


def _merge_clusters(state1, state2, merged_node, radius_fn,
                    local_matrix, global_matrix, diversity):
    """Paper Section 2.3.2 — Merge two clusters.

    state1: ClusterState with higher local_sim (cluster 1)
    state2: ClusterState with lower local_sim (cluster 2)
    merged_node: ACCNode of cluster 3 (most inclusive)

    Returns updated ClusterState.
    """
    theta1 = state1.total_angle
    theta2 = state2.total_angle
    theta3 = merged_node.angle

    # Step 2: θ_btw = θ₃ - θ₁/2 - θ₂/2
    theta_btw = theta3 - theta1 / 2.0 - theta2 / 2.0

    # Find closest inter-cluster pair: compare against cluster 1's score
    cluster1_score = state1.local_sim
    best_pair = None
    best_diff = float("inf")
    best_pair_sim = 0.0
    for a1 in state1.sequence:
        for a2 in state2.sequence:
            sim = get_similarity(local_matrix, a1, a2)
            if sim is None:
                sim = 0.0
            diff = abs(sim - cluster1_score)
            if diff < best_diff:
                best_diff = diff
                best_pair = (a1, a2)
                best_pair_sim = sim

    # Four candidate sequences
    s1 = list(state1.sequence)
    s2 = list(state2.sequence)
    s2_rev = list(reversed(state2.sequence))

    candidates = [
        (s1 + s2, list(state1.sub_angles) + [theta_btw] + list(state2.sub_angles)),
        (s1 + s2_rev, list(state1.sub_angles) + [theta_btw] + list(reversed(state2.sub_angles))),
        (s2 + s1, list(state2.sub_angles) + [theta_btw] + list(state1.sub_angles)),
        (s2_rev + s1, list(reversed(state2.sub_angles)) + [theta_btw] + list(state1.sub_angles)),
    ]

    # Select candidate with shortest angular separation for closest pair
    best_sep = float("inf")
    chosen_seq = None
    chosen_angles = None
    for seq, angles in candidates:
        sep = _angular_separation(seq, angles, best_pair[0], best_pair[1])
        if sep < best_sep:
            best_sep = sep
            chosen_seq = seq
            chosen_angles = angles

    # Step 3: Revert θ_btw to original pairwise value
    theta_original = THETA_MAX_DEGREES * (1.0 - best_pair_sim)
    btw_idx = _find_btw_index(chosen_seq, chosen_angles, best_pair[0], best_pair[1], theta_btw)
    chosen_angles[btw_idx] = theta_original

    total_after_reversion = sum(chosen_angles)

    # Step 4: Proportional θ adjustment
    if total_after_reversion > theta3:
        scale = theta3 / total_after_reversion
        chosen_angles = [a * scale for a in chosen_angles]

    # Proportional d adjustment
    area_radius = {}
    area_radius.update(state1.area_radius)
    area_radius.update(state2.area_radius)

    max_existing_d = max(state1.total_diameter, state2.total_diameter)
    d3 = merged_node.diameter
    if d3 > max_existing_d and max_existing_d > 0:
        d_scale = d3 / max_existing_d
        area_radius = {a: r * d_scale for a, r in area_radius.items()}

    return ClusterState(
        sequence=chosen_seq,
        sub_angles=chosen_angles,
        area_radius=area_radius,
        total_angle=theta3,
        total_diameter=merged_node.diameter,
        local_sim=merged_node.local_sim,
    )


def _find_btw_index(sequence, angles, area1, area2, theta_btw):
    """Find the sub_angle index that represents θ_btw between area1 and area2.

    This is the angle at the boundary between the existing cluster and the new
    area/cluster. We look for the angle entry that equals theta_btw and lies
    between the two areas.
    """
    try:
        i1 = sequence.index(area1)
        i2 = sequence.index(area2)
    except ValueError:
        return 0
    lo, hi = min(i1, i2), max(i1, i2)
    # Find the angle closest to theta_btw in the range [lo, hi)
    best_idx = lo
    best_diff = float("inf")
    for idx in range(lo, hi):
        diff = abs(angles[idx] - theta_btw)
        if diff < best_diff:
            best_diff = diff
            best_idx = idx
    return best_idx


# ────────────────────────────────────────────────────────────
# Coordinate computation
# ────────────────────────────────────────────────────────────
def _compute_positions(state, direction=0.0):
    """Compute Cartesian coordinates from ClusterState.

    Areas are placed along the sequence, spanning total_angle centred on `direction`.
    Each area sits on its own circle (area_radius).

    Args:
        state: ClusterState with sequence, sub_angles, area_radius.
        direction: compass direction in degrees (0° = north) for midpoint.

    Returns:
        dict mapping area_name → (x, y).
    """
    n = len(state.sequence)
    if n == 0:
        return {}
    if n == 1:
        name = state.sequence[0]
        r = state.area_radius.get(name, 0.0)
        # Single area on circle at the direction
        angle_acc = -direction  # compass → ACC convention
        return {name: pol2cart(r, angle_acc)}

    # Calculate cumulative angles from start
    total = sum(state.sub_angles)
    half_total = total / 2.0

    # First area starts at direction - half_total
    # Each subsequent area is offset by sub_angles[i]
    positions = {}
    current_angle = direction - half_total  # compass angle of first area

    for i, name in enumerate(state.sequence):
        r = state.area_radius.get(name, 0.0)
        angle_acc = -current_angle  # compass → ACC convention
        positions[name] = pol2cart(r, angle_acc)
        if i < len(state.sub_angles):
            current_angle += state.sub_angles[i]

    return positions


# ────────────────────────────────────────────────────────────
# Main rendering function
# ────────────────────────────────────────────────────────────
def render_paper(root, merge_log, local_matrix, global_matrix,
                 radius_fn, diversity):
    """Render ACC using the paper's incremental 4-step procedure.

    Takes the tree built by build_acc_tree() and produces coordinates
    using the paper algorithm instead of recursive angle splitting.

    Args:
        root: ACCNode root of the tree.
        merge_log: list of (merge_order, parent_node) tuples.
        local_matrix: dict-of-dict local similarity matrix.
        global_matrix: dict-of-dict global similarity matrix.
        radius_fn: function mapping global_sim → display radius.
        diversity: dict mapping area_name → int (present taxa count).

    Returns:
        (steps, cached_steps) where:
          steps: list of step dicts for GUI
          cached_steps: list of CachedStep for re-rendering
    """
    if not merge_log:
        return [], []

    # Map: frozenset(members) → ClusterState
    cluster_states = {}
    cached_steps = []

    steps = []

    for step_idx, (merge_order, merged_node) in enumerate(merge_log):
        left = merged_node.left
        right = merged_node.right

        if left.is_leaf and right.is_leaf:
            # Create initial pair
            state = _create_pair(left, right, merged_node, radius_fn,
                                 local_matrix, global_matrix, diversity)
            action = "initial" if step_idx == 0 else "new_pair"
            highlighted = merged_node.members

        elif left.is_leaf or right.is_leaf:
            # Add area to cluster
            if left.is_leaf:
                new_node, existing_node = left, right
            else:
                new_node, existing_node = right, left

            new_area_name = next(iter(new_node.members))
            existing_key = frozenset(existing_node.members)

            if existing_key not in cluster_states:
                # Existing cluster might be a leaf that was never created as a state
                # This shouldn't happen in normal flow, but handle gracefully
                existing_state = ClusterState(
                    sequence=sorted(existing_node.members),
                    sub_angles=[],
                    area_radius={m: radius_fn(existing_node.global_sim)
                                 for m in existing_node.members},
                    total_angle=existing_node.angle,
                    total_diameter=existing_node.diameter,
                    local_sim=existing_node.local_sim,
                )
            else:
                existing_state = cluster_states[existing_key]

            state = _add_area(existing_state, new_area_name, merged_node,
                              radius_fn, local_matrix)
            action = "add_area"
            highlighted = new_node.members

        else:
            # Merge two clusters
            key_left = frozenset(left.members)
            key_right = frozenset(right.members)

            state_left = cluster_states.get(key_left)
            state_right = cluster_states.get(key_right)

            # Fallback for missing states
            if state_left is None:
                state_left = _make_fallback_state(left, radius_fn)
            if state_right is None:
                state_right = _make_fallback_state(right, radius_fn)

            # Higher local_sim → state1 (cluster 1)
            if state_left.local_sim >= state_right.local_sim:
                s1, s2 = state_left, state_right
            else:
                s1, s2 = state_right, state_left

            state = _merge_clusters(s1, s2, merged_node, radius_fn,
                                    local_matrix, global_matrix, diversity)
            action = "merge_clusters"
            highlighted = set()

        # Store state
        merged_key = frozenset(merged_node.members)
        cluster_states[merged_key] = state

        # Cache for re-render
        total = sum(state.sub_angles) if state.sub_angles else 1.0
        angle_ratios = [a / total if total > 0 else 0 for a in state.sub_angles]
        max_r = max(state.area_radius.values()) if state.area_radius else 1.0
        radius_ratios = {a: r / max_r if max_r > 0 else 0
                         for a, r in state.area_radius.items()}

        cached = CachedStep(
            sequence=list(state.sequence),
            sub_angles=list(state.sub_angles),
            area_radius=dict(state.area_radius),
            total_angle=state.total_angle,
            total_diameter=state.total_diameter,
            local_sim=state.local_sim,
            angle_ratios=angle_ratios,
            radius_ratios=radius_ratios,
        )
        cached_steps.append(cached)

        # Build step dict for GUI
        active_nodes = _subtree_for_step(root, merge_order)

        cluster_dicts = []
        placed_areas = set()
        for node in active_nodes:
            placed_areas |= node.members
            node_key = frozenset(node.members)

            if node.is_leaf:
                name = next(iter(node.members))
                node.points = {name: (0.0, 0.0)}
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": {name: (0.0, 0.0)},
                    "radius": 0,
                    "diameter": 0,
                    "angle": node.angle,
                    "local_sim": node.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })
            elif node_key in cluster_states:
                ns = cluster_states[node_key]
                points = _compute_positions(ns)
                node.points = points
                max_radius = max(ns.area_radius.values()) if ns.area_radius else 0
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": points,
                    "radius": max_radius,
                    "diameter": max_radius * 2.0,
                    "angle": ns.total_angle,
                    "local_sim": ns.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })
            else:
                # Fallback: node not yet processed
                node.points = dict.fromkeys(node.members, (0.0, 0.0))
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": dict(node.points),
                    "radius": 0,
                    "diameter": 0,
                    "angle": node.angle,
                    "local_sim": node.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })

        # Description
        left_members = merged_node.left.members if merged_node.left else set()
        right_members = merged_node.right.members if merged_node.right else set()
        desc = _make_description(action, step_idx, merged_node, left_members, right_members)

        steps.append({
            "step": step_idx,
            "action": action,
            "description": desc,
            "clusters": cluster_dicts,
            "highlighted_members": highlighted,
            "placed_areas": placed_areas,
        })

    return steps, cached_steps


def _make_fallback_state(node, radius_fn):
    """Create a ClusterState for a node that wasn't tracked (shouldn't happen normally)."""
    members = sorted(node.members)
    n = len(members)
    radius = radius_fn(node.global_sim)
    if n <= 1:
        sub_angles = []
    else:
        per_angle = node.angle / (n - 1) if n > 1 else 0
        sub_angles = [per_angle] * (n - 1)
    return ClusterState(
        sequence=members,
        sub_angles=sub_angles,
        area_radius=dict.fromkeys(members, radius),
        total_angle=node.angle,
        total_diameter=node.diameter,
        local_sim=node.local_sim,
    )


def _format_members(members):
    """Format member set for display."""
    return "(" + ", ".join(sorted(members)) + ")"


def _make_description(action, step_idx, merged_node, left_members, right_members):
    """Generate step description string."""
    if action == "initial":
        return (
            f"Initial: {_format_members(left_members)} and "
            f"{_format_members(right_members)} "
            f"(local={merged_node.local_sim:.3f}, global={merged_node.global_sim:.3f})"
        )
    if action == "new_pair":
        return (
            f"New pair: {_format_members(left_members)} and "
            f"{_format_members(right_members)} "
            f"(local={merged_node.local_sim:.3f}, global={merged_node.global_sim:.3f})"
        )
    if action == "add_area":
        if len(left_members) == 1:
            new_m, exist_m = left_members, right_members
        else:
            new_m, exist_m = right_members, left_members
        return (
            f"Add {_format_members(new_m)} to "
            f"{_format_members(exist_m)} "
            f"(sim={merged_node.local_sim:.3f})"
        )
    # merge_clusters
    return (
        f"Merge {_format_members(left_members)} and "
        f"{_format_members(right_members)} "
        f"(sim={merged_node.local_sim:.3f})"
    )


# ────────────────────────────────────────────────────────────
# Re-render with cached sequences
# ────────────────────────────────────────────────────────────
def rerender_paper(root, merge_log, cached_steps, local_matrix, global_matrix,
                   radius_fn, diversity):
    """Re-render using cached sequence decisions but new radius_fn.

    Sequence order and angle ratios are preserved. Only radii change.

    Args:
        root: ACCNode root.
        merge_log: list of (merge_order, parent_node) tuples.
        cached_steps: list of CachedStep from previous render_paper().
        local_matrix, global_matrix: similarity matrices.
        radius_fn: new radius function (from changed diameter settings).
        diversity: dict mapping area_name → present taxa count.

    Returns:
        steps: list of step dicts for GUI.
    """
    if not merge_log or not cached_steps:
        return []

    # Rebuild cluster_states from cached info, applying new radius_fn
    cluster_states = {}
    steps = []

    for step_idx, (merge_order, merged_node) in enumerate(merge_log):
        if step_idx >= len(cached_steps):
            break

        cached = cached_steps[step_idx]

        # Recompute area_radius using new radius_fn but same ratios
        new_max_radius = radius_fn(merged_node.global_sim)
        area_radius = {}
        for area, ratio in cached.radius_ratios.items():
            area_radius[area] = ratio * new_max_radius if new_max_radius > 0 else 0

        # Recompute sub_angles: keep ratios, apply to merged_node.angle
        new_total_angle = merged_node.angle
        sub_angles = [r * new_total_angle for r in cached.angle_ratios]

        state = ClusterState(
            sequence=list(cached.sequence),
            sub_angles=sub_angles,
            area_radius=area_radius,
            total_angle=new_total_angle,
            total_diameter=merged_node.diameter,
            local_sim=merged_node.local_sim,
        )

        merged_key = frozenset(merged_node.members)
        cluster_states[merged_key] = state

        # Build step dict
        active_nodes = _subtree_for_step(root, merge_order)

        left = merged_node.left
        right = merged_node.right
        left_members = left.members if left else set()
        right_members = right.members if right else set()

        if left.is_leaf and right.is_leaf:
            action = "initial" if step_idx == 0 else "new_pair"
            highlighted = merged_node.members
        elif left.is_leaf or right.is_leaf:
            action = "add_area"
            new_node = left if left.is_leaf else right
            highlighted = new_node.members
        else:
            action = "merge_clusters"
            highlighted = set()

        cluster_dicts = []
        placed_areas = set()
        for node in active_nodes:
            placed_areas |= node.members
            node_key = frozenset(node.members)

            if node.is_leaf:
                name = next(iter(node.members))
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": {name: (0.0, 0.0)},
                    "radius": 0,
                    "diameter": 0,
                    "angle": node.angle,
                    "local_sim": node.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })
            elif node_key in cluster_states:
                ns = cluster_states[node_key]
                points = _compute_positions(ns)
                max_radius = max(ns.area_radius.values()) if ns.area_radius else 0
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": points,
                    "radius": max_radius,
                    "diameter": max_radius * 2.0,
                    "angle": ns.total_angle,
                    "local_sim": ns.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })
            else:
                cluster_dicts.append({
                    "members": set(node.members),
                    "points": dict.fromkeys(node.members, (0.0, 0.0)),
                    "radius": 0,
                    "diameter": 0,
                    "angle": node.angle,
                    "local_sim": node.local_sim,
                    "global_sim": node.global_sim,
                    "internal_nodes": [],
                    "diversity": _collect_leaf_diversity(node),
                })

        desc = _make_description(action, step_idx, merged_node, left_members, right_members)

        steps.append({
            "step": step_idx,
            "action": action,
            "description": desc,
            "clusters": cluster_dicts,
            "highlighted_members": highlighted,
            "placed_areas": placed_areas,
        })

    return steps
