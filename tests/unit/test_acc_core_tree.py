"""Unit tests for acc_core_tree module."""

import math

import pytest

from acc_core_tree import (
    THETA_MAX_DEGREES,
    ACCNode,
    _determine_order,
    _make_radius_fn,
    build_acc_from_tree,
    build_acc_tree,
    generate_steps,
    render_tree,
)

# ────────────────────────────────────────────────────────────
# Fixtures
# ────────────────────────────────────────────────────────────


@pytest.fixture
def two_area_matrices():
    """Minimal 2-area matrices."""
    local = {"A": {"B": 0.8}, "B": {"A": 0.8}}
    glb = {"A": {"B": 0.6}, "B": {"A": 0.6}}
    return local, glb


@pytest.fixture
def three_area_matrices():
    """3-area matrices with clear ordering: A-B closest, then C."""
    local = {
        "A": {"B": 0.9, "C": 0.4},
        "B": {"A": 0.9, "C": 0.5},
        "C": {"A": 0.4, "B": 0.5},
    }
    glb = {
        "A": {"B": 0.85, "C": 0.35},
        "B": {"A": 0.85, "C": 0.45},
        "C": {"A": 0.35, "B": 0.45},
    }
    return local, glb


@pytest.fixture
def six_area_matrices():
    """6-area matrices for full pipeline testing."""
    local = {
        "J": {"T": 0.9, "Y": 0.8, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.9, "Y": 0.8, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.8, "T": 0.8, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.75, "Q": 0.75},
        "O": {"Q": 0.85},
        "Q": {},
    }
    glb = {
        "J": {"T": 0.88, "Y": 0.82, "N": 0.4, "O": 0.35, "Q": 0.36},
        "T": {"J": 0.88, "Y": 0.80, "N": 0.38, "O": 0.33, "Q": 0.34},
        "Y": {"J": 0.82, "T": 0.80, "N": 0.37, "O": 0.32, "Q": 0.33},
        "N": {"O": 0.7, "Q": 0.68},
        "O": {"Q": 0.83},
        "Q": {},
    }
    return local, glb


# ────────────────────────────────────────────────────────────
# TestACCNode
# ────────────────────────────────────────────────────────────
class TestACCNode:
    def test_leaf_node(self):
        node = ACCNode(members={"A"}, diversity=5)
        assert node.is_leaf
        assert node.leftmost_leaf is node
        assert node.rightmost_leaf is node
        assert node.merge_order == -1

    def test_internal_node(self):
        left = ACCNode(members={"A"})
        right = ACCNode(members={"B"})
        parent = ACCNode(members={"A", "B"}, left=left, right=right, merge_order=0)
        assert not parent.is_leaf
        assert parent.leftmost_leaf is left
        assert parent.rightmost_leaf is right

    def test_deep_tree_leftmost_rightmost(self):
        a = ACCNode(members={"A"})
        b = ACCNode(members={"B"})
        c = ACCNode(members={"C"})
        ab = ACCNode(members={"A", "B"}, left=a, right=b)
        abc = ACCNode(members={"A", "B", "C"}, left=ab, right=c)
        assert abc.leftmost_leaf is a
        assert abc.rightmost_leaf is c

    def test_radius_property(self):
        node = ACCNode(members={"A", "B"}, diameter=2.5)
        assert node.radius == pytest.approx(1.25)


