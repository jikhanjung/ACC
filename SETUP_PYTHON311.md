# Python 3.11 환경 설정 가이드

## 문제 원인
Python 3.14는 너무 최신 버전이라 matplotlib와 PyQt5가 제대로 컴파일된 바이너리가 없습니다.
이로 인해 `FigureCanvasQTAgg` 임포트 시 충돌이 발생합니다.

## 해결 방법: Python 3.11 환경 사용

### 방법 1: 자동 설정 (권장)

```powershell
.\setup_py311_env.bat
```

### 방법 2: conda environment.yml 사용

```powershell
conda env create -f environment.yml
conda activate ACC_py311
```

### 방법 3: 수동 설정

```powershell
# 1. 새 환경 생성
conda create -n ACC_py311 python=3.11 -y

# 2. 환경 활성화
conda activate ACC_py311

# 3. 패키지 설치
conda install -y pyqt=5.15 scipy pandas "numpy>=2.0"
pip install PyQt5-sip==12.12.2 "matplotlib>=3.9.0" pyinstaller==5.13.0
```

## 환경 활성화 및 테스트

```powershell
# 환경 활성화
conda activate ACC_py311

# 프로젝트 디렉토리로 이동
cd D:\projects\ACC

# matplotlib + PyQt5 테스트
python test_canvas_import.py

# GUI 실행
python acc_gui.py
```

## 환경 관리

### 환경 목록 보기
```powershell
conda env list
```

### 환경 삭제 (필요시)
```powershell
conda env remove -n ACC_py311
```

### 기존 ACC 환경과 새 환경 비교
- `ACC` (Python 3.14): matplotlib 바이너리 호환성 문제
- `ACC_py311` (Python 3.11): 모든 패키지 안정적으로 작동

## PyInstaller 빌드

Python 3.11 환경에서 빌드:
```powershell
conda activate ACC_py311
cd D:\projects\ACC
pyinstaller --name "ACCViz_v0.0.1_py311" --onefile --noconsole acc_gui.py
```

## 권장 패키지 버전

- Python: 3.11
- PyQt5: 5.15.9
- PyQt5-sip: 12.12.2 (PyQt5 5.15.9 호환)
- Qt5: 5.15.2
- matplotlib: 3.9.0+ (NumPy 2.x 호환)
- scipy: 1.11.0+
- pandas: 2.0.0+
- numpy: 2.0.0+
- pyinstaller: 5.13.0+

**중요 호환성 정보:**
- NumPy 2.x를 사용하려면 matplotlib 3.9.0 이상이 필요합니다.
- PyQt5 5.15.9는 PyQt5-sip 12.12.2와 가장 호환성이 좋습니다 (DeprecationWarning 없음).
