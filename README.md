# ACC (Adaptive Cluster Circle)

[![Tests](https://github.com/jikhanjung/ACC/workflows/Tests/badge.svg)](https://github.com/jikhanjung/ACC/actions)
[![Build](https://github.com/jikhanjung/ACC/workflows/Manual%20Build/badge.svg)](https://github.com/jikhanjung/ACC/actions)
[![codecov](https://codecov.io/gh/jikhanjung/ACC/branch/main/graph/badge.svg)](https://codecov.io/gh/jikhanjung/ACC)
[![Release](https://img.shields.io/github/v/release/jikhanjung/ACC)](https://github.com/jikhanjung/ACC/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)

ACC는 두 종류의 덴드로그램(하위 local, 포괄 global)에서 유사도 정보를 결합해, 클러스터 간의 상대적 관계를 원형 도식(concentric circles)으로 시각화하는 알고리즘입니다.

---

## 📋 목차

- [주요 기능](#주요-기능)
- [빠른 시작](#빠른-시작)
- [설치](#설치)
- [사용법](#사용법)
- [개발](#개발)
- [문서](#문서)
- [빌드 및 배포](#빌드-및-배포)
- [기여하기](#기여하기)
- [라이선스](#라이선스)

---

## 🎯 주요 기능

### 핵심 알고리즘
- **이중 덴드로그램 분석**: Local와 Global 두 종류의 덴드로그램 결합
- **기하학적 변환**: 유사도 → 지름(diameter)과 각도(theta)로 변환
- **계층적 시각화**: Concentric circles로 클러스터 관계 표현
- **결정론적 처리**: 동일 입력 → 동일 출력 보장

### GUI 애플리케이션
- **PyQt5 기반**: 직관적인 5패널 워크플로우 (Data | Similarity | Dendrogram | ACC | NMDS)
- **Raw Data 입력**: Presence/Absence Matrix로 원시 데이터 직접 입력
- **Similarity Index 4종**: Jaccard, Ochiai, Raup-Crick, Simpson 자동 계산
- **NMDS 시각화**: 2D/3D Non-metric Multidimensional Scaling
- **CSV 입력**: Similarity matrix를 CSV 파일로 간편하게 로드
- **실시간 시각화**: Matplotlib 기반 인터랙티브 차트
- **자동 덴드로그램**: Scipy hierarchical clustering 자동 생성
- **Undo/Redo**: 모든 데이터 편집에 대한 실행 취소/다시 실행
- **프로젝트 파일**: .accdata 형식으로 프로젝트 저장/로드
- **패널 토글**: View 메뉴에서 필요한 패널만 선택적 표시
- **이미지 저장**: PNG/SVG 형식 고해상도 내보내기

### 개발자 도구
- **Python API**: 핵심 알고리즘을 Python 코드에서 직접 사용
- **코드 품질**: Ruff, pytest, pre-commit hooks 완비
- **CI/CD**: GitHub Actions 자동화 테스트 및 빌드
- **크로스 플랫폼**: Windows, macOS, Linux 지원

---

## ⚡ 빠른 시작

### 실행 파일 다운로드 (권장)

최신 릴리스를 다운로드하세요:

- **Windows**: [ACC-Windows-Installer.zip](https://github.com/jikhanjung/ACC/releases/latest)
- **macOS**: [ACC-macOS-Installer.dmg](https://github.com/jikhanjung/ACC/releases/latest)
- **Linux**: [ACC-Linux.AppImage](https://github.com/jikhanjung/ACC/releases/latest)

### Python으로 실행

```bash
# 저장소 클론
git clone https://github.com/jikhanjung/ACC.git
cd ACC

# 의존성 설치
pip install -r requirements.txt

# GUI 실행
python acc_gui.py
```

---

## 📦 설치

### 요구사항

- **Python**: 3.11 이상
- **운영체제**: Windows, macOS, Linux

### 의존성

```bash
# 프로덕션 환경
pip install -r requirements.txt

# 개발 환경
pip install -r requirements-dev.txt
```

**주요 라이브러리**:
- PyQt5 >= 5.15.0 (GUI)
- numpy >= 2.0.0 (수치 계산)
- scipy >= 1.11.0 (클러스터링)
- pandas >= 2.0.0 (데이터 처리)
- matplotlib >= 3.9.0 (시각화)
- scikit-learn >= 1.6.0 (NMDS 분석)

자세한 설치 방법은 [설치 가이드](https://jikhanjung.github.io/ACC/installation.html)를 참조하세요.

---

## 🚀 사용법

### GUI 애플리케이션

```bash
python acc_gui.py
```

#### 워크플로우

**방법 A: Raw Data에서 시작** (권장)
1. **Data 패널**에서 Presence/Absence Matrix 입력 (또는 CSV 가져오기)
2. Similarity Index 선택 (Jaccard, Ochiai, Raup-Crick, Simpson)
3. **Calculate Similarity** 클릭 → Similarity Matrix 자동 생성
4. Dendrogram 자동 생성 확인
5. **Generate ACC** 또는 **Generate ACC2** 클릭
6. **NMDS 패널**에서 2D/3D 시각화 확인

**방법 B: Similarity Matrix에서 시작** (기존 방식)
1. "Local Similarity Matrix" 섹션에서 **Load CSV** 클릭
2. "Global Similarity Matrix" 섹션에서 **Load CSV** 클릭
3. **Generate ACC Visualization** 버튼 클릭

**프로젝트 저장/로드**:
- File → Save로 .accdata 파일에 프로젝트 저장
- File → Open으로 기존 프로젝트 로드

### Python API 사용

```python
from acc_core import build_acc, DendroNode
from acc_utils import matrix_to_dendrogram
import pandas as pd

# CSV에서 Matrix 로드
local_matrix = pd.read_csv('data/sample_local.csv', index_col=0)
global_matrix = pd.read_csv('data/sample_global.csv', index_col=0)

# Dendrogram 생성
local_dendro = matrix_to_dendrogram(local_matrix)
global_dendro = matrix_to_dendrogram(global_matrix)

# ACC 알고리즘 실행
result = build_acc(
    local_dendro,
    global_dendro,
    global_matrix.to_dict(),
    unit=1.0
)

# 결과 확인
print(result["points"])      # 각 멤버의 (x, y) 좌표
print(result["diameter"])    # 원의 지름
print(result["theta"])       # 각도
print(result["members"])     # 클러스터 멤버 목록
```

### CSV 파일 형식

Similarity matrix는 다음 형식이어야 합니다:

```csv
,J,T,Y,N,O,Q
J,1.0,0.9,0.8,0.4,0.35,0.36
T,0.9,1.0,0.8,0.38,0.33,0.34
Y,0.8,0.8,1.0,0.37,0.32,0.33
N,0.4,0.38,0.37,1.0,0.75,0.75
O,0.35,0.33,0.32,0.75,1.0,0.85
Q,0.36,0.34,0.33,0.75,0.85,1.0
```

**요구사항**:
- 첫 행과 첫 열은 라벨 (동일해야 함)
- 대각선 값은 1.0
- 대칭 행렬
- 값의 범위: 0.0 ~ 1.0 (유사도)

---

## 💻 개발

### 빠른 설정

```bash
# 개발 환경 설정 (Makefile 사용)
make install-dev

# 또는 수동 설정
pip install -r requirements.txt
pip install -r requirements-dev.txt
pre-commit install
```

### Makefile 명령어

```bash
make help         # 전체 명령어 보기
make install-dev  # 개발 환경 설정
make test         # 테스트 실행
make coverage     # Coverage 측정
make lint         # 코드 검사
make format       # 코드 포맷팅
make pdf          # PDF 문서 생성
make docs         # 모든 문서 빌드
make clean        # 빌드 아티팩트 제거
```

### 코드 품질 도구

이 프로젝트는 다음 도구들을 사용합니다:

| 도구 | 용도 | 실행 방법 |
|------|------|-----------|
| **Ruff** | 빠른 Python linter & formatter | `make lint`, `make format` |
| **pytest** | 테스팅 프레임워크 | `make test` |
| **pytest-cov** | 코드 커버리지 측정 | `make coverage` |
| **pre-commit** | Git commit hooks | 자동 실행 |
| **GitHub Actions** | CI/CD 자동화 | Push 시 자동 |

### 테스트

```bash
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=. --cov-report=html

# 특정 마커만 실행
pytest -m unit          # 단위 테스트만
pytest -m integration   # 통합 테스트만
pytest -m "not slow"    # 빠른 테스트만
```

**테스트 마커**:
- `unit` - 빠른 단위 테스트
- `integration` - 통합 테스트
- `gui` - GUI 테스트
- `slow` - 느린 테스트 (>1s)
- `algorithm` - 핵심 알고리즘 테스트

### Pre-commit Hooks

Git commit 시 자동으로 실행됩니다:

```bash
# 수동 실행
pre-commit run --all-files

# 특정 hook만 실행
pre-commit run ruff --all-files
```

**설치된 Hooks**:
- Ruff linter (자동 수정)
- Ruff formatter
- YAML/JSON 검증
- 대용량 파일 차단
- 병합 충돌 마커 검사
- 후행 공백 제거

---

## 📚 문서

### 사용자 문서

- **[사용자 매뉴얼 (온라인)](https://jikhanjung.github.io/ACC/)** - Sphinx HTML 문서
- **[사용자 매뉴얼 (Markdown)](doc/USER_MANUAL.md)** - 상세 사용 가이드
- **[사용자 매뉴얼 (PDF)](doc/ACC_USER_MANUAL.pdf)** - PDF 버전

### 개발자 문서

- **[개발 가이드](doc/development.md)** - 개발 환경 설정, 테스트, CI/CD
- **[QA 설정](doc/QA_SETUP_SUMMARY.md)** - Code coverage, pre-commit hooks
- **[PDF 생성 가이드](doc/PDF_GENERATION.md)** - Markdown → PDF 자동 변환
- **[빌드 가이드](doc/build/BUILDING.md)** - 실행 파일 빌드 방법
- **[프로젝트 구조](STRUCTURE.md)** - 디렉토리 구조 및 파일 조직

### 알고리즘 문서

- **[알고리즘 개요](doc/ACC_Algorithm_Overview.md)** - 핵심 알고리즘 상세 설명
- **[FAQ](https://jikhanjung.github.io/ACC/faq.html)** - 자주 묻는 질문
- **[데이터 형식](https://jikhanjung.github.io/ACC/data_format.html)** - CSV, .accdata 파일 형식
- **[고급 기능](https://jikhanjung.github.io/ACC/advanced_features.html)** - NMDS, ACC2 옵션, Undo/Redo

### 문서 빌드

```bash
# PDF 생성 (Markdown → PDF)
make pdf

# Sphinx HTML 문서
make sphinx

# 모든 문서 빌드
make docs
```

---

## 🔨 빌드 및 배포

### 로컬 빌드

```bash
# PyInstaller 설치
pip install pyinstaller

# 빌드 스크립트 실행
python build.py
```

빌드된 실행 파일은 `dist/` 디렉토리에 생성됩니다.

자세한 내용은 [빌드 가이드](doc/build/BUILDING.md)를 참조하세요.

### GitHub Actions 자동화

프로젝트는 완전 자동화된 CI/CD 파이프라인을 갖추고 있습니다:

| 워크플로우 | 트리거 | 기능 |
|-----------|--------|------|
| **Tests** | Push, PR | 자동 테스트, Coverage 측정, Codecov 업로드 |
| **Build** | Push to main | 크로스 플랫폼 빌드 (Windows, macOS, Linux) |
| **Release** | Tag push (`v*`) | 실행 파일 빌드 및 GitHub Releases 자동 배포 |
| **Docs** | 문서 변경 | Sphinx HTML 빌드, GitHub Pages 배포 |
| **Generate Docs** | USER_MANUAL.md 변경 | PDF 자동 생성 및 커밋 |

**릴리스 프로세스**:
```bash
# 버전 태그 생성
git tag v0.0.6
git push origin v0.0.6

# → GitHub Actions가 자동으로:
#    1. 테스트 실행
#    2. Windows/macOS/Linux 빌드
#    3. GitHub Releases 생성
#    4. 설치 파일 업로드
```

---

## 🤝 기여하기

기여를 환영합니다! 다음 단계를 따라주세요:

1. **Fork** 이 저장소
2. **Feature 브랜치** 생성 (`git checkout -b feature/amazing-feature`)
3. **개발 환경** 설정 (`make install-dev`)
4. **변경사항** 작성 및 테스트
5. **Pre-commit hooks** 통과 확인
6. **Commit** (`git commit -m 'feat: add amazing feature'`)
7. **Push** (`git push origin feature/amazing-feature`)
8. **Pull Request** 생성

### 기여 가이드라인

- 모든 테스트가 통과해야 합니다 (`make test`)
- Code coverage를 유지하거나 향상시켜야 합니다
- Pre-commit hooks를 통과해야 합니다
- 코드 스타일을 따라야 합니다 (Ruff)
- 변경사항에 대한 문서를 업데이트해야 합니다

### 개발 로그

개발 과정과 설계 결정사항은 [`devlog/`](devlog/) 디렉토리에 기록되어 있습니다.

---

## 📄 라이선스

이 프로젝트는 MIT License를 따릅니다. 자세한 내용은 [LICENSE](LICENSE) 파일을 참조하세요.

```
MIT License

Copyright (c) 2024 jikhanjung

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction...
```

---

## 🔗 링크

- **GitHub Repository**: https://github.com/jikhanjung/ACC
- **Issues**: https://github.com/jikhanjung/ACC/issues
- **Releases**: https://github.com/jikhanjung/ACC/releases
- **Documentation**: https://jikhanjung.github.io/ACC (Sphinx)
- **Codecov**: https://codecov.io/gh/jikhanjung/ACC

---

## 📊 프로젝트 상태

- **버전**: 0.0.6
- **Python**: 3.11, 3.12
- **테스트**: [![Tests](https://github.com/jikhanjung/ACC/workflows/Tests/badge.svg)](https://github.com/jikhanjung/ACC/actions)
- **커버리지**: [![codecov](https://codecov.io/gh/jikhanjung/ACC/branch/main/graph/badge.svg)](https://codecov.io/gh/jikhanjung/ACC)
- **빌드**: [![Build](https://github.com/jikhanjung/ACC/workflows/Manual%20Build/badge.svg)](https://github.com/jikhanjung/ACC/actions)

---

**Made with ❤️ by jikhanjung**
