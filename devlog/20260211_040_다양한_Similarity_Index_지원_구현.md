# 040: 다양한 Similarity Index 지원 구현

- **계획 문서**: P37
- **날짜**: 2026-02-11

## 변경 파일

### `acc_utils.py`
- `SIMILARITY_METHODS` 딕셔너리 추가 (key → 표시명 매핑)
- `similarity_from_presence(areas, taxa, matrix, method="jaccard")` 함수 추가
  - 지원 지표: Jaccard, Dice (Sørensen), Simpson, Ochiai, Braun-Blanquet
  - a(공유), b(i전용), c(j전용) 기반 분기 계산
- 기존 `jaccard_similarity_from_presence()`는 `similarity_from_presence(..., method="jaccard")` 호출로 위임 (하위호환 유지)

### `acc_gui.py`
- `QComboBox` import 추가
- `DataPanel.init_ui()`: Calculate Similarity 버튼 위에 유사도 방식 선택 콤보박스 배치
- `DataPanel.calculate_similarity()`: local/global 두 곳의 호출을 `similarity_from_presence(..., method=...)` 로 교체

## 지원 유사도 지표

| Key | 이름 | 수식 (a=공유, b=i전용, c=j전용) |
|-----|------|------|
| `jaccard` | Jaccard | a / (a+b+c) |
| `dice` | Dice (Sørensen) | 2a / (2a+b+c) |
| `simpson` | Simpson | a / min(a+b, a+c) |
| `ochiai` | Ochiai | a / sqrt((a+b)(a+c)) |
| `braun_blanquet` | Braun-Blanquet | a / max(a+b, a+c) |

## 검증 결과

- 하위호환: `jaccard_similarity_from_presence()` 출력이 `similarity_from_presence(..., method="jaccard")`와 동일함을 확인
- 비대칭 데이터(A=[1,1,1,1], B=[1,0,0,1])에서 방법별 값 차이 확인:
  - jaccard=0.5, dice=0.667, simpson=1.0, ochiai=0.707, braun_blanquet=0.5
- 기존 테스트 26개 전체 통과
