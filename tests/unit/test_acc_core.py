"""
Unit tests for acc_core.py
"""

import pytest
from acc_core import (
    DendroNode,
    find_cluster_in_dendro_by_members,
    average_pairwise_similarity,
    extract_clusters_from_dendro,
    decorate_clusters,
)


class TestDendroNode:
    """Tests for DendroNode data structure"""

    def test_create_leaf_node(self):
        """Leaf node 생성"""
        node = DendroNode(["A"], sim=1.0)

        assert node.members == {"A"}
        assert node.sim == 1.0
        assert node.left is None
        assert node.right is None

    def test_create_internal_node(self):
        """Internal node 생성"""
        left = DendroNode(["A"], sim=1.0)
        right = DendroNode(["B"], sim=1.0)
        node = DendroNode(["A", "B"], sim=0.9, left=left, right=right)

        assert node.members == {"A", "B"}
        assert node.sim == 0.9
        assert node.left is left
        assert node.right is right

    def test_members_set(self):
        """Members는 set으로 저장"""
        node = DendroNode(["A", "B", "C"], sim=0.8)

        assert isinstance(node.members, set)
        assert len(node.members) == 3
        assert "A" in node.members
        assert "B" in node.members
        assert "C" in node.members


class TestFindClusterInDendro:
    """Tests for find_cluster_in_dendro_by_members"""

    def test_find_exact_match(self):
        """정확히 일치하는 cluster 찾기"""
        left = DendroNode(["A"], sim=1.0)
        right = DendroNode(["B"], sim=1.0)
        root = DendroNode(["A", "B"], sim=0.9, left=left, right=right)

        result = find_cluster_in_dendro_by_members(root, {"A", "B"})

        assert result is not None
        assert result == 0.9

    def test_find_subset(self):
        """부분집합 찾기"""
        a = DendroNode(["A"], sim=1.0)
        b = DendroNode(["B"], sim=1.0)
        ab = DendroNode(["A", "B"], sim=0.9, left=a, right=b)
        c = DendroNode(["C"], sim=1.0)
        root = DendroNode(["A", "B", "C"], sim=0.8, left=ab, right=c)

        result = find_cluster_in_dendro_by_members(root, {"A"})

        assert result is not None
        assert result == 1.0

    def test_not_found(self):
        """찾을 수 없는 경우"""
        node = DendroNode(["A", "B"], sim=0.9)

        result = find_cluster_in_dendro_by_members(node, {"X", "Y"})

        assert result is None


class TestAveragePairwiseSimilarity:
    """Tests for average_pairwise_similarity"""

    def test_simple_similarity(self):
        """간단한 pairwise similarity 계산"""
        members = {"A", "B"}
        matrix = {
            "A": {"B": 0.8},
            "B": {"A": 0.8}
        }

        avg = average_pairwise_similarity(members, matrix)

        assert avg == 0.8

    def test_three_members(self):
        """3개 member의 평균"""
        members = {"A", "B", "C"}
        matrix = {
            "A": {"B": 0.9, "C": 0.8},
            "B": {"A": 0.9, "C": 0.7},
            "C": {"A": 0.8, "B": 0.7}
        }

        avg = average_pairwise_similarity(members, matrix)

        # (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert abs(avg - 0.8) < 0.01

    def test_single_member(self):
        """단일 member는 1.0"""
        members = {"A"}
        matrix = {}

        avg = average_pairwise_similarity(members, matrix)

        assert avg == 1.0

    def test_asymmetric_matrix(self):
        """비대칭 matrix 처리"""
        members = {"A", "B"}
        matrix = {
            "A": {"B": 0.8},
            "B": {}  # B의 값이 없음
        }

        avg = average_pairwise_similarity(members, matrix)

        # A->B 값만 사용
        assert avg == 0.8


