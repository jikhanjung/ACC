"""
ACC Core Tree — Tree-based ACC algorithm implementation.

Builds an explicit ACCNode binary tree (with sim, diameter, angle stored at each node),
then renders coordinates in a separate pass.  Diameter changes trigger re-render only
(no tree rebuild).

Key differences from acc_core_new.py:
  - Explicit ACCNode tree instead of dict-based "structure"
  - Diversity index determines left/right ordering of leaves
  - Edge similarity determines ordering when merging clusters
  - Separate build (tree) and render (coordinates) phases
"""

import logging
import math
from dataclasses import dataclass, field
from itertools import combinations

logger = logging.getLogger("ACC_Tree")

THETA_MAX_DEGREES = 180.0
DEFAULT_SIMILARITY = 0.5
DEFAULT_MIN_DIAMETER = 1.0   # diameter at similarity=1
DEFAULT_MAX_DIAMETER = 6.0   # diameter at similarity≈0


# ────────────────────────────────────────────────────────────
# Data structure
# ────────────────────────────────────────────────────────────
@dataclass
class ACCNode:
    """Binary tree node representing a cluster in the ACC algorithm."""

    members: set
    left: "ACCNode | None" = None
    right: "ACCNode | None" = None
    local_sim: float = 1.0
    global_sim: float = 1.0
    diameter: float = 0.0
    angle: float = 0.0
    merge_order: int = -1  # -1 = leaf, 0+ = merge step
    diversity: int = 0     # leaf only: count of present taxa
    points: dict = field(default_factory=dict)

    @property
    def is_leaf(self) -> bool:
        return self.left is None and self.right is None

    @property
    def leftmost_leaf(self) -> "ACCNode":
        node = self
        while node.left is not None:
            node = node.left
        return node

    @property
    def rightmost_leaf(self) -> "ACCNode":
        node = self
        while node.right is not None:
            node = node.right
        return node

    @property
    def radius(self) -> float:
        return self.diameter / 2.0


# ────────────────────────────────────────────────────────────
# Utility functions (same conventions as acc_core_new.py)
# ────────────────────────────────────────────────────────────
def pol2cart(r, angle_deg):
    """Polar to Cartesian. 0° = north (0,1), +90° rotation."""
    rad = math.radians(angle_deg + 90)
    return (r * math.cos(rad), r * math.sin(rad))


def cart2pol(x, y):
    """Cartesian to polar. 0° = north."""
    r = math.sqrt(x**2 + y**2)
    angle_rad = math.atan2(y, x)
    angle_deg = math.degrees(angle_rad) - 90
    return (r, angle_deg)


def get_similarity(matrix, area1, area2):
    """Look up similarity in a dict-of-dict matrix (tries both directions)."""
    if area1 in matrix and area2 in matrix[area1]:
        return matrix[area1][area2]
    if area2 in matrix and area1 in matrix[area2]:
        return matrix[area2][area1]
    return None


def average_pairwise_similarity(members, matrix):
    """Average pairwise similarity for a set of members."""
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


def find_highest_similarity_pair(local_matrix):
    """Return (area1, area2, similarity) for the highest-sim pair."""
    best_pair = None
    best_sim = -1.0
    areas = list(local_matrix.keys())
    for area1, area2 in combinations(areas, 2):
        sim = get_similarity(local_matrix, area1, area2)
        if sim is not None and sim > best_sim:
            best_sim = sim
            best_pair = (area1, area2)
    if best_pair:
        return (best_pair[0], best_pair[1], best_sim)
    return None


