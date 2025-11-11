# 20251111 P08: 레이아웃 개선 및 Similarity 표시

## 개요

사용자 요청에 따라 두 가지 개선 작업 진행:
1. 왼쪽 매트릭스 패널의 레이아웃 개선 및 표시 공간 확대
2. Dendrogram X축을 Distance에서 Similarity로 변경

## 1. 매트릭스 패널 레이아웃 개선

### 문제 (Before)

```
┌─────────────────────────────┐
│ Similarity Matrices          │
├─────────────────────────────┤
│ 1. Subordinate Matrix        │  ← 섹션 레이블
│                              │
│ Subordinate      [Load CSV]  │  ← 중복된 제목 + 버튼
│ Step: 0  [슬라이더] [Prev][Next]│
│ ┌─────────────┐             │
│ │   Matrix    │  (높이 300px)│  ← 작은 표시 공간
│ └─────────────┘             │
│ No data loaded               │  ← 긴 info label
│                              │
│ <hr>                         │
│                              │
│ 2. Inclusive Matrix          │
│ ...                          │
└─────────────────────────────┘
```

**문제점:**
- ❌ "Subordinate" 제목이 중복 (섹션 레이블과 위젯 제목)
- ❌ 매트릭스 표시 공간이 작음 (300px 최대 높이)
- ❌ 불필요한 여백과 정보
- ❌ Step 정보가 두 줄로 표시되어 공간 낭비

### 해결 (After)

```
┌─────────────────────────────┐
│ Similarity Matrices          │
├─────────────────────────────┤
│ 1. Subordinate Matrix [Load]│  ← 한 줄에 레이블 + 버튼
│ Step: 0 | Load matrix [→][→]│  ← 한 줄에 step 정보 + 컨트롤
│ ┌──────────────────────┐    │
│ │                       │    │
│ │      Matrix           │    │  ← 확대된 표시 공간
│ │   (높이 제한 없음)   │    │
│ │                       │    │
│ └──────────────────────┘    │
│ ✓ Loaded 6x6              │  ← 축약된 info
│ ──────                      │  ← 짧은 구분선
│ 2. Inclusive Matrix [Load]  │
│ ...                          │
└─────────────────────────────┘
```

**개선점:**
- ✅ 중복 제목 제거
- ✅ 섹션 레이블과 버튼이 같은 줄에 배치
- ✅ 매트릭스 표시 공간 확대 (최대 높이 제한 제거, stretch=1 적용)
- ✅ Step 정보를 한 줄로 축약
- ✅ 내비게이션 버튼 크기 축소 (◀/▶ 아이콘만)
- ✅ 전체적인 여백 최소화

### 구현

#### 1. StepMatrixWidget에 show_header 파라미터 추가

```python
class StepMatrixWidget(QWidget):
    def __init__(self, title="Matrix", parent=None, show_header=True):
        super().__init__(parent)
        self.title = title
        self.show_header = show_header  # 헤더 표시 여부
        # ...
```

#### 2. init_ui 수정

```python
def init_ui(self):
    layout = QVBoxLayout()
    layout.setContentsMargins(0, 0, 0, 0)  # 여백 제거
    layout.setSpacing(5)  # 간격 축소

    # 헤더는 선택적으로 표시
    if self.show_header:
        # ... 기존 헤더 코드 ...
    else:
        # load_btn만 생성 (외부에서 접근 가능하도록)
        self.load_btn = QPushButton("Load CSV")
        self.load_btn.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                padding: 5px 10px;
                border-radius: 3px;
                font-size: 10px;
            }
        """)
```

#### 3. Step Controls 축약

**Before:**
```python
# Step label (한 줄)
self.step_label = QLabel("Step: 0")
layout.addWidget(self.step_label)

# Step description (또 한 줄)
self.step_desc_label = QLabel("Load matrix to begin")
layout.addWidget(self.step_desc_label)

# Slider + 버튼
self.prev_btn = QPushButton("◀ Prev")  # 넓은 버튼
self.next_btn = QPushButton("Next ▶")
```

