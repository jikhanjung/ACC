# P37: 다양한 Similarity Index 지원

## 목표
현재 Jaccard Index만 지원하는 유사도 계산을 확장하여, 생물지리학/고생물학에서 널리 쓰이는 5가지 유사도 지표를 선택할 수 있도록 한다.

## 배경
- 현재 `acc_utils.py`의 `jaccard_similarity_from_presence()`만 사용
- `acc_gui.py`의 `DataPanel.calculate_similarity()`에서 local/global 두 곳에서 호출

## 지원할 유사도 지표

a = 공유 taxa 수, b = i 전용, c = j 전용

| Method | 수식 | 이름 |
|--------|------|------|
| `jaccard` | a / (a+b+c) | Jaccard |
| `dice` | 2a / (2a+b+c) | Dice (Sørensen) |
| `simpson` | a / min(a+b, a+c) | Simpson |
| `ochiai` | a / sqrt((a+b)(a+c)) | Ochiai |
| `braun_blanquet` | a / max(a+b, a+c) | Braun-Blanquet |

## 수정 대상

### 1. `acc_utils.py` — 범용 유사도 함수 추가
- `jaccard_similarity_from_presence()` (line 338) 아래에 `similarity_from_presence(areas, taxa, matrix, method="jaccard")` 추가
- method 파라미터에 따라 위 5가지 수식 분기
- 기존 `jaccard_similarity_from_presence()`는 하위호환 유지 — 내부에서 `similarity_from_presence(..., method="jaccard")` 호출하도록 위임

### 2. `acc_gui.py` — DataPanel UI에 콤보박스 추가
- `DataPanel.init_ui()`에서 Calculate Similarity 버튼 앞에 유사도 방식 선택 콤보박스 배치
- `QComboBox` import 추가
- 항목: Jaccard / Dice (Sørensen) / Simpson / Ochiai / Braun-Blanquet
- `self.similarity_combo`에 저장, `currentData()`로 method key 획득

### 3. `acc_gui.py` — `calculate_similarity()` 수정
- `jaccard_similarity_from_presence()` 호출 2곳을 `similarity_from_presence(..., method=...)` 로 교체

## 검증
1. 같은 데이터에서 방식 변경 시 매트릭스 값이 달라지는지 확인
2. 기존 단위 테스트 통과 (`jaccard_similarity_from_presence` 하위호환)
