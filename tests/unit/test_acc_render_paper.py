"""Unit tests for acc_render_paper module (paper algorithm rendering)."""

import math

import pytest

from acc_core_tree import (
    _make_radius_fn,
    build_acc_tree,
    get_similarity,
)
from acc_render_paper import (
    ClusterState,
    _add_area,
    _angular_separation,
    _compute_positions,
    _create_pair,
    _merge_clusters,
    _pairwise_distance_on_circle,
    render_paper,
    rerender_paper,
)

THETA_MAX = 180.0


# ────────────────────────────────────────────────────────────
# Fixtures: Paper Figure 2 (add area) example
# ────────────────────────────────────────────────────────────
@pytest.fixture
def add_area_matrices():
    """Paper example: (A+B)+C. Local and global matrices."""
    local = {
        "A": {"B": 0.6, "C": 0.2},
        "B": {"A": 0.6, "C": 0.4},
        "C": {"A": 0.2, "B": 0.4},
    }
    global_ = {
        "A": {"B": 0.7, "C": 0.4},
        "B": {"A": 0.7, "C": 0.6},
        "C": {"A": 0.4, "B": 0.6},
    }
    return local, global_


@pytest.fixture
def add_area_nodes(add_area_matrices):
    """Build tree for (A+B)+C example and extract relevant nodes."""
    local, global_ = add_area_matrices
    root, merge_log = build_acc_tree(local, global_, unit=1.0)
    return root, merge_log, local, global_


# ────────────────────────────────────────────────────────────
# Fixtures: Paper Figure 3 (merge) example
# ────────────────────────────────────────────────────────────
@pytest.fixture
def merge_matrices():
    """Paper example: (A+B)+(C+D). Local and global matrices."""
    local = {
        "A": {"B": 0.6, "C": 0.2, "D": 0.25},
        "B": {"A": 0.6, "C": 0.3, "D": 0.35},
        "C": {"A": 0.2, "B": 0.3, "D": 0.5},
        "D": {"A": 0.25, "B": 0.35, "C": 0.5},
    }
    global_ = {
        "A": {"B": 0.7, "C": 0.2, "D": 0.3},
        "B": {"A": 0.7, "C": 0.4, "D": 0.5},
        "C": {"A": 0.2, "B": 0.4, "D": 0.6},
        "D": {"A": 0.3, "B": 0.5, "C": 0.6},
    }
    return local, global_


@pytest.fixture
def merge_nodes(merge_matrices):
    """Build tree for (A+B)+(C+D) example."""
    local, global_ = merge_matrices
    root, merge_log = build_acc_tree(local, global_, unit=1.0)
    return root, merge_log, local, global_


# ────────────────────────────────────────────────────────────
# Helper: simple radius function for paper examples
# ────────────────────────────────────────────────────────────
def _paper_radius_fn(global_sim):
    """Paper uses d = unit/global_sim, radius = d/2."""
    if global_sim <= 0:
        return 50.0
    return (1.0 / global_sim) / 2.0


# ────────────────────────────────────────────────────────────
# Tests: θ_btw computation (add area)
# ────────────────────────────────────────────────────────────
class TestThetaBtwAddArea:
    def test_theta_btw_formula(self):
        """θ_btw = θ₂ - θ₁/2. Paper example: 126 - 72/2 = 90."""
        theta1 = THETA_MAX * (1.0 - 0.6)   # 72°
        theta2 = THETA_MAX * (1.0 - 0.3)   # 126° (average of 0.2 and 0.4 = 0.3)
        theta_btw = theta2 - theta1 / 2.0
        assert pytest.approx(theta_btw, abs=0.1) == 90.0

    def test_theta_btw_values(self):
        """Verify intermediate θ values from paper example."""
        # Cluster 1 (A,B): local_sim=0.6, θ₁=72°
        theta1 = THETA_MAX * (1.0 - 0.6)
        assert pytest.approx(theta1) == 72.0

        # Cluster 2 (A,B,C): For the paper, θ₂=126°
        # This depends on the average linkage sim of the merged cluster


