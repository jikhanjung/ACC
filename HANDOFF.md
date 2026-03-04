# ACC Project Handover

**Last updated:** 2026-03-04

## Project Overview

ACC (Adaptive Cluster Circle)는 계층적 클러스터 관계를 원형 다이어그램으로 시각화하는 Python 알고리즘. Local/Global 두 종류의 dendrogram 유사도 정보를 결합하여 2D 기하학적 표현을 생성한다.

- **버전**: 0.1.0
- **Python**: 3.11+ 필수 (`datetime.UTC`)
- **GUI**: PyQt5 기반 5패널 워크플로우
- **저장소**: https://github.com/jikhanjung/ACC

## Current Status

| 항목 | 값 |
|------|-----|
| 버전 | 0.1.0 |
| Git 상태 | clean (main 브랜치) |
| 테스트 | 147 케이스 (unit/integration/gui) |
| CI/CD | GitHub Actions 7개 워크플로우 |
| 린팅 | Ruff 0.13+ (pre-commit hooks) |
| 문서 | v0.1.0 기준 최신 상태 |
| 빌드 | PyInstaller + InnoSetup (Windows), --onefile 지원 |

## Core Architecture

### 핵심 파일

| 파일 | 줄수 | 역할 |
|------|------|------|
| `acc_core.py` | 531 | 핵심 ACC 알고리즘 (build_acc 파이프라인) |
| `acc_core_new.py` | ~1,200 | 대안 알고리즘 (matrix 직접 기반) |
| `acc_core_tree.py` | ~646 | 트리 기반 ACC (ACCNode, build/render 분리) |
| `acc_render_paper.py` | ~890 | Paper 알고리즘 (4-step 증분, 연산 로그 포함) |
| `acc_gui.py` | ~5,013 | PyQt5 GUI 애플리케이션 (Adjust 체크박스, Angle Info 라벨) |
| `acc_utils.py` | ~657 | 유틸리티 (similarity↔distance, tree/paper 래퍼) |
| `version.py` | 23 | 버전 정보 (Single Source of Truth) |

### 알고리즘 파이프라인 (acc_core.py: build_acc)

1. `extract_clusters_from_dendro` — Local dendrogram 순회, 클러스터 수집
2. `decorate_clusters` — sim_global, diameter, theta 계산
3. Sort by sim_local 내림차순
4. `place_first_cluster` — 원점에 기본 클러스터 배치
5. 반복 병합:
   - `add_area_to_cluster` — 기존 클러스터에 새 멤버 추가
   - `merge_two_clusters` — 두 다중 멤버 클러스터 결합

### 기하학적 변환

- **Diameter (d)**: `unit / sim_global` (역수 관계)
- **Angle (θ)**: `180° * (1 - sim_local)` (유사도↑ → 각도↓)
- 극좌표 → 직교좌표 변환, 원점 중심 배치

## GUI Architecture (5-Panel Workflow)

```
[Data] → [Similarity] → [Dendrogram] → [ACC] → [NMDS]
  │          │               │            │        │
  │          │               │            │        └ NMDS 2D/3D (scikit-learn)
  │          │               │            └ ACC 동심원 시각화 (트리 기반, diversity index)
  │          │               └ UPGMA dendrogram (scipy)
  │          └ Local/Global similarity matrix 편집
  └ Raw Data: Presence/Absence matrix 입력
```

- **Raw Data 패널**: Presence/Absence 행렬 입력, 유사도 지수 선택
- **Similarity 패널**: Local/Global 탭, CSV 로드, 직접 편집, Undo/Redo
- **Dendrogram 패널**: UPGMA 기반, 단계별 클러스터링 시각화
- **ACC 패널**: 트리 기반 알고리즘, diversity index, min/max diameter 스케일링
- **NMDS 패널**: 2D/3D 산점도, Stress 품질 표시 (Excellent/Good/Fair/Poor)

### 유사도 지수 4종

| 지수 | 설명 |
|------|------|
| Jaccard | `a / (a + b + c)` |
| Ochiai | `a / sqrt((a+b)(a+c))` |
| Raup-Crick | Monte Carlo 시뮬레이션 (기본 10,000회) |
| Simpson | `a / min(a+b, a+c)` |

### 파일 형식

- **`.accdata`**: JSON 기반 프로젝트 파일 (유사도 행렬, 설정 저장)
- **CSV**: 유사도 행렬 가져오기/내보내기
- **이미지 내보내기**: PNG, PDF, SVG (우클릭 메뉴)

## Recent Changes

### 053: v0.1.0 릴리스 (2026-03-04)

- **Adjust 체크박스** (`acc_gui.py`): θ 스케일링 ON/OFF 제어
  - Flip 체크박스 옆 배치, 기본값: 체크됨
  - Angle Info 라벨: `raw° → target° (scale: x.xxxx)` 형식 표시
  - `acc_render_paper.py`: `_compute_positions(adjust=True)` 파라미터 추가
  - `acc_utils.py`: `build_acc_paper`/`rerender_acc_paper`에 `adjust` 파라미터 추가
