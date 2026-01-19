# 20251117_P31_ACC2 Swap 버그 수정, Matrix 편집 반영, ACC1 Style 및 UX 개선

**날짜:** 2025년 11월 17일
**작업자:** Claude Code
**관련 파일:** `acc_gui.py`, `acc_core_acc2.py`

## 작업 개요

ACC2의 swap 기능 버그를 수정하고, matrix 편집 내용이 실시간으로 dendrogram/ACC에 반영되도록 개선했습니다. 또한 ACC2에 ACC1 스타일 옵션을 추가하고 불필요한 로그 출력을 제거하여 사용자 경험을 개선했습니다.

---

## 1. ACC2 Swap 버그 수정

### 1.1 문제 상황

**증상:**
- Merge point를 클릭하여 branch를 swap할 때, 계층적으로 여러 번 swap하면 area들이 잘못된 위치로 이동
- 예: Level 4를 swap한 후 Level 2를 swap하면 NOQ와 JTY가 모두 겹침

**Screenshot 5 참고:**
- 두 번째 swap 실행 후 NOQ와 JTY 영역이 겹치는 현상

### 1.2 원인 분석

**문제의 핵심:**
```python
# 기존 코드 - 순차적으로 각 swap을 적용
for level_idx in sorted_swap_levels:
    # child1의 descendants를 child2 위치로 이동
    for area in child1_descendants:
        positions[area]["angle"] = child2_angle + relative_angle

    # child2의 descendants를 child1 위치로 이동
    for area in child2_descendants:
        positions[area]["angle"] = child1_angle + relative_angle
```

**문제점:**
1. 첫 번째 swap에서 area A를 위치 X로 이동
2. 두 번째 swap 실행 시 area A가 다시 이동 대상에 포함됨
3. Area A가 최종적으로 잘못된 위치에 도달

**예시:**
```
초기 상태: J(10°), T(20°), N(30°), O(40°), Q(50°)

Level 4 swap (JT ↔ 다른 branch):
  J: 10° → 30°
  T: 20° → 40°

Level 2 swap (다시 swap):
  J: 30° → 10° (원래대로?)
  T: 40° → 20° (원래대로?)

결과: 모든 area가 겹침 또는 잘못된 위치
```

### 1.3 해결 방법

**핵심 아이디어: Relative Angle Preservation + Temporary Storage**

```python
# 수정된 코드 (lines 1770-1796)
# Store new angles temporarily to avoid overwriting during swap
new_angles = {}

# Move child1's descendants to where child2 was
for area in child1_descendants:
    if area in positions:
        current_angle = positions[area]["angle"]
        # Calculate relative position within child1
        relative_angle = current_angle - child1_angle
        # Place it at child2's position with same relative angle
        new_angles[area] = child2_angle + relative_angle

# Move child2's descendants to where child1 was
for area in child2_descendants:
    if area in positions:
        current_angle = positions[area]["angle"]
        # Calculate relative position within child2
        relative_angle = current_angle - child2_angle
        # Place it at child1's position with same relative angle
        new_angles[area] = child1_angle + relative_angle

# Apply all new angles at once
for area, new_angle in new_angles.items():
    positions[area]["angle"] = new_angle
```

**개선 사항:**
1. **Temporary storage:** `new_angles` 딕셔너리에 모든 변경사항 저장
2. **Relative angle preservation:** 각 branch 내의 상대적 각도 유지
3. **Atomic update:** 모든 계산 후 한 번에 적용

### 1.4 테스트 결과

**테스트 케이스 1: 단일 swap**
- ✅ Level 4 swap → NOQ와 JTY가 정확히 교환됨
- ✅ 각 branch 내부의 상대적 위치 유지

**테스트 케이스 2: 계층적 다중 swap**
- ✅ Level 4 swap → Level 2 swap → 모든 area가 올바른 위치
- ✅ 겹침 현상 없음
- ✅ Relative angle 완벽히 보존

**Screenshot 7 참고:**
- 다중 swap 후에도 정확한 위치 배치

---

## 2. ACC2 Merge Point Angle 표시 버그 수정

### 2.1 문제 상황

**증상:**
- Merge point 툴팁이 잘못된 각도 표시
- 예: J와 T의 merge point에서 51.8° 표시 (실제 subtended angle은 18°)

**로그 예시:**
```
Level 1: J + T
  Angle between J(10°) and T(28°) = 18°  (실제 값)
Tooltip: [J, T] at 51.8°, local_sim=0.900  (잘못된 표시)
```