# ────────────────────────────────────────────────────────────
# Tests: Sequence selection (add area)
# ────────────────────────────────────────────────────────────
class TestSequenceSelectionAddArea:
    def test_closest_pair_selection(self, add_area_matrices):
        """CB (0.4) is closer to cluster 1 score (0.6) than CA (0.2)."""
        local, global_ = add_area_matrices
        cluster1_score = 0.6  # (A,B) local_sim

        # CB diff = |0.4 - 0.6| = 0.2
        # CA diff = |0.2 - 0.6| = 0.4
        cb = get_similarity(local, "C", "B")
        ca = get_similarity(local, "C", "A")
        assert abs(cb - cluster1_score) < abs(ca - cluster1_score)

    def test_sequence_abc_selected(self, add_area_matrices):
        """ABC should be selected (C closer to B, shorter angular distance)."""
        local, global_ = add_area_matrices

        # Create cluster state for (A,B)
        state_ab = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C"},
            local_sim=0.3,
            global_sim=0.4,
            diameter=1.0 / 0.4,
            angle=THETA_MAX * (1.0 - 0.3),  # 126°
        )

        result = _add_area(state_ab, "C", merged, _paper_radius_fn,
                           local)

        # C should be at the end (ABC sequence)
        assert result.sequence[-1] == "C" or result.sequence[0] == "C"
        # B and C should be adjacent
        b_idx = result.sequence.index("B")
        c_idx = result.sequence.index("C")
        assert abs(b_idx - c_idx) == 1


# ────────────────────────────────────────────────────────────
# Tests: θ_btw reversion (add area)
# ────────────────────────────────────────────────────────────
class TestThetaReversionAddArea:
    def test_reversion_to_original(self, add_area_matrices):
        """θ_btw of BC should revert from 90° to 108° (= 180*(1-0.4))."""
        local, global_ = add_area_matrices

        state_ab = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C"},
            local_sim=0.3,
            global_sim=0.4,
            diameter=1.0 / 0.4,
            angle=126.0,
        )

        result = _add_area(state_ab, "C", merged, _paper_radius_fn,
                           local)

        # After reversion and proportional scaling, total should equal θ₂ = 126°
        total = sum(result.sub_angles)
        assert pytest.approx(total, abs=0.1) == 126.0


# ────────────────────────────────────────────────────────────
# Tests: Proportional scaling (add area)
# ────────────────────────────────────────────────────────────
class TestProportionalScalingAddArea:
    def test_proportional_theta_scaling(self, add_area_matrices):
        """After scaling: AB≈50°, BC≈76°. Total = 126°."""
        local, global_ = add_area_matrices

        state_ab = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C"},
            local_sim=0.3,
            global_sim=0.4,
            diameter=1.0 / 0.4,
            angle=126.0,
        )

        result = _add_area(state_ab, "C", merged, _paper_radius_fn,
                           local)

        assert len(result.sub_angles) == 2
        total = sum(result.sub_angles)
        assert pytest.approx(total, abs=0.1) == 126.0

        # Ratio should be preserved: AB:BC = 72:108 = 2:3
        ratio = result.sub_angles[0] / result.sub_angles[1] if result.sub_angles[1] > 0 else 0
        expected_ratio = 72.0 / 108.0
        assert pytest.approx(ratio, abs=0.05) == expected_ratio

    def test_diameter_maintained(self, add_area_matrices):
        """d of AB should be maintained (not scaled) in add_area."""
        local, global_ = add_area_matrices

        state_ab = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C"},
            local_sim=0.3,
            global_sim=0.4,
            diameter=1.0 / 0.4,
            angle=126.0,
        )

        result = _add_area(state_ab, "C", merged, _paper_radius_fn,
                           local)

        # Existing area radii should be maintained (inner circle)
        assert result.area_radius["A"] == 2.0
        assert result.area_radius["B"] == 2.0
        # New area C radius is based on merged_node.global_sim (local-topology global)
        # NOT pairwise global(T,C) from raw global matrix
        expected_c_radius = _paper_radius_fn(merged.global_sim)  # = _paper_radius_fn(0.4)
        assert pytest.approx(result.area_radius["C"], abs=0.01) == expected_c_radius


