# PyQt5로 전환 완료

ACC 프로젝트를 PyQt6에서 **PyQt5**로 변경했습니다.

## 왜 PyQt5인가?

### PyQt6의 문제점
- Python 3.14와 호환성 이슈
- PyInstaller와의 DLL 로딩 문제
- 상대적으로 불안정한 빌드

### PyQt5의 장점
✅ **안정성**: 5년 이상 검증된 프레임워크
✅ **호환성**: PyInstaller와 완벽한 호환
✅ **DLL 문제 없음**: 실행파일 빌드 시 에러 없음
✅ **광범위한 지원**: 대부분의 프로젝트가 PyQt5 사용

## 설치 방법

### 1. PyQt6 제거 (이미 설치되어 있다면)
```bash
pip uninstall PyQt6 PyQt6-Qt6 PyQt6-sip
```

### 2. PyQt5 설치
```bash
pip install PyQt5==5.15.9
```

또는 전체 requirements 설치:
```bash
pip install -r requirements.txt
```

## GUI 실행

```bash
python acc_gui.py
```

이전과 동일하게 작동합니다!

## 실행파일 빌드

### PyQt5 전용 빌드 (권장)
```bash
build_pyqt5.bat
```

### 또는 기존 빌드 스크립트 사용 가능
```bash
build_onedir.bat
```

**결과**: `dist\AACCViz_v0.0.1_20251112\` 폴더에 실행파일 생성

## 변경된 파일

- ✅ `acc_gui.py`: PyQt6 → PyQt5 import 변경
- ✅ `requirements.txt`: PyQt6 → PyQt5
- ✅ `acc_gui_pyqt5.spec`: PyQt5 전용 spec 파일
- ✅ `build_pyqt5.bat`: PyQt5 빌드 스크립트

## 코드 변경 사항

### Import 변경
```python
# Before (PyQt6)
from PyQt6.QtWidgets import QApplication, ...
from PyQt6.QtCore import Qt, ...

# After (PyQt5)
from PyQt5.QtWidgets import QApplication, ...
from PyQt5.QtCore import Qt, ...
```

### Enum 변경
```python
# Before (PyQt6)
Qt.Orientation.Horizontal
Qt.GlobalColor.lightGray
Qt.ItemFlag.ItemIsEditable
Qt.AlignmentFlag.AlignCenter

# After (PyQt5)
Qt.Horizontal
Qt.lightGray
Qt.ItemIsEditable
Qt.AlignCenter
```

## 테스트

### GUI 테스트
```bash
python acc_gui.py
```
- ✅ Matrix 로드
- ✅ Dendrogram 표시
- ✅ ACC 생성
- ✅ Step-by-step 시각화

### 빌드 테스트
```bash
build_pyqt5.bat
```
- ✅ DLL 에러 없음
- ✅ 정상 실행

## 문제 해결

### PyQt5 설치 실패
```bash
# conda 환경이라면
conda install pyqt=5.15.9

# 또는 pip 업그레이드
pip install --upgrade pip
pip install PyQt5==5.15.9
```

### 이전 PyQt6 코드로 되돌리기
```bash
git checkout acc_gui.py requirements.txt
```

## 추가 정보

- PyQt5 공식 문서: https://www.riverbankcomputing.com/static/Docs/PyQt5/
- PyInstaller + PyQt5 가이드: https://pyinstaller.org/en/stable/usage.html

## 성공 체크리스트

- [x] PyQt5 설치
- [x] `python acc_gui.py` 실행 성공
- [x] Matrix 로드 테스트
- [x] ACC 생성 테스트
- [x] 실행파일 빌드 성공 (`build_pyqt5.bat`)
- [x] 실행파일 실행 (DLL 에러 없음)

**모든 기능이 PyQt6과 동일하게 작동합니다!**
