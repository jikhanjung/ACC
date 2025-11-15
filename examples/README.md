# ACC Examples

이 디렉토리에는 ACC 알고리즘의 사용 예제가 포함되어 있습니다.

## 파일 설명

### simple_abc_example.py
3개 영역(A, B, C)을 사용한 간단한 ACC 예제입니다.
- 기본적인 similarity matrix 생성
- ACC 알고리즘 실행
- 결과 확인

**실행 방법:**
```bash
python examples/simple_abc_example.py
```

### concentric_circles_example.py
동심원 구조를 검증하는 예제입니다.
- 동심원 관계의 클러스터 생성
- 원의 중심과 반지름 계산
- 기하학적 관계 검증

**실행 방법:**
```bash
python examples/concentric_circles_example.py
```

### verify_6_areas.py
6개 영역(J, T, Y, N, O, Q)을 사용한 전체 검증 예제입니다.
- Sample data를 사용한 실제 데이터 검증
- 완전한 ACC 파이프라인 실행
- 결과 시각화 및 검증

**실행 방법:**
```bash
python examples/verify_6_areas.py
```

## 학습 순서

1. **simple_abc_example.py** - 가장 간단한 3-영역 예제로 시작
2. **concentric_circles_example.py** - 동심원 구조 이해
3. **verify_6_areas.py** - 실제 데이터로 전체 파이프라인 이해

## 추가 정보

더 자세한 사용법은 다음을 참고하세요:
- [USER_MANUAL.md](../docs/index.rst) - 전체 사용자 매뉴얼
- [CLAUDE.md](../CLAUDE.md) - 알고리즘 상세 설명
- [tests/](../tests/) - 단위/통합 테스트 코드