# ────────────────────────────────────────────────────────────
# Left/Right ordering
# ────────────────────────────────────────────────────────────
def _determine_order(node_a, node_b, local_matrix, _diversity=None):
    """Decide which node is left vs right.

    Rules:
      - Two leaves: higher diversity → left. Tie → alphabetical.
      - Otherwise: compare edge similarities to decide adjacency.
    """
    if node_a.is_leaf and node_b.is_leaf:
        div_a = node_a.diversity
        div_b = node_b.diversity
        if div_a > div_b:
            return node_a, node_b
        if div_b > div_a:
            return node_b, node_a
        # tie-break: alphabetical
        name_a = next(iter(node_a.members))
        name_b = next(iter(node_b.members))
        return (node_a, node_b) if name_a <= name_b else (node_b, node_a)

    # Edge similarity: which arrangement puts the most-similar edges adjacent?
    a_right = next(iter(node_a.rightmost_leaf.members))
    b_left = next(iter(node_b.leftmost_leaf.members))
    b_right = next(iter(node_b.rightmost_leaf.members))
    a_left = next(iter(node_a.leftmost_leaf.members))

    sim_ab = get_similarity(local_matrix, a_right, b_left) or 0
    sim_ba = get_similarity(local_matrix, b_right, a_left) or 0

    if sim_ab >= sim_ba:
        return node_a, node_b
    return node_b, node_a


# ────────────────────────────────────────────────────────────
# Tree building
# ────────────────────────────────────────────────────────────
def build_acc_tree(local_matrix, global_matrix, unit=1.0, method="weighted",
                   diversity=None):
    """Build an ACCNode tree using greedy agglomeration (WPGMA).

    Uses simple /2 averaging at each merge (WPGMA), matching the dendrogram
    display in the GUI (ClusteringStepManager with method='weighted').

    Args:
        local_matrix: dict-of-dict local similarity matrix.
        global_matrix: dict-of-dict global similarity matrix.
        unit: diameter scaling factor.
        method: kept for API compatibility (always uses WPGMA).
        diversity: dict mapping area name → int (present taxa count).
                   If None, all areas get diversity=0.

    Returns:
        root: ACCNode (root of the tree).
        merge_log: list of (merge_order, parent_node) tuples.
    """
    if diversity is None:
        diversity = {}

    # Create leaf nodes
    active_nodes: list[ACCNode] = []
    for area in sorted(local_matrix.keys()):
        node = ACCNode(
            members={area},
            diversity=diversity.get(area, 0),
        )
        active_nodes.append(node)

    # Initialise WPGMA similarity caches with leaf-level pairwise values.
    # Keys are frozenset pairs so order doesn't matter.
    local_cache: dict[tuple, float] = {}
    global_cache: dict[tuple, float] = {}
    for i, na in enumerate(active_nodes):
        for j, nb in enumerate(active_nodes):
            if i == j:
                continue
            a = next(iter(na.members))
            b = next(iter(nb.members))
            key = (frozenset(na.members), frozenset(nb.members))
            ls = get_similarity(local_matrix, a, b)
            gs = get_similarity(global_matrix, a, b)
            local_cache[key] = ls if ls is not None else DEFAULT_SIMILARITY
            global_cache[key] = gs if gs is not None else DEFAULT_SIMILARITY

    def _get(cache, fa, fb):
        return cache.get((fa, fb), cache.get((fb, fa), DEFAULT_SIMILARITY))

    merge_log: list[tuple[int, ACCNode]] = []
    merge_counter = 0

    while len(active_nodes) > 1:
        # Find the pair with highest WPGMA local similarity.
        best_sim = -1.0
        best_i, best_j = 0, 1
        for i in range(len(active_nodes)):
            for j in range(i + 1, len(active_nodes)):
                fa = frozenset(active_nodes[i].members)
                fb = frozenset(active_nodes[j].members)
                sim = _get(local_cache, fa, fb)
                if sim > best_sim:
                    best_sim = sim
                    best_i, best_j = i, j

        node_a = active_nodes[best_i]
        node_b = active_nodes[best_j]
        fa = frozenset(node_a.members)
        fb = frozenset(node_b.members)

        new_local_sim = _get(local_cache, fa, fb)
        new_global_sim = _get(global_cache, fa, fb)

        # Geometry
        new_diameter = unit / new_global_sim if new_global_sim > 0 else unit * 100
        new_angle = THETA_MAX_DEGREES * (1.0 - new_local_sim)

        # Determine left/right order
        left, right = _determine_order(node_a, node_b, local_matrix, diversity)

        parent = ACCNode(
            members=node_a.members | node_b.members,
            left=left,
            right=right,
            local_sim=new_local_sim,
            global_sim=new_global_sim,
            diameter=new_diameter,
            angle=new_angle,
            merge_order=merge_counter,
        )

        # Update WPGMA caches for the new merged node with every remaining node.
        # WPGMA recurrence: sim(A∪B, C) = (sim(A, C) + sim(B, C)) / 2
        new_members = frozenset(parent.members)
        for node_c in active_nodes:
            if node_c is node_a or node_c is node_b:
                continue
            fc = frozenset(node_c.members)
            new_ls = (_get(local_cache, fa, fc) + _get(local_cache, fb, fc)) / 2.0
            new_gs = (_get(global_cache, fa, fc) + _get(global_cache, fb, fc)) / 2.0
            local_cache[(new_members, fc)] = new_ls
            local_cache[(fc, new_members)] = new_ls
            global_cache[(new_members, fc)] = new_gs
            global_cache[(fc, new_members)] = new_gs

        merge_log.append((merge_counter, parent))
        merge_counter += 1

        # Remove old, add new
        if best_i < best_j:
            del active_nodes[best_j]
            del active_nodes[best_i]
        else:
            del active_nodes[best_i]
            del active_nodes[best_j]
        active_nodes.append(parent)

    root = active_nodes[0]
    return root, merge_log


