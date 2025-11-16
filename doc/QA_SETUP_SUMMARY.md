# QA Setup Summary

이 문서는 ACC 프로젝트에 구현된 코드 품질 관리(QA) 설정을 요약합니다.

## 설정된 도구들

### 1. Code Coverage (.coveragerc)

**파일**: `.coveragerc`

**기능**:
- pytest-cov와 함께 코드 커버리지 측정
- HTML, XML, Terminal 리포트 생성
- 테스트 파일, 빌드 파일, 문서 등 제외
- Codecov 업로드를 위한 XML 출력

**사용법**:
```bash
pytest --cov=. --cov-report=html
open htmlcov/index.html
```

### 2. Pre-commit Hooks (.pre-commit-config.yaml)

**파일**: `.pre-commit-config.yaml`

**설치된 Hook들**:
- **Ruff linter** - 코드 품질 검사 및 자동 수정
- **Ruff formatter** - 코드 포맷팅 (black 대체)
- **check-added-large-files** - 대용량 파일 커밋 방지
- **check-yaml** - YAML 문법 검사
- **check-json** - JSON 문법 검사
- **check-case-conflict** - 파일명 대소문자 충돌 검사
- **check-merge-conflict** - 병합 충돌 마커 검사
- **end-of-file-fixer** - 파일 끝 줄바꿈 추가
- **trailing-whitespace** - 후행 공백 제거

**설치**:
```bash
pip install pre-commit
pre-commit install
```

**실행**:
```bash
# 자동 실행 (git commit 시)
git commit -m "message"

# 수동 실행 (전체 파일)
pre-commit run --all-files

# 특정 hook만 실행
pre-commit run ruff --all-files
```

### 3. Ruff Configuration (pyproject.toml)

**파일**: `pyproject.toml`

**설정**:
- **Line length**: 120자
- **Target Python**: 3.11+
- **활성화된 규칙**: pycodestyle, pyflakes, isort, pep8-naming, pyupgrade, bugbear 등
- **파일별 예외**: GUI 파일, 테스트 파일, 예제 등

**사용법**:
```bash
# 검사
ruff check .

# 자동 수정
ruff check --fix .

# 포맷팅
ruff format .
```

### 4. Pytest Configuration (pytest.ini, pyproject.toml)

**파일**: `pytest.ini`, `pyproject.toml`

**설정**:
- **Test markers**: unit, integration, gui, slow, performance 등
- **Coverage 자동 측정**: --cov 플래그 기본 활성화
- **Qt API**: PyQt5 지정
- **출력 형식**: HTML, XML, Terminal

**Test Markers**:
```python
@pytest.mark.unit        # 빠른 단위 테스트
@pytest.mark.integration # 통합 테스트
@pytest.mark.gui         # GUI 테스트
@pytest.mark.slow        # 느린 테스트 (>1s)
@pytest.mark.algorithm   # 알고리즘 테스트
```

**사용법**:
```bash
# 전체 테스트
pytest

# 특정 마커만 실행
pytest -m unit

# 느린 테스트 제외
pytest -m "not slow"

# Coverage와 함께
pytest --cov=. --cov-report=html
```

### 5. GitHub Actions Workflow (.github/workflows/test.yml)

**파일**: `.github/workflows/test.yml`

**기능**:
- **Python 버전**: 3.11, 3.12 매트릭스 테스트
- **Headless GUI 테스트**: Xvfb를 사용한 GUI 테스트
- **Coverage 측정**: 자동 커버리지 측정 및 리포트
- **Codecov 업로드**: coverage.xml을 Codecov에 자동 업로드
- **Artifact 업로드**: Coverage HTML 리포트 보관

**트리거**:
- main, develop 브랜치 push
- main 브랜치 Pull Request
- Manual dispatch

### 6. Development Dependencies (requirements-dev.txt)

**파일**: `requirements-dev.txt`

**포함된 도구**:
- pytest >= 8.4.0
- pytest-cov >= 7.0.0
- pytest-qt >= 4.5.0
- pytest-mock >= 3.14.0
- pytest-timeout >= 2.3.0
- coverage[toml] >= 7.10.0
- ruff >= 0.13.0
- pre-commit >= 4.0.0

**설치**:
```bash
pip install -r requirements-dev.txt
```

## 빠른 시작

### 개발 환경 설정

```bash
# 1. 의존성 설치
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 2. Pre-commit hooks 설치
pre-commit install

# 3. Pre-commit hooks 실행 (선택사항)
pre-commit run --all-files
```

### 코드 작성 워크플로우

```bash
# 1. 코드 작성
vim acc_core.py

# 2. 린팅 및 포맷팅
ruff check --fix .
ruff format .

# 3. 테스트 실행
pytest -v

# 4. Coverage 확인
pytest --cov=. --cov-report=html

# 5. 커밋 (pre-commit hooks 자동 실행)
git add .
git commit -m "feat: add new feature"
```

## 현재 상태

### 코드 품질 통계 (2025-11-16)

```
Ruff 검사 결과:
- 발견된 문제: 300개
- 자동 수정 가능: 237개
- 주요 문제:
  - 산술 연산자 주변 공백 누락 (105개)
  - f-string 플레이스홀더 누락 (48개)
  - 정렬되지 않은 import (39개)
  - 사용되지 않는 import (23개)
```

### 다음 단계

1. **자동 수정 실행**:
   ```bash
   ruff check --fix .
   ruff format .
   ```

2. **수동 수정 필요한 항목**:
   - 사용되지 않는 변수 (8개)
   - 루프 제어 변수 미사용 (7개)
   - bare except 구문 (4개)
   - 모호한 변수명 (2개)

3. **테스트 작성**:
   - 현재 테스트 커버리지 측정 필요
   - 목표: 핵심 알고리즘 70%+, 전체 50%+

## 문서

- **개발 가이드**: [docs/development.md](docs/development.md)
- **빌드 가이드**: [BUILDING.md](BUILDING.md)
- **README**: [README.md](README.md)

## Modan2 프로젝트와의 비교

ACC 프로젝트는 Modan2 프로젝트와 동일한 수준의 QA 설정을 갖추게 되었습니다:

| 기능 | Modan2 | ACC |
|------|--------|-----|
| Code Coverage (.coveragerc) | ✅ | ✅ |
| Pre-commit Hooks | ✅ | ✅ |
| Ruff Linter | ✅ | ✅ |
| Pytest Configuration | ✅ | ✅ |
| GitHub Actions CI/CD | ✅ | ✅ |
| Codecov Integration | ✅ | ✅ |
| Test Markers | ✅ | ✅ |
| Development Documentation | ✅ | ✅ |

## 참고 자료

- [Ruff Documentation](https://docs.astral.sh/ruff/)
- [pytest Documentation](https://docs.pytest.org/)
- [coverage.py Documentation](https://coverage.readthedocs.io/)
- [pre-commit Documentation](https://pre-commit.com/)
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Codecov Documentation](https://docs.codecov.com/)