class TestExtractClustersFromDendro:
    """Tests for extract_clusters_from_dendro"""

    def test_simple_tree(self):
        """간단한 tree에서 cluster 추출"""
        left = DendroNode(["A"], sim=1.0)
        right = DendroNode(["B"], sim=1.0)
        root = DendroNode(["A", "B"], sim=0.9, left=left, right=right)

        clusters = extract_clusters_from_dendro(root)

        # 모든 노드 포함 (리프 포함): root + left + right = 3
        assert len(clusters) == 3

        # Root cluster 찾기
        root_cluster = [c for c in clusters if c['members'] == {"A", "B"}][0]
        assert root_cluster['sim_sub'] == 0.9

    def test_complex_tree(self):
        """복잡한 tree 구조"""
        a = DendroNode(["A"], sim=1.0)
        b = DendroNode(["B"], sim=1.0)
        ab = DendroNode(["A", "B"], sim=0.9, left=a, right=b)
        c = DendroNode(["C"], sim=1.0)
        root = DendroNode(["A", "B", "C"], sim=0.8, left=ab, right=c)

        clusters = extract_clusters_from_dendro(root)

        # 모든 노드: root + ab + a + b + c = 5
        assert len(clusters) == 5

        members_sets = [c['members'] for c in clusters]
        assert {"A", "B"} in members_sets
        assert {"A", "B", "C"} in members_sets
        assert {"A"} in members_sets
        assert {"B"} in members_sets
        assert {"C"} in members_sets

    def test_cluster_fields(self):
        """Cluster가 필요한 필드를 포함하는지"""
        left = DendroNode(["A"], sim=1.0)
        right = DendroNode(["B"], sim=1.0)
        root = DendroNode(["A", "B"], sim=0.9, left=left, right=right)

        clusters = extract_clusters_from_dendro(root)
        cluster = clusters[0]

        assert 'members' in cluster
        assert 'sim_sub' in cluster
        assert 'sim_inc' in cluster
        assert 'diameter' in cluster
        assert 'theta' in cluster
        assert 'center' in cluster
        assert 'points' in cluster


class TestDecorateClusters:
    """Tests for decorate_clusters"""

    def test_decorate_with_inc_dendro(self):
        """Inclusive dendrogram으로 cluster 장식"""
        # Subordinate tree
        sub_root = DendroNode(["A", "B"], sim=0.9)

        # Inclusive tree
        inc_root = DendroNode(["A", "B"], sim=0.8)

        # Extract clusters
        clusters = [{'members': {"A", "B"}, 'sim_sub': 0.9}]

        # Decorate
        inc_matrix = {"A": {"B": 0.8}, "B": {"A": 0.8}}
        decorate_clusters(clusters, inc_root, inc_matrix, unit=1.0)

        cluster = clusters[0]
        assert cluster['sim_inc'] == 0.8
        assert 'diameter' in cluster
        assert 'theta' in cluster

    def test_diameter_calculation(self):
        """Diameter 계산 검증"""
        clusters = [{'members': {"A", "B"}, 'sim_sub': 0.9}]
        inc_root = DendroNode(["A", "B"], sim=0.8)
        inc_matrix = {"A": {"B": 0.8}, "B": {"A": 0.8}}

        decorate_clusters(clusters, inc_root, inc_matrix, unit=1.0)

        cluster = clusters[0]
        # diameter = unit / sim_inc = 1.0 / 0.8 = 1.25
        expected_diameter = 1.0 / 0.8
        assert abs(cluster['diameter'] - expected_diameter) < 0.01

    def test_theta_calculation(self):
        """Theta 계산 검증"""
        clusters = [{'members': {"A", "B"}, 'sim_sub': 0.9}]
        inc_root = DendroNode(["A", "B"], sim=0.8)
        inc_matrix = {"A": {"B": 0.8}, "B": {"A": 0.8}}

        decorate_clusters(clusters, inc_root, inc_matrix, unit=1.0)

        cluster = clusters[0]
        # theta = 180 * (1 - sim_sub) = 180 * (1 - 0.9) = 18
        expected_theta = 180 * (1 - 0.9)
        assert abs(cluster['theta'] - expected_theta) < 0.01

    def test_fallback_to_matrix(self):
        """Dendrogram에 없는 cluster는 matrix 사용"""
        # Cluster가 inc_dendro에 없는 경우
        clusters = [{'members': {"A", "B"}, 'sim_sub': 0.9}]
        inc_root = DendroNode(["X", "Y"], sim=0.8)  # 다른 members
        inc_matrix = {"A": {"B": 0.7}, "B": {"A": 0.7}}

        decorate_clusters(clusters, inc_root, inc_matrix, unit=1.0)

        cluster = clusters[0]
        # Matrix의 평균값 사용: 0.7
        assert cluster['sim_inc'] == 0.7
