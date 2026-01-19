# 20251112 P19: Matrix 편집 제한 및 Area List 관리 기능

## 개요

Similarity matrix의 편집 기능 개선 및 area (row/column entry) 관리 기능 추가.

## 요구사항

### 1. Matrix 편집 제한
- **Lower triangle cells**: 편집 불가능하게 설정
  - 대칭 행렬이므로 upper triangle만 편집 가능
  - Lower triangle은 upper triangle의 mirror
- **Diagonal cells**: 편집 불가능하게 설정
  - 항상 1.0이어야 하므로 편집 불필요

### 2. Area List 편집 기능
- **다이얼로그 생성**: Area 추가/수정/삭제를 위한 별도 다이얼로그
- **버튼 추가**: "Edit Area List" 버튼을 Load CSV 옆에 배치
- **공유 Area List**: Local와 Global가 동일한 area list 사용
  - 버튼은 하나만 필요
  - 변경 시 두 matrix 모두 업데이트

## 설계

### 1. 셀 편집 제한 구현

**위치**: `StepMatrixWidget.populate_table()` 메서드

**방법**:
```python
# QTableWidgetItem에 flags 설정
if i < j:
    # Upper triangle: editable
    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEditable)
elif i == j:
    # Diagonal: read-only
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
else:
    # Lower triangle: read-only
    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEditable)
```

**편집 이벤트 처리**:
- Upper triangle 셀 편집 시 → Lower triangle의 대응 셀도 자동 업데이트
- 입력 값 검증 (0.0 ~ 1.0 범위)
- `itemChanged` 시그널 연결

### 2. Area List Editor 다이얼로그

**클래스**: `AreaListEditorDialog(QDialog)`

**UI 구성**:
```
┌─────────────────────────────────────┐
│  Edit Area List                     │
├─────────────────────────────────────┤
│  Current Areas:                     │
│  ┌───────────────┐  ┌────────────┐ │
│  │ J             │  │  Add       │ │
│  │ T             │  │  Edit      │ │
│  │ Y             │  │  Delete    │ │
│  │ N             │  └────────────┘ │
│  │ O             │                  │
│  │ Q             │                  │
│  └───────────────┘                  │
├─────────────────────────────────────┤
│           [OK]  [Cancel]            │
└─────────────────────────────────────┘
```

**기능**:
1. **Add**: 새로운 area 추가
   - 입력 다이얼로그로 이름 받기
   - 중복 검사
   - Matrix에 새로운 row/column 추가 (기본값 0.5)
2. **Edit**: 기존 area 이름 변경
   - 선택된 area 이름 수정
   - Matrix의 label 업데이트
3. **Delete**: area 삭제
   - 확인 다이얼로그
   - Matrix에서 해당 row/column 제거

**데이터 구조**:
```python
{
    "labels": ["J", "T", "Y", "N", "O", "Q"],
    "matrix": pandas.DataFrame
}
```

### 3. 버튼 배치

**위치**: `LeftPanel.setup_content()`

**레이아웃 변경**:
```python
# Before:
# [Label]                    [Load CSV]

# After:
# [Label]         [Edit Area List] [Load CSV]
```

