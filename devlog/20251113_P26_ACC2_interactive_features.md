# P26: ACC2 Interactive Features & UI Improvements (2025-11-13)

## 개요

ACC2 visualization에 interactive 기능들을 추가하고, dendrogram 단계별 보기의 UX를 개선했습니다.

## 작업 내역

### 1. ACC2 동심원 라벨 개선

**변경 사항:**
- 동심원 라벨을 반지름(r) 값에서 **global similarity** 값으로 변경
- 가장 안쪽 원(r=0.5)은 "Areas"로 표시

**이유:**
- ACC2의 공식이 `diameter = 1 + (1 - global_sim)`이므로 radius 값보다 similarity 값이 더 직관적
- 사용자가 실제 similarity 값을 바로 확인 가능

**구현:**
- `visualize_acc2.py`: `visualize_acc2()` 함수 수정
- `acc_gui.py`: `ACCVisualizationWidget.plot_acc2()` 메서드 수정
- `radius_to_sim` 매핑 생성하여 각 radius에 해당하는 global_sim 값 저장

**결과:**
```
보라색 원: "Areas"
파란색 원: "global_sim=0.880"
하늘색 원: "global_sim=0.830"
초록색 원: "global_sim=0.810"
...
```

---

### 2. Merge Point Hover 정보 표시

**기능:**
- Merge point(빨간색 점)에 마우스를 올리면 노란색 툴팁 박스 표시
- 표시 정보:
  - Cluster ID (예: `[J, T]`)
  - Angle (각도)
  - Local similarity

**구현:**
- matplotlib의 `annotate()` 사용
- `motion_notify_event` 이벤트 핸들러 연결
- 마우스 위치에서 가장 가까운 merge point 찾기 (threshold: axis limit의 5%)
- `merge_point_data` 리스트에 모든 merge point 정보 저장

**코드 위치:**
- `visualize_acc2.py`: lines 121-218
- `acc_gui.py`: lines 1563-1727

---

### 3. Merge Point 클릭으로 Branch Swap

**기능:**
- Merge point를 클릭하면 양쪽 branch가 swap됨
- 다시 클릭하면 원래대로 복구
- 하단 info label에 swap 상태 표시

**동작 방식:**
1. 사용자가 merge point 클릭
2. 해당 merge의 두 children subtree의 모든 descendant areas 찾기
3. 각 area의 angle을 merge_angle 기준으로 mirror: `new_angle = 2 * merge_angle - old_angle`
4. Merge points와 connection lines 재계산
5. Visualization 업데이트

**구현 메서드:**
- `get_all_descendants(cluster_id, levels, positions)`: Cluster의 모든 descendant areas 찾기
- `apply_acc2_swaps(acc2_data, swaps)`: Swap 적용하여 수정된 데이터 생성
- `plot_acc2(acc2_data, reset_swaps=True)`: Swap 상태 관리 및 visualization

**상태 관리:**
- `self.acc2_swaps`: `{level_idx: True/False}` dict로 swap 상태 저장
- `reset_swaps=False`로 호출하면 기존 swap 상태 유지

**이벤트 핸들러:**
- `button_press_event` 연결
- Click threshold: axis limit의 5%

**코드 위치:**
- `acc_gui.py`: lines 1468-1523 (helper methods), lines 1729-1772 (click handler)

---

### 4. Dendrogram 단계별 네비게이션 버튼 추가

**변경 사항:**
- 기존: `◀ [슬라이더] ▶`
- 신규: `⏮ ◀ [슬라이더] ▶ ⏭`

**버튼 기능:**
- `⏮` (First): 첫 번째 단계로 이동
- `◀` (Previous): 이전 단계로 이동
- `▶` (Next): 다음 단계로 이동 (preview animation 포함)
- `⏭` (Last): 마지막 단계로 이동

**구현 메서드:**
- `first_step()`: 슬라이더를 0으로 설정
- `last_step()`: 슬라이더를 최대값으로 설정
- 기존 `prev_step()`, `next_step()` 유지

**버튼 상태 관리:**
- 첫 번째 단계: `⏮`, `◀` 비활성화
- 마지막 단계: `▶`, `⏭` 비활성화
- 중간 단계: 모든 버튼 활성화

**적용 위치:**
1. `StepMatrixWidget` (Local/Global similarity matrix 단계별 보기)
2. `ACCVisualizationWidget` (ACC visualization 단계별 보기)

**코드 위치:**
- `acc_gui.py`:
  - StepMatrixWidget: lines 536-563 (UI), 650-760 (methods), 792-795 (button state)
  - ACCVisualizationWidget: lines 1202-1234 (UI), 1253-1271 (methods), 1288-1291 (button state)

---

### 5. Dendrogram 마지막 단계에서 원본 매트릭스 복구

**기능:**
- Dendrogram 단계별 보기에서 마지막 단계(모든 클러스터가 하나로 합쳐진 상태)에 도달하면
- 원본 매트릭스를 다시 표시