**After:**
```python
# Step label과 description을 한 줄로
step_info_layout = QHBoxLayout()
self.step_label = QLabel("Step: 0")
self.step_label.setStyleSheet("font-size: 10px; font-weight: bold;")
step_info_layout.addWidget(self.step_label)

self.step_desc_label = QLabel("Load matrix to begin")
self.step_desc_label.setStyleSheet("font-size: 9px; color: #666;")
step_info_layout.addWidget(self.step_desc_label)
step_info_layout.addStretch()

# Slider + 작은 버튼
self.prev_btn = QPushButton("◀")  # 아이콘만
self.prev_btn.setMaximumWidth(40)  # 좁은 버튼
self.next_btn = QPushButton("▶")
self.next_btn.setMaximumWidth(40)
```

#### 4. Table 크기 확대

**Before:**
```python
self.table = QTableWidget()
self.table.setMaximumHeight(300)  # 최대 300px
layout.addWidget(self.table)
```

**After:**
```python
self.table = QTableWidget()
self.table.setMinimumHeight(200)  # 최소 200px
layout.addWidget(self.table, stretch=1)  # stretch로 남은 공간 모두 사용
```

#### 5. Info Label 축약

**Before:**
```python
self.info_label = QLabel("No data loaded")
self.info_label.setStyleSheet("font-size: 10px; color: gray;")
layout.addWidget(self.info_label)
```

**After:**
```python
self.info_label = QLabel("No data loaded")
self.info_label.setStyleSheet("font-size: 9px; color: gray;")
self.info_label.setMaximumHeight(15)  # 높이 제한
layout.addWidget(self.info_label)
```

#### 6. LeftPanel 레이아웃 수정

**Before:**
```python
def setup_content(self):
    # 섹션 레이블
    sub_label = QLabel("<b>1. Subordinate Matrix</b>")
    self.content_layout.addWidget(sub_label)

    # 위젯 (자체 헤더 포함)
    self.sub_matrix_widget = StepMatrixWidget("Subordinate")
    self.content_layout.addWidget(self.sub_matrix_widget)
```

**After:**
```python
def setup_content(self):
    # 섹션 헤더: 레이블 + 버튼
    sub_header_layout = QHBoxLayout()
    sub_label = QLabel("<b>1. Subordinate Matrix</b>")
    sub_header_layout.addWidget(sub_label)
    sub_header_layout.addStretch()

    # 위젯 (헤더 숨김)
    self.sub_matrix_widget = StepMatrixWidget("Subordinate", show_header=False)
    sub_header_layout.addWidget(self.sub_matrix_widget.load_btn)  # 버튼을 헤더에 배치
    self.content_layout.addLayout(sub_header_layout)

    # 위젯 추가
    self.content_layout.addWidget(self.sub_matrix_widget)
```

### 효과

#### 공간 절약
- **헤더**: ~40px 절약
- **Step controls**: ~25px 절약
- **Info label**: ~10px 절약
- **여백**: ~15px 절약
- **총 절약**: ~90px

#### 표시 공간 증가
- Before: 최대 300px
- After: 최소 200px + stretch (실제로 400-500px 이상 가능)
- **증가율**: 50% 이상

#### 시각적 개선
- 더 깔끔한 레이아웃
- 정보 밀도 증가
- 중복 제거로 인지 부하 감소

## 2. Dendrogram X축을 Similarity로 표시

### 문제 (Before)

```
Dendrogram X축: Distance
┌────────────────────┐
│      Distance      │
│ 0.0  0.1  0.2  0.3 │
│                    │
│ J ├──┐             │
│ T │  ├──┐          │
│ Y ├──┘  │          │
│      ...│          │
└────────────────────┘
```

**문제점:**
- ❌ 사용자가 입력한 데이터는 Similarity Matrix
- ❌ 내부적으로 Distance로 변환 (max_sim - similarity)
- ❌ Dendrogram은 Distance로 표시
- ❌ Matrix는 Similarity로 표시
- ❌ **일관성 부족**: 같은 값이 다른 단위로 표시됨

### 해결 (After)