**버튼 스타일**:
- Edit Area List: 보라색 (#9C27B0)
- Load CSV: 파란색 (#2196F3) - 기존 유지

### 4. 데이터 동기화

**MainWindow에 메서드 추가**:
```python
def update_area_list(self, new_labels, new_local_matrix, new_global_matrix):
    """Update both matrices with new area list"""
    # Update local matrix
    self.left_panel.local_matrix_widget.update_matrix(new_labels, new_local_matrix)

    # Update global matrix
    self.left_panel.global_matrix_widget.update_matrix(new_labels, new_global_matrix)

    # Refresh dendrograms
    self.update_dendrograms()
```

**StepMatrixWidget에 메서드 추가**:
```python
def update_matrix(self, labels, matrix_df):
    """Update matrix with new labels and data"""
    self.matrix_data = matrix_df
    # Recreate step manager
    self.step_manager = ClusteringStepManager(
        matrix_df.values,
        labels
    )
    # Reset to step 0
    self.current_step = 0
    self.step_slider.setValue(0)
    self.update_step_display()
```

## 구현 계획

### Phase 1: 셀 편집 제한
1. `populate_table()` 수정
   - Lower triangle과 diagonal 셀에 read-only flag 설정
2. `itemChanged` 시그널 연결
   - Upper triangle 편집 시 lower triangle 자동 업데이트
3. 값 검증 로직 추가
   - 0.0 ~ 1.0 범위 체크
   - 잘못된 입력 시 이전 값으로 복원

### Phase 2: Area List Editor 다이얼로그
1. `AreaListEditorDialog` 클래스 생성
2. UI 레이아웃 구성
   - QListWidget for areas
   - Add/Edit/Delete 버튼
3. Add 기능 구현
   - QInputDialog로 이름 입력
   - DataFrame에 row/column 추가
4. Edit 기능 구현
   - 선택된 area 이름 변경
   - DataFrame labels 업데이트
5. Delete 기능 구현
   - 선택된 area 삭제
   - DataFrame에서 row/column 제거

### Phase 3: GUI 통합
1. Edit Area List 버튼 추가
   - `LeftPanel.setup_content()` 수정
   - 버튼 클릭 시 다이얼로그 표시
2. `MainWindow.update_area_list()` 구현
   - 두 matrix 모두 업데이트
   - Dendrogram 새로고침
3. `StepMatrixWidget.update_matrix()` 구현
   - Matrix data 업데이트
   - Step manager 재생성

### Phase 4: 테스트
1. 셀 편집 제한 테스트
   - Upper triangle 편집 가능 확인
   - Lower triangle/diagonal 편집 불가 확인
   - Mirror 업데이트 동작 확인
2. Area List 편집 테스트
   - Add: 새로운 area 추가
   - Edit: 이름 변경
   - Delete: area 삭제
3. 통합 테스트
   - Area list 변경 후 clustering 동작 확인
   - Dendrogram 업데이트 확인
   - ACC 생성 정상 동작 확인

## 파일 변경 사항

### acc_gui.py
1. **StepMatrixWidget 클래스**:
   - `populate_table()`: 셀 편집 제한 추가
   - `init_ui()`: itemChanged 시그널 연결
   - `on_item_changed()`: 새 메서드, upper/lower triangle sync
   - `update_matrix()`: 새 메서드, matrix 업데이트
   - `get_labels()`: 새 메서드, 현재 labels 반환

2. **AreaListEditorDialog 클래스**: 새로 추가
   - `__init__()`: 초기화, UI 구성
   - `add_area()`: Area 추가
   - `edit_area()`: Area 이름 변경
   - `delete_area()`: Area 삭제
   - `get_result()`: 수정된 데이터 반환

3. **LeftPanel 클래스**:
   - `setup_content()`: Edit Area List 버튼 추가
   - `edit_area_list()`: 새 메서드, 다이얼로그 표시

4. **MainWindow 클래스**:
   - `update_area_list()`: 새 메서드, 두 matrix 동기화

## 예상 결과

### 사용자 워크플로우

1. **Matrix 로드 후 직접 편집**:
   ```
   User: CSV 로드
   User: Upper triangle 셀 클릭하여 값 수정
   System: Lower triangle의 대응 셀도 자동 업데이트
   User: Diagonal 셀 클릭 시도
   System: 편집 불가 (회색 배경 유지)
   ```

2. **Area List 관리**:
   ```
   User: "Edit Area List" 버튼 클릭
   Dialog: 현재 area list 표시 (J, T, Y, N, O, Q)
   User: "Add" 클릭 → "K" 입력
   Dialog: 리스트에 "K" 추가
   User: "OK" 클릭
   System: 두 matrix 모두 7x7로 확장, 기본값으로 채움
   System: Dendrogram 자동 재생성
   ```

3. **Area 삭제**:
   ```
   User: "Edit Area List" 버튼 클릭
   User: "Q" 선택 후 "Delete" 클릭
   Dialog: 확인 요청 "정말 'Q'를 삭제하시겠습니까?"
   User: "Yes" 클릭
   System: 두 matrix에서 Q row/column 제거
   System: 5x5 matrix로 축소
   ```

## 주의사항

1. **Data Integrity**:
   - Area list 변경 시 기존 similarity 값 보존
   - 새로운 area 추가 시 기본값 설정 (0.5 또는 사용자 지정)
   - 삭제 시 되돌릴 수 없음을 경고

2. **Validation**:
   - Area 이름 중복 불허
   - Area 이름 공백 불허
   - Similarity 값 범위 체크 (0.0 ~ 1.0)
   - 대각선은 항상 1.0 유지

3. **UI/UX**:
   - 편집 불가능한 셀은 시각적으로 구분 (배경색, 툴팁)
   - Area list 변경 후 자동으로 dendrogram 재생성
   - 변경사항이 있을 때만 OK 버튼 활성화

4. **Performance**:
   - Matrix 크기가 클 때 업데이트 성능 고려
   - Step manager 재생성 시간 최소화

## 구현 완료

### Phase 1: 셀 편집 제한 ✅
- `StepMatrixWidget.__init__()`: `updating_mirror` 플래그 추가
- `StepMatrixWidget.init_ui()`: `itemChanged` 시그널 연결
- `StepMatrixWidget.populate_table()`: 셀 편집 플래그 설정
  - Upper triangle: 편집 가능 (ItemIsEditable)
  - Diagonal: 빈 칸, 회색 배경, 툴팁 "always 1.0 (not shown)"
  - Lower triangle: 빈 칸, 회색 배경, 툴팁 "mirrored from upper triangle (not shown)"
- `StepMatrixWidget.on_item_changed()`: 새 메서드
  - 값 검증 (0.0 ~ 1.0 범위)
  - Lower triangle 자동 업데이트
  - Step manager 재생성
  - Dendrogram 업데이트 트리거

### Phase 2: Area List Editor 다이얼로그 ✅
- `AreaListEditorDialog` 클래스 생성
- UI 구성:
  - QListWidget로 area 목록 표시
  - Add/Edit/Delete 버튼
  - OK/Cancel 버튼
- 기능 구현:
  - `add_area()`: 새 area 추가, 기본값 0.5
  - `edit_area()`: area 이름 변경
  - `delete_area()`: area 삭제 (확인 다이얼로그)
  - `get_result()`: 수정된 데이터 반환

### Phase 3: GUI 통합 ✅
- `StepMatrixWidget.update_matrix()`: 새 메서드
  - Matrix data 업데이트
  - Step manager 재생성
  - 슬라이더 리셋
- `StepMatrixWidget.get_labels()`: 새 메서드
  - 현재 labels 반환
- `LeftPanel.setup_content()`: Edit Area List 버튼 추가
  - 보라색 스타일 (#9C27B0)
  - Load CSV 버튼 옆에 배치
  - 두 matrix 모두 로드될 때까지 비활성화
- `LeftPanel.edit_area_list()`: 새 메서드
  - 다이얼로그 표시
  - 결과 처리
  - 두 matrix 모두 업데이트
- `LeftPanel.on_matrix_loaded()`: 수정
  - 두 matrix 로드 시 Edit Area List 버튼 활성화

### Phase 4: 테스트 ✅
- `test_area_editor.py` 생성
- 테스트 항목:
  - ✅ Area 추가 테스트
  - ✅ Area 이름 변경 테스트
  - ✅ Area 삭제 테스트
  - ✅ 대칭성 보존 테스트

모든 테스트 통과!

## 테스트 결과

```
Running Area List Editor Tests
==================================================
✓ Addition test passed!
✓ Renaming test passed!
✓ Deletion test passed!
✓ Symmetry test passed!
==================================================
All tests passed! ✓
```

## 사용 방법

### 1. Matrix 편집
1. CSV 파일 로드
2. Upper triangle 셀 더블클릭하여 편집
3. 값 입력 (0.0 ~ 1.0)
4. Enter 키 입력
5. Lower triangle의 대응 셀 자동 업데이트
6. Dendrogram 자동 재생성

### 2. Area List 관리
1. 두 matrix 모두 로드
2. "Edit Area List" 버튼 클릭 (보라색)
3. 다이얼로그에서 Add/Edit/Delete 수행
4. OK 버튼 클릭
5. 두 matrix 모두 자동 업데이트

## 추가 구현: 빈 상태에서 Area List 생성 (P19 Update)

### 문제
- 초기 구현에서는 두 matrix가 모두 로드되어야만 "Edit Area List" 버튼이 활성화됨
- 사용자가 CSV 없이 처음부터 area list를 만들 수 없음

### 해결 방법
1. **버튼 항상 활성화**:
   - `edit_areas_btn.setEnabled(False)` 제거
   - 주석: "Always enabled - can create area list from scratch"

2. **빈 상태 처리**:
   - `edit_area_list()` 메서드 수정
   - 두 matrix 모두 로드됨: 기존 편집
   - 하나만 로드됨: 경고 메시지
   - 둘 다 로드 안 됨: 빈 상태로 시작 (labels=[], df=empty)

3. **첫 번째 area 추가**:
   - `AreaListEditorDialog.add_area()` 수정
   - n == 1일 때: 1×1 matrix 생성 (diagonal 1.0)
   - n > 1일 때: 기존 로직 (새 row/column 추가)

4. **단일 area 표시**:
   - `StepMatrixWidget.update_matrix()` 수정
   - shape[0] < 2: clustering 불가 상태
   - shape[0] == 1: 단일 area 표시, 경고 메시지
   - shape[0] >= 2: 정상 clustering

### 테스트
`test_empty_area_list.py` 생성:
```
✓ Test 1: 빈 상태에서 첫 area 생성 (1×1 matrix)
✓ Test 2: 두 번째 area 추가 (2×2 matrix)
✓ Test 3: 여러 area 추가 (5×5 matrix)
```

모든 테스트 통과! ✓

### 사용 시나리오
```
1. GUI 실행 (matrix 없음)
2. "Edit Area List" 버튼 클릭
3. "Add" 버튼으로 area 추가:
   - J (1×1 matrix 생성)
   - T (2×2 matrix로 확장)
   - Y, N, O (계속 확장)
4. "OK" 클릭
5. 두 matrix에 자동으로 로드됨
6. Dendrogram 자동 생성
```

## 다음 단계

이 기능이 완료되면:
1. CSV 저장 기능 추가 (수정된 matrix 저장)
2. Undo/Redo 기능 고려
3. Batch editing (여러 셀 동시 수정)
4. Matrix 검증 도구 (대칭성, 범위 등 자동 체크)