- **Show Data 연산 상세** (`acc_render_paper.py`, `acc_gui.py`):
  - `_create_pair`, `_add_area`, `_merge_clusters`가 `(ClusterState, log_lines)` 튜플 반환
  - `render_paper`에서 `computation_log` 키로 각 step에 저장
  - `show_acc_data()` 재작성 — 중간값 전체 포맷팅 표시
- **θ_btw 복원 버그 수정** (`acc_render_paper.py`):
  - 기존: closest pair의 sim으로 각도 복원 (잘못됨)
  - 수정: boundary adjacent pair의 sim으로 복원 (올바름)
  - 검증: Simpson Arenig raw total 555.78°, scale 0.2834
- **build.py `--onefile` 옵션**: PyInstaller 단일 실행파일 빌드 지원
- **버전 0.1.0 업그레이드**: `version.py`, `pyproject.toml`
- 테스트: 147개 통과 (기존 126개 → +21)

### 051: ACC Node Tree 팝업 다이얼로그 (2026-03-03)

- **`_draw_acc_node_tree(ax, root, title)`** 함수 추가 (`acc_gui.py`):
  - In-order traversal로 cladogram 레이아웃 계산
  - 검은 원 + 흰색 텍스트로 leaf 표시
  - 내부 노드에 파란 박스(sim_local) + 빨간 박스(sim_global) 표시
- **`ACCNodeTreeDialog(QDialog)`** 클래스 추가 (`acc_gui.py`):
  - 비모달 독립 윈도우, 520×420 크기
  - matplotlib FigureCanvas 기반 렌더링
- **`generate_acc()` 수정**: ACC 생성 후 자동으로 ACCNodeTreeDialog 팝업

### 048~050: Paper 알고리즘 기반 ACC 렌더링 (2026-03-03)

- **`acc_render_paper.py` 신규**: 논문 4-step 증분 알고리즘 구현
  - `ClusterState`, `CachedStep` 자료구조
  - `_create_pair`, `_add_area`, `_merge_clusters`, `_compute_positions`
  - `render_paper()`, `rerender_paper()` 메인 함수
- **UPGMA 버그 수정** (`acc_core_tree.py`): 쌍 선택에 평균 유사도 사용 (max → avg)
- **Global sim 계산 수정** (`acc_render_paper.py`): `_add_area`에서 raw pairwise 대신 `merged_node.global_sim` 사용
- **Leaf hover 툴팁** (`acc_gui.py`): diameter, 인접 angle, sim_local, sim_global, diversity 표시
- **Algorithm combo** (`acc_gui.py`): "Paper"/"Tree" 선택 콤보박스 추가 (default: Paper)
- **max_diameter default**: "6" → "11"
- 테스트: `tests/unit/test_acc_render_paper.py` 29개 추가 (총 **126개** pass)

### 041: 트리 기반 ACC 알고리즘 (2026-03-03)

- **`acc_core_tree.py` 신규**: ACCNode 트리 기반 ACC 알고리즘 구현
  - Build/Render 분리: diameter 변경 시 트리 재구축 없이 좌표만 재계산
  - Diversity index로 area 순서(left/right) 결정
- **ACC2 완전 제거**: GUI에서 ACC2 탭, 관련 메서드 ~420줄 삭제
- **Diameter 컨트롤**: ACC 패널에 Min/Max Diameter 입력 필드 추가
- 테스트: `test_acc_core_tree.py` 35개 추가 (총 106개 unit+integration pass)

### 이전 변경:

- Magic numbers → 명명 상수화 (`THETA_MAX_DEGREES`, `DEFAULT_SIMILARITY`)
- `print()` → `logging` 모듈 전환 (acc_gui.py)
- Bare `except:` → `except (ValueError, AttributeError):`
- GUI 테스트 스위트 추가 (`tests/gui/test_acc_gui.py`)

## CI/CD

GitHub Actions 워크플로우 (`.github/workflows/`):

| 워크플로우 | 트리거 | 동작 |
|-----------|--------|------|
| `test.yml` | push (main, develop), PR (main) | pytest (Python 3.11, 3.12), xvfb |
| `build.yml` | - | PyInstaller 빌드 |
| `reusable_build.yml` | - | 재사용 가능 빌드 |
| `release.yml` | tag push | 릴리스 자동화 |
| `manual-release.yml` | workflow_dispatch | 수동 릴리스 |
| `generate_docs.yml` | - | 문서 생성 |
| `docs.yml` | push (docs/) | Sphinx → GitHub Pages 배포 |

## Test Status

| 카테고리 | 파일 | 테스트 수 | 비고 |
|----------|------|----------|------|
| unit | `test_acc_core.py`, `test_acc_core_new.py`, `test_acc_utils.py` | ~25 | 핵심 알고리즘 + 유틸리티 |
| integration | `test_pipeline.py` | ~8 | 전체 워크플로우 |
| gui | `test_acc_gui.py` | 13 | 위젯 + 코드 품질 |
| legacy | 20개 파일 | ~40 | CI에서 제외 |
| performance | 벤치마크 | - | CI에서 제외 |