# ────────────────────────────────────────────────────────────
# TestDetermineOrder
# ────────────────────────────────────────────────────────────
class TestDetermineOrder:
    def test_diversity_higher_left(self):
        """Higher diversity node should be left."""
        a = ACCNode(members={"A"}, diversity=10)
        b = ACCNode(members={"B"}, diversity=3)
        local = {"A": {"B": 0.5}, "B": {"A": 0.5}}
        left, right = _determine_order(a, b, local)
        assert left is a
        assert right is b

    def test_diversity_equal_alphabetical(self):
        """Equal diversity → alphabetical order."""
        a = ACCNode(members={"A"}, diversity=5)
        b = ACCNode(members={"B"}, diversity=5)
        local = {"A": {"B": 0.5}, "B": {"A": 0.5}}
        left, right = _determine_order(a, b, local)
        assert left is a  # "A" < "B"
        assert right is b

    def test_diversity_equal_reverse_alphabetical(self):
        """Equal diversity, Z before A → Z is right."""
        z = ACCNode(members={"Z"}, diversity=5)
        a = ACCNode(members={"A"}, diversity=5)
        local = {"A": {"Z": 0.5}, "Z": {"A": 0.5}}
        left, right = _determine_order(z, a, local)
        assert left is a
        assert right is z

    def test_edge_similarity_cluster_leaf(self):
        """When merging cluster + leaf, edge similarity decides ordering."""
        a = ACCNode(members={"A"})
        b = ACCNode(members={"B"})
        ab = ACCNode(members={"A", "B"}, left=a, right=b)
        c = ACCNode(members={"C"})

        # ab's right edge is B, c's left edge is C
        # sim(B, C) = 0.9 → arrangement (ab, c) is good
        # ab's left edge is A, so for arrangement (c, ab): sim(C, A) = 0.1
        local = {
            "A": {"B": 0.8, "C": 0.1},
            "B": {"A": 0.8, "C": 0.9},
            "C": {"A": 0.1, "B": 0.9},
        }
        left, right = _determine_order(ab, c, local)
        assert left is ab
        assert right is c

    def test_edge_similarity_two_clusters(self):
        """Edge similarity for two multi-member clusters."""
        a = ACCNode(members={"A"})
        b = ACCNode(members={"B"})
        ab = ACCNode(members={"A", "B"}, left=a, right=b)

        c = ACCNode(members={"C"})
        d = ACCNode(members={"D"})
        cd = ACCNode(members={"C", "D"}, left=c, right=d)

        # ab.rightmost = B, cd.leftmost = C
        # cd.rightmost = D, ab.leftmost = A
        local = {
            "A": {"B": 0.8, "C": 0.2, "D": 0.7},
            "B": {"A": 0.8, "C": 0.3, "D": 0.2},
            "C": {"A": 0.2, "B": 0.3, "D": 0.8},
            "D": {"A": 0.7, "B": 0.2, "C": 0.8},
        }
        # sim(B, C) = 0.3 (arrangement ab,cd)
        # sim(D, A) = 0.7 (arrangement cd,ab)
        left, right = _determine_order(ab, cd, local)
        assert left is cd  # (cd, ab) because sim(D, A)=0.7 > sim(B, C)=0.3
        assert right is ab


# ────────────────────────────────────────────────────────────
# TestBuildACCTree
# ────────────────────────────────────────────────────────────
class TestBuildACCTree:
    def test_two_areas(self, two_area_matrices):
        local, glb = two_area_matrices
        root, merge_log = build_acc_tree(local, glb)

        assert len(root.members) == 2
        assert root.members == {"A", "B"}
        assert len(merge_log) == 1
        assert root.merge_order == 0
        assert root.local_sim == pytest.approx(0.8)
        assert root.global_sim == pytest.approx(0.6)

    def test_two_areas_diameter_angle(self, two_area_matrices):
        local, glb = two_area_matrices
        root, _ = build_acc_tree(local, glb, unit=1.0)

        # diameter = unit / global_sim = 1.0 / 0.6
        assert root.diameter == pytest.approx(1.0 / 0.6)
        # angle = 180 * (1 - 0.8) = 36
        assert root.angle == pytest.approx(THETA_MAX_DEGREES * (1.0 - 0.8))

    def test_three_areas(self, three_area_matrices):
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)

        assert len(root.members) == 3
        assert root.members == {"A", "B", "C"}
        assert len(merge_log) == 2

        # First merge should be A+B (sim=0.9)
        first_merge = merge_log[0][1]
        assert first_merge.members == {"A", "B"}
        assert first_merge.local_sim == pytest.approx(0.9)

    def test_six_areas(self, six_area_matrices):
        local, glb = six_area_matrices
        root, merge_log = build_acc_tree(local, glb)

        assert len(root.members) == 6
        assert len(merge_log) == 5  # n-1 merges for n areas

    def test_merge_order_sequential(self, six_area_matrices):
        local, glb = six_area_matrices
        _, merge_log = build_acc_tree(local, glb)

        for i, (order, _) in enumerate(merge_log):
            assert order == i

    def test_diversity_affects_order(self, two_area_matrices):
        local, glb = two_area_matrices
        # A has higher diversity → should be left
        diversity = {"A": 10, "B": 3}
        root, _ = build_acc_tree(local, glb, diversity=diversity)
        assert root.left.members == {"A"}
        assert root.right.members == {"B"}

    def test_diversity_reverse(self, two_area_matrices):
        local, glb = two_area_matrices
        # B has higher diversity → B should be left
        diversity = {"A": 3, "B": 10}
        root, _ = build_acc_tree(local, glb, diversity=diversity)
        assert root.left.members == {"B"}
        assert root.right.members == {"A"}

    def test_no_diversity_alphabetical(self, two_area_matrices):
        local, glb = two_area_matrices
        # No diversity → alphabetical: A < B
        root, _ = build_acc_tree(local, glb)
        assert root.left.members == {"A"}
        assert root.right.members == {"B"}


