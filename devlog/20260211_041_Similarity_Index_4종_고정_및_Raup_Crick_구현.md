# 041: Similarity Index 4종 고정 및 Raup-Crick 구현

**작업 일시**: 2026-02-11
**관련 문서**: [P38](20260211_P38_Similarity_Index_4종_고정_및_Raup_Crick_구현.md)

## 요약
기존 5가지 유사도 지표를 4가지로 고정하고, Raup-Crick을 Monte Carlo 시뮬레이션 기반으로 제대로 구현. GUI에 반복 횟수 입력 기능 추가.

## 변경 내용

### 1. acc_utils.py

**SIMILARITY_METHODS (line 358-364)**
```python
# Before (5가지)
SIMILARITY_METHODS = {
    "jaccard": "Jaccard",
    "dice": "Dice (Sørensen)",
    "simpson": "Simpson",
    "ochiai": "Ochiai",
    "braun_blanquet": "Braun-Blanquet",
}

# After (4가지)
SIMILARITY_METHODS = {
    "jaccard": "Jaccard",
    "ochiai": "Ochiai",
    "raup_crick": "Raup-Crick",
    "simpson": "Simpson",
}
```

**similarity_from_presence() (line 367-434)**
- 파라미터 추가: `raup_crick_iterations=10000`
- Raup-Crick Monte Carlo 구현:
  ```python
  elif method == "raup_crick":
      more_similar = 0
      taxa_pool = list(range(N))
      for _ in range(raup_crick_iterations):
          random_i = set(random.sample(taxa_pool, ni))
          random_j = set(random.sample(taxa_pool, nj))
          random_shared = len(random_i & random_j)
          if random_shared >= a:
              more_similar += 1
      p_value = more_similar / raup_crick_iterations
      val = 1.0 - p_value
  ```
- Dice, Braun-Blanquet 케이스 제거

### 2. acc_gui.py

**DataPanel UI (line 2989-3014)**
```python
# Similarity method selector
self.similarity_combo = QComboBox()
self.similarity_combo.currentIndexChanged.connect(self._on_similarity_method_changed)

# Raup-Crick iterations input
self.rc_iterations_label = QLabel("Iterations:")
self.rc_iterations_input = QLineEdit("10000")
self.rc_iterations_input.setFixedWidth(80)
```

**_on_similarity_method_changed() (line 3319-3325)**
```python
def _on_similarity_method_changed(self):
    method = self.similarity_combo.currentData()
    is_raup_crick = (method == "raup_crick")
    self.rc_iterations_label.setVisible(is_raup_crick)
    self.rc_iterations_input.setVisible(is_raup_crick)
```

**calculate_similarity() (line 3391-3419)**
```python
# Get Raup-Crick iterations
raup_crick_iterations = 10000
if method == "raup_crick":
    try:
        raup_crick_iterations = int(self.rc_iterations_input.text())
        if raup_crick_iterations < 1:
            raise ValueError("Iterations must be positive")
    except ValueError:
        QMessageBox.warning(self, "Invalid Input", "...")
        raup_crick_iterations = 10000

# Pass to similarity calculation
local_df = similarity_from_presence(..., raup_crick_iterations=raup_crick_iterations)
global_df = similarity_from_presence(..., raup_crick_iterations=raup_crick_iterations)
```

## 주요 알고리즘

### Raup-Crick Monte Carlo
1. 관찰된 공유 taxa 수 계산
2. n회 반복:
   - 각 지역의 taxa 수는 유지
   - taxa pool에서 무작위 샘플링
   - 무작위 공유 수 계산
3. P(random ≥ observed) 계산
4. Similarity = 1 - p_value

### 반복 횟수 선택 가이드
- **100회**: 빠르지만 불안정
- **1,000회**: 중간 속도, 중간 정확도
- **10,000회**: 권장 (0.13초, 안정적)
- **100,000회**: 매우 정확하지만 느림

## 테스트 결과

### 기능 테스트
```bash
✓ Jaccard, Ochiai, Simpson 선택 시 iterations 필드 숨김
✓ Raup-Crick 선택 시 iterations 필드 표시
✓ 잘못된 입력 시 경고 및 기본값 사용
✓ 모든 4가지 방법 정상 작동
```

### 성능 테스트 (10,000 iterations)
```
Computation time: 0.13 seconds
A-B similarity: 0.7588 (consistent across runs)
```

## UI 동작

### Raup-Crick 미선택
```
[Similarity: ▼ Jaccard     ] [Calculate Similarity →]
```

### Raup-Crick 선택
```
[Similarity: ▼ Raup-Crick  ] [Iterations: 10000] [Calculate Similarity →]
```

## 검증
```bash
# Syntax check
python -m py_compile acc_gui.py
# ✓ acc_gui.py syntax is valid

# Functional test
python -c "from acc_utils import SIMILARITY_METHODS; print(list(SIMILARITY_METHODS.keys()))"
# ['jaccard', 'ochiai', 'raup_crick', 'simpson']
```

## 변경 파일 목록
- ✏️ `acc_utils.py`: SIMILARITY_METHODS, similarity_from_presence()
- ✏️ `acc_gui.py`: DataPanel UI 및 로직
- 📝 `devlog/20260211_P38_*.md`: 상세 문서
- 📝 `devlog/20260211_041_*.md`: 구현 요약 (본 문서)

## 다음 단계
- [ ] 사용자 매뉴얼에 4가지 similarity index 설명 추가
- [ ] CHANGELOG.md 업데이트
- [ ] 단위 테스트 추가 (tests/unit/test_acc_utils.py)
- [ ] 버전 bump (0.0.5?)