```bash
# 테스트 실행
pytest tests/

# 커버리지 포함
pytest tests/ --cov=. --cov-report=html

# 린팅
ruff check .
```

## File Structure

```
ACC/
├── CLAUDE.md                    # Claude Code 가이드
├── HANDOFF.md                   # 인수인계 문서 (이 파일)
├── CHANGELOG.md                 # 버전 변경 이력
├── STRUCTURE.md                 # 디렉토리 구조 가이드
├── README.md                    # 프로젝트 소개
├── Makefile                     # 개발 태스크 자동화
├── pyproject.toml               # 프로젝트 설정 (Ruff, pytest, coverage)
├── version.py                   # 버전 정보 (0.0.6)
├── requirements.txt             # 프로덕션 의존성
├── requirements-dev.txt         # 개발 의존성
│
├── acc_core.py                  # 핵심 ACC 알고리즘
├── acc_core_new.py              # 대안 알고리즘
├── acc_core_acc2.py             # ACC2 시각화
├── acc_gui.py                   # PyQt5 GUI (4,557줄)
├── acc_utils.py                 # 유틸리티 함수
├── build.py                     # 빌드 자동화
├── manage_version.py            # 버전 관리 스크립트
├── version_utils.py             # 버전 유틸리티
│
├── tests/
│   ├── conftest.py              # pytest 픽스처 (QApplication 세션)
│   ├── unit/                    # 단위 테스트
│   ├── integration/             # 통합 테스트
│   ├── gui/                     # GUI 테스트
│   ├── legacy/                  # 레거시 테스트 (CI 제외)
│   ├── performance/             # 성능 벤치마크 (CI 제외)
│   └── test_data/               # 테스트용 CSV
│
├── data/                        # 샘플 유사도 행렬 CSV
├── examples/                    # 예제 스크립트
├── doc/                         # Markdown 문서
│   ├── USER_MANUAL.md
│   ├── ACC_Algorithm_Overview.md
│   ├── development.md
│   ├── images/                  # 스크린샷
│   └── build/                   # 빌드 가이드
├── docs/                        # Sphinx 문서 (.rst)
├── devlog/                      # 개발 기록 (48개 문서)
│   └── DEVLOG_SUMMARY.md        # 개발 기록 요약
│
├── build/                       # PyInstaller 아티팩트
├── dist/                        # 배포 파일
├── InnoSetup/                   # Windows 인스톨러
├── packaging/                   # 크로스플랫폼 패키징
│   ├── linux/
│   ├── macos/
│   └── windows/
└── .github/workflows/           # CI/CD (7개 워크플로우)
```

## Dependencies

**프로덕션:**
- PyQt5 (>=5.15), PyQt5-sip (>=12.12)
- NumPy (>=2.0), SciPy (>=1.11), Pandas (>=2.0)
- scikit-learn (>=1.6) — NMDS
- Matplotlib (>=3.9)
- semver (>=3.0)
- PyInstaller (>=5.13) — 빌드

**개발:**
- pytest (>=8.4), pytest-cov, pytest-qt, pytest-mock, pytest-timeout
- coverage[toml] (>=7.10)
- ruff (>=0.13)
- pre-commit (>=4.0)

## Open Issues

- 코드에 TODO 없음
- 알려진 크리티컬 버그 없음
- CHANGELOG에 Unreleased 항목 존재 (리팩토링 + GUI 테스트 추가)

## Future Extensions

- Animation/video export of clustering steps
- Batch processing for multiple datasets
- Additional clustering methods beyond UPGMA
- Type hints + mypy 지원
- 3D 시각화 확장

## Development Convention

- **커밋 메시지**: Semantic commit (`feat:`, `fix:`, `docs:`, `refactor:`, `chore:`)
- **브랜치**: main (릴리스), develop (통합), feature branches
- **devlog**: `devlog/YYYYMMDD_NNN_제목.md` (작업 로그) / `devlog/YYYYMMDD_PNN_제목.md` (계획)
- **Phase 완료 시**: devlog 기록 → HANDOFF.md 갱신 → 필요시 README.md 갱신

## Version History

| 날짜 | 버전 | 주요 내용 |
|------|------|-----------|
| 2024-11-11 | 0.0.1 | 초기 프로젝트 셋업 |
| 2024-11-15 | 0.1.0 | PyQt5 GUI 초기 구현 |
| 2025-11-16 | 0.0.3 | QA 인프라, Ruff, pytest, CI/CD |
| 2026-02-10 | 0.0.4 | InnoSetup, ACC1 스타일, semver |
| 2026-02-26 | 0.0.5 | NMDS, 유사도 4종, Raw Data, Undo/Redo, 패널 토글 |
| 2026-03-03 | 0.0.6 | 트리 기반 ACC, Diversity index, ACC2 제거, 코드 품질 개선 |
| 2026-03-04 | 0.1.0 | Adjust 체크박스, Show Data 연산 상세, θ_btw 버그 수정, --onefile 빌드 |
