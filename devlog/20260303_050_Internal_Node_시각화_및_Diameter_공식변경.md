# devlog 050: Internal Node 시각화 + Diameter 공식 변경

**날짜:** 2026-03-03
**Phase:** 050
**작업자:** Claude Code

## 요약

- ACC 다이어그램에 internal node(병합 지점) 다이아몬드 마커 표시
- Hover tooltip: internal node → members, similarity, diameter, angle, merge step; leaf node → area name, diversity
- Diameter 공식을 `unit/sim`에서 `min_d + (max_d - min_d) * (1 - sim_global)` 선형 보간으로 변경
- Min/Max Diameter 기본값 1/6, GUI 필드에 기본값 세팅
- Show Data 버튼: 트리 구조를 계층적으로 표시 (members 계층 포함)
- Internal node show/hide 체크박스 추가

## 변경 파일

| 파일 | 변경 | 설명 |
|------|------|------|
| `acc_core_tree.py` | 수정 | `_collect_internal_node_info()`, `_make_radius_fn()`, `_collect_leaf_diversity()` 추가; `_make_scale_fn`/`_collect_radii` 제거 |
| `acc_gui.py` | 수정 | internal node 마커, hover tooltip, Show Data, Nodes 체크박스, UI 텍스트 정리 |
| `tests/unit/test_acc_core_tree.py` | 수정 | `TestInternalNodes` 4건, `TestRadiusFn` 3건 추가 |

## 상세

### 1. Internal Node 위치 데이터 (`acc_core_tree.py`)

**`_collect_internal_node_info(node, radius_fn, direction=0.0)`**:
- 각 internal node를 렌더링 direction 기반으로 원 위에 배치
- Root node direction=0° → Y축 위 `(0, radius)`
- 자식 노드는 `direction ± half_angle`로 재귀
- 반환: position, radius, members, local_sim, global_sim, angle, diameter, merge_order

**`_collect_leaf_diversity(node)`**: 서브트리의 leaf diversity를 `{area: diversity}` dict로 수집

`generate_steps()`의 cluster dict에 `"internal_nodes"`, `"diversity"` 필드 추가.

### 2. Diameter 공식 변경

**이전**: `diameter = unit / global_sim` → `_make_scale_fn`으로 2차 매핑
**이후**: `diameter = min_d + (max_d - min_d) * (1 - global_sim)` 직접 계산

- `_collect_radii()` / `_make_scale_fn()` 제거
- `_make_radius_fn(min_diameter, max_diameter)` 신규: `global_sim → radius` 직접 매핑
- 모든 call site를 `scale_fn(node.radius)` → `radius_fn(node.global_sim)`으로 변경
- 기본값: `DEFAULT_MIN_DIAMETER = 1.0` (sim=1), `DEFAULT_MAX_DIAMETER = 6.0` (sim≈0)

### 3. GUI 변경 (`acc_gui.py`)

**Internal node 마커**:
- `plot_acc_step()` STEP 4: 다이아몬드(◇) 마커, 회색 #888888, 7pt, 반투명
- Nodes 체크박스로 show/hide 제어

**Hover tooltip**:
- `_on_hover()`: internal node + leaf node 모두 거리 비교, 가장 가까운 것 표시
- `_show_annotation()`: internal node는 members/similarity/diameter/angle/merge step, leaf는 area name/diversity
- `_hide_annotation()`: 커서 벗어나면 숨김

**Show Data 버튼** (이전 Show Log):
- `_format_acc_tree()`: 트리 재귀 순회, 각 노드의 속성 + display diameter + position 표시
- `_format_members_hierarchical()`: `{{A, B}, {C, D}}` 형태로 계층 구조 표시
- min/max diameter 반영한 실제 diameter 값 계산

**UI 정리**:
- Min/Max Diameter → Min/Max Dia., Edit 박스 폭 60→30
- Show internal nodes → Nodes (체크박스, 기본 unchecked)
- diameter 필드 기본값 "1" / "6" 세팅
- ACC 다이어그램 info 캡션(Active Clusters 등) 삭제

### 4. 테스트 (`tests/unit/test_acc_core_tree.py`)

**TestInternalNodes** (4건):
- `test_step_has_internal_nodes`: 병합된 클러스터에 internal_nodes 존재 확인
- `test_internal_node_fields`: 필수 필드 8개 확인
- `test_internal_node_on_circle`: position 원점 거리 ≈ radius
- `test_leaf_cluster_no_internal_nodes`: leaf 클러스터는 빈 리스트

**TestRadiusFn** (3건, 이전 TestScaleFn 대체):
- `test_defaults_when_none`: 기본값 min=1, max=6 확인
- `test_custom_range`: 사용자 지정 범위
- `test_linear_interpolation`: 선형 보간 정확도

## 테스트 결과

```
39 passed in ~6s
ruff: All checks passed
```
