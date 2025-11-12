========================================
ACC 실행파일 빌드 - DLL 에러 해결 가이드
========================================

현재 에러:
  ImportError: DLL load failed while importing QtWidgets

이 에러는 PyQt6와 PyInstaller 호환성 문제입니다.


■ 해결 방법 (순서대로 시도)
========================================

방법 1: 개선된 spec 파일로 다시 빌드
----------------------------------------
spec 파일을 업데이트했으니 다시 시도하세요:

  build_onedir.bat

→ 성공하면 dist\AACCViz_v0.0.1_20251112\ 폴더에 실행파일 생성


방법 2: PyQt6 버전 다운그레이드
----------------------------------------
PyQt6 6.5.0 (안정 버전)으로 다운그레이드:

  fix_pyqt6.bat

완료 후:
  build_onedir.bat


방법 3: 디버그 모드로 에러 확인
----------------------------------------
콘솔 창이 있는 디버그 버전 빌드:

  build_debug.bat

실행 후 콘솔에 나타나는 전체 에러 메시지 확인


방법 4: 가상환경에서 클린 빌드
----------------------------------------
1. 새 가상환경 생성:
   python -m venv clean_env
   clean_env\Scripts\activate

2. 필수 패키지만 설치:
   pip install PyQt6==6.5.0 matplotlib scipy pandas pyinstaller

3. 빌드:
   build_onedir.bat


방법 5: PySide6로 전환 (최후의 수단)
----------------------------------------
PyQt6 대신 PySide6 사용 (코드 수정 필요)


■ 빌드 파일 설명
========================================

build_onedir.bat    → OneDir 버전 (권장, DLL 문제 적음)
build_onefile.bat   → OneFile 버전 (단일 .exe)
build_debug.bat     → 디버그 버전 (콘솔 창 표시)
fix_pyqt6.bat       → PyQt6 버전 수정

acc_gui_onedir.spec → OneDir 빌드 설정
acc_gui.spec        → OneFile 빌드 설정
acc_gui_debug.spec  → 디버그 빌드 설정


■ 권장 빌드 순서
========================================

1차 시도: build_onedir.bat
  ↓ 실패시
2차 시도: fix_pyqt6.bat → build_onedir.bat
  ↓ 실패시
3차 시도: build_debug.bat (에러 메시지 확인)
  ↓ 실패시
4차 시도: 가상환경에서 클린 빌드


■ 테스트된 패키지 버전
========================================
PyQt6==6.5.0
matplotlib==3.7.1
scipy==1.11.0
pandas==2.0.3
numpy==1.24.3
pyinstaller==5.13.0

설치:
  pip install -r requirements_frozen.txt


■ 추가 정보
========================================
- BUILD_INSTRUCTIONS.md: 상세 가이드
- 문제가 계속되면 이슈 등록:
  https://github.com/pyinstaller/pyinstaller/issues
