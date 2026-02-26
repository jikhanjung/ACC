ACC 사용자 매뉴얼
==================

**ACC (Area Affinity in Concentric Circles)** - 계층적 클러스터 관계 시각화 도구

버전: 0.0.5

최종 업데이트: 2026-02-26

환영합니다
----------

ACC는 계층적 클러스터링 결과를 **동심원 기반 원형 다이어그램**으로 시각화하는 Python 애플리케이션입니다.
두 종류의 유사도 정보(Local와 Global)를 결합하여 영역(area) 간의 친화도(affinity) 관계를 직관적으로 표현합니다.

주요 특징
----------

* **5패널 통합 인터페이스**: Data | Similarity | Dendrogram | ACC | NMDS
* **Raw Data 입력**: Presence/Absence Matrix를 통한 원시 데이터 직접 입력
* **Similarity Index 4종**: Jaccard, Ochiai, Raup-Crick, Simpson 자동 계산
* **NMDS 분석**: 2D/3D Non-metric Multidimensional Scaling 시각화
* **이중 유사도 통합**: Local와 Global 유사도를 동시에 고려
* **대화형 시각화**: 단계별 클러스터링 과정 재생 가능
* **동심원 표현**: 클러스터 계층을 동심원으로 직관적 표현
* **인터랙티브 조정**: Branch swap으로 레이아웃 최적화
* **Undo/Redo**: 모든 데이터 편집 작업의 실행 취소/다시 실행 (Ctrl+Z/Ctrl+Y)
* **프로젝트 파일**: .accdata 형식으로 전체 프로젝트 저장/로드
* **패널 토글**: View 메뉴에서 필요한 패널만 선택적 표시

사용 사례
---------

* 지역/그룹 간 유사도 관계 분석
* 계층적 클러스터링 결과 시각화
* 생태학적/지리적 데이터 분석
* 계통발생학적 관계 탐색

목차
----

.. toctree::
   :maxdepth: 2
   :caption: 목차:

   installation
   getting_started
   basic_usage
   advanced_features
   data_format
   visualization
   troubleshooting
   faq
   changelog

빠른 시작
----------

설치
~~~~

1. GitHub Releases 페이지에서 최신 버전의 ``ACC_v[버전].exe`` 다운로드
2. 원하는 폴더에 저장 후 실행

기본 사용법
~~~~~~~~~~~

**방법 A: Raw Data에서 시작** (권장)

1. **Data 패널**: Presence/Absence Matrix 입력 (또는 CSV 가져오기)
2. **Similarity Index 선택**: Jaccard, Ochiai, Raup-Crick, Simpson 중 선택
3. **Calculate Similarity**: 유사도 행렬 자동 계산
4. **ACC/NMDS 생성**: 시각화 버튼 클릭

**방법 B: Similarity Matrix에서 시작**

1. **Local Matrix 로드**: CSV 파일 선택 → Dendrogram 자동 표시
2. **Global Matrix 로드**: CSV 파일 선택 → Dendrogram 자동 표시
3. **ACC 생성**: "Generate ACC Visualization" 버튼 클릭 → 동심원 자동 표시

자세한 내용은 :doc:`getting_started` 를 참조하세요.

기술 스택
---------

* **언어**: Python 3.11+
* **GUI**: PyQt5
* **핵심 라이브러리**:

  * 수치 계산: NumPy, SciPy
  * 데이터 처리: Pandas
  * 시각화: Matplotlib
  * 클러스터링: SciPy hierarchy
  * NMDS 분석: scikit-learn

라이선스
--------

MIT License

Copyright (c) 2025 ACC Project

색인 및 검색
============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