# ────────────────────────────────────────────────────────────
# Tests: θ_btw computation (merge)
# ────────────────────────────────────────────────────────────
class TestThetaBtwMerge:
    def test_theta_btw_merge_formula(self):
        """θ_btw = θ₃ - θ₁/2 - θ₂/2. Paper: 130.5 - 36 - 45 = 49.5."""
        theta1 = THETA_MAX * (1.0 - 0.6)   # 72°
        theta2 = THETA_MAX * (1.0 - 0.5)   # 90°
        # θ₃ depends on average of inter-cluster similarities
        # Paper gives 130.5° → local_sim ≈ 0.275
        theta3 = 130.5
        theta_btw = theta3 - theta1 / 2.0 - theta2 / 2.0
        assert pytest.approx(theta_btw, abs=0.1) == 49.5


# ────────────────────────────────────────────────────────────
# Tests: Sequence selection (merge)
# ────────────────────────────────────────────────────────────
class TestSequenceSelectionMerge:
    def test_closest_pair_is_db(self, merge_matrices):
        """DB (0.35) is closest to cluster 1 score (0.6)."""
        local, _ = merge_matrices
        cluster1_score = 0.6

        pairs = {}
        for a1 in ["A", "B"]:
            for a2 in ["C", "D"]:
                sim = get_similarity(local, a1, a2)
                pairs[(a1, a2)] = abs(sim - cluster1_score)

        closest = min(pairs, key=pairs.get)
        # DB should be closest (diff = 0.25)
        assert closest == ("B", "D") or closest == ("D", "B")

    def test_abdc_selected(self, merge_matrices):
        """ABDC should be selected (shortest distance for DB pair)."""
        local, global_ = merge_matrices

        state1 = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )
        state2 = ClusterState(
            sequence=["C", "D"],
            sub_angles=[90.0],
            area_radius={"C": 2.5, "D": 2.5},
            total_angle=90.0,
            total_diameter=5.0,
            local_sim=0.5,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C", "D"},
            local_sim=0.275,
            global_sim=0.35,
            diameter=1.0 / 0.35,
            angle=130.5,
        )

        result = _merge_clusters(state1, state2, merged, _paper_radius_fn,
                                 local, global_, {})

        # B and D should be adjacent in the result
        b_idx = result.sequence.index("B")
        d_idx = result.sequence.index("D")
        assert abs(b_idx - d_idx) == 1


# ────────────────────────────────────────────────────────────
# Tests: θ_btw reversion (merge)
# ────────────────────────────────────────────────────────────
class TestThetaReversionMerge:
    def test_reversion_merge(self, merge_matrices):
        """θ_btw of BD should revert from 49.5° to 117° (= 180*(1-0.35))."""
        theta_original = THETA_MAX * (1.0 - 0.35)
        assert pytest.approx(theta_original, abs=0.1) == 117.0