# ────────────────────────────────────────────────────────────
# TestRenderTree
# ────────────────────────────────────────────────────────────
class TestRenderTree:
    def test_single_leaf(self):
        node = ACCNode(members={"A"})
        render_tree(node)
        assert "A" in node.points
        assert node.points["A"] == (0.0, 0.0)

    def test_two_areas_coordinates(self, two_area_matrices):
        local, glb = two_area_matrices
        root, _ = build_acc_tree(local, glb)
        render_tree(root)

        assert "A" in root.points
        assert "B" in root.points

        # Both should be at the same radius from origin
        ax, ay = root.points["A"]
        bx, by = root.points["B"]
        r_a = math.sqrt(ax**2 + ay**2)
        r_b = math.sqrt(bx**2 + by**2)
        assert r_a == pytest.approx(r_b, abs=1e-10)

    def test_deterministic(self, three_area_matrices):
        """Same input → same output."""
        local, glb = three_area_matrices
        root1, _ = build_acc_tree(local, glb)
        render_tree(root1)

        root2, _ = build_acc_tree(local, glb)
        render_tree(root2)

        for member in root1.points:
            assert root1.points[member][0] == pytest.approx(root2.points[member][0])
            assert root1.points[member][1] == pytest.approx(root2.points[member][1])

    def test_scaling(self, three_area_matrices):
        """Min/max diameter scaling changes coordinates."""
        local, glb = three_area_matrices
        root1, _ = build_acc_tree(local, glb)
        render_tree(root1)
        coords_original = dict(root1.points)

        root2, _ = build_acc_tree(local, glb)
        render_tree(root2, min_diameter=2.0, max_diameter=4.0)
        coords_scaled = dict(root2.points)

        # At least one coordinate should differ
        any_different = False
        for member in coords_original:
            if (coords_original[member][0] != pytest.approx(coords_scaled[member][0], abs=1e-10) or
                    coords_original[member][1] != pytest.approx(coords_scaled[member][1], abs=1e-10)):
                any_different = True
                break
        assert any_different

    def test_all_members_have_coordinates(self, six_area_matrices):
        local, glb = six_area_matrices
        root, _ = build_acc_tree(local, glb)
        render_tree(root)

        assert set(root.points.keys()) == set(local.keys())


# ────────────────────────────────────────────────────────────
# TestGenerateSteps
# ────────────────────────────────────────────────────────────
class TestGenerateSteps:
    def test_step_count(self, three_area_matrices):
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)
        assert len(steps) == 2  # 3 areas → 2 merges → 2 steps

    def test_step_format(self, three_area_matrices):
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        for step in steps:
            assert "step" in step
            assert "action" in step
            assert "description" in step
            assert "clusters" in step
            assert "highlighted_members" in step
            assert "placed_areas" in step

    def test_first_step_is_initial(self, three_area_matrices):
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)
        assert steps[0]["action"] == "initial"

    def test_final_step_has_all_members(self, six_area_matrices):
        local, glb = six_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        final = steps[-1]
        all_members = set()
        for cluster in final["clusters"]:
            all_members |= cluster["members"]
        assert all_members == set(local.keys())

    def test_cluster_dicts_have_required_fields(self, three_area_matrices):
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        for step in steps:
            for cluster in step["clusters"]:
                assert "members" in cluster
                assert "points" in cluster
                assert "radius" in cluster
                assert "diameter" in cluster
                assert "angle" in cluster
                assert "local_sim" in cluster
                assert "global_sim" in cluster

    def test_six_areas_step_count(self, six_area_matrices):
        local, glb = six_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)
        assert len(steps) == 5  # 6 areas → 5 merges


