# 20251111 P12: 노드에 Similarity 값 표시 옵션 추가

## 개요

Dendrogram의 각 병합 노드에 similarity 값을 표시하는 옵션을 체크박스로 추가.

## 요구사항

1. **체크박스**: "Show similarity values" 체크박스 추가
2. **값 표시**: 체크 시 각 병합 노드 옆에 similarity 값 표시
3. **위치**: 각 병합 지점 바로 옆
4. **동적 업데이트**: 체크박스 클릭 시 즉시 반영

## 구현

### 1. 체크박스 추가

**StepDendrogramWidget.init_ui()**

```python
def init_ui(self):
    layout = QVBoxLayout()

    # Title and checkbox
    header_layout = QHBoxLayout()
    title_label = QLabel(f"<b>{self.title}</b>")
    header_layout.addWidget(title_label)
    header_layout.addStretch()

    # Checkbox for showing similarity values
    self.show_values_checkbox = QCheckBox("Show similarity values")
    self.show_values_checkbox.setStyleSheet("font-size: 10px;")
    self.show_values_checkbox.stateChanged.connect(self.on_checkbox_changed)
    header_layout.addWidget(self.show_values_checkbox)

    layout.addLayout(header_layout)
    # ...
```

### 2. 체크박스 이벤트 핸들러

```python
def on_checkbox_changed(self):
    """Called when checkbox state changes"""
    self.update_dendrogram()  # Re-draw dendrogram with/without values
```

### 3. 노드에 값 표시

**StepDendrogramWidget.update_dendrogram()**

```python
# Plot dendrogram
ddata = dendrogram(full_linkage, ...)

# Add similarity values to each merge point if checkbox is checked
if self.show_values_checkbox.isChecked():
    # Dendrogram data contains coordinates
    # dcoord[i] = [x1, x2, x2, x3] where x2 is the merge height (distance)
    # icoord[i] = [y1, y2, y2, y3] where y2 is the merge Y position
    for i, (xs, ys) in enumerate(zip(ddata['dcoord'], ddata['icoord'])):
        # Get merge distance (x2 or x3, they're the same)
        merge_distance = xs[1]

        # Get merge Y position (middle of horizontal line)
        merge_y = (ys[1] + ys[2]) / 2.0

        # Convert distance to similarity
        merge_similarity = max_sim - merge_distance

        # Add text annotation with box
        ax.text(merge_distance, merge_y, f' {merge_similarity:.2f}',
               fontsize=8, color='darkblue',
               verticalalignment='center',
               bbox=dict(boxstyle='round,pad=0.3',
                        facecolor='white',
                        edgecolor='lightblue',
                        alpha=0.8))
```

### 4. Import 추가

```python
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTableWidget, QTableWidgetItem, QPushButton, QFileDialog,
    QLabel, QSlider, QMessageBox, QScrollArea, QCheckBox  # ← 추가
)
```

## Dendrogram 좌표 이해

### ddata 구조

scipy의 `dendrogram()` 함수는 `ddata` 딕셔너리를 반환:

```python
ddata = {
    'icoord': [[y1, y2, y2, y3], ...],  # Y 좌표들
    'dcoord': [[x1, x2, x2, x3], ...],  # X 좌표들 (distance)
    'ivl': ['J', 'T', 'Y', ...],        # Leaf labels
    'leaves': [0, 1, 2, ...],           # Leaf indices
    'color_list': ['b', 'b', ...],      # Link colors
}
```

### 각 병합의 좌표

각 병합은 하나의 "U자형" 선분으로 표시됨:

```
icoord[i] = [y1, y2, y2, y3]
dcoord[i] = [x1, x2, x2, x3]

그래프:
      (x2,y2)────(x2,y3)
         │
      (x1,y1)

- (x1, y1): 왼쪽 자식의 위치
- (x2, y2): 병합 지점 (수평선 시작)
- (x2, y3): 병합 지점 (수평선 끝)
- (x2, y2/y3): 실제 병합 높이 (distance)
```

### 병합 지점 계산

```python
merge_distance = xs[1]  # or xs[2], 동일 (x2)
merge_y = (ys[1] + ys[2]) / 2.0  # 수평선 중간
merge_similarity = max_sim - merge_distance
```

## 시각적 효과

### 체크박스 OFF (기본)

```
Similarity
1.0  0.9  0.8  0.7  ...
     │
     J───T
     │
     O───Q
```

깔끔한 dendrogram, 값 없음.

### 체크박스 ON

```
Similarity
1.0  0.9  0.8  0.7  ...
     │
     J───T [0.90]  ← 각 노드에 값 표시
     │
     O───Q [0.85]
```

