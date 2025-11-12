# PyQt5 실행 문제 해결

## 현상
- `python acc_gui.py` 실행 시 창이 안 열리고 바로 종료됨
- Segmentation fault 발생

## 가능한 원인

### 1. WSL에서 실행 중 (X11 디스플레이 없음)
WSL에서는 GUI를 실행하려면 X11 서버가 필요합니다.

**해결방법**: **Windows 네이티브 Python에서 실행**
```cmd
# Windows PowerShell 또는 CMD에서
cd D:\projects\ACC
python acc_gui.py
```

### 2. PyQt5 플랫폼 플러그인 문제

**해결방법**: QT 플랫폼 플러그인 확인
```bash
python -c "from PyQt5.QtCore import QLibraryInfo; print(QLibraryInfo.location(QLibraryInfo.PluginsPath))"
```

### 3. 환경 변수 설정 필요

**해결방법**: QT_QPA_PLATFORM 설정
```bash
# Windows CMD/PowerShell
set QT_QPA_PLATFORM=windows
python acc_gui.py
```

### 4. PyQt5 재설치

**해결방법**: 깨끗하게 재설치
```bash
pip uninstall PyQt5 PyQt5-Qt5 PyQt5-sip
pip install PyQt5==5.15.9
```

## 빠른 테스트

### 1단계: 간단한 테스트 실행
```bash
python test_pyqt5.py
```

이 스크립트는 단계별로 어디서 문제가 발생하는지 보여줍니다.

### 2단계: 플랫폼 확인
```bash
python -c "from PyQt5.QtWidgets import QApplication; import sys; app = QApplication(sys.argv); print('Platform:', app.platformName())"
```

### 3단계: 전체 환경 확인
```bash
python -c "import PyQt5; print('PyQt5 version:', PyQt5.QtCore.PYQT_VERSION_STR); print('Qt version:', PyQt5.QtCore.QT_VERSION_STR)"
```

## 권장 해결 순서

1. **Windows 네이티브 환경에서 실행** (가장 확실)
   ```cmd
   # Windows PowerShell/CMD
   cd D:\projects\ACC
   python acc_gui.py
   ```

2. WSL에서 꼭 실행해야 한다면:
   - WSLg 사용 (Windows 11)
   - VcXsrv 또는 X410 설치
   - DISPLAY 환경 변수 설정

## 현재 환경 확인

### Python 위치 확인
```bash
which python
python --version
```

- `/usr/bin/python` → Linux Python (WSL)
- `/c/Users/.../python.exe` 또는 `/mnt/c/...` → Windows Python

### Conda 환경 확인
```bash
conda info --envs
```

## 최종 권장 사항

**Windows에서 직접 실행하세요:**

```powershell
# Windows PowerShell 열기
cd D:\projects\ACC

# 가상환경 활성화 (conda 사용 중이라면)
conda activate ACC

# GUI 실행
python acc_gui.py
```

이렇게 하면 X11 문제 없이 네이티브 Windows GUI로 실행됩니다.
