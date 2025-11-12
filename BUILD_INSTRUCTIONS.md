# ACC Visualization 실행파일 빌드 가이드

## 문제: PyQt6 DLL 로드 실패

```
ImportError: DLL load failed while importing QtWidgets: 지정된 프로시저를 찾을 수 없습니다.
```

이 에러는 PyInstaller가 PyQt6의 필요한 DLL들을 제대로 포함하지 못할 때 발생합니다.

## 해결 방법

### 방법 1: .spec 파일 사용 (권장)

**1단계: 빌드**
```bash
# onefile 버전 (단일 .exe 파일)
pyinstaller --clean acc_gui.spec

# 또는 bat 파일 실행
build_with_spec.bat
```

**2단계: 테스트**
```
dist/AACCViz_v0.0.1_20251112.exe
```

### 방법 2: onedir 버전으로 먼저 테스트

문제가 계속되면 onedir 버전으로 먼저 테스트:

```bash
pyinstaller --clean acc_gui_onedir.spec
```

결과: `dist/AACCViz_v0.0.1_20251112/` 폴더에 실행파일과 DLL들이 생성됨

**장점**:
- DLL 문제 디버깅이 쉬움
- 빌드 속도가 빠름
- 실행 속도가 빠름 (압축 해제 불필요)

**단점**:
- 배포 시 폴더 전체를 압축해야 함

### 방법 3: 콘솔 창 켜서 디버깅

에러 메시지를 보려면 spec 파일에서 `console=True`로 변경:

```python
exe = EXE(
    ...
    console=True,  # 콘솔 창 표시
    ...
)
```

## 추가 해결 방법

### 1. PyQt6 재설치

```bash
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
pip install PyQt6==6.5.0  # 안정 버전 사용
```

### 2. PyInstaller 업데이트

```bash
pip install --upgrade pyinstaller
```

### 3. 가상환경에서 Clean Build

```bash
# 가상환경 생성
python -m venv venv

# 가상환경 활성화
venv\Scripts\activate

# 필수 패키지만 설치
pip install PyQt6==6.5.0 matplotlib scipy pandas numpy pyinstaller

# 빌드
pyinstaller --clean acc_gui.spec
```

### 4. 호환 버전 사용

테스트된 버전 조합:
```
PyQt6==6.5.0
matplotlib==3.7.1
scipy==1.11.0
pandas==2.0.3
numpy==1.24.3
pyinstaller==5.13.0
```

설치:
```bash
pip install -r requirements_frozen.txt
```

## Spec 파일 설명

### acc_gui.spec (onefile)
- **용도**: 배포용 단일 실행파일
- **장점**: 배포 간편
- **단점**: 느린 시작 속도, 디버깅 어려움

### acc_gui_onedir.spec (onedir)
- **용도**: 개발/디버깅용
- **장점**: 빠른 시작, 쉬운 디버깅
- **단점**: 많은 파일

## 빌드 후 체크리스트

✅ dist 폴더에 실행파일 생성 확인
✅ 실행 시 GUI가 정상적으로 표시되는지 확인
✅ CSV 파일 로드 기능 테스트
✅ Generate ACC 버튼 기능 테스트
✅ Dendrogram 표시 테스트
✅ 다른 PC에서 테스트 (개발 환경이 없는 PC)

## 문제 해결 팁

1. **여전히 DLL 에러 발생**:
   - onedir 버전으로 빌드해보기
   - console=True로 설정하여 전체 에러 메시지 확인

2. **빈 화면만 표시**:
   - matplotlib 백엔드 문제일 수 있음
   - spec 파일의 hiddenimports에 `matplotlib.backends.backend_qt5agg` 추가 확인

3. **CSV 로드 안됨**:
   - pandas 관련 hiddenimports 추가
   - datas에 샘플 CSV 파일 포함

4. **실행파일 크기가 너무 큼 (>100MB)**:
   - 정상입니다. PyQt6 + matplotlib + scipy 포함 시 보통 80-120MB

## UPX 압축 (선택사항)

실행파일 크기를 줄이려면:

1. UPX 다운로드: https://upx.github.io/
2. upx.exe를 PATH에 추가
3. spec 파일에서 `upx=True` 유지
4. 재빌드

압축률: 약 30-40% 크기 감소

## 최종 권장 빌드 명령

```bash
# 1. 이전 빌드 클리어
rmdir /s /q build dist

# 2. onedir로 먼저 테스트
pyinstaller --clean acc_gui_onedir.spec

# 3. 테스트 성공 후 onefile 빌드
pyinstaller --clean acc_gui.spec
```