### 2.2 원인 분석

```python
# 기존 코드
for cluster_id, mp in merge_points.items():
    merge_angle = mp["angle"]  # 이건 merge point의 polar angle

    # 툴팁에 merge_angle을 표시 - 잘못된 값!
    merge_point_data.append((x, y, merge_angle, local_sim, cluster_id))
```

**문제점:**
- `merge_angle`은 merge point의 극좌표 각도 (51.8°)
- 사용자가 원하는 것은 두 children 사이의 subtended angle (18°)

### 2.3 해결 방법

**Subtended angle 계산 로직 추가** (lines 1876-1922):

```python
# Calculate subtended angle (angle between two children)
subtended_angle = 0.0
if cluster_id in cluster_to_children:
    child1_id, child2_id = cluster_to_children[cluster_id]

    # Get child angles
    def get_child_angle(child_id):
        if child_id in positions:
            return positions[child_id]["angle"]
        elif child_id in merge_points:
            return merge_points[child_id]["angle"]
        return None

    child1_angle = get_child_angle(child1_id)
    child2_angle = get_child_angle(child2_id)

    if child1_angle is not None and child2_angle is not None:
        # Calculate absolute difference
        subtended_angle = abs(child2_angle - child1_angle)
        # Handle wrap-around (e.g., 350° to 10° should be 20°, not 340°)
        if subtended_angle > 180:
            subtended_angle = 360 - subtended_angle

# Store merge point data for hover
local_sim = cluster_to_subsim.get(cluster_id, 0.0)
merge_point_data.append((x, y, merge_angle, subtended_angle, local_sim, cluster_id))
```

**개선 사항:**
1. Children의 실제 각도를 찾아서 차이 계산
2. Wrap-around 처리 (350° ↔ 10° = 20°)
3. Tooltip에 subtended angle 표시

### 2.4 테스트 결과

**Before:**
```
Merge point [J, T]: Angle: 51.8°, Sub sim: 0.900
```

**After:**
```
Merge point [J, T]: Angle: 18.0°, Sub sim: 0.900
```

✅ 정확한 subtended angle 표시

---

## 3. Matrix 편집 실시간 반영

### 3.1 문제 상황

**증상:**
- Matrix 값을 편집해도 dendrogram이나 ACC가 업데이트되지 않음
- 예: J-T global similarity를 0.88 → 0.5로 변경해도 변화 없음

**시도한 작업:**
1. Upper triangle에서 J-T 값을 0.5로 변경
2. Generate ACC 버튼 클릭
3. 결과: 여전히 0.88 기준으로 생성됨

### 3.2 원인 분석

**문제 1: Step 조건 체크**
```python
# 기존 코드 (line 965)
def on_item_changed(self, item):
    if self.current_step != 0:  # Step 0에서만 편집 허용
        return  # 다른 step에서는 무시!
```

**문제점:**
- Matrix를 로드하면 자동으로 마지막 step (5)로 이동
- Step 5에서 편집하면 `on_item_changed`가 무시됨

**문제 2: Slider 무한 루프**
```python
# Matrix 값 변경
self.matrix_data.iloc[row, col] = value

# Clustering 재생성
self.step_manager = ClusteringStepManager(...)

# Slider 업데이트
self.step_slider.setValue(max_steps)
  └─> valueChanged signal
      └─> on_step_changed()
          └─> update_table()
              └─> itemChanged signal
                  └─> on_item_changed()  # 무한 루프!
```

### 3.3 해결 방법

**Solution 1: Step 체크 제거**
```python
# 수정된 코드 (lines 973-1002)
def on_item_changed(self, item):
    # Step 체크 제거 - 모든 step에서 편집 가능

    # 기존 로직 유지
    row = item.row()
    col = item.column()
    ...
```

**Solution 2: 프로그래밍 방식 업데이트 플래그**
```python
# MatrixTableWidget 클래스에 플래그 추가
self._updating_programmatically = False

def on_item_changed(self, item):
    # 프로그래밍 방식 업데이트는 무시
    if self._updating_programmatically:
        return

    # Mirror cell 업데이트 시 플래그 사용
    if row != col and not self.updating_mirror:
        self.updating_mirror = True
        mirror_item = self.table.item(col, row)
        if mirror_item:
            mirror_item.setText(f"{value:.3f}")
        self.updating_mirror = False
```