각 병합 노드 옆에 similarity 값이 흰색 박스에 표시됨.

## 텍스트 스타일

```python
ax.text(x, y, f' {similarity:.2f}',
       fontsize=8,                    # 작은 글씨
       color='darkblue',              # 진한 파란색
       verticalalignment='center',    # 세로 중앙 정렬
       bbox=dict(
           boxstyle='round,pad=0.3',  # 둥근 박스, 약간의 패딩
           facecolor='white',         # 흰색 배경
           edgecolor='lightblue',     # 연한 파란색 테두리
           alpha=0.8                  # 약간 투명
       ))
```

### 효과:
- **가독성**: 흰색 배경으로 선과 겹쳐도 잘 보임
- **미적**: 둥근 박스로 부드러운 느낌
- **투명도**: alpha=0.8로 dendrogram 구조 가림 최소화

## 사용 시나리오

### 시나리오 1: 개별 값 확인

```
사용자: "J와 T가 정확히 몇에서 병합되었지?"
       ↓ 체크박스 클릭
화면: J-T 노드 옆에 "0.90" 표시
사용자: "0.90이구나! ✓"
```

### 시나리오 2: 여러 병합 비교

```
사용자: "J-T와 O-Q 중 어느 쪽이 더 유사한가?"
       ↓ 체크박스 클릭
화면:
  J-T: 0.90
  O-Q: 0.85
사용자: "J-T가 더 유사하네! ✓"
```

### 시나리오 3: 교육/발표

```
발표자: "여기 보시면 각 병합의 similarity 값이..."
       ↓ 체크박스 클릭
화면: 모든 노드에 값 표시
청중: "아, 숫자로 보니 명확하네요! ✓"
```

## 장점

### 1. 선택적 표시
- 기본: 깔끔한 dendrogram
- 필요 시: 체크박스로 값 표시
- 사용자가 제어 가능

### 2. 정확한 값
- X축 눈금보다 정확
- 각 노드의 정확한 similarity
- 수치 확인 용이

### 3. 비교 용이
- 여러 병합을 한눈에 비교
- Matrix 값과 대조 가능
- 교육/분석에 유용

### 4. 시각적으로 깔끔
- 흰색 박스로 가독성 확보
- 투명도로 dendrogram 구조 유지
- 둥근 모서리로 부드러운 디자인

## Matrix와의 연계

### Matrix (왼쪽)
```
       J    T    Y
J      -   0.9  0.8
T          -    0.8
```

### Dendrogram (중앙, 체크박스 ON)
```
J───T [0.90]  ← Matrix의 0.9와 일치!
```

### 사용자 경험
```
사용자: "Matrix에서 J-T가 0.9"
      → "Dendrogram에서도 0.90으로 확인!" ✓
      → "일관성 완벽!" 👍
```

## 기술적 고려사항

### 1. 성능
- 체크박스 클릭 시 전체 dendrogram 재그리기
- 6개 항목 기준 5개 병합 → 5개 텍스트 추가
- 빠르고 부드러움 ✓

### 2. 좌표 정확도
- dendrogram() 반환 좌표 사용
- scipy가 계산한 위치 그대로
- 정확한 위치 보장 ✓

### 3. X축 반전 고려
- `ax.invert_xaxis()` 후에도 텍스트 위치 정확
- 좌표는 반전 전 값 (distance) 사용
- matplotlib이 자동으로 처리 ✓

### 4. 여백/겹침
- 박스 패딩으로 여백 확보
- 투명도로 겹침 최소화
- 폰트 크기 8pt로 적절 ✓

## 테스트

```bash
$ python acc_gui.py
# Load sample_subordinate.csv
# Navigate through steps
# Toggle "Show similarity values" checkbox
```

**확인 항목:**
1. ✅ 체크박스가 dendrogram 제목 옆에 표시
2. ✅ 체크 OFF: 값 표시 없음 (깔끔)
3. ✅ 체크 ON: 각 노드에 값 표시
4. ✅ 값이 정확함 (Matrix 값과 일치)
5. ✅ 위치가 적절함 (노드 바로 옆)
6. ✅ 가독성 좋음 (흰색 박스)
7. ✅ 체크박스 토글 시 즉시 반영

## 결론

체크박스로 similarity 값 표시 옵션 추가:
- ✅ 선택적 표시 (사용자 제어)
- ✅ 정확한 값 표시
- ✅ 깔끔한 디자인
- ✅ Matrix와 일관성
- ✅ 교육/분석에 유용

**사용자가 필요할 때만 값을 확인할 수 있어 편리합니다!**
