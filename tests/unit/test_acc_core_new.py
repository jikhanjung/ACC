"""
Unit tests for acc_core_new.py
Tests iterative ACC algorithm implementation
"""

import pytest
import math
from acc_core_new import (
    pol2cart,
    cart2pol,
    cart_add,
    find_highest_similarity_pair,
    get_similarity,
    average_pairwise_similarity,
    format_cluster_structure,
    place_first_two_areas,
)


class TestCoordinateConversion:
    """Tests for coordinate conversion utilities"""

    def test_pol2cart_zero_angle(self):
        """0도는 (0,1) 방향 (위쪽)"""
        x, y = pol2cart(1.0, 0)
        assert abs(x - 0.0) < 0.01
        assert abs(y - 1.0) < 0.01

    def test_pol2cart_90_degrees(self):
        """90도는 (-1,0) 방향 (왼쪽)"""
        x, y = pol2cart(1.0, 90)
        assert abs(x - (-1.0)) < 0.01
        assert abs(y - 0.0) < 0.01

    def test_pol2cart_180_degrees(self):
        """180도는 (0,-1) 방향 (아래쪽)"""
        x, y = pol2cart(1.0, 180)
        assert abs(x - 0.0) < 0.01
        assert abs(y - (-1.0)) < 0.01

    def test_cart2pol_roundtrip(self):
        """Polar → Cartesian → Polar 변환 검증"""
        r_orig, angle_orig = 2.5, 45.0
        x, y = pol2cart(r_orig, angle_orig)
        r_calc, angle_calc = cart2pol(x, y)

        assert abs(r_calc - r_orig) < 0.01
        assert abs(angle_calc - angle_orig) < 0.01

    def test_cart_add(self):
        """Cartesian 좌표 덧셈"""
        a = (1.0, 2.0)
        b = (3.0, 4.0)
        result = cart_add(a, b)

        assert result == (4.0, 6.0)


class TestFindHighestSimilarityPair:
    """Tests for find_highest_similarity_pair"""

    def test_simple_pair(self):
        """간단한 2-영역 matrix"""
        matrix = {
            "A": {"B": 0.9},
            "B": {"A": 0.9}
        }
        result = find_highest_similarity_pair(matrix)

        assert result is not None
        assert result[2] == 0.9  # similarity
        assert set(result[:2]) == {"A", "B"}

    def test_three_areas(self):
        """3개 영역 중 최고 유사도 찾기"""
        matrix = {
            "A": {"B": 0.7, "C": 0.9},
            "B": {"A": 0.7, "C": 0.6},
            "C": {"A": 0.9, "B": 0.6}
        }
        result = find_highest_similarity_pair(matrix)

        assert result is not None
        assert result[2] == 0.9
        assert set(result[:2]) == {"A", "C"}

    def test_asymmetric_matrix(self):
        """비대칭 matrix (한쪽 방향만 값 존재)"""
        matrix = {
            "A": {"B": 0.8},
            "B": {}  # B->A 값 없음
        }
        result = find_highest_similarity_pair(matrix)

        assert result is not None
        assert result[2] == 0.8

    def test_empty_matrix(self):
        """빈 matrix"""
        matrix = {}
        result = find_highest_similarity_pair(matrix)

        assert result is None


class TestGetSimilarity:
    """Tests for get_similarity"""

    def test_forward_direction(self):
        """정방향 조회"""
        matrix = {"A": {"B": 0.8}}
        sim = get_similarity(matrix, "A", "B")

        assert sim == 0.8

    def test_reverse_direction(self):
        """역방향 조회"""
        matrix = {"B": {"A": 0.8}}
        sim = get_similarity(matrix, "A", "B")

        assert sim == 0.8

    def test_not_found(self):
        """값 없음"""
        matrix = {"A": {"C": 0.7}}
        sim = get_similarity(matrix, "A", "B")

        assert sim is None


