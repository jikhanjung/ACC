"""
pytest configuration and fixtures for ACC tests
"""

import pytest
import pandas as pd
from pathlib import Path
import sys

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))


@pytest.fixture
def test_data_dir():
    """테스트 데이터 디렉토리"""
    return Path(__file__).parent / "test_data"


@pytest.fixture
def sample_local_df(test_data_dir):
    """샘플 local DataFrame (6-영역)"""
    return pd.read_csv(test_data_dir / "sample_local.csv", index_col=0)


@pytest.fixture
def sample_global_df(test_data_dir):
    """샘플 global DataFrame (6-영역)"""
    return pd.read_csv(test_data_dir / "sample_global.csv", index_col=0)


@pytest.fixture
def sample_local_matrix(sample_local_df):
    """샘플 local matrix (dict 형식)"""
    result = {}
    for idx in sample_local_df.index:
        result[idx] = {}
        for col in sample_local_df.columns:
            if idx != col:
                result[idx][col] = float(sample_local_df.loc[idx, col])
    return result


@pytest.fixture
def sample_global_matrix(sample_global_df):
    """샘플 global matrix (dict 형식)"""
    result = {}
    for idx in sample_global_df.index:
        result[idx] = {}
        for col in sample_global_df.columns:
            if idx != col:
                result[idx][col] = float(sample_global_df.loc[idx, col])
    return result


@pytest.fixture
def simple_abc_local_matrix():
    """간단한 3-영역 local matrix"""
    return {
        "A": {"B": 0.9, "C": 0.5},
        "B": {"A": 0.9, "C": 0.5},
        "C": {"A": 0.5, "B": 0.5}
    }


@pytest.fixture
def simple_abc_global_matrix():
    """간단한 3-영역 global matrix"""
    return {
        "A": {"B": 0.8, "C": 0.4},
        "B": {"A": 0.8, "C": 0.4},
        "C": {"A": 0.4, "B": 0.4}
    }


@pytest.fixture
def invalid_asymmetric_matrix():
    """비대칭 matrix (검증 실패용)"""
    import numpy as np
    arr = np.array([
        [1.0, 0.9, 0.8],
        [0.8, 1.0, 0.7],  # 비대칭: [0,1]=0.9 but [1,0]=0.8
        [0.8, 0.7, 1.0]
    ])
    return arr


@pytest.fixture
def invalid_diagonal_matrix():
    """대각선 != 1.0 matrix (검증 실패용)"""
    import numpy as np
    arr = np.array([
        [0.9, 0.8, 0.7],  # 대각선이 0.9
        [0.8, 1.0, 0.6],
        [0.7, 0.6, 1.0]
    ])
    return arr


@pytest.fixture
def invalid_range_matrix():
    """범위 초과 matrix (검증 실패용)"""
    import numpy as np
    arr = np.array([
        [1.0, 1.5, 0.8],  # 1.5 > 1.0
        [1.5, 1.0, 0.6],
        [0.8, 0.6, 1.0]
    ])
    return arr
