# ACC (Adaptive Cluster Circle)

[![Tests](https://github.com/jikhanjung/ACC/workflows/Tests/badge.svg)](https://github.com/jikhanjung/ACC/actions)
[![codecov](https://codecov.io/gh/jikhanjung/ACC/branch/main/graph/badge.svg)](https://codecov.io/gh/jikhanjung/ACC)

ACC는 두 종류의 덴드로그램(하위 subordinate, 포괄 inclusive)에서 유사도 정보를 결합해, 클러스터 간의 상대적 관계를 원형 도식으로 시각화하는 알고리즘입니다.

## 기능

- **Core Algorithm**: 계층적 클러스터링 데이터를 concentric circles로 시각화
- **GUI Application**: PyQt6 기반 대화형 인터페이스
- **Matrix Input**: CSV 파일로부터 similarity matrix 입력
- **Interactive Visualization**: matplotlib 기반 시각화

## 설치

### 필요한 라이브러리

```bash
pip install PyQt6 matplotlib scipy pandas numpy
```

## 사용법

### GUI 애플리케이션 (3단계 워크플로우)

```bash
python acc_gui.py
```

#### Step 1: Subordinate Matrix 로드
1. "Subordinate Similarity Matrix" 섹션에서 **Load CSV** 버튼 클릭
2. `data/sample_subordinate.csv` 파일 선택
3. Matrix 데이터 확인
4. **Dendrogram 자동 생성** - 계층적 클러스터링 구조 확인

#### Step 2: Inclusive Matrix 로드
1. "Inclusive Similarity Matrix" 섹션에서 **Load CSV** 버튼 클릭
2. `data/sample_inclusive.csv` 파일 선택
3. Matrix 데이터 확인
4. **Dendrogram 자동 생성** - 계층적 클러스터링 구조 확인

#### Step 3: ACC 시각화 생성
1. **Generate ACC Visualization** 버튼 클릭
2. Concentric circles 시각화 확인
3. 각 멤버의 위치와 클러스터 정보 확인

### Core Algorithm만 사용 (프로그래밍)

```python
from acc_core import build_acc, DendroNode

# 덴드로그램 구조 생성
sub_dendro = DendroNode(...)
inc_dendro = DendroNode(...)
inc_matrix = {...}

# ACC 알고리즘 실행
result = build_acc(sub_dendro, inc_dendro, inc_matrix, unit=1.0)

# 결과 확인
print(result["points"])  # 각 멤버의 좌표
print(result["diameter"])  # 원의 지름
print(result["theta"])  # 각도
```

## 파일 구조

```
ACC/
├── acc_core.py              # 핵심 알고리즘 구현
├── acc_utils.py             # 유틸리티 함수 (matrix → dendrogram 변환)
├── acc_gui.py               # PyQt6 GUI 애플리케이션
├── data/
│   ├── sample_subordinate.csv  # 예제 subordinate matrix
│   └── sample_inclusive.csv    # 예제 inclusive matrix
├── devlog/
│   └── 20251111_P01_*.md    # 개발 로그
├── CLAUDE.md                # Claude Code를 위한 가이드
└── README.md
```

## CSV 파일 형식

Similarity matrix는 다음과 같은 형식이어야 합니다:

```csv
,J,T,Y,N,O,Q
J,1.0,0.9,0.8,0.4,0.35,0.36
T,0.9,1.0,0.8,0.38,0.33,0.34
Y,0.8,0.8,1.0,0.37,0.32,0.33
N,0.4,0.38,0.37,1.0,0.75,0.75
O,0.35,0.33,0.32,0.75,1.0,0.85
Q,0.36,0.34,0.33,0.75,0.85,1.0
```

- 첫 행과 첫 열은 라벨 (동일해야 함)
- 대각선 값은 1.0
- 대칭 행렬이어야 함
- 값의 범위: 0.0 ~ 1.0 (유사도)

## 알고리즘 개요

1. **Similarity Matrix → Dendrogram 변환**: scipy의 hierarchical clustering 사용
2. **클러스터별 이중 점수 계산**: subordinate와 inclusive 유사도
3. **도형 변수 변환**: 지름(d) = unit / sim_inc, 각도(θ) = 180° × (1 - sim_sub)
4. **순차적 배치**: 유사도가 높은 클러스터부터 배치하고 병합

자세한 내용은 `ACC_Algorithm_Overview.md` 참조.

## 개발 로그

개발 과정과 설계 결정사항은 `devlog/` 디렉토리에 기록되어 있습니다.

## 라이선스

MIT License
