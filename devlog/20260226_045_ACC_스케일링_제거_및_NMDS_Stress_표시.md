# 045: ACC 포인트 스케일링 제거 및 NMDS Stress 품질 표시

**작업 일시**: 2026-02-26

## 요약
ACC 알고리즘에서 클러스터 병합 시 기존 포인트를 강제 스케일링하던 로직을 제거하여, 이미 배치된 포인트가 원래 반지름을 유지하도록 수정. 단일 멤버 클러스터를 병합 대상에서 제외. NMDS 패널에 Stress 값의 품질 해석(Excellent/Good/Fair/Poor)을 색상과 함께 표시하는 기능 추가.

## 변경 내용

### 1. acc_core.py — add_area_to_cluster() 스케일링 제거

기존에는 `final_d / base["diameter"]`로 스케일 팩터를 계산하여 모든 기존 포인트를 원점 기준으로 확대/축소했으나, 이를 제거. 기존 포인트는 `dict(base["points"])`로 그대로 복사하고, 새 멤버만 `new_cluster["diameter"] / 2.0` 반지름 위에 배치.

```python
# 기존 포인트는 원래 반지름 유지 (이미 배치된 원 위에 고정)
new_points = dict(base["points"])
new_r = new_cluster["diameter"] / 2.0
# 새 점은 새 클러스터의 반지름 위에 배치
new_xy = pol2cart(new_r, ang)
```

### 2. acc_core.py — merge_two_clusters() 스케일링 제거

마찬가지로 base와 new 양쪽 포인트에 적용하던 스케일링을 제거. `atan2(x, y)` 순서 오류가 있던 중복 라인도 정리.

```python
# 기존 포인트는 원래 반지름 유지
new_points = dict(base["points"])
# 새 클러스터 포인트도 자체 반지름 유지
tmp_points = dict(tmp["points"])
```

### 3. acc_core.py — 단일 멤버 클러스터 제외

`build_acc_merged()`와 `build_acc_steps()` 모두에서 멤버가 1개인 클러스터를 필터링하여 기하 정보가 없는 단일 멤버 클러스터가 병합 과정에 포함되지 않도록 처리.

```python
# 단일 멤버 클러스터 제외 (자체 기하 정보 없음)
clusters = [c for c in clusters if len(c["members"]) >= 2]
```

### 4. acc_gui.py — NMDS Stress 품질 라벨 추가

- `NMDSVisualizationWidget.run_nmds()`에서 stress 값을 반환하도록 수정
- `NMDSPanel`에 `stress_label` 위젯 추가
- `MainWindow.run_nmds()`에서 stress 값을 받아 품질 해석과 색상을 적용:
  - `< 0.05` → Excellent (녹색 #4CAF50)
  - `< 0.1` → Good (연두 #8BC34A)
  - `< 0.2` → Fair (주황 #FF9800)
  - `≥ 0.2` → Poor (빨강 #F44336)

## 수정 파일
- `acc_core.py`
- `acc_gui.py`

## 검증 방법
- ACC 시각화에서 클러스터 병합 시 기존 포인트 위치가 변하지 않는지 확인
- 단일 멤버만 있는 클러스터가 병합 과정에서 제외되는지 확인
- NMDS 실행 후 Stress 라벨에 값과 품질 텍스트가 색상과 함께 표시되는지 확인
