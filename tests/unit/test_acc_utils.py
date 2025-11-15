"""
Unit tests for acc_utils.py
"""

import pytest
import numpy as np
import pandas as pd
from acc_utils import (
    similarity_to_distance,
    validate_similarity_matrix,
    dict_matrix_from_dataframe,
    matrix_to_dendrogram,
    linkage_to_dendronode,
)


class TestSimilarityToDistance:
    """Tests for similarity_to_distance function"""

    def test_dict_matrix_conversion(self, simple_abc_sub_matrix):
        """Dict matrix를 distance matrix로 변환"""
        dist_matrix, labels = similarity_to_distance(simple_abc_sub_matrix)

        assert isinstance(dist_matrix, np.ndarray)
        assert len(labels) == 3
        assert set(labels) == {"A", "B", "C"}
        assert dist_matrix.shape == (3, 3)

    def test_distance_calculation(self):
        """Distance = max - similarity 계산 검증"""
        matrix = {
            "A": {"B": 0.8},
            "B": {"A": 0.8}
        }
        dist_matrix, labels = similarity_to_distance(matrix)

        max_sim = 1.0  # 대각선
        expected_dist = max_sim - 0.8  # 0.2

        idx_a = labels.index("A")
        idx_b = labels.index("B")
        assert np.isclose(dist_matrix[idx_a, idx_b], expected_dist)

    def test_array_input(self):
        """NumPy array 입력 처리"""
        arr = np.array([
            [1.0, 0.9, 0.8],
            [0.9, 1.0, 0.7],
            [0.8, 0.7, 1.0]
        ])
        dist_matrix, labels = similarity_to_distance(arr)

        assert dist_matrix.shape == (3, 3)
        assert len(labels) == 3
        assert all(label.startswith("Item_") for label in labels)


class TestValidateSimilarityMatrix:
    """Tests for validate_similarity_matrix function"""

    def test_valid_matrix_dict(self, simple_abc_sub_matrix):
        """유효한 dict matrix 검증 통과"""
        # Dict를 array로 변환
        labels = sorted(simple_abc_sub_matrix.keys())
        n = len(labels)
        arr = np.eye(n)
        for i, label1 in enumerate(labels):
            for j, label2 in enumerate(labels):
                if label1 in simple_abc_sub_matrix and label2 in simple_abc_sub_matrix[label1]:
                    arr[i, j] = simple_abc_sub_matrix[label1][label2]

        valid, msg = validate_similarity_matrix(arr)
        assert valid
        assert "valid" in msg.lower()

    def test_valid_matrix_array(self):
        """유효한 NumPy array 검증 통과"""
        arr = np.array([
            [1.0, 0.9, 0.8],
            [0.9, 1.0, 0.7],
            [0.8, 0.7, 1.0]
        ])
        valid, msg = validate_similarity_matrix(arr)
        assert valid

    def test_asymmetric_matrix(self, invalid_asymmetric_matrix):
        """비대칭 matrix 검증 실패"""
        valid, msg = validate_similarity_matrix(invalid_asymmetric_matrix)
        assert not valid
        assert "symmetric" in msg.lower()

    def test_invalid_diagonal(self, invalid_diagonal_matrix):
        """대각선 != 1.0 검증 실패"""
        valid, msg = validate_similarity_matrix(invalid_diagonal_matrix)
        assert not valid
        assert "diagonal" in msg.lower()

    def test_value_out_of_range(self, invalid_range_matrix):
        """값 범위 초과 검증 실패"""
        valid, msg = validate_similarity_matrix(invalid_range_matrix)
        assert not valid
        assert ("range" in msg.lower() or "1.0" in msg)


class TestDictMatrixFromDataframe:
    """Tests for dict_matrix_from_dataframe function"""

    def test_dataframe_conversion(self, sample_sub_df):
        """DataFrame을 dict matrix로 변환"""
        matrix = dict_matrix_from_dataframe(sample_sub_df)

        assert isinstance(matrix, dict)
        assert len(matrix) == len(sample_sub_df)

        # 모든 행이 dict인지 확인
        for row in matrix.values():
            assert isinstance(row, dict)

    def test_values_preserved(self):
        """값이 정확히 보존되는지 확인"""
        df = pd.DataFrame({
            'A': [1.0, 0.9],
            'B': [0.9, 1.0]
        }, index=['A', 'B'])

        matrix = dict_matrix_from_dataframe(df)

        assert matrix['A']['B'] == 0.9
        assert matrix['B']['A'] == 0.9


class TestMatrixToDendrogram:
    """Tests for matrix_to_dendrogram function"""

    def test_creates_dendrogram(self, simple_abc_sub_matrix):
        """Dendrogram 생성 확인"""
        dendro, labels = matrix_to_dendrogram(simple_abc_sub_matrix, method='average')

        assert dendro is not None
        assert len(labels) == 3
        assert set(labels) == {"A", "B", "C"}

    def test_dendrogram_structure(self, simple_abc_sub_matrix):
        """Dendrogram 구조 검증"""
        dendro, labels = matrix_to_dendrogram(simple_abc_sub_matrix, method='average')

        # Root는 모든 멤버를 포함해야 함
        assert len(dendro.members) == 3
        assert dendro.members == {"A", "B", "C"}

    def test_different_methods(self, simple_abc_sub_matrix):
        """다양한 linkage method 테스트"""
        methods = ['average', 'single', 'complete']

        for method in methods:
            dendro, labels = matrix_to_dendrogram(simple_abc_sub_matrix, method=method)
            assert dendro is not None
            assert len(dendro.members) == 3


class TestLinkageToDendronode:
    """Tests for linkage_to_dendronode function"""

    def test_creates_nodes(self):
        """Linkage matrix에서 DendroNode 생성"""
        from scipy.cluster.hierarchy import linkage
        from scipy.spatial.distance import squareform

        # 간단한 distance matrix
        dist = np.array([0.1, 0.2, 0.3])  # condensed form for 3 items
        link_matrix = linkage(dist, method='average')

        labels = ['A', 'B', 'C']
        dendro = linkage_to_dendronode(link_matrix, labels, max_sim=1.0)

        assert dendro is not None
        assert len(dendro.members) == 3

    def test_leaf_nodes_have_sim_1(self):
        """Leaf node는 sim=1.0을 가져야 함"""
        from scipy.cluster.hierarchy import linkage

        dist = np.array([0.1, 0.2, 0.3])
        link_matrix = linkage(dist, method='average')

        labels = ['A', 'B', 'C']
        dendro = linkage_to_dendronode(link_matrix, labels, max_sim=1.0)

        # Traverse to find leaf nodes
        def find_leaves(node):
            if node.left is None and node.right is None:
                return [node]
            leaves = []
            if node.left:
                leaves.extend(find_leaves(node.left))
            if node.right:
                leaves.extend(find_leaves(node.right))
            return leaves

        leaves = find_leaves(dendro)
        for leaf in leaves:
            assert leaf.sim == 1.0
