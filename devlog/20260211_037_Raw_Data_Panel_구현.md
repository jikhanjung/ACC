# 37: Raw Data Panel 구현 결과

**작성일**: 2026-02-11
**관련 계획**: P34
**커밋**: cf81954

---

## 구현 내용

DataPanel과 PresenceAbsenceTable을 추가하여 presence/absence 원시 데이터 입력 기능 구현.

### 추가된 클래스

| 클래스 | 위치 | 역할 |
|--------|------|------|
| `PresenceAbsenceTable` | acc_gui.py | QTableWidget 기반 0/1 매트릭스 편집기 |
| `DataPanel` | acc_gui.py | 멀티시트 관리, 파일 I/O, 시트간 Area 동기화 |

### 주요 기능

1. **스프레드시트 편집**: 더블클릭 토글, 직접 입력, 셀 색상(0=흰색, 1=연녹색)
2. **멀티시트**: 시대별 탭 관리 (추가/삭제/이름변경)
3. **Area 동기화**: Area 추가/삭제/이름변경 시 모든 시트에 반영
4. **복사/붙여넣기**: Ctrl+C/V, Excel 호환 헤더 포함 붙여넣기
5. **컨텍스트 메뉴**: Area/Taxon 추가·삭제·이름변경, Fill Selection
6. **파일 I/O**: `.accdata` JSON 형식 저장/불러오기, CSV 임포트
7. **4컬럼 레이아웃**: MainWindow의 QSplitter에 DataPanel 추가

### 수정된 파일

- `acc_gui.py` — PresenceAbsenceTable, DataPanel 클래스 추가, MainWindow 레이아웃 변경
