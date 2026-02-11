# P34: Raw Data 입력 패널 추가 (Presence/Absence Matrix)

**작성일**: 2026-02-11
**상태**: 계획

---

## 1. 목표

메인 화면 왼쪽에 새로운 패널을 추가하여 유사도 계산의 원시 데이터(presence/absence matrix)를 입력할 수 있게 한다. 이 패널은 엑셀과 유사한 스프레드시트 형태이며, 시대(geological period)별로 여러 시트를 관리할 수 있다.

## 2. 현재 구조

```
┌─────────────┬─────────────────┬──────────────────┐
│  LeftPanel   │  CenterPanel    │   RightPanel      │
│ (Similarity  │ (Dendrograms)   │ (ACC Viz)         │
│  Matrices)   │                 │                   │
│              │  - Subordinate  │  - ACC1 tab       │
│ - Subordinate│  - Inclusive    │  - ACC2 tab       │
│ - Inclusive  │                 │                   │
└─────────────┴─────────────────┴──────────────────┘
          QSplitter (Horizontal, 3 panels)
```

- `MainWindow` → `QSplitter` → `[LeftPanel, CenterPanel, RightPanel]`
- 각 패널은 `ColumnPanel(QWidget)` 상속
- LeftPanel: `StepMatrixWidget` 2개 (Subordinate, Inclusive)
- CenterPanel: `StepDendrogramWidget` 2개
- RightPanel: ACC 시각화 + 옵션

## 3. 변경 후 구조

```
┌──────────────┬─────────────┬─────────────────┬──────────────────┐
│  DataPanel    │  LeftPanel   │  CenterPanel    │   RightPanel      │
│ (Raw Data)   │ (Similarity  │ (Dendrograms)   │ (ACC Viz)         │
│              │  Matrices)   │                 │                   │
│ [Tab: 캄브리] │              │                 │                   │
│ [Tab: 오르도] │ - Subordinate│  - Subordinate  │  - ACC1 tab       │
│ [Tab: 실루리] │ - Inclusive  │  - Inclusive    │  - ACC2 tab       │
│              │              │                 │                   │
│ Rows = Areas │              │                 │                   │
│ Cols = Taxa  │              │                 │                   │
│ Cells = 0/1 │              │                 │                   │
└──────────────┴─────────────┴─────────────────┴──────────────────┘
             QSplitter (Horizontal, 4 panels)
```

## 4. 핵심 설계

### 4.1 새 클래스: `DataPanel(ColumnPanel)`

LeftPanel 왼쪽에 위치하는 새 패널. 주요 구성요소:

```
DataPanel
├── 헤더 영역
│   ├── "Raw Data" 라벨
│   ├── [New] 버튼 - 새 프로젝트(시트 집합) 생성
│   ├── [Load] 버튼 - 파일 로드
│   └── [Save] 버튼 - 파일 저장
├── QTabWidget (시대별 시트)
│   ├── Tab "Cambrian" → PresenceAbsenceTable
│   ├── Tab "Ordovician" → PresenceAbsenceTable
│   └── Tab "Silurian" → PresenceAbsenceTable
├── 시트 관리 버튼
│   ├── [+ Add Sheet] - 새 시트 추가
│   ├── [Rename] - 현재 시트 이름 변경
│   └── [Delete] - 현재 시트 삭제
└── 하단 버튼
    └── [Calculate Similarity →] - 유사도 계산 후 LeftPanel에 전달
```

### 4.2 새 클래스: `PresenceAbsenceTable(QTableWidget)`

각 시트의 테이블 위젯:

- **행(Row)**: Area (지역명, 예: "North America", "Europe")
- **열(Column)**: Taxon (분류군명, 예: "Trilobita sp.1", "Brachiopoda sp.2")
- **셀 값**: 0 또는 1 (absent/present)
- 셀 클릭으로 0↔1 토글 가능
- 행/열 추가/삭제/이름변경 기능 (우클릭 컨텍스트 메뉴)

### 4.3 데이터 모델

```python
# 전체 프로젝트 데이터 구조
{
    "sheets": [
        {
            "name": "Cambrian",
            "areas": ["Area_A", "Area_B", "Area_C"],
            "taxa": ["Taxon_1", "Taxon_2", "Taxon_3"],
            "matrix": [
                [1, 0, 1],   # Area_A
                [1, 1, 0],   # Area_B
                [0, 1, 1],   # Area_C
            ]
        },
        {
            "name": "Ordovician",
            "areas": ["Area_A", "Area_B", "Area_C"],
            "taxa": ["Taxon_4", "Taxon_5"],
            "matrix": [
                [1, 1],
                [0, 1],
                [1, 0],
            ]
        }
    ]
}
```

