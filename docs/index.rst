ACC 사용자 매뉴얼
==================

**ACC (Area Affinity in Concentric Circles)** - 계층적 클러스터 관계 시각화 도구

버전: 2.0

최종 업데이트: 2025-11-15

환영합니다
----------

ACC는 계층적 클러스터링 결과를 **동심원 기반 원형 다이어그램**으로 시각화하는 Python 애플리케이션입니다.
두 종류의 유사도 정보(Subordinate와 Inclusive)를 결합하여 영역(area) 간의 친화도(affinity) 관계를 직관적으로 표현합니다.

주요 특징
----------

* **이중 유사도 통합**: Subordinate와 Inclusive 유사도를 동시에 고려
* **대화형 시각화**: 단계별 클러스터링 과정 재생 가능
* **동심원 표현**: 클러스터 계층을 동심원으로 직관적 표현
* **인터랙티브 조정**: Branch swap으로 레이아웃 최적화
* **3단계 워크플로우**: 직관적인 데이터 입력 및 분석 프로세스

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

1. **Subordinate Matrix 로드**: CSV 파일 선택 → Dendrogram 자동 표시
2. **Inclusive Matrix 로드**: CSV 파일 선택 → Dendrogram 자동 표시
3. **ACC 생성**: "Generate ACC Visualization" 버튼 클릭 → 동심원 자동 표시

자세한 내용은 :doc:`getting_started` 를 참조하세요.

기술 스택
---------

* **언어**: Python 3.8+
* **GUI**: PyQt5
* **핵심 라이브러리**:

  * 수치 계산: NumPy, SciPy
  * 데이터 처리: Pandas
  * 시각화: Matplotlib
  * 클러스터링: SciPy hierarchy

라이선스
--------

MIT License

Copyright (c) 2025 ACC Project

색인 및 검색
============

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