**이유:**
- 사용자가 전체 clustering 과정을 보고 난 후
- 원본 매트릭스로 돌아와서 전체 구조를 다시 확인 가능
- 순환적인 학습/탐색 경험 제공

**구현:**
- `StepMatrixWidget.update_step_display()` 수정
- `current_step == max_step` 체크
- `step_manager.original_similarity`와 `original_labels` 사용
- 설명 텍스트: "Final step - Original matrix restored"

**코드 위치:**
- `acc_gui.py`: lines 768-795

---

## 수정된 파일

### 신규 파일
1. `acc_core_acc2.py`: ACC2 알고리즘 구현
2. `visualize_acc2.py`: ACC2 standalone visualization
3. `devlog/20251113_P25_ACC2_개발계획.md`: ACC2 개발 계획 문서
4. `acc2_visualization.png`: ACC2 샘플 출력

### 수정된 파일
1. `acc_gui.py`:
   - ACC2 visualization 추가 (`plot_acc2()` 메서드)
   - Interactive features (hover, click)
   - Branch swap 기능
   - Navigation 버튼 추가 (⏮, ⏭)
   - 마지막 단계 원본 복구
   - Import 추가: `calculate_merge_points`, `generate_connection_lines`

2. `visualize_acc2.py`:
   - Global similarity 라벨 표시
   - Hover annotation
   - Interactive features

---

## 사용 시나리오

### ACC2 Interactive Exploration
1. "Generate ACC2" 버튼 클릭
2. 동심원의 라벨에서 global similarity 값 확인
3. 빨간색 merge point에 마우스 올려서 상세 정보 확인
4. 원하는 merge point 클릭하여 branch swap
5. 여러 merge point를 조합하여 최적의 layout 생성

### Dendrogram Step-by-Step Navigation
1. Local/Global matrix 로드
2. 단계별 슬라이더 활성화
3. `⏮` 버튼으로 첫 단계로 이동
4. `▶` 버튼으로 천천히 clustering 과정 관찰
5. `⏭` 버튼으로 마지막 단계 이동 → 원본 매트릭스 복구
6. 다시 `◀` 버튼으로 되돌아가며 특정 단계 확인

---

## 기술적 세부사항

### Branch Swap 알고리즘
```python
# 1. 모든 descendants 찾기
child1_areas = get_all_descendants(level['cluster1'], levels, positions)
child2_areas = get_all_descendants(level['cluster2'], levels, positions)

# 2. Merge angle 기준으로 mirror
for area in child1_areas + child2_areas:
    old_angle = positions[area]['angle']
    new_angle = 2 * merge_angle - old_angle
    positions[area]['angle'] = new_angle

# 3. Merge points와 lines 재계산
merge_points = calculate_merge_points(levels, positions)
lines = generate_connection_lines(levels, positions, merge_points)
```

### Hover Detection
```python
# 가장 가까운 merge point 찾기
for x, y, angle, local_sim, cluster_id in merge_point_data:
    dist = ((event.xdata - x)**2 + (event.ydata - y)**2)**0.5
    if dist < min_dist:
        min_dist = dist
        closest_point = (x, y, angle, local_sim, cluster_id)

# Threshold 기반 표시 여부 결정
threshold = lim * 0.05  # 5% of axis limit
if min_dist < threshold:
    show_annotation()
```

---

## 향후 개선 가능성

1. **ACC2 Export**: Swap이 적용된 최종 layout을 SVG/PDF로 저장
2. **Swap History**: Undo/Redo 기능
3. **Preset Layouts**: 자주 사용하는 swap 조합을 저장/불러오기
4. **Keyboard Shortcuts**:
   - Home/End: 첫/마지막 단계
   - Space: Swap toggle
   - Arrow keys: 단계 이동
5. **Animation**: Branch swap 시 애니메이션 효과
6. **Comparison View**: 원본 ACC2와 swap 적용 버전을 나란히 표시

---

## 테스트 결과

✅ ACC2 동심원 라벨에 global similarity 표시
✅ Merge point hover 시 정보 표시
✅ Merge point 클릭 시 branch swap 작동
✅ Navigation 버튼(⏮, ⏭) 정상 작동
✅ 마지막 단계에서 원본 매트릭스 복구
✅ Local/Global matrix 양쪽에서 모두 작동
✅ ACC visualization에서도 navigation 버튼 작동

---

## 예상 시간 vs 실제 시간

- 예상: 3-4시간
- 실제: 약 3시간
  - ACC2 라벨 변경: 30분
  - Hover 기능: 30분
  - Branch swap: 1.5시간
  - Navigation 버튼: 30분
  - 원본 복구: 30분

---

## 참고사항

- Branch swap은 dendrogram의 구조를 변경하지 않고 시각적 배치만 변경
- Swap 상태는 세션 내에서만 유지되며, 재생성 시 초기화됨
- 원본 매트릭스는 `ClusteringStepManager`에 항상 보존됨