```
Dendrogram X축: Similarity
┌────────────────────┐
│     Similarity     │
│ 0.7  0.8  0.9  1.0 │
│                    │
│ J ├──┐             │
│ T │  ├──────┐      │
│ Y ├──┘      │      │
│      ...    │      │
└────────────────────┘
```

**개선점:**
- ✅ Similarity Matrix와 일관성 유지
- ✅ 직관적: 높은 값 = 더 유사함
- ✅ 사용자가 입력한 값과 동일한 스케일
- ✅ Distance 변환이 내부 구현 세부사항임을 숨김

### 구현

#### StepDendrogramWidget.update_dendrogram() 수정

**Before:**
```python
def update_dendrogram(self):
    if not self.step_manager:
        return

    self.figure.clear()
    ax = self.figure.add_subplot(111)

    if self.current_step == 0:
        # ...
    else:
        full_linkage = self.step_manager.linkage_matrix  # Distance 그대로

        # ... dendrogram 그리기 ...

        # Current step 높이 (distance)
        current_height = full_linkage[self.current_step - 1, 2]
        ax.axvline(x=current_height, ...)

        ax.set_xlabel('Distance', fontsize=9)  # Distance 레이블
```

**After:**
```python
def update_dendrogram(self):
    if not self.step_manager:
        return

    self.figure.clear()
    ax = self.figure.add_subplot(111)

    if self.current_step == 0:
        # ...
    else:
        # Linkage matrix를 복사하고 distance를 similarity로 변환
        full_linkage = self.step_manager.linkage_matrix.copy()
        max_sim = self.step_manager.max_sim

        # Distance → Similarity 변환
        full_linkage[:, 2] = max_sim - full_linkage[:, 2]

        # ... dendrogram 그리기 (변환된 linkage 사용) ...

        # Current step 높이 (similarity)
        current_height = full_linkage[self.current_step - 1, 2]
        ax.axvline(x=current_height, ...)

        ax.set_xlabel('Similarity', fontsize=9)  # Similarity 레이블
```

### 변환 로직

#### Linkage Matrix 구조

```
linkage_matrix = [
    [cluster_i, cluster_j, distance, count],  # Step 1
    [...],                                     # Step 2
    ...
]
```

- Column 0, 1: 병합되는 클러스터 ID
- **Column 2**: Distance (변환 대상)
- Column 3: 병합된 클러스터의 멤버 수

#### 변환 수식

```python
# Original (ClusteringStepManager.__init__)
distance_matrix = max_sim - similarity_matrix
linkage_matrix = linkage(distance_matrix, method='average')

# Display (StepDendrogramWidget.update_dendrogram)
display_linkage = linkage_matrix.copy()
display_linkage[:, 2] = max_sim - linkage_matrix[:, 2]  # Distance → Similarity
```

#### 예시

```
입력 Similarity Matrix:
       J    T    Y
J    1.0  0.9  0.8
T    0.9  1.0  0.8
Y    0.8  0.8  1.0

max_sim = 1.0

Distance Matrix (내부):
       J    T    Y
J    0.0  0.1  0.2
T    0.1  0.0  0.2
Y    0.2  0.2  0.0

Linkage Matrix (내부):
Step 1: [J, T, distance=0.1]

Dendrogram 표시:
- Before: X = 0.1 (distance)
- After:  X = 1.0 - 0.1 = 0.9 (similarity) ✓
```

### 빨간 점선 (Current Step)도 변환

**Before:**
```python
current_height = full_linkage[self.current_step - 1, 2]  # Distance
ax.axvline(x=current_height, color='red', ...)
```

**After:**
```python
current_height = full_linkage[self.current_step - 1, 2]  # Similarity (이미 변환됨)
ax.axvline(x=current_height, color='red', ...)
```

### 일관성 확보

#### Matrix (왼쪽 패널)
```
       J    T    Y
J      -   0.9  0.8   ← Similarity
T          -    0.8
Y               -
```

#### Dendrogram (중앙 패널)
```
Similarity (X축)
0.7  0.8  0.9  1.0
     |    |    |
     J────T    Y      ← 같은 Similarity 값 사용
     0.9 merge
```