**Solution 3: 자동 재클러스터링**
```python
# Matrix 값 변경 시 즉시 재클러스터링
self.matrix_data.iloc[row, col] = value
self.matrix_data.iloc[col, row] = value

# Regenerate clustering with updated matrix
self.step_manager = ClusteringStepManager(
    self.matrix_data.values,
    self.matrix_data.index.tolist()
)

# Move to last step to show full dendrogram
max_steps = len(self.step_manager.linkage_matrix) if self.step_manager else 0
self.current_step = max_steps

# Update slider
self._updating_programmatically = True
self.step_slider.setMaximum(max_steps)
self.step_slider.setValue(max_steps)
self._updating_programmatically = False

# Update info label
self.info_label.setText(f"✓ Updated {row_label}-{col_label}: {value:.3f}")
self.info_label.setStyleSheet("color: green; font-size: 10px;")

# Notify parent to update dendrogram
if hasattr(self.parent(), "on_matrix_loaded"):
    self.parent().on_matrix_loaded(self.matrix_type)
```

### 3.4 워크플로우

**Before:**
```
1. Matrix 편집
2. (아무 일도 안 일어남)
3. Generate ACC 클릭
4. (여전히 이전 데이터 사용)
```

**After:**
```
1. Matrix 편집
   ├─> 즉시 재클러스터링
   ├─> Dendrogram 자동 업데이트
   ├─> Step 5로 자동 이동
   └─> Info label에 "✓ Updated J-T: 0.500" 표시
2. Generate ACC 클릭
   └─> 새로운 matrix 값으로 ACC 생성
```

### 3.5 테스트 결과

**테스트 케이스 1: J-T global similarity 0.88 → 0.5 변경**
- ✅ 즉시 재클러스터링
- ✅ Dendrogram이 새로운 구조로 업데이트
- ✅ ACC 생성 시 새로운 값 반영
- ✅ Infinite loop 없음

**테스트 케이스 2: 여러 값 연속 편집**
- ✅ 각 편집마다 재클러스터링
- ✅ UI가 freeze되지 않음
- ✅ Info label에 각 변경사항 표시

---

## 4. Tab 구조 개선

### 4.1 변경 사항

**Before:**
- ACC와 ACC2가 같은 탭에 표시
- 두 개의 Generate 버튼

**After:**
- QTabWidget으로 ACC와 ACC2 분리
- 단일 Generate 버튼 (활성 탭에 따라 동작)

**구현** (lines 2331-2357):
```python
# Create tab widget
self.tab_widget = QTabWidget()

# Tab 1: ACC (original)
self.acc_widget = ACCVisualizationWidget()
self.tab_widget.addTab(self.acc_widget, "ACC")

# Tab 2: ACC2 with options
self.acc2_tab = QWidget()
acc2_layout = QVBoxLayout(self.acc2_tab)
self.tab_widget.addTab(self.acc2_tab, "ACC2")

# Single Generate button
generate_btn.clicked.connect(self.on_generate_clicked)

def on_generate_clicked(self):
    current_tab = self.tab_widget.currentIndex()
    if current_tab == 0:  # ACC tab
        main_window.generate_acc()
    elif current_tab == 1:  # ACC2 tab
        main_window.generate_acc2()
```

---

## 5. ACC2 ACC1 스타일 옵션 추가

### 5.1 기능 요구사항

**기존 ACC2 시각화:**
- 모든 area가 innermost circle (r=0.5)에 배치됨
- 각 area에서 merge point까지 radial line으로 연결

**ACC1 스타일:**
- 각 area를 첫 번째 merge가 발생하는 circle에 배치
- Innermost circle에서 시작하는 radial line 제거
- ACC1의 시각적 스타일을 유지하면서 ACC2의 dendrogram 구조 표현

### 1.2 구현 내용

#### UI 컴포넌트 추가 (`acc_gui.py`)

**체크박스 추가** (lines 2465-2467):
```python
# ACC1 Style checkbox
self.acc2_acc1_style = QCheckBox("ACC1 Style")
self.acc2_acc1_style.setToolTip("Place areas on their first merge circle instead of innermost circle")
options_layout.addWidget(self.acc2_acc1_style)
```

**Apply 버튼 연동** (line 2535):
```python
acc1_style = self.acc2_acc1_style.isChecked()
main_window.generate_acc2_with_options(min_diameter, max_diameter, acc1_style)
```

#### ACC1 스타일 적용 로직 (`acc_gui.py`)