# ────────────────────────────────────────────────────────────
# Coordinate rendering
# ────────────────────────────────────────────────────────────
def _make_radius_fn(min_diameter, max_diameter):
    """Build a function mapping global_sim → display radius.

    diameter = min_d + (max_d - min_d) * (1 - global_sim)
    radius   = diameter / 2

    min_diameter: diameter at sim=1 (default 1).
    max_diameter: diameter at sim≈0 (default 6).
    """
    min_d = min_diameter if min_diameter is not None else DEFAULT_MIN_DIAMETER
    max_d = max_diameter if max_diameter is not None else DEFAULT_MAX_DIAMETER

    def fn(global_sim):
        diameter = min_d + (max_d - min_d) * (1.0 - global_sim)
        return diameter / 2.0

    return fn


def _render_node(node, direction, radius_fn):
    """Recursively compute leaf coordinates.

    Args:
        node: ACCNode to render.
        direction: compass direction in degrees (0° = north).
        radius_fn: function mapping global_sim → display radius.
    """
    if node.is_leaf:
        return

    half_angle = node.angle / 2.0
    left_dir = direction - half_angle
    right_dir = direction + half_angle

    scaled_radius = radius_fn(node.global_sim)

    # Position left subtree leaves
    _position_subtree(node.left, left_dir, scaled_radius, radius_fn)
    # Position right subtree leaves
    _position_subtree(node.right, right_dir, scaled_radius, radius_fn)


def _position_subtree(node, direction, parent_radius, radius_fn):
    """Position all leaves in a subtree."""
    if node.is_leaf:
        name = next(iter(node.members))
        # Leaf on parent's circle at the given direction
        angle_acc = -direction  # Convert compass→ACC convention
        pos = pol2cart(parent_radius, angle_acc)
        node.points = {name: pos}
        return

    # Internal node: recurse into children
    half_angle = node.angle / 2.0
    left_dir = direction - half_angle
    right_dir = direction + half_angle

    scaled_radius = radius_fn(node.global_sim)

    _position_subtree(node.left, left_dir, scaled_radius, radius_fn)
    _position_subtree(node.right, right_dir, scaled_radius, radius_fn)

    # Collect points from children
    node.points = {}
    node.points.update(node.left.points)
    node.points.update(node.right.points)


def render_tree(root, min_diameter=None, max_diameter=None):
    """Compute coordinates for all leaves in the tree.

    Args:
        root: ACCNode root.
        min_diameter: diameter at sim=1 (default 1).
        max_diameter: diameter at sim≈0 (default 6).

    Modifies each node's .points dict in-place.
    """
    if root is None:
        return
    if root.is_leaf:
        name = next(iter(root.members))
        root.points = {name: (0.0, 0.0)}
        return

    radius_fn = _make_radius_fn(min_diameter, max_diameter)

    # Start rendering from root, direction = 0° (north)
    _position_subtree(root, 0.0, radius_fn(root.global_sim), radius_fn)