#### ACC Visualization (오른쪽 패널)
```
Concentric circles with similarity-based distances
```

모든 패널이 **Similarity** 단위로 통일됨!

## 사용자 경험 개선

### Before (일관성 부족)

```
왼쪽: "J와 T의 similarity는 0.9입니다"
중앙: "J와 T가 distance 0.1에서 병합됩니다"  ← ???
사용자: "어? 0.9인데 왜 0.1이지? 🤔"
```

### After (일관성 유지)

```
왼쪽: "J와 T의 similarity는 0.9입니다"
중앙: "J와 T가 similarity 0.9에서 병합됩니다"  ← ✓
사용자: "아! 같은 값이네! 👍"
```

## 테스트

### 레이아웃 테스트

```bash
$ python acc_gui.py
```

**확인 항목:**
1. ✅ "1. Subordinate Matrix [Load CSV]" 한 줄로 표시
2. ✅ "Subordinate" 중복 제목 제거됨
3. ✅ Step 정보가 한 줄로 축약됨
4. ✅ 내비게이션 버튼이 작아짐 (◀, ▶)
5. ✅ 매트릭스 표시 공간이 확대됨
6. ✅ 전체적으로 더 깔끔함

### Similarity 표시 테스트

```bash
$ python acc_gui.py
# Load sample_subordinate.csv
# Navigate through steps
```

**확인 항목:**
1. ✅ Dendrogram X축 레이블이 "Similarity"
2. ✅ X축 값이 0.7~1.0 범위 (similarity)
3. ✅ 빨간 점선이 올바른 위치 (similarity 값)
4. ✅ Matrix의 값과 dendrogram의 높이가 일치

### 예시

```
Step 1: J + T 병합

Matrix:
       J+T  Y    N    ...
J+T     -   0.8  0.39 ...   ← J+T - Y similarity = 0.8

Dendrogram:
Similarity
0.7  0.8  0.9  1.0
     │    │    │
     Y    J────T             ← J-T merge at 0.9
          │                  ← Red line at 0.9
```

## 코드 변경 요약

### acc_gui.py

#### StepMatrixWidget 클래스
- `__init__`: show_header 파라미터 추가
- `init_ui`:
  - 헤더를 선택적으로 표시
  - Step controls 한 줄로 축약
  - Table에 stretch=1 적용
  - 여백과 간격 최소화
  - 버튼 크기 축소

#### LeftPanel 클래스
- `setup_content`:
  - 섹션 헤더 레이아웃 생성
  - Load CSV 버튼을 헤더에 배치
  - StepMatrixWidget을 show_header=False로 생성

#### StepDendrogramWidget 클래스
- `update_dendrogram`:
  - Linkage matrix를 복사
  - Distance를 Similarity로 변환 (max_sim - distance)
  - X축 레이블을 "Similarity"로 변경

## 장점

### 레이아웃 개선
1. **공간 효율성**: 90px 이상 절약 → 매트릭스 표시 공간으로 할당
2. **시각적 깔끔함**: 중복 제거, 간격 최소화
3. **정보 밀도**: 같은 공간에 더 많은 데이터 표시
4. **사용성**: 버튼과 컨트롤이 더 컴팩트하게 배치

### Similarity 표시
1. **일관성**: 모든 패널이 Similarity 단위 사용
2. **직관성**: 높은 값 = 더 유사함
3. **이해도**: 사용자 입력과 동일한 스케일
4. **교육적**: Distance 변환이 내부 구현임을 명확히 함

## 결론

두 가지 개선으로:
1. **레이아웃**: 매트릭스 표시 공간 확대, 중복 제거, 깔끔한 UI
2. **Similarity 표시**: 모든 패널 간 일관성 유지

결과:
- ✅ 더 많은 데이터 표시 가능
- ✅ 더 깔끔한 UI
- ✅ 더 직관적인 시각화
- ✅ 더 나은 사용자 경험

**사용자가 클러스터링 과정을 더 쉽게 이해하고 분석할 수 있습니다!**