### 4.4 파일 포맷

**저장/로드 형식**: JSON (`.accdata` 확장자)

```json
{
    "version": "1.0",
    "sheets": [ ... ]
}
```

**CSV Import 지원**: 기존 CSV도 단일 시트로 import 가능

```csv
,Taxon_1,Taxon_2,Taxon_3
Area_A,1,0,1
Area_B,1,1,0
Area_C,0,1,1
```

### 4.5 유사도 계산 (향후 확장)

현재 단계에서는 DataPanel에서 직접 유사도를 계산하지 않고, 데이터 입력/관리 기능만 구현한다. "Calculate Similarity" 버튼은 향후 Jaccard/Simpson 등 유사도 계수를 선택하여 similarity matrix를 자동 생성하고 LeftPanel에 전달하는 기능으로 확장할 수 있다.

단, 이번 구현에서 버튼과 기본 틀은 미리 만들어 두되, 실제 계산 로직은 다음 단계에서 구현한다.

## 5. 구현 단계

### Phase 1: DataPanel 기본 틀 생성

1. `DataPanel(ColumnPanel)` 클래스 생성
2. QTabWidget 기반 멀티 시트 UI
3. 시트 추가/삭제/이름변경 버튼
4. MainWindow의 QSplitter에 4번째 패널로 추가
5. 초기 사이즈 배분 조정: `[400, 450, 450, 600]`

### Phase 2: PresenceAbsenceTable 구현

1. `PresenceAbsenceTable(QTableWidget)` 클래스 생성
2. Area(행) 추가/삭제/이름변경 (컨텍스트 메뉴)
3. Taxon(열) 추가/삭제/이름변경 (컨텍스트 메뉴)
4. 셀 클릭 시 0↔1 토글
5. 셀 배경색: 1=연초록, 0=흰색 (시각적 구분)

### Phase 3: 파일 저장/로드

1. JSON 기반 `.accdata` 파일 포맷 구현
2. Save/Load 기능 (QFileDialog)
3. CSV import 기능 (단일 시트로 변환)
4. 메뉴바에 File 메뉴 추가 (New/Open/Save/Save As)

### Phase 4: 행/열 관리 기능 강화

1. 시트 간 Area 공유/동기화 옵션 (동일 지역들에 대한 시대별 데이터)
2. 행/열 드래그 정렬
3. Undo/Redo (선택)

### Phase 5: 유사도 계산 연동 (후속 작업)

1. Jaccard/Simpson/Dice 등 유사도 계수 선택 UI
2. Presence/absence → similarity matrix 변환
3. LeftPanel의 Sub/Inc matrix에 자동 입력
4. 데이터 변경 시 자동 재계산 옵션

## 6. 수정 대상 파일

| 파일 | 변경 내용 |
|------|----------|
| `acc_gui.py` | DataPanel, PresenceAbsenceTable 클래스 추가, MainWindow 수정 |
| `acc_gui.py` | QSplitter에 4번째 패널 추가, 사이즈 조정 |
| `acc_gui.py` | (선택) File 메뉴바 추가 |

현 시점에서는 `acc_gui.py` 단일 파일 수정으로 충분하다. 유사도 계산 로직은 별도 모듈(`acc_utils.py` 확장 또는 `similarity.py` 신규)에 배치할 수 있으나 Phase 5에서 결정한다.

## 7. 기술적 고려사항

- **QTabWidget**: `setTabsClosable(True)` 대신 별도 Delete 버튼 사용 (실수 방지)
- **QTableWidget**: 대용량 데이터 시 `QTableView` + `QAbstractTableModel` 전환 고려하나, 일반적인 고생물 데이터 규모(수십 area × 수백 taxa)에서는 QTableWidget으로 충분
- **셀 입력 검증**: 0과 1만 허용, 다른 값 입력 시 자동 보정
- **스프레드시트 편의 기능**: Tab/Enter 키로 셀 이동, 복사/붙여넣기 지원

## 8. 우선순위

이번 작업에서는 **Phase 1 ~ Phase 3**을 우선 구현한다:
- 패널 UI + 멀티 시트 + 테이블 편집 + 파일 저장/로드

Phase 4~5는 기본 기능 확인 후 후속 작업으로 진행한다.
