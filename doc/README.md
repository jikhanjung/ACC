# ACC Documentation (Markdown)

ACC (Adaptive Cluster Circle) 프로젝트의 Markdown 문서 모음입니다.

> **Note**: Sphinx 기반 HTML 문서(`.rst`)는 `../docs/` 디렉토리에서 관리됩니다.
> 이 디렉토리(`doc/`)는 Markdown 파일만 포함합니다.

## 디렉토리 구분

- **`doc/`** (이 디렉토리) - Markdown 문서 (`.md`, `.pdf`)
- **`../docs/`** - Sphinx 문서 (`.rst`, Makefile, conf.py)

## 문서 구조

### 📘 사용자 문서

- **[USER_MANUAL.md](USER_MANUAL.md)** - 사용자 매뉴얼 (Markdown)
  - GUI 애플리케이션 사용법
  - 3단계 워크플로우 설명
  - CSV 파일 형식 및 예제

- **[ACC_USER_MANUAL.pdf](ACC_USER_MANUAL.pdf)** - 사용자 매뉴얼 (PDF)
  - Markdown에서 자동 생성
  - 생성 방법: [PDF_GENERATION.md](PDF_GENERATION.md)

### 🔬 알고리즘 문서

- **[ACC_Algorithm_Overview.md](ACC_Algorithm_Overview.md)** - 알고리즘 개요
  - 핵심 개념 및 데이터 구조
  - 알고리즘 파이프라인
  - 기하학적 배치 전략

### 👨‍💻 개발자 문서

- **[development.md](development.md)** - 개발 가이드
  - 개발 환경 설정
  - 코드 품질 도구 (Ruff, pytest, pre-commit)
  - 테스트 및 Coverage
  - CI/CD 설정

- **[QA_SETUP_SUMMARY.md](QA_SETUP_SUMMARY.md)** - QA 설정 요약
  - Code coverage 설정
  - Pre-commit hooks
  - GitHub Actions 워크플로우

- **[PDF_GENERATION.md](PDF_GENERATION.md)** - PDF 생성 가이드
  - Markdown → PDF 자동 변환
  - 로컬 생성 및 CI/CD 자동화
  - 트러블슈팅

### 🔧 빌드 문서

- **[build/](build/)** - 빌드 관련 문서
  - 빌드 가이드
  - 환경 설정
  - 트러블슈팅

### 🖼️ 이미지 및 예제

- **[images/](images/)** - 사용자 매뉴얼 스크린샷
  - GUI 스크린샷
  - 튜토리얼 이미지
  - 단계별 가이드 이미지

- **[examples/](examples/)** - 예제 시각화 결과물
  - ACC 시각화 예제 (PNG)
  - 덴드로그램 테스트 결과
  - 알고리즘 출력 샘플

## Sphinx 문서 (별도 디렉토리)

Sphinx를 사용한 HTML 문서는 `../docs/` 디렉토리에서 관리됩니다:

```bash
# Sphinx 설치
pip install sphinx sphinx-rtd-theme

# 문서 빌드
cd ../docs
make html

# 결과 확인
open _build/html/index.html
```

Sphinx 문서는 `.rst` 형식으로 작성되며, 웹 기반 문서 생성에 사용됩니다.

## 빠른 참조

### 새로운 사용자

1. [설치 가이드](../docs/installation.rst) - ACC 설치 방법 (Sphinx)
2. [시작 가이드](../docs/getting_started.rst) - 첫 실행 (Sphinx)
3. [사용자 매뉴얼](USER_MANUAL.md) - 상세 사용법 (Markdown)

### 개발자

1. [개발 가이드](development.md) - 개발 환경 설정
2. [QA 설정](QA_SETUP_SUMMARY.md) - 코드 품질 도구
3. [빌드 가이드](build/BUILDING.md) - 실행 파일 빌드

### 알고리즘 연구자

1. [알고리즘 개요](ACC_Algorithm_Overview.md) - 핵심 알고리즘
2. [데이터 형식](../docs/data_format.rst) - 입력 데이터 구조 (Sphinx)
3. [시각화](../docs/visualization.rst) - 결과 해석 (Sphinx)

## 기여

문서 개선을 위한 기여를 환영합니다:

1. 오타 및 문법 수정
2. 설명 추가 및 개선
3. 예제 추가
4. 새로운 섹션 제안

Pull Request를 통해 기여해주세요.

## 라이선스

문서는 프로젝트와 동일한 MIT 라이선스를 따릅니다.