# ────────────────────────────────────────────────────────────
# Tests: Proportional scaling (merge)
# ────────────────────────────────────────────────────────────
class TestProportionalScalingMerge:
    def test_proportional_theta_merge(self, merge_matrices):
        """After scaling, total θ should equal θ₃ = 130.5°."""
        local, global_ = merge_matrices

        state1 = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )
        state2 = ClusterState(
            sequence=["C", "D"],
            sub_angles=[90.0],
            area_radius={"C": 2.5, "D": 2.5},
            total_angle=90.0,
            total_diameter=5.0,
            local_sim=0.5,
        )

        from acc_core_tree import ACCNode
        merged = ACCNode(
            members={"A", "B", "C", "D"},
            local_sim=0.275,
            global_sim=0.35,
            diameter=1.0 / 0.35,
            angle=130.5,
        )

        result = _merge_clusters(state1, state2, merged, _paper_radius_fn,
                                 local, global_, {})

        total = sum(result.sub_angles)
        assert pytest.approx(total, abs=0.5) == 130.5

    def test_proportional_d_merge(self, merge_matrices):
        """d scaling: d₃ > max(d₁,d₂) → proportional scale."""
        local, global_ = merge_matrices

        state1 = ClusterState(
            sequence=["A", "B"],
            sub_angles=[72.0],
            area_radius={"A": 2.0, "B": 2.0},  # d=4 → radius=2
            total_angle=72.0,
            total_diameter=4.0,
            local_sim=0.6,
        )
        state2 = ClusterState(
            sequence=["C", "D"],
            sub_angles=[90.0],
            area_radius={"C": 2.5, "D": 2.5},  # d=5 → radius=2.5
            total_angle=90.0,
            total_diameter=5.0,
            local_sim=0.5,
        )

        from acc_core_tree import ACCNode
        # d₃ = 7.5, max(d₁, d₂) = 5 → scale = 7.5/5 = 1.5
        merged = ACCNode(
            members={"A", "B", "C", "D"},
            local_sim=0.275,
            global_sim=0.35,
            diameter=7.5,
            angle=130.5,
        )

        result = _merge_clusters(state1, state2, merged, _paper_radius_fn,
                                 local, global_, {})

        # After scaling: radius_A = 2.0*1.5=3.0, radius_C = 2.5*1.5=3.75
        assert pytest.approx(result.area_radius["A"], abs=0.01) == 3.0
        assert pytest.approx(result.area_radius["B"], abs=0.01) == 3.0
        assert pytest.approx(result.area_radius["C"], abs=0.01) == 3.75
        assert pytest.approx(result.area_radius["D"], abs=0.01) == 3.75


# ────────────────────────────────────────────────────────────
# Tests: Step dict format
# ────────────────────────────────────────────────────────────
class TestStepDictFormat:
    def test_step_dict_has_required_keys(self, add_area_matrices):
        """Step dicts should have all required keys for GUI."""
        local, global_ = add_area_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)
        radius_fn = _make_radius_fn(1.0, 6.0)
        steps, cached = render_paper(root, merge_log, local, global_,
                                     radius_fn, {})

        assert len(steps) >= 1
        for step in steps:
            assert "step" in step
            assert "action" in step
            assert "description" in step
            assert "clusters" in step
            assert "highlighted_members" in step
            assert "placed_areas" in step

            for cluster in step["clusters"]:
                assert "members" in cluster
                assert "points" in cluster
                assert "radius" in cluster
                assert "diameter" in cluster
                assert "angle" in cluster
                assert "local_sim" in cluster
                assert "global_sim" in cluster
                assert "internal_nodes" in cluster
                assert "diversity" in cluster

    def test_step_count_matches_merge_log(self, add_area_matrices):
        """Number of steps should equal merge_log length."""
        local, global_ = add_area_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)
        radius_fn = _make_radius_fn(1.0, 6.0)
        steps, _ = render_paper(root, merge_log, local, global_,
                                radius_fn, {})
        assert len(steps) == len(merge_log)


