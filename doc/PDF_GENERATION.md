# PDF Generation Guide

이 문서는 Markdown 사용자 매뉴얼을 PDF로 자동 변환하는 방법을 설명합니다.

## 개요

`doc/USER_MANUAL.md`를 `doc/ACC_USER_MANUAL.pdf`로 자동 변환할 수 있습니다.

### 자동화 방식

1. **로컬 생성**: 스크립트 또는 Makefile 사용
2. **CI/CD 자동화**: GitHub Actions로 자동 생성 및 커밋

## 로컬에서 PDF 생성

### 방법 1: Makefile 사용 (권장)

```bash
# PDF 생성
make pdf

# 모든 문서 빌드 (PDF + Sphinx)
make docs
```

### 방법 2: Python 스크립트 직접 실행

```bash
# 기본 실행 (xelatex 엔진 사용 - 한글 지원)
python scripts/generate_pdf.py
```

커스텀 옵션:
```bash
python scripts/generate_pdf.py \
  --input doc/USER_MANUAL.md \
  --output doc/ACC_USER_MANUAL.pdf \
  --engine xelatex
```

## 필수 요구사항

### 1. Python 패키지

```bash
pip install pypandoc
```

### 2. Pandoc 설치

**자동 설치 (권장)**:
```bash
python -c "import pypandoc; pypandoc.download_pandoc()"
```

**수동 설치**:
- **Windows**: https://pandoc.org/installing.html 에서 설치 프로그램 다운로드
- **macOS**: `brew install pandoc`
- **Linux**: `sudo apt-get install pandoc`

### 3. LaTeX 설치 (PDF 엔진)

PDF 생성을 위해 XeLaTeX이 포함된 LaTeX이 필요합니다 (한글 지원):

**Windows**:
```bash
# MiKTeX 설치 (권장)
# https://miktex.org/download
# XeLaTeX 포함, 한글 폰트 "Malgun Gothic" 필요
```

**macOS**:
```bash
brew install --cask mactex-no-gui
# 또는 전체 버전: brew install --cask mactex
# XeLaTeX 자동 포함
```

**Linux (Ubuntu/Debian)**:
```bash
sudo apt-get update
sudo apt-get install -y \
  texlive-xetex \
  texlive-latex-base \
  texlive-fonts-recommended \
  texlive-fonts-extra \
  texlive-latex-extra \
  fonts-noto-cjk
```

## 스크립트 옵션

### 기본 사용법

```bash
python scripts/generate_pdf.py
```

### 커스텀 입력/출력

```bash
python scripts/generate_pdf.py \
  --input doc/custom.md \
  --output output/custom.pdf
```

### PDF 엔진 선택

```bash
# xelatex (기본값, 한글 지원 권장)
python scripts/generate_pdf.py --engine xelatex

# pdflatex (영문 전용)
python scripts/generate_pdf.py --engine pdflatex

# wkhtmltopdf (HTML 기반, 대안)
python scripts/generate_pdf.py --engine wkhtmltopdf
```

**주의**: 한글 문서는 반드시 `xelatex` 엔진을 사용해야 합니다.

## PDF 생성 기능

생성된 PDF에는 다음이 포함됩니다:

- ✅ **목차 (Table of Contents)** - 자동 생성
- ✅ **섹션 번호** - 자동 번호 매기기
- ✅ **이미지** - 모든 이미지 포함
- ✅ **코드 하이라이팅** - 구문 강조 표시
- ✅ **링크** - 클릭 가능한 하이퍼링크
- ✅ **포맷팅** - 표, 리스트, 강조 등

### PDF 설정

`scripts/generate_pdf.py`에서 다음을 커스터마이징할 수 있습니다:

- 여백 (margin)
- 폰트 크기 (fontsize)
- 링크 색상 (linkcolor)
- 목차 깊이 (toc-depth)
- 코드 하이라이팅 스타일 (highlight-style)

## GitHub Actions 자동화

### 트리거

PDF는 다음 경우에 자동 생성됩니다:

1. **Push to main**: `doc/USER_MANUAL.md` 변경 시
2. **Pull Request**: 미리보기 PDF 생성
3. **Manual**: GitHub Actions UI에서 수동 실행