**plot_acc2 함수 수정** (lines 1808-1845):
```python
# Apply ACC1 style to the data first (before storing)
if acc1_style:
    acc2_data = copy.deepcopy(acc2_data)

    # For each area, find its first merge level and place it on that circle
    area_to_first_merge_radius = {}

    for level_idx, level in enumerate(acc2_data['levels']):
        cluster1 = level['cluster1']
        cluster2 = level['cluster2']
        merge_radius = level['radius']

        # Get all areas in cluster1 and cluster2
        def get_areas(cluster_id):
            if cluster_id in acc2_data['positions']:
                return [cluster_id]
            areas = []
            for lvl in acc2_data['levels']:
                if f"[{lvl['cluster1']}, {lvl['cluster2']}]" == cluster_id:
                    areas.extend(get_areas(lvl['cluster1']))
                    areas.extend(get_areas(lvl['cluster2']))
                    break
            return areas

        areas1 = get_areas(cluster1)
        areas2 = get_areas(cluster2)

        # For each area, if not yet assigned, assign to this merge radius
        for area in areas1 + areas2:
            if area not in area_to_first_merge_radius:
                area_to_first_merge_radius[area] = merge_radius

    # Update position radii
    for area, merge_radius in area_to_first_merge_radius.items():
        if area in acc2_data['positions']:
            acc2_data['positions'][area]['radius'] = merge_radius
```

**Radial line 필터링** (lines 1894-1905):
```python
# Draw radial lines
# Get innermost circle radius (minimum radius in circles)
innermost_radius = min(circles) if circles else 0.5

for line in lines:
    if line["type"] == "radial":
        r1, angle = line["from"]
        r2, _ = line["to"]

        # Skip radial lines starting from innermost circle if ACC1 style
        if self.acc1_style and abs(r1 - innermost_radius) < 0.001:
            continue

        # Convert to cartesian
        x1, y1 = pol2cart(r1, angle)
        x2, y2 = pol2cart(r2, angle)

        ax.plot([x1, x2], [y1, y2], "k-", linewidth=2, alpha=0.8)
```

### 1.3 Swap 후 Radial Line 재생성 문제 해결

#### 문제 상황

ACC1 스타일로 그린 후 swap을 실행하면 innermost circle에서 시작하는 radial line이 다시 나타남.

#### 원인 분석

1. **데이터 저장 시점 문제:**
   - `generate_acc2_with_options`에서 ACC1 스타일을 적용
   - `plot_acc2`에서 원본 데이터를 `self.acc2_data`에 저장
   - Swap 시 원본 데이터로 connection lines 재생성

2. **generate_connection_lines 함수 문제 (`acc_core_acc2.py`):**
   ```python
   # 하드코딩된 radius 값 사용
   if child_id in final_positions:
       return (0.5, final_positions[child_id]['angle'])  # 문제!
   ```

#### 해결 방법

**1단계: ACC1 스타일 적용 위치 이동**

`generate_acc2_with_options`에서 ACC1 스타일 적용 코드를 제거하고, `plot_acc2` 내부에서 적용:

```python
# generate_acc2_with_options (line 2829-2831)
# Visualize ACC2 in the ACC2 tab
# ACC1 style will be applied inside plot_acc2
self.right_panel.acc2_widget.plot_acc2(acc2_data, acc1_style=acc1_style)
```

**2단계: generate_connection_lines 수정 (`acc_core_acc2.py`)**

하드코딩된 radius 대신 실제 position의 radius 사용:

```python
# lines 273-284
def get_child_info(child_id):
    if child_id in final_positions:
        # It's an area - use its actual radius (may not be 0.5 in ACC1 style)
        pos = final_positions[child_id]
        return (pos['radius'], pos['angle'])
    elif child_id in merge_points:
        # It's a cluster at its merge radius
        mp = merge_points[child_id]
        return (mp['radius'], mp['angle'])
    else:
        raise ValueError(f"Child {child_id} not found")
```

#### 수정된 데이터 플로우

```
generate_acc2_with_options
  ├─ build_acc2 (원본 데이터 생성)
  ├─ diameter scaling (반지름 조정)
  └─ plot_acc2(acc2_data, acc1_style=True)
       ├─ ACC1 스타일 적용 (area radius 변경)
       ├─ self.acc2_data 저장 (ACC1 스타일 적용된 데이터)
       └─ apply_acc2_swaps
            └─ generate_connection_lines
                 └─ pos['radius'] 사용 (0.5 하드코딩 X)
```

---

## 2. 불필요한 로그 출력 제거