# ────────────────────────────────────────────────────────────
# Step generation for GUI
# ────────────────────────────────────────────────────────────
def _collect_nodes_by_merge_order(root):
    """Return list of internal nodes sorted by merge_order."""
    nodes = []

    def _walk(n):
        if n is None or n.is_leaf:
            return
        nodes.append(n)
        _walk(n.left)
        _walk(n.right)

    _walk(root)
    nodes.sort(key=lambda n: n.merge_order)
    return nodes


def _subtree_for_step(root, max_merge_order):
    """Identify which nodes/leaves are 'active' at a given merge step.

    At step k, all merges with merge_order <= k have happened.
    Returns list of top-level nodes (ACCNode) visible at that step.
    """
    def _walk(node):
        if node.is_leaf:
            return [node]
        if node.merge_order <= max_merge_order:
            # This merge has happened — node is active as a cluster
            return [node]
        # This merge hasn't happened yet — descend
        result = []
        result.extend(_walk(node.left))
        result.extend(_walk(node.right))
        return result

    return _walk(root)


def _collect_leaf_diversity(node):
    """Collect {area_name: diversity} from leaf nodes in a subtree."""
    if node is None:
        return {}
    if node.is_leaf:
        name = next(iter(node.members))
        return {name: node.diversity}
    result = {}
    result.update(_collect_leaf_diversity(node.left))
    result.update(_collect_leaf_diversity(node.right))
    return result


def _format_members(members):
    """Format member set for display."""
    return "(" + ", ".join(sorted(members)) + ")"


def _collect_internal_node_info(node, radius_fn, direction=0.0):
    """Collect internal node positions and metadata for GUI visualization.

    Each internal node is placed on its circle at the rendering direction.
    Root direction=0° → positive Y-axis.
    """
    if node is None or node.is_leaf:
        return []
    results = []
    sr = radius_fn(node.global_sim)
    angle_acc = -direction  # compass → ACC convention (same as _position_subtree)
    nx, ny = pol2cart(sr, angle_acc)
    results.append({
        "position": (nx, ny),
        "radius": sr,
        "members": sorted(node.members),
        "local_sim": node.local_sim,
        "global_sim": node.global_sim,
        "angle": node.angle,
        "diameter": sr * 2,
        "merge_order": node.merge_order,
    })
    half_angle = node.angle / 2.0
    left_dir = direction - half_angle
    right_dir = direction + half_angle
    results.extend(_collect_internal_node_info(node.left, radius_fn, left_dir))
    results.extend(_collect_internal_node_info(node.right, radius_fn, right_dir))
    return results