class TestAveragePairwiseSimilarity:
    """Tests for average_pairwise_similarity"""

    def test_single_member(self):
        """단일 멤버는 1.0"""
        members = {"A"}
        matrix = {}
        avg = average_pairwise_similarity(members, matrix)

        assert avg == 1.0

    def test_two_members(self):
        """2개 멤버 평균"""
        members = {"A", "B"}
        matrix = {"A": {"B": 0.8}}
        avg = average_pairwise_similarity(members, matrix)

        assert avg == 0.8

    def test_three_members(self):
        """3개 멤버 평균"""
        members = {"A", "B", "C"}
        matrix = {
            "A": {"B": 0.9, "C": 0.8},
            "B": {"C": 0.7}
        }
        avg = average_pairwise_similarity(members, matrix)

        # (0.9 + 0.8 + 0.7) / 3 = 0.8
        assert abs(avg - 0.8) < 0.01

    def test_missing_similarities(self):
        """일부 유사도 누락"""
        members = {"A", "B", "C"}
        matrix = {"A": {"B": 0.6}}  # A-C, B-C 없음
        avg = average_pairwise_similarity(members, matrix)

        # 0.6 / 1 = 0.6 (하나만 계산)
        assert avg == 0.6


class TestFormatClusterStructure:
    """Tests for format_cluster_structure"""

    def test_single_area(self):
        """단일 영역"""
        result = format_cluster_structure("A")
        assert result == "A"

    def test_nested_list(self):
        """중첩 리스트"""
        structure = ["A", "B"]
        result = format_cluster_structure(structure)
        assert result == "[A, B]"

    def test_deeply_nested(self):
        """깊게 중첩된 구조"""
        structure = [["A", "B"], "C"]
        result = format_cluster_structure(structure)
        assert result == "[[A, B], C]"

    def test_empty_list(self):
        """빈 리스트"""
        result = format_cluster_structure([])
        assert result == "[]"


class TestPlaceFirstTwoAreas:
    """Tests for place_first_two_areas"""

    def test_perfect_similarity(self):
        """완벽한 유사도 (sub=1.0, inc=1.0)"""
        cluster = place_first_two_areas("A", "B", local_sim=1.0, global_sim=1.0, unit=1.0)

        assert cluster['members'] == {"A", "B"}
        assert cluster['angle'] == 0.0  # 180 * (1 - 1.0) = 0
        assert cluster['diameter'] == 1.0  # 1.0 / 1.0 = 1.0

    def test_medium_similarity(self):
        """중간 유사도 (sub=0.5, inc=0.5)"""
        cluster = place_first_two_areas("A", "B", local_sim=0.5, global_sim=0.5, unit=1.0)

        assert cluster['angle'] == 90.0  # 180 * (1 - 0.5) = 90
        assert cluster['diameter'] == 2.0  # 1.0 / 0.5 = 2.0

    def test_zero_similarity(self):
        """0 유사도 (sub=0.0, inc=0.0)"""
        cluster = place_first_two_areas("A", "B", local_sim=0.0, global_sim=0.0, unit=1.0)

        assert cluster['angle'] == 180.0  # 180 * (1 - 0.0) = 180
        assert cluster['diameter'] == 100.0  # global_sim=0 방지용 큰 값

    def test_positions_on_circle(self):
        """영역들이 원 위에 올바르게 배치되는지 확인"""
        cluster = place_first_two_areas("A", "B", local_sim=0.5, global_sim=1.0, unit=1.0)

        # radius = 0.5, angle = 90도
        # area1: -45도, area2: +45도
        pos1 = cluster['points']['A']
        pos2 = cluster['points']['B']

        # 원점으로부터 거리가 radius와 같아야 함
        radius = cluster['radius']
        dist1 = math.sqrt(pos1[0]**2 + pos1[1]**2)
        dist2 = math.sqrt(pos2[0]**2 + pos2[1]**2)

        assert abs(dist1 - radius) < 0.01
        assert abs(dist2 - radius) < 0.01

    def test_cluster_structure(self):
        """Cluster가 올바른 구조를 가지는지 확인"""
        cluster = place_first_two_areas("J", "T", local_sim=0.9, global_sim=0.8, unit=1.0)

        assert 'members' in cluster
        assert 'center' in cluster
        assert 'radius' in cluster
        assert 'diameter' in cluster
        assert 'angle' in cluster
        assert 'points' in cluster
        assert 'structure' in cluster
        assert 'local_sim' in cluster
        assert 'global_sim' in cluster

    def test_unit_parameter(self):
        """다양한 unit 값"""
        cluster1 = place_first_two_areas("A", "B", local_sim=0.5, global_sim=0.5, unit=1.0)
        cluster2 = place_first_two_areas("A", "B", local_sim=0.5, global_sim=0.5, unit=2.0)

        # Unit이 2배면 diameter도 2배
        assert abs(cluster2['diameter'] - cluster1['diameter'] * 2.0) < 0.01