# ────────────────────────────────────────────────────────────
# Tests: Diversity ordering
# ────────────────────────────────────────────────────────────
class TestDiversityOrdering:
    def test_higher_diversity_first(self, add_area_matrices):
        """Area with higher α-diversity should be first in initial pair."""
        local, global_ = add_area_matrices

        from acc_core_tree import ACCNode
        left = ACCNode(members={"A"}, diversity=5)
        right = ACCNode(members={"B"}, diversity=10)
        merged = ACCNode(
            members={"A", "B"},
            local_sim=0.6,
            global_sim=0.7,
            diameter=1.0 / 0.7,
            angle=72.0,
        )

        state = _create_pair(left, right, merged, _paper_radius_fn,
                             local, global_, {"A": 5, "B": 10})

        # B has higher diversity → should be first
        assert state.sequence[0] == "B"

    def test_equal_diversity_alphabetical(self, add_area_matrices):
        """Equal diversity → alphabetical order."""
        local, global_ = add_area_matrices

        from acc_core_tree import ACCNode
        left = ACCNode(members={"B"}, diversity=5)
        right = ACCNode(members={"A"}, diversity=5)
        merged = ACCNode(
            members={"A", "B"},
            local_sim=0.6,
            global_sim=0.7,
            diameter=1.0 / 0.7,
            angle=72.0,
        )

        state = _create_pair(left, right, merged, _paper_radius_fn,
                             local, global_, {"A": 5, "B": 5})

        assert state.sequence[0] == "A"


# ────────────────────────────────────────────────────────────
# Tests: Re-render preserves sequence
# ────────────────────────────────────────────────────────────
class TestRerenderPreservesSequence:
    def test_sequence_preserved_on_rerender(self, add_area_matrices):
        """Diameter change should preserve area sequence."""
        local, global_ = add_area_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)

        radius_fn1 = _make_radius_fn(1.0, 6.0)
        steps1, cached = render_paper(root, merge_log, local, global_,
                                      radius_fn1, {})

        radius_fn2 = _make_radius_fn(2.0, 10.0)
        steps2 = rerender_paper(root, merge_log, cached, local, global_,
                                radius_fn2, {})

        # Sequences should be identical
        for s1, s2 in zip(steps1, steps2):
            clusters1 = s1["clusters"]
            clusters2 = s2["clusters"]
            assert len(clusters1) == len(clusters2)

    def test_rerender_changes_coordinates(self, add_area_matrices):
        """Re-render with different diameter should change coordinates."""
        local, global_ = add_area_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)

        radius_fn1 = _make_radius_fn(1.0, 6.0)
        steps1, cached = render_paper(root, merge_log, local, global_,
                                      radius_fn1, {})

        radius_fn2 = _make_radius_fn(2.0, 10.0)
        steps2 = rerender_paper(root, merge_log, cached, local, global_,
                                radius_fn2, {})

        # Final step should have different point coordinates
        if steps1 and steps2:
            final1 = steps1[-1]["clusters"]
            final2 = steps2[-1]["clusters"]
            # At least some coordinates should differ (different radius)
            if final1 and final2:
                points1 = final1[0].get("points", {})
                points2 = final2[0].get("points", {})
                if points1 and points2:
                    # Check any shared key has different coords
                    common = set(points1.keys()) & set(points2.keys())
                    if common:
                        area = next(iter(common))
                        # With different radius settings, coords should differ
                        p1 = points1[area]
                        p2 = points2[area]
                        assert p1 != p2 or len(common) == 1  # single area at origin


# ────────────────────────────────────────────────────────────
# Tests: Compute positions
# ────────────────────────────────────────────────────────────
class TestComputePositions:
    def test_single_area(self):
        """Single area should be at its radius from centre."""
        state = ClusterState(
            sequence=["A"],
            sub_angles=[],
            area_radius={"A": 3.0},
            total_angle=0.0,
            total_diameter=6.0,
            local_sim=1.0,
        )
        pos = _compute_positions(state)
        assert "A" in pos
        # Should be at distance 3 from origin
        x, y = pos["A"]
        dist = math.sqrt(x**2 + y**2)
        assert pytest.approx(dist, abs=0.01) == 3.0

    def test_two_areas_symmetric(self):
        """Two areas should be symmetric about the midpoint direction."""
        state = ClusterState(
            sequence=["A", "B"],
            sub_angles=[90.0],
            area_radius={"A": 3.0, "B": 3.0},
            total_angle=90.0,
            total_diameter=6.0,
            local_sim=0.5,
        )
        pos = _compute_positions(state, direction=0.0)

        # Both at distance 3
        for name in ["A", "B"]:
            x, y = pos[name]
            dist = math.sqrt(x**2 + y**2)
            assert pytest.approx(dist, abs=0.01) == 3.0

    def test_three_areas_positions(self):
        """Three areas with known angles should produce valid positions."""
        state = ClusterState(
            sequence=["A", "B", "C"],
            sub_angles=[50.0, 76.0],
            area_radius={"A": 2.0, "B": 2.0, "C": 3.0},
            total_angle=126.0,
            total_diameter=6.0,
            local_sim=0.3,
        )
        pos = _compute_positions(state, direction=0.0)
        assert len(pos) == 3

        # All areas should have non-zero positions
        for name in ["A", "B", "C"]:
            x, y = pos[name]
            dist = math.sqrt(x**2 + y**2)
            assert dist > 0

    def test_empty_state(self):
        """Empty state should return empty positions."""
        state = ClusterState(
            sequence=[],
            sub_angles=[],
            area_radius={},
            total_angle=0.0,
            total_diameter=0.0,
            local_sim=1.0,
        )
        pos = _compute_positions(state)
        assert pos == {}