# ────────────────────────────────────────────────────────────
# TestBuildACCFromTree (integration)
# ────────────────────────────────────────────────────────────
class TestBuildACCFromTree:
    def test_full_pipeline(self, six_area_matrices):
        local, glb = six_area_matrices
        root, steps = build_acc_from_tree(local, glb)

        assert root is not None
        assert len(steps) == 5
        assert len(root.members) == 6

    def test_rerender_changes_coordinates(self, three_area_matrices):
        local, glb = three_area_matrices
        root, steps1 = build_acc_from_tree(local, glb)
        coords1 = dict(root.points)

        # Re-render with different diameter
        render_tree(root, min_diameter=2.0, max_diameter=4.0)
        coords2 = dict(root.points)

        any_different = False
        for member in coords1:
            if (coords1[member][0] != pytest.approx(coords2[member][0], abs=1e-10) or
                    coords1[member][1] != pytest.approx(coords2[member][1], abs=1e-10)):
                any_different = True
                break
        assert any_different

    def test_with_diversity(self, three_area_matrices):
        local, glb = three_area_matrices
        diversity = {"A": 10, "B": 5, "C": 2}
        root, steps = build_acc_from_tree(local, glb, diversity=diversity)

        assert root is not None
        assert len(steps) == 2

    def test_min_max_diameter(self, three_area_matrices):
        local, glb = three_area_matrices
        root, steps = build_acc_from_tree(
            local, glb, min_diameter=1.0, max_diameter=3.0,
        )
        assert root is not None
        assert len(steps) > 0


# ────────────────────────────────────────────────────────────
# TestInternalNodes
# ────────────────────────────────────────────────────────────
class TestInternalNodes:
    def test_step_has_internal_nodes(self, three_area_matrices):
        """Last step's merged cluster should contain internal_nodes."""
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        # The final step has one cluster with all 3 members (2 merges done)
        final_clusters = steps[-1]["clusters"]
        big_cluster = [c for c in final_clusters if len(c["members"]) == 3]
        assert len(big_cluster) == 1
        assert len(big_cluster[0]["internal_nodes"]) > 0

    def test_internal_node_fields(self, three_area_matrices):
        """Each internal node dict must have all 8 required fields."""
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        required_fields = {
            "position", "radius", "members", "local_sim",
            "global_sim", "angle", "diameter", "merge_order",
        }
        for step in steps:
            for cluster in step["clusters"]:
                for inode in cluster.get("internal_nodes", []):
                    assert required_fields.issubset(inode.keys())

    def test_internal_node_on_circle(self, three_area_matrices):
        """Internal node position distance from origin ≈ its radius."""
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        for step in steps:
            for cluster in step["clusters"]:
                for inode in cluster.get("internal_nodes", []):
                    ix, iy = inode["position"]
                    dist = math.sqrt(ix**2 + iy**2)
                    assert dist == pytest.approx(inode["radius"], abs=1e-6)

    def test_leaf_cluster_no_internal_nodes(self, three_area_matrices):
        """Leaf clusters should have empty internal_nodes list."""
        local, glb = three_area_matrices
        root, merge_log = build_acc_tree(local, glb)
        steps = generate_steps(root, merge_log)

        for step in steps:
            for cluster in step["clusters"]:
                if len(cluster["members"]) == 1:
                    assert cluster["internal_nodes"] == []


class TestRadiusFn:
    def test_defaults_when_none(self):
        """None → defaults (min_d=1, max_d=6)."""
        fn = _make_radius_fn(None, None)
        # sim=1.0 → diameter=1 → radius=0.5
        assert fn(1.0) == pytest.approx(0.5)
        # sim=0.0 → diameter=6 → radius=3.0
        assert fn(0.0) == pytest.approx(3.0)
        # sim=0.5 → diameter=3.5 → radius=1.75
        assert fn(0.5) == pytest.approx(1.75)

    def test_custom_range(self):
        fn = _make_radius_fn(2.0, 10.0)
        # sim=1.0 → diameter=2 → radius=1.0
        assert fn(1.0) == pytest.approx(1.0)
        # sim=0.0 → diameter=10 → radius=5.0
        assert fn(0.0) == pytest.approx(5.0)
        # sim=0.5 → diameter=6 → radius=3.0
        assert fn(0.5) == pytest.approx(3.0)

    def test_linear_interpolation(self):
        fn = _make_radius_fn(1.0, 6.0)
        # diameter = 1 + 5*(1-sim), radius = diameter/2
        assert fn(0.8) == pytest.approx((1 + 5 * 0.2) / 2)
        assert fn(0.3) == pytest.approx((1 + 5 * 0.7) / 2)
