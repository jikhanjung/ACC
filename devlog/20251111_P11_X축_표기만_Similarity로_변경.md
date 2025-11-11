# 20251111 P11: X축 표기만 Similarity로 변경

## 개요

Dendrogram 구조는 distance 기반으로 그대로 유지하되, X축 눈금 표기만 similarity로 변환하여 표시.

## 요구사항

1. **Dendrogram 구조**: Distance 기반으로 그리기 (변경 없음)
2. **X축 표기**: Similarity로 변환 (`similarity = max_sim - distance`)
3. **X축 방향**: 왼쪽 끝이 1.0 (high similarity), 오른쪽으로 갈수록 값 감소

## 구현

### 핵심 아이디어

```
1. Dendrogram을 distance로 그리기 (그래프 위치는 distance 기반)
2. X축 tick 위치는 distance 값
3. Tick label만 similarity로 변환해서 표시
4. X축을 반전하여 high similarity가 왼쪽에 오도록
```

### 코드

**acc_gui.py - StepDendrogramWidget.update_dendrogram()**

```python
def update_dendrogram(self):
    # ...

    # 1. Dendrogram을 distance로 그리기 (기존 방식)
    full_linkage = self.step_manager.linkage_matrix

    ddata = dendrogram(
        full_linkage,  # Distance 값 사용
        labels=self.step_manager.original_labels,
        ax=ax,
        orientation='right',
        # ...
    )

    # 2. 빨간 점선 (distance 위치)
    current_height = full_linkage[self.current_step - 1, 2]  # distance
    ax.axvline(x=current_height, ...)

    # 3. X축 tick labels를 similarity로 변환
    max_sim = self.step_manager.max_sim

    # 현재 X축 tick 위치들 가져오기 (distance 값)
    xticks = ax.get_xticks()

    # 각 tick을 similarity로 변환
    # similarity = max_sim - distance
    similarity_labels = [f'{max_sim - x:.2f}' if 0 <= x <= max_sim else ''
                        for x in xticks]
    ax.set_xticklabels(similarity_labels)

    # 4. X축 반전: high similarity (왼쪽), low similarity (오른쪽)
    ax.invert_xaxis()

    # 5. X축 레이블
    ax.set_xlabel('Similarity', fontsize=9)
```

## 동작 원리

### Step 1: Distance로 Dendrogram 그리기

```
Dendrogram 내부 위치 (distance 기반):
distance 0.0 ──────────> distance 0.7

J, T가 distance=0.1에서 병합 → X=0.1 위치에 그려짐
O, Q가 distance=0.15에서 병합 → X=0.15 위치에 그려짐
```

### Step 2: X축 Tick Labels 변환

```
원래 tick 위치 (distance):
0.0    0.1    0.2    0.3    ...    0.7

변환된 tick labels (similarity = 1.0 - distance):
1.0    0.9    0.8    0.7    ...    0.3
```

### Step 3: X축 반전

```
화면 표시:
1.0    0.9    0.8    0.7    ...    0.3
왼쪽                              오른쪽
(high similarity)            (low similarity)

그래프 요소들:
- J-T 병합: distance=0.1 위치 → 화면에서 similarity=0.9 근처 (왼쪽)
- O-Q 병합: distance=0.15 위치 → 화면에서 similarity=0.85 근처 (왼쪽)
- Root: 높은 distance → 낮은 similarity (오른쪽)
```

## 예시

### Sample Data (J, T, Y, N, O, Q)

#### Similarity Matrix (입력)
```
       J    T    Y    N    O    Q
J    1.0  0.9  0.8  0.4  0.35 0.36
T    0.9  1.0  0.8  0.38 0.33 0.34
```

max_sim = 1.0

#### Distance Matrix (내부)
```
distance = max_sim - similarity
J-T distance = 1.0 - 0.9 = 0.1
```

#### Dendrogram 표시

**Dendrogram 구조 (distance 기반으로 그려짐):**
```
내부적으로 X=0.1 위치에 J-T 노드
```

**X축 표시 (similarity):**
```
Similarity
1.0  0.9  0.8  0.7  0.6  0.5  0.4  0.3
     │
     J───T  ← X=0.1 (distance) 위치이지만
            화면에서는 0.9 (similarity) 로 표시
```