def generate_steps(root, merge_log, min_diameter=None, max_diameter=None):
    """Generate progressive step snapshots for GUI visualization.

    Args:
        root: ACCNode root of the tree.
        merge_log: list of (merge_order, parent_node) tuples.
        min_diameter: target minimum diameter.
        max_diameter: target maximum diameter.

    Returns:
        list of step dicts compatible with ACCVisualizationWidget.set_acc_steps().
    """
    if root is None:
        return []

    radius_fn = _make_radius_fn(min_diameter, max_diameter)

    steps = []

    for step_idx, (merge_order, merged_node) in enumerate(merge_log):
        # Get active top-level nodes at this step
        active_nodes = _subtree_for_step(root, merge_order)

        # Render each active node's coordinates
        for node in active_nodes:
            if node.is_leaf:
                name = next(iter(node.members))
                node.points = {name: (0.0, 0.0)}
            else:
                # Render this sub-tree with its own root direction = 0°
                _position_subtree(node, 0.0, radius_fn(node.global_sim), radius_fn)

        # Determine highlighted members and action
        left_members = merged_node.left.members if merged_node.left else set()
        right_members = merged_node.right.members if merged_node.right else set()

        if step_idx == 0:
            action = "initial"
            highlighted = merged_node.members
            desc = (
                f"Initial: {_format_members(left_members)} and "
                f"{_format_members(right_members)} "
                f"(local={merged_node.local_sim:.3f}, global={merged_node.global_sim:.3f})"
            )
        elif merged_node.left.is_leaf and merged_node.right.is_leaf:
            action = "new_pair"
            highlighted = merged_node.members
            desc = (
                f"New pair: {_format_members(left_members)} and "
                f"{_format_members(right_members)} "
                f"(local={merged_node.local_sim:.3f}, global={merged_node.global_sim:.3f})"
            )
        elif merged_node.left.is_leaf or merged_node.right.is_leaf:
            new_area = merged_node.left if merged_node.left.is_leaf else merged_node.right
            existing = merged_node.right if merged_node.left.is_leaf else merged_node.left
            action = "add_area"
            highlighted = new_area.members
            desc = (
                f"Add {_format_members(new_area.members)} to "
                f"{_format_members(existing.members)} "
                f"(sim={merged_node.local_sim:.3f})"
            )
        else:
            action = "merge_clusters"
            highlighted = set()
            desc = (
                f"Merge {_format_members(left_members)} and "
                f"{_format_members(right_members)} "
                f"(sim={merged_node.local_sim:.3f})"
            )

        # Build cluster dicts for the step
        placed_areas = set()
        cluster_dicts = []
        for node in active_nodes:
            placed_areas |= node.members
            scaled_radius = radius_fn(node.global_sim) if not node.is_leaf else 0
            cluster_dicts.append({
                "members": set(node.members),
                "points": dict(node.points),
                "radius": scaled_radius,
                "diameter": scaled_radius * 2.0,
                "angle": node.angle,
                "local_sim": node.local_sim,
                "global_sim": node.global_sim,
                "structure": _node_to_structure(node, radius_fn),
                "internal_nodes": _collect_internal_node_info(node, radius_fn) if not node.is_leaf else [],
                "diversity": _collect_leaf_diversity(node),
            })

        steps.append({
            "step": step_idx,
            "action": action,
            "description": desc,
            "clusters": cluster_dicts,
            "highlighted_members": highlighted,
            "placed_areas": placed_areas,
        })

    return steps


def _node_to_structure(node, radius_fn):
    """Convert ACCNode subtree to the dict structure expected by the GUI."""
    if node.is_leaf:
        return next(iter(node.members))

    left_struct = _node_to_structure(node.left, radius_fn)
    right_struct = _node_to_structure(node.right, radius_fn)
    return {
        "children": [left_struct, right_struct],
        "angle": node.angle,
        "radius": radius_fn(node.global_sim),
    }


# ────────────────────────────────────────────────────────────
# Top-level API
# ────────────────────────────────────────────────────────────
def build_acc_from_tree(local_matrix, global_matrix, unit=1.0, method="average",
                        min_diameter=None, max_diameter=None,
                        diversity=None):
    """Build ACC tree and generate step-by-step visualisation data.

    Args:
        local_matrix: dict-of-dict local similarity matrix.
        global_matrix: dict-of-dict global similarity matrix.
        unit: diameter scaling factor (default 1.0).
        method: linkage method (default "average").
        min_diameter: optional min diameter for scaling.
        max_diameter: optional max diameter for scaling.
        diversity: optional dict mapping area name → present taxa count.

    Returns:
        (root, steps) where root is the ACCNode tree root and steps is
        a list of step dicts for the GUI.
    """
    logger.info("Building ACC tree (areas=%d, unit=%.2f)", len(local_matrix), unit)

    root, merge_log = build_acc_tree(
        local_matrix, global_matrix, unit=unit, method=method, diversity=diversity,
    )

    # Attach merge_log to root for later re-rendering
    root._merge_log = merge_log

    # Full render
    render_tree(root, min_diameter=min_diameter, max_diameter=max_diameter)

    # Generate steps
    steps = generate_steps(root, merge_log, min_diameter=min_diameter, max_diameter=max_diameter)

    logger.info("ACC tree built: %d merges, %d steps", len(merge_log), len(steps))
    return root, steps
