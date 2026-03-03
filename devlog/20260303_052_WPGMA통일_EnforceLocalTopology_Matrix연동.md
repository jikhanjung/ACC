# 052: WPGMA 통일 + Enforce Local Topology 행렬 연동

**날짜**: 2026-03-03
**작업 유형**: bugfix + feat

---

## 배경

Caradoc local.csv 데이터를 사용해 단계별 시각화를 확인하던 중, 덴드로그램에 표시되는 병합 유사도 값이 왼쪽 행렬 패널의 값과 다른 문제 발견.

- 행렬에는 (S,Q)=0.429가 다음 병합 대상으로 보임
- 덴드로그램은 ((J,T),Y)+O를 sim=0.457로 병합

---

## 근본 원인 분석

### WPGMA vs UPGMA 불일치

`ClusteringStepManager._merge_matrix` 는 항상 `(row_i + row_j) / 2.0` (WPGMA) 로 행렬을 축약하는 반면, `linkage(method="average")` 는 클러스터 크기로 가중 평균하는 UPGMA를 사용했다.

**예시** (Caradoc, max_sim=1.0):

| 방법 | d((TJY), O) | sim |
|---|---|---|
| WPGMA /2 (행렬) | 0.595 | **0.405** |
| UPGMA 가중 (덴드로그램) | 0.543 | **0.457** |

UPGMA에서는 d(TJY,O)=0.543 < d(S,Q)=0.571 → (TJY)+O 먼저 병합
WPGMA에서는 d(TJY,O)=0.595 > d(S,Q)=0.571 → S+Q 먼저 병합
→ 행렬과 덴드로그램이 서로 다른 병합 순서를 보여주는 불일치 발생

---

## 변경 내용

### 1. `clustering_steps.py` — 덴드로그램을 WPGMA로 통일

```python
# 전: UPGMA
self.linkage_matrix = linkage(condensed_dist, method="average")

# 후: WPGMA (행렬 축약과 동일한 단순 /2 평균)
self.linkage_matrix = linkage(condensed_dist, method="weighted")
```

`_merge_matrix`의 단순 /2 평균은 유지 (WPGMA 그대로).

### 2. `acc_core_tree.py` — `build_acc_tree` WPGMA 전환

기존: 전체 쌍 평균 (UPGMA-like) 으로 best pair 탐색 및 sim 계산
변경: WPGMA 유사도 캐시 (`local_cache`, `global_cache`) 사용

```python
# 초기화: leaf-level 원본 유사도로 캐시 구성
local_cache[key] = get_similarity(local_matrix, a, b)
global_cache[key] = get_similarity(global_matrix, a, b)

# 병합 시: WPGMA 재귀 갱신
new_sim = (_get(cache, fa, fc) + _get(cache, fb, fc)) / 2.0
```

이제 `build_acc_tree`의 병합 순서가 GUI 덴드로그램(WPGMA)과 정확히 일치.

**Caradoc 검증**:
```
GUI 덴드로그램:  T+J → (TJ)+Y → S+Q → (TJY)+O → all
ACC 트리:        T+J → (TJ)+Y → S+Q → (TJY)+O → all  ✓
```

### 3. `acc_gui.py` — ACCNodeTreeDialog 제거 + Enforce Local Topology 기능 추가

**제거**: `_draw_acc_node_tree()`, `ACCNodeTreeDialog` 클래스, `generate_acc()` 내 다이얼로그 표시 블록

**추가**: `_build_enforced_linkage()` 모듈 함수 (local topology + global WPGMA distance로 linkage 재구성)

**`StepDendrogramWidget` 수정**:
- `_enforced_linkage`, `_enforced_max_sim` 속성 추가
- Global 패널 전용 "Enforce local topology" 체크박스 추가
- `set_enforced_linkage()` 메서드 추가
- `update_dendrogram()`: 체크 시 enforced linkage로 덴드로그램 그림

**`MainWindow._on_enforce_topology_changed(state)` 추가**:
- 체크 시: `EnforcedClusteringStepManager` 생성 → 글로벌 행렬 위젯 + 덴드로그램 동시 업데이트
- 언체크 시: 원래 step_manager 복원, 원래 덴드로그램 복원

**`StepMatrixWidget` 수정**:
- `set_enforced_step_manager(enforced_mgr)`: 원래 step_manager 백업 후 교체
- `restore_step_manager()`: 원래 step_manager 복원

### 4. `clustering_steps.py` — `EnforcedClusteringStepManager` 클래스 추가

Local topology를 따르되 global 행렬 값으로 단계별 표시를 제공하는 step manager:

- `linkage_matrix`: local topology + global WPGMA distance (덴드로그램용)
- `steps[]`: local 병합 순서에 따른 global 행렬 축약 시퀀스 (행렬 위젯용)
- `get_step()`, `get_num_steps()`, `get_step_description()`: `ClusteringStepManager`와 동일 인터페이스

---

## 테스트 결과

```
pytest tests/unit/ -v → 126 passed
ruff check acc_gui.py clustering_steps.py → All checks passed
```

---

## 변경 파일

| 파일 | 변경 유형 | 내용 |
|------|-----------|------|
| `clustering_steps.py` | bugfix + feat | method="weighted", EnforcedClusteringStepManager 추가 |
| `acc_core_tree.py` | bugfix | WPGMA 캐시 기반 build_acc_tree |
| `acc_gui.py` | feat + refactor | ACCNodeTreeDialog 제거, Enforce Local Topology 기능 |