**의미:**
- Dendrogram 상에서 J-T는 distance=0.1 위치에 그려짐
- 하지만 X축에는 similarity=0.9로 표시됨
- 사용자는 "J와 T가 similarity 0.9에서 병합" 으로 이해

## 장점

### 1. 안정적인 구현
- Dendrogram 그리기는 scipy 기본 방식 사용 (distance)
- 변환은 시각화 레이어에서만 수행
- 버그 가능성 최소화

### 2. 사용자 친화적
- X축에 similarity 표시 → Matrix와 일관성
- 입력 데이터와 같은 단위
- 직관적인 이해

### 3. 유연성
- Dendrogram 구조는 변경 없음
- Tick labels만 변경하므로 원복 용이
- 다른 변환도 쉽게 적용 가능

## Matrix와의 일관성

### Matrix (왼쪽 패널)
```
       J    T    Y
J      -   0.9  0.8   ← Similarity 값
T          -    0.8
Y               -
```

### Dendrogram (중앙 패널)
```
Similarity
1.0  0.9  0.8  0.7  ...
     │    │
     J────T         ← X축에 0.9 표시

사용자: "Matrix에서 J-T가 0.9, Dendrogram에서도 0.9! ✓"
```

### 내부 동작
```
1. Distance 계산: 1.0 - 0.9 = 0.1
2. Dendrogram 그리기: X=0.1 위치
3. X축 표시: 0.1 → 0.9로 변환
```

## 비교

### 이전 시도들

#### 시도 1: Linkage 값 변환
```python
full_linkage[:, 2] = max_sim - full_linkage[:, 2]
dendrogram(full_linkage, ...)
ax.set_xlabel('Similarity')
```
**문제**: Dendrogram 구조 자체가 변경됨

#### 시도 2: Linkage 변환 + X축 반전
```python
full_linkage[:, 2] = max_sim - full_linkage[:, 2]
dendrogram(full_linkage, ...)
ax.invert_xaxis()
```
**문제**: 이중 반전으로 원위치

#### 시도 3: Distance 복원
```python
full_linkage = linkage_matrix  # 그대로
dendrogram(full_linkage, ...)
ax.set_xlabel('Distance')
```
**문제**: Matrix와 단위 불일치

### 최종 해결 (현재)

```python
# Dendrogram은 distance로 그리기
full_linkage = linkage_matrix
dendrogram(full_linkage, ...)

# X축 tick labels만 similarity로 변환
xticks = ax.get_xticks()
similarity_labels = [f'{max_sim - x:.2f}' for x in xticks]
ax.set_xticklabels(similarity_labels)

# X축 반전 (high similarity 왼쪽)
ax.invert_xaxis()
ax.set_xlabel('Similarity')
```

**장점**:
- ✅ Dendrogram 구조는 안정적 (distance 기반)
- ✅ X축 표시는 사용자 친화적 (similarity)
- ✅ Matrix와 일관성 유지
- ✅ 구현 간단, 버그 적음

## 테스트

```bash
$ python acc_gui.py
# Load sample_subordinate.csv
# Navigate through steps
```

**확인 항목:**
1. ✅ X축 레이블: "Similarity"
2. ✅ X축 방향: 1.0 (왼쪽) → 낮은 값 (오른쪽)
3. ✅ Dendrogram 구조: 정상 (distance 기반)
4. ✅ X축 값: Matrix의 similarity 값과 일치
5. ✅ 빨간 점선: 올바른 위치

### 예상 결과

Step 1: J + T 병합 (similarity=0.9)
```
Similarity
1.0  0.9  0.8  0.7  ...
     │
     J───T  ← 0.9 근처에 표시
     └─ 빨간 점선
```

## 결론

Dendrogram 구조는 distance 기반 유지, X축 표기만 similarity로 변환:
- ✅ 안정적인 그래프 구조
- ✅ 사용자 친화적인 표시
- ✅ Matrix와 일관성
- ✅ 간단한 구현

**최고의 절충안: 내부는 distance, 외부는 similarity!**
