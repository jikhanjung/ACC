# Project Structure

ACC 프로젝트의 디렉토리 구조 및 파일 조직 가이드입니다.

## Directory Layout

```
ACC/
├── README.md                   # 프로젝트 소개 및 시작 가이드
├── CLAUDE.md                   # Claude Code를 위한 프로젝트 가이드
├── STRUCTURE.md                # 이 파일 - 프로젝트 구조 설명
│
├── requirements.txt            # 프로덕션 의존성
├── requirements-dev.txt        # 개발/테스트 의존성
├── pyproject.toml             # 프로젝트 메타데이터 및 도구 설정
├── pytest.ini                 # Pytest 설정
├── .coveragerc                # Code coverage 설정
├── .pre-commit-config.yaml    # Pre-commit hooks 설정
├── .gitignore                 # Git ignore 패턴
│
├── version.py                 # 버전 정보
├── acc_core.py               # 핵심 알고리즘 구현
├── acc_utils.py              # 유틸리티 함수
├── acc_gui.py                # PyQt5 GUI 애플리케이션
├── build.py                  # 빌드 스크립트
│
├── data/                     # 샘플 데이터 파일
│   ├── sample_local.csv
│   └── sample_global.csv
│
├── tests/                    # 테스트 코드
│   ├── conftest.py          # Pytest fixtures
│   ├── test_acc_core.py
│   ├── test_acc_utils.py
│   └── test_acc_gui.py
│
├── doc/                      # 📄 Markdown 문서 (개발자/사용자)
│   ├── README.md            # 문서 디렉토리 가이드
│   ├── ACC_Algorithm_Overview.md
│   ├── USER_MANUAL.md
│   ├── ACC_USER_MANUAL.pdf
│   ├── development.md
│   ├── QA_SETUP_SUMMARY.md
│   ├── images/              # 사용자 매뉴얼 스크린샷
│   │   ├── 01_main_window.png
│   │   ├── 02_sample_loaded.png
│   │   └── ...
│   ├── examples/            # 예제 시각화 결과물
│   │   ├── ACC_visualization.png
│   │   ├── test_step_dendro.png
│   │   └── ...
│   └── build/               # 빌드 관련 문서
│       ├── README.md
│       ├── BUILDING.md
│       ├── BUILD_INSTRUCTIONS.md
│       ├── INSTALL_PYQT5.md
│       ├── SETUP_PYTHON311.md
│       ├── MATPLOTLIB_ISSUE.md
│       └── TROUBLESHOOT_PYQT5.md
│
├── docs/                     # 📚 Sphinx 문서 (.rst)
│   ├── conf.py              # Sphinx 설정
│   ├── index.rst            # 메인 페이지
│   ├── installation.rst
│   ├── getting_started.rst
│   ├── basic_usage.rst
│   ├── advanced_features.rst
│   ├── data_format.rst
│   ├── visualization.rst
│   ├── troubleshooting.rst
│   ├── faq.rst
│   ├── changelog.rst
│   ├── Makefile             # Unix 빌드
│   ├── make.bat             # Windows 빌드
│   └── _build/              # 생성된 HTML (gitignore)
│
├── examples/                 # 예제 스크립트
│   └── ...
│
├── devlog/                   # 개발 로그 및 노트
│   └── ...
│
├── packaging/                # 배포 패키징 파일
│   ├── linux/
│   ├── macos/
│   └── windows/
│
└── .github/                  # GitHub 설정
    └── workflows/           # CI/CD 워크플로우
        ├── test.yml         # 테스트 자동화
        ├── build.yml        # 빌드 트리거
        ├── reusable_build.yml
        ├── release.yml
        └── docs.yml         # 문서 배포
```

## Documentation Organization

프로젝트는 두 가지 문서 시스템을 사용합니다:

### 1. Markdown 문서 (`doc/`)

**대상**: 개발자, 빌드 엔지니어, GitHub 사용자
**형식**: `.md`, `.pdf`
**용도**:
- 개발 가이드 및 QA 설정
- 빌드 및 환경 설정 지침
- 알고리즘 상세 설명
- GitHub에서 직접 읽을 수 있는 문서

**주요 파일**:
- `development.md` - 개발 환경 설정, 테스트, CI/CD
- `QA_SETUP_SUMMARY.md` - Code coverage, pre-commit hooks
- `ACC_Algorithm_Overview.md` - 알고리즘 상세
- `USER_MANUAL.md` - 사용자 매뉴얼 (Markdown)
- `build/` - 빌드 관련 모든 문서

### 2. Sphinx 문서 (`docs/`)

**대상**: 최종 사용자, 웹 방문자
**형식**: `.rst` (reStructuredText)
**용도**:
- HTML 웹 문서 생성
- 공식 문서 사이트 (GitHub Pages)
- 설치, 사용법, FAQ 등 사용자 가이드

**생성 방법**:
```bash
cd docs/
make html
open _build/html/index.html
```

## File Naming Conventions

- **Configuration files**: lowercase with dots (`.coveragerc`, `pytest.ini`)
- **Python files**: snake_case (`acc_core.py`, `test_acc_utils.py`)
- **Markdown docs**: PascalCase or snake_case (`README.md`, `development.md`)
- **Sphinx docs**: snake_case (`.rst`)

## Key Configuration Files

| File | Purpose |
|------|---------|
| `pyproject.toml` | 프로젝트 메타데이터, Ruff, Coverage 설정 |
| `pytest.ini` | Pytest 설정 (markers, coverage) |
| `.coveragerc` | Code coverage 상세 설정 |
| `.pre-commit-config.yaml` | Pre-commit hooks 정의 |
| `requirements.txt` | 프로덕션 의존성 |
| `requirements-dev.txt` | 개발/테스트 도구 |
| `docs/conf.py` | Sphinx 문서 설정 |

## Build Artifacts (Ignored by Git)

다음 디렉토리와 파일은 `.gitignore`에 의해 제외됩니다:

```
build/                  # PyInstaller 빌드 아티팩트
dist/                   # 배포 파일
*.egg-info/             # Python 패키지 메타데이터
__pycache__/            # Python 바이트코드
.pytest_cache/          # Pytest 캐시
.ruff_cache/            # Ruff 캐시
htmlcov/                # Coverage HTML 리포트
.coverage               # Coverage 데이터 파일
docs/_build/            # Sphinx 빌드 결과
```

## Quick Navigation

- **Start developing**: [doc/development.md](doc/development.md)
- **Build the app**: [doc/build/BUILDING.md](doc/build/BUILDING.md)
- **Understand the algorithm**: [doc/ACC_Algorithm_Overview.md](doc/ACC_Algorithm_Overview.md)
- **User guide**: [doc/USER_MANUAL.md](doc/USER_MANUAL.md)
- **QA setup**: [doc/QA_SETUP_SUMMARY.md](doc/QA_SETUP_SUMMARY.md)

## Guidelines

### Adding New Documentation

1. **Markdown 문서 (개발/빌드)**:
   - `doc/` 또는 `doc/build/`에 추가
   - GitHub에서 읽기 쉬운 형식
   - 개발자 대상

2. **Sphinx 문서 (사용자 가이드)**:
   - `docs/`에 `.rst` 파일 추가
   - `docs/index.rst`에 링크 추가
   - HTML 생성 대상

### Directory Naming

- `doc/` - Markdown 문서 (단수형, 짧음)
- `docs/` - Sphinx 문서 (복수형, 관례)
- `tests/` - 테스트 코드 (복수형)
- `examples/` - 예제 (복수형)

## License

모든 파일은 MIT License를 따릅니다.
