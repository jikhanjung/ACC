# Legacy Tests

이 디렉토리에는 구버전 테스트 파일들이 보관되어 있습니다.

## ⚠️ 주의사항

이 디렉토리의 파일들은 **참고용**으로만 보관되며, 더 이상 활발히 유지보수되지 않습니다.

새로운 pytest 기반 테스트 스위트는 `tests/unit/` 및 `tests/integration/` 디렉토리에 있습니다.

## 파일 분류

### 알고리즘 테스트 (통합됨)
이 파일들의 기능은 새 테스트 스위트에 통합되었습니다:

- `test_integration.py` → `tests/integration/test_pipeline.py`로 통합
- `test_acc_steps.py` → step-by-step 테스트는 통합 테스트에 포함
- `test_linkage_abc.py` → `tests/unit/test_acc_utils.py`의 linkage 테스트로 통합
- `test_nested_structure.py` → 구조 테스트는 core 테스트에 통합
- `test_merge_radii.py` → 병합 테스트는 core 테스트에 포함

### GUI 테스트 (미구현)
향후 pytest-qt를 사용하여 재구현 예정:

- `test_area_editor.py` - Area 편집 다이얼로그 테스트
- `test_empty_area_list.py` - 빈 area list 처리 테스트
- `test_dialog.py` - 기본 다이얼로그 테스트
- `test_gui_simple.py` - 간단한 GUI 테스트
- `test_step_dendro.py` - Dendrogram 단계 시각화 테스트

### 환경/의존성 테스트 (더 이상 불필요)
개발 초기 환경 확인용 테스트:

- `test_pyqt5.py` - PyQt5 import 테스트
- `test_matplotlib_qt5.py` - Matplotlib Qt5 백엔드 테스트
- `test_canvas_import.py` - Canvas import 테스트
- `test_clustering_steps.py` - Clustering manager 테스트
- `test_acc_with_log.py` - 로깅 기능 테스트

## 새 테스트 스위트 사용하기

현재 활발히 유지보수되는 테스트를 실행하려면:

```bash
# 전체 테스트 실행
python -m pytest tests/

# 단위 테스트만 실행
python -m pytest tests/unit/

# 통합 테스트만 실행
python -m pytest tests/integration/

# 커버리지 포함
python -m pytest tests/ --cov=. --cov-report=html
```

자세한 내용은 [테스트 계획 문서](../../devlog/20251115_P28_테스트_체계화_계획.md)를 참고하세요.

## 참고

이 파일들은 git 히스토리에 보존되어 있으며, 필요시 언제든지 복원할 수 있습니다.