### 워크플로우

`.github/workflows/generate_docs.yml`:

```yaml
on:
  push:
    branches: [ main ]
    paths:
      - 'doc/USER_MANUAL.md'
      - 'doc/images/**'
```

### 자동 커밋

`main` 브랜치에 push하면:
1. PDF 자동 생성
2. 변경사항이 있으면 자동 커밋
3. `[skip ci]` 태그로 무한 루프 방지

### 아티팩트

Pull Request의 경우:
- PDF가 아티팩트로 업로드됨
- GitHub Actions UI에서 다운로드 가능
- 30일간 보관

## 트러블슈팅

### Pandoc not found

**문제**: `pandoc: command not found`

**해결**:
```bash
# Python으로 자동 다운로드
python -c "import pypandoc; pypandoc.download_pandoc()"

# 또는 시스템 패키지 관리자 사용
# macOS: brew install pandoc
# Linux: sudo apt-get install pandoc
```

### LaTeX errors

**문제**: `! LaTeX Error: File 'xxx.sty' not found`

**해결**:
```bash
# Linux
sudo apt-get install texlive-latex-extra

# macOS
brew install --cask mactex

# Windows: MiKTeX에서 자동으로 패키지 설치 옵션 활성화
```

### 이미지가 PDF에 표시되지 않음

**문제**: 상대 경로 이미지가 보이지 않음

**해결**:
스크립트는 자동으로 `doc/` 디렉토리로 이동하여 상대 경로를 처리합니다.
USER_MANUAL.md에서 이미지 경로는 다음과 같이 작성해야 합니다:

```markdown
✅ 올바름: ![설명](images/screenshot.png)
❌ 잘못됨: ![설명](doc/images/screenshot.png)
❌ 잘못됨: ![설명](../images/screenshot.png)
```

### 한글 폰트 문제

**문제**: 한글이 깨지거나 표시되지 않음

**해결**:
```bash
# 1. XeLaTeX 엔진 사용 (기본값)
python scripts/generate_pdf.py --engine xelatex

# 2. Windows: Malgun Gothic 폰트 확인
# 제어판 > 글꼴에서 "맑은 고딕" 설치 확인

# 3. Linux: Noto CJK 폰트 설치
sudo apt-get install fonts-noto-cjk

# 4. macOS: 시스템 한글 폰트 자동 사용
```

스크립트의 폰트 설정 (`scripts/generate_pdf.py`):
```python
# Windows: Malgun Gothic (맑은 고딕)
"-V", "CJKmainfont=Malgun Gothic"

# Linux/macOS에서 다른 폰트 사용 시 수정:
# "-V", "CJKmainfont=Noto Sans CJK KR"
```

## 대안 방법

### 방법 1: md-to-pdf (Node.js)

```bash
npm install -g md-to-pdf
md-to-pdf doc/USER_MANUAL.md
```

### 방법 2: grip (GitHub Markdown)

```bash
pip install grip
grip doc/USER_MANUAL.md --export doc/USER_MANUAL.html
# 브라우저에서 HTML을 PDF로 인쇄
```

### 방법 3: VSCode 확장

- **Markdown PDF** 확장 설치
- Markdown 파일 열기
- `Ctrl+Shift+P` → "Markdown PDF: Export (pdf)"

## 참고 자료

- **Pandoc 문서**: https://pandoc.org/MANUAL.html
- **pypandoc**: https://github.com/JessicaTegner/pypandoc
- **LaTeX 설치**: https://www.latex-project.org/get/
- **GitHub Actions**: https://docs.github.com/en/actions

## 개발자 노트

### 스크립트 구조

`scripts/generate_pdf.py`:
- Pandoc 설치 확인 및 자동 다운로드
- PDF 변환 옵션 설정
- 에러 처리 및 문제 해결 가이드

### 향후 개선 사항

- [ ] PDF 테마/템플릿 커스터마이징
- [ ] 여러 언어 버전 지원
- [ ] PDF 메타데이터 (저자, 제목, 키워드) 설정
- [ ] 워터마크 또는 헤더/푸터 추가
- [ ] PDF/A 표준 준수 (장기 보관용)