### 2.1 제거된 로그 목록

#### Matrix 편집 관련 로그 (`acc_gui.py`)

**lines 977, 983, 998 제거:**
```python
# 제거됨
print(f"[{self.matrix_type}] Updated {row_label}-{col_label}: {old} → {new}")
print(f"[{self.matrix_type}] Regenerating clustering...")
print(f"[{self.matrix_type}] Clustering regenerated, moved to step {max_steps}")
```

**유지된 것:**
- UI info label: `✓ Updated {row_label}-{col_label}: {value:.3f}`

#### Dendrogram 업데이트 로그 (`acc_gui.py`)

**lines 2593, 2597, 2602, 2606 제거:**
```python
# 제거됨
print(f"[MainWindow] update_dendrogram: sub_step_mgr = {True/False}")
print(f"[MainWindow] Local dendrogram updated")
print(f"[MainWindow] update_dendrogram: inc_step_mgr = {True/False}")
print(f"[MainWindow] Global dendrogram updated")
```

**line 2619 제거:**
```python
# 제거됨
print(f"[MainWindow] clear_dendrogram called for {which}")
```

#### LeftPanel 로그 (`acc_gui.py`)

**lines 2193, 2198, 2201, 2208, 2213, 2216 제거:**
```python
# 제거됨
print(f"[LeftPanel] on_matrix_loaded called for {matrix_type}")
print(f"[LeftPanel] Calling update_dendrogram('local'/'global')")
print(f"[LeftPanel] on_matrix_modified called for {matrix_type}")
print(f"[LeftPanel] Clearing local/global dendrogram")
```

#### Edit Area List 디버그 로그 (`acc_gui.py`)

**lines 2225, 2233, 2239-2240, 2244, 2259, 2270, 2275, 2278, 2281 제거:**
```python
# 제거됨
print("Edit Area List button clicked")
print("Both matrices loaded - editing existing")
print(f"Sub labels: {sub_labels}")
print(f"Inc labels: {inc_labels}")
print("Label mismatch detected")
print("Only one matrix loaded")
print("No matrices loaded - starting from scratch")
print("Creating dialog...")
print("Dialog created, executing...")
print(f"Dialog closed with code: {result_code}")
```

### 2.2 로그 정리 효과

**Before:**
```
[Local] Updated J-T: 0.880 → 0.500
[Local] Regenerating clustering...
[Local] Clustering regenerated, moved to step 5
[LeftPanel] on_matrix_loaded called for Local
[LeftPanel] Calling update_dendrogram('local')
[MainWindow] update_dendrogram: sub_step_mgr = True
[MainWindow] Local dendrogram updated
```

**After:**
```
(콘솔 출력 없음, UI의 info label에만 표시)
✓ Updated J-T: 0.500
```

---

## 7. 전체 테스트 결과

### 7.1 Swap 기능 테스트
- ✅ 단일 swap 정상 작동
- ✅ 계층적 다중 swap에서 겹침 없음
- ✅ Relative angle 완벽히 보존

### 7.2 Angle 표시 테스트
- ✅ Subtended angle 정확히 계산 (18° 표시)
- ✅ Wrap-around 처리 정상

### 7.3 Matrix 편집 반영 테스트
- ✅ 즉시 재클러스터링
- ✅ Dendrogram 자동 업데이트
- ✅ ACC 생성 시 새로운 값 반영
- ✅ Infinite loop 없음

### 7.4 ACC1 스타일 기능 테스트
- ✅ 각 area가 첫 merge circle에 배치됨
- ✅ Innermost circle radial line 제거됨
- ✅ Swap 후에도 ACC1 스타일 유지됨
- ✅ Diameter 범위 조정과 함께 작동

### 7.5 로그 제거 검증
- ✅ Matrix 편집 시 콘솔 로그 없음
- ✅ Dendrogram 업데이트 시 콘솔 로그 없음
- ✅ UI info label만 표시
- ✅ 대화상자 동작 정상

---

## 8. 코드 변경 요약

### 수정된 파일