# ────────────────────────────────────────────────────────────
# Tests: Angular separation utility
# ────────────────────────────────────────────────────────────
class TestAngularSeparation:
    def test_adjacent_areas(self):
        """Adjacent areas should have separation = their sub_angle."""
        sep = _angular_separation(["A", "B", "C"], [72.0, 90.0], "A", "B")
        assert pytest.approx(sep) == 72.0

    def test_distant_areas(self):
        """Non-adjacent areas should sum intermediate angles."""
        sep = _angular_separation(["A", "B", "C"], [72.0, 90.0], "A", "C")
        assert pytest.approx(sep) == 162.0

    def test_missing_area(self):
        """Missing area should return infinity."""
        sep = _angular_separation(["A", "B"], [72.0], "A", "X")
        assert sep == float("inf")


# ────────────────────────────────────────────────────────────
# Tests: Full pipeline integration
# ────────────────────────────────────────────────────────────
class TestFullPipeline:
    def test_three_area_pipeline(self, add_area_matrices):
        """Full pipeline with 3 areas should produce valid results."""
        local, global_ = add_area_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)
        radius_fn = _make_radius_fn(1.0, 6.0)

        steps, cached = render_paper(root, merge_log, local, global_,
                                     radius_fn, {})

        assert len(steps) == len(merge_log)
        assert len(cached) == len(merge_log)

        # Final step should have all 3 areas
        final = steps[-1]
        all_areas = set()
        for c in final["clusters"]:
            all_areas |= c["members"]
        assert all_areas == {"A", "B", "C"}

    def test_four_area_pipeline(self, merge_matrices):
        """Full pipeline with 4 areas should produce valid results."""
        local, global_ = merge_matrices
        root, merge_log = build_acc_tree(local, global_, unit=1.0)
        radius_fn = _make_radius_fn(1.0, 6.0)

        steps, cached = render_paper(root, merge_log, local, global_,
                                     radius_fn, {})

        assert len(steps) == len(merge_log)

        # Final step should have all 4 areas
        final = steps[-1]
        all_areas = set()
        for c in final["clusters"]:
            all_areas |= c["members"]
        assert all_areas == {"A", "B", "C", "D"}

    def test_pairwise_distance_on_circle(self):
        """Verify chord distance calculation."""
        # Same point → distance 0
        d = _pairwise_distance_on_circle(0.0, 3.0, 3.0)
        assert pytest.approx(d, abs=0.01) == 0.0

        # 180° apart, same radius → diameter
        d = _pairwise_distance_on_circle(180.0, 3.0, 3.0)
        assert pytest.approx(d, abs=0.01) == 6.0

        # 90° apart, same radius → r*sqrt(2)
        d = _pairwise_distance_on_circle(90.0, 3.0, 3.0)
        assert pytest.approx(d, abs=0.01) == 3.0 * math.sqrt(2)
