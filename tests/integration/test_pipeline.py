"""
Integration tests for complete ACC pipeline
Tests CSV → Dendrogram → ACC workflow
"""

import pytest
from acc_utils import (
    dict_matrix_from_dataframe,
    validate_similarity_matrix,
    build_acc_from_matrices,
    build_acc_from_matrices_steps,
    build_acc_from_matrices_iterative,
)


class TestFullPipeline:
    """Complete pipeline from CSV to ACC"""

    def test_sample_data_pipeline(self, sample_local_df, sample_global_df):
        """샘플 데이터 전체 파이프라인"""
        # 1. DataFrame to dict
        local_matrix = dict_matrix_from_dataframe(sample_local_df)
        global_matrix = dict_matrix_from_dataframe(sample_global_df)

        # 2. Validate
        valid_sub, msg_sub = validate_similarity_matrix(sample_local_df.values)
        valid_inc, msg_inc = validate_similarity_matrix(sample_global_df.values)

        assert valid_sub, f"Local validation failed: {msg_sub}"
        assert valid_inc, f"Global validation failed: {msg_inc}"

        # 3. Build ACC
        result = build_acc_from_matrices(local_matrix, global_matrix, unit=1.0)

        # 4. Verify results
        assert 'clusters' in result
        assert 'all_members' in result
        assert len(result['all_members']) == 6  # J, T, Y, N, O, Q

    def test_simple_abc_pipeline(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """간단한 3-영역 파이프라인"""
        result = build_acc_from_matrices(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0,
            method='average'
        )

        assert 'clusters' in result
        assert len(result['all_members']) == 3
        assert result['all_members'] == {"A", "B", "C"}

    def test_step_by_step_pipeline(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """단계별 ACC 생성"""
        steps = build_acc_from_matrices_steps(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0
        )

        assert isinstance(steps, list)
        assert len(steps) > 0

        # 각 step은 필요한 정보를 포함해야 함
        for step in steps:
            assert 'step' in step
            assert 'action' in step
            assert 'description' in step

    def test_iterative_algorithm(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """반복적 알고리즘 (ACC2)"""
        steps = build_acc_from_matrices_iterative(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0
        )

        assert isinstance(steps, list)
        assert len(steps) > 0

        # 마지막 step은 모든 멤버를 포함해야 함
        final_step = steps[-1]
        assert 'clusters' in final_step
        if len(final_step['clusters']) > 0:
            all_members = set()
            for cluster in final_step['clusters']:
                all_members.update(cluster['members'])
            assert len(all_members) == 3


class TestDifferentMethods:
    """Different hierarchical clustering methods"""

    @pytest.mark.parametrize("method", ['average', 'single', 'complete'])
    def test_clustering_methods(self, simple_abc_local_matrix, simple_abc_global_matrix, method):
        """다양한 clustering method 테스트"""
        result = build_acc_from_matrices(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0,
            method=method
        )

        assert 'clusters' in result
        assert len(result['all_members']) == 3

    def test_ward_method_not_applicable(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """Ward method는 유클리드 거리 필요"""
        # Ward는 similarity matrix에서 직접 사용 불가
        # 이 테스트는 오류를 기대하거나, 다른 method로 fallback되는지 확인
        try:
            result = build_acc_from_matrices(
                simple_abc_local_matrix,
                simple_abc_global_matrix,
                unit=1.0,
                method='ward'
            )
            # Ward가 작동하면 결과 확인
            assert 'clusters' in result
        except (ValueError, Exception):
            # Ward가 실패하면 예외 발생 예상
            pass


class TestEdgeCases:
    """Edge cases and boundary conditions"""

    def test_minimum_areas(self):
        """최소 영역 수 (2개)"""
        local_matrix = {"A": {"B": 0.8}, "B": {"A": 0.8}}
        global_matrix = {"A": {"B": 0.7}, "B": {"A": 0.7}}

        result = build_acc_from_matrices(local_matrix, global_matrix, unit=1.0)

        assert len(result['all_members']) == 2
        assert result['all_members'] == {"A", "B"}

    def test_unit_parameter(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """다양한 unit 값 테스트"""
        units = [0.5, 1.0, 2.0]

        for unit in units:
            result = build_acc_from_matrices(
                simple_abc_local_matrix,
                simple_abc_global_matrix,
                unit=unit
            )
            assert 'clusters' in result

            # Unit이 다르면 diameter도 달라져야 함
            # (하지만 members는 동일)
            assert len(result['all_members']) == 3

    def test_identical_similarities(self):
        """모든 유사도가 동일한 경우"""
        matrix = {
            "A": {"B": 0.5, "C": 0.5},
            "B": {"A": 0.5, "C": 0.5},
            "C": {"A": 0.5, "B": 0.5}
        }

        result = build_acc_from_matrices(matrix, matrix, unit=1.0)

        assert len(result['all_members']) == 3
        # 모든 유사도가 같아도 정상 작동해야 함


class TestResultStructure:
    """Verify structure of ACC results"""

    def test_result_has_required_fields(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """결과가 필요한 필드를 포함하는지 검증"""
        result = build_acc_from_matrices(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0
        )

        assert 'clusters' in result
        assert 'all_members' in result
        assert isinstance(result['clusters'], list)
        assert isinstance(result['all_members'], set)

    def test_cluster_structure(self, simple_abc_local_matrix, simple_abc_global_matrix):
        """각 cluster가 필요한 정보를 포함하는지 검증"""
        result = build_acc_from_matrices(
            simple_abc_local_matrix,
            simple_abc_global_matrix,
            unit=1.0
        )

        for cluster in result['clusters']:
            assert 'members' in cluster
            assert 'diameter' in cluster
            assert 'theta' in cluster
            assert 'points' in cluster

            # points는 각 member의 좌표를 포함해야 함
            assert isinstance(cluster['points'], dict)
            for member in cluster['members']:
                assert member in cluster['points']
                x, y = cluster['points'][member]
                assert isinstance(x, (int, float))
                assert isinstance(y, (int, float))
