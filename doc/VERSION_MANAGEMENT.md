# Version Management Guide

ACC 프로젝트의 버전 관리 가이드입니다.

## 개요

이 프로젝트는 [Semantic Versioning 2.0.0](https://semver.org/)을 따릅니다.

### 버전 형식

```
MAJOR.MINOR.PATCH[-PRERELEASE]
```

- **MAJOR**: 호환되지 않는 API 변경
- **MINOR**: 하위 호환성을 유지하는 기능 추가
- **PATCH**: 하위 호환성을 유지하는 버그 수정
- **PRERELEASE**: 선택적 pre-release 식별자 (alpha, beta, rc)

### 예제

- `0.0.3` - 안정 버전
- `0.1.0-alpha.1` - Alpha 프리릴리스
- `0.1.0-beta.2` - Beta 프리릴리스
- `1.0.0-rc.1` - Release Candidate

## 버전 관리 도구

### manage_version.py

프로젝트 루트에 있는 `manage_version.py` 스크립트를 사용하여 버전을 관리합니다.

```bash
python manage_version.py <command> [token]
```

## 사용법

### 1. 기본 버전 증가

#### Patch 버전 증가 (버그 수정)

```bash
python manage_version.py patch
# 0.0.3 → 0.0.4
```

#### Minor 버전 증가 (새 기능 추가)

```bash
python manage_version.py minor
# 0.0.3 → 0.1.0
```

#### Major 버전 증가 (호환되지 않는 변경)

```bash
python manage_version.py major
# 0.0.3 → 1.0.0
```

### 2. Pre-release 버전

#### Pre-release 시작

```bash
# Alpha 시작
python manage_version.py preminor
# 0.0.3 → 0.1.0-alpha.1

# Beta 시작
python manage_version.py preminor beta
# 0.0.3 → 0.1.0-beta.1

# Release Candidate 시작
python manage_version.py prepatch rc
# 0.0.3 → 0.0.4-rc.1
```

#### Pre-release 번호 증가

```bash
python manage_version.py prerelease
# 0.1.0-alpha.1 → 0.1.0-alpha.2
# 0.1.0-beta.1 → 0.1.0-beta.2
```

#### Pre-release 단계 전환

```bash
python manage_version.py stage beta
# 0.1.0-alpha.2 → 0.1.0-beta.1

python manage_version.py stage rc
# 0.1.0-beta.3 → 0.1.0-rc.1
```

#### Pre-release를 안정 버전으로 전환

```bash
python manage_version.py release
# 0.1.0-rc.1 → 0.1.0
```

## 버전 증가 워크플로우

### 일반적인 개발 사이클

```bash
# 1. 새 기능 개발 시작 (minor 버전)
python manage_version.py preminor alpha
# 0.0.3 → 0.1.0-alpha.1

# 2. Alpha 테스트 중 추가 개발
python manage_version.py prerelease
# 0.1.0-alpha.1 → 0.1.0-alpha.2

# 3. Beta 단계로 전환
python manage_version.py stage beta
# 0.1.0-alpha.2 → 0.1.0-beta.1

# 4. Beta 테스트 중 수정
python manage_version.py prerelease
# 0.1.0-beta.1 → 0.1.0-beta.2

# 5. Release Candidate
python manage_version.py stage rc
# 0.1.0-beta.2 → 0.1.0-rc.1

# 6. 최종 릴리스
python manage_version.py release
# 0.1.0-rc.1 → 0.1.0
```

### 핫픽스 사이클

```bash
# 긴급 버그 수정
python manage_version.py patch
# 0.1.0 → 0.1.1
```

## 대화형 프로세스

`manage_version.py`는 대화형으로 작동합니다:

```bash
$ python manage_version.py minor

Current version: 0.0.3
New version will be: 0.1.0
Update version to 0.1.0? (y/N): y
✅ Version updated to 0.1.0

Update CHANGELOG.md? (y/N): y
✅ CHANGELOG.md updated
⚠️  Please update the changelog entries before committing

Create git commit? (y/N): y
✅ Git commit created: chore: bump version to 0.1.0

Create git tag? (y/N): y
✅ Git tag created: v0.1.0
   To push: git push origin v0.1.0

🎉 Version 0.1.0 is ready!

Next steps:
1. Manually edit CHANGELOG.md to add details for this version.
2. Push your changes: git push
3. Push the tag: git push origin v0.1.0
```

## 자동 업데이트되는 파일

버전 증가 시 자동으로 업데이트되는 파일:

1. **`version.py`** - `__version__` 변수
2. **`CHANGELOG.md`** - 새 버전 섹션 추가 (선택 사항)

수동으로 업데이트해야 하는 파일:

1. **`pyproject.toml`** - `version` 필드
2. **`README.md`** - "프로젝트 상태" 섹션

## CHANGELOG.md 관리

### 자동 생성된 템플릿

```markdown
## [0.1.0] - 2025-11-16

### Added
-

### Changed
-

### Fixed
-
```

### 수동 작성 예제

```markdown
## [0.1.0] - 2025-11-16

### Added
- 새로운 시각화 옵션 추가
- CSV 내보내기 기능

### Changed
- GUI 레이아웃 개선
- 성능 최적화

### Fixed
- Matrix 로딩 버그 수정
- 메모리 누수 해결
```

## Git 태그

버전 태그는 `v` 접두사를 사용합니다:

```bash
v0.0.3
v0.1.0
v0.1.0-alpha.1
v1.0.0
```

### 태그 푸시

```bash
# 특정 태그 푸시
git push origin v0.1.0

# 모든 태그 푸시
git push --tags
```

## GitHub Release

태그를 푸시하면 GitHub Actions가 자동으로:

1. 테스트 실행
2. 크로스 플랫폼 빌드 (Windows, macOS, Linux)
3. GitHub Release 생성
4. 빌드된 실행 파일 업로드

## 버전 확인

### Python에서

```python
from version import __version__, __version_info__

print(__version__)        # "0.0.3"
print(__version_info__)   # (0, 0, 3)
```

### 명령줄에서

```bash
python -c "from version import __version__; print(__version__)"
```

## 트러블슈팅

### semver 라이브러리 누락

```bash
pip install semver
```

### version.py 백업 파일

버전 업데이트 중 오류가 발생하면 `version.py.bak` 파일이 생성됩니다.
오류 해결 후 수동으로 복원할 수 있습니다.

### Git 작업 디렉토리가 깨끗하지 않음

```bash
$ python manage_version.py patch
⚠️  Warning: You have uncommitted changes
Continue anyway? (y/N):
```

변경사항을 먼저 커밋하거나 stash하는 것을 권장합니다.

## 모범 사례

### 1. 의미 있는 버전 증가

- **PATCH**: 버그 수정만
- **MINOR**: 새 기능 추가 (하위 호환)
- **MAJOR**: API 변경 (하위 호환 불가)

### 2. CHANGELOG 업데이트

버전을 올린 후 **반드시** CHANGELOG.md를 작성하세요:
- 사용자가 변경사항을 이해할 수 있도록
- 구체적이고 명확하게
- 카테고리별로 정리 (Added, Changed, Fixed)

### 3. Pre-release 사용

정식 릴리스 전에 pre-release 버전을 사용하세요:
- **Alpha**: 초기 개발, 불안정
- **Beta**: 기능 완성, 테스트 중
- **RC**: 릴리스 후보, 최종 검증

### 4. Git 태그

버전마다 Git 태그를 생성하세요:
- 특정 버전으로 쉽게 되돌아갈 수 있음
- GitHub Release 자동화 트리거

## 참고 자료

- [Semantic Versioning 2.0.0](https://semver.org/)
- [Keep a Changelog](https://keepachangelog.com/)
- [Python semver library](https://python-semver.readthedocs.io/)

## 예제 시나리오

### 시나리오 1: 버그 수정

```bash
# 현재: 0.0.3
python manage_version.py patch
# → 0.0.4

# CHANGELOG.md 업데이트
## [0.0.4] - 2025-11-17
### Fixed
- CSV 로딩 버그 수정
- GUI 충돌 문제 해결
```

### 시나리오 2: 새 기능 개발

```bash
# 현재: 0.0.4
python manage_version.py preminor alpha
# → 0.1.0-alpha.1

# 개발 중...
python manage_version.py prerelease
# → 0.1.0-alpha.2

# Beta 전환
python manage_version.py stage beta
# → 0.1.0-beta.1

# 릴리스
python manage_version.py release
# → 0.1.0
```

### 시나리오 3: Major 업데이트

```bash
# 현재: 0.9.5
python manage_version.py premajor beta
# → 1.0.0-beta.1

# 테스트 후 릴리스
python manage_version.py release
# → 1.0.0
```