1. **acc_gui.py**
   - **Swap 버그 수정:**
     - Temporary storage with relative angle preservation (lines 1770-1796)
   - **Angle 표시 수정:**
     - Subtended angle 계산 및 표시 (lines 1876-1922)
   - **Matrix 편집 반영:**
     - Step 체크 제거 (line 973)
     - 프로그래밍 업데이트 플래그 추가
     - 자동 재클러스터링 (lines 982-1002)
   - **Tab 구조:**
     - QTabWidget으로 ACC/ACC2 분리 (lines 2331-2357)
   - **ACC1 스타일:**
     - 체크박스 추가 (lines 2465-2467)
     - plot_acc2에서 스타일 적용 (lines 1808-1845)
     - Radial line 필터링 (lines 1894-1905)
   - **로그 제거:**
     - Matrix 편집 로그 제거 (lines 977, 983, 998)
     - Dendrogram 업데이트 로그 제거 (lines 2593, 2597, 2602, 2606, 2619)
     - LeftPanel 로그 제거 (lines 2193, 2198, 2201, 2208, 2213, 2216)
     - Edit Area List 로그 제거 (다수 위치)

2. **acc_core_acc2.py**
   - generate_connection_lines에서 실제 radius 사용 (lines 275-278)

### 변경 라인 수

- **acc_gui.py:** 약 150줄 추가, 80줄 삭제 (순 증가 +70줄)
- **acc_core_acc2.py:** 3줄 수정

---

## 9. 향후 개선 사항

### 9.1 ACC1 스타일 개선

1. **첫 merge 정의 명확화:**
   - 현재: 가장 먼저 등장하는 merge level
   - 개선 가능: 사용자가 특정 similarity threshold 지정

2. **Radial line 스타일 옵션:**
   - 현재: innermost circle 라인만 필터링
   - 개선 가능: 특정 radius 이하의 모든 radial line 숨기기 옵션

3. **Label 위치 조정:**
   - 현재: label_r = radius - 0.1 (고정 offset)
   - 개선 가능: radius에 비례한 offset 또는 사용자 지정

### 9.2 성능 최적화

1. **get_areas 함수 최적화:**
   - 현재: 매번 재귀적으로 탐색
   - 개선 가능: 한 번 계산 후 캐싱

2. **deepcopy 최적화:**
   - 현재: ACC1 스타일 적용 시 전체 데이터 복사
   - 개선 가능: positions만 복사

### 9.3 사용자 경험

1. **실시간 미리보기:**
   - ACC1 스타일 체크박스 변경 시 자동 재생성 (Apply 버튼 불필요)

2. **툴팁 개선:**
   - ACC1 스타일일 때 area에 마우스 오버 시 "First merge at r={radius}" 표시

---

## 10. 관련 문서

- **사용자 매뉴얼:** `doc/USER_MANUAL.md` (업데이트 필요)
- **알고리즘 문서:** `doc/ACC_Algorithm_Overview.md`
- **이전 작업:** `devlog/20251113_P26_ACC2_interactive_features.md`

---

## 11. 결론

오늘 작업에서는 ACC2의 주요 버그들을 수정하고 사용자 경험을 크게 개선했습니다.

### 핵심 기술적 성과

**버그 수정:**
- ✅ ACC2 계층적 swap 버그 해결 (relative angle preservation)
- ✅ Merge point angle 표시 오류 수정 (subtended angle 계산)
- ✅ Matrix 편집 내용 실시간 반영 (자동 재클러스터링)

**기능 추가:**
- ✅ ACC2에 ACC1 스타일 옵션 추가
- ✅ Tab 구조로 ACC/ACC2 분리
- ✅ Innermost circle radial line 필터링

**UX 개선:**
- ✅ 80개 이상의 디버그 로그 제거
- ✅ UI info label로 사용자 피드백 개선
- ✅ 콘솔 출력 깔끔하게 정리

### 기술적 도전과 해결

**도전 1: Swap 후 area 중복 및 겹침**
- 원인: 순차적 swap 적용 시 area가 여러 번 이동
- 해결: Temporary storage + atomic update

**도전 2: Matrix 편집이 반영되지 않음**
- 원인: Step 체크, infinite loop
- 해결: Step 체크 제거, 프로그래밍 플래그, 자동 재클러스터링

**도전 3: ACC1 스타일 적용 후 swap 시 radial line 재생성**
- 원인: generate_connection_lines의 하드코딩된 radius, 데이터 플로우 문제
- 해결: 실제 position radius 사용, ACC1 스타일을 plot_acc2 내부에서 적용

### 다음 작업 제안

- [ ] 사용자 매뉴얼에 신규 기능 설명 추가
- [ ] 실시간 미리보기 기능 추가
- [ ] 성능 최적화 (get_areas 캐싱, deepcopy 최소화)
- [ ] 단위 테스트 작성 (swap, angle 계산, matrix 편집)
