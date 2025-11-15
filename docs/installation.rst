설치
====

시스템 요구사항
----------------

* **운영체제**: Windows 10/11, macOS 10.14+, Linux (Ubuntu 18.04+)
* **메모리**: 최소 4GB RAM (권장: 8GB)
* **디스플레이**: 1280x800 이상 권장
* **디스크 공간**: 최소 200MB

프로그램 다운로드
------------------

실행파일 다운로드 (Python 설치 불필요)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

1. GitHub Releases 페이지 방문
2. 최신 버전의 ``ACC_v[버전].exe`` 다운로드
3. 원하는 폴더에 저장

**파일 크기**: 약 80-120MB (모든 필수 라이브러리 포함)

설치 (선택사항)
----------------

실행파일은 별도 설치가 필요 없습니다. 다운로드 후 바로 실행 가능합니다.

권장 설정
~~~~~~~~~

* 프로그램 전용 폴더 생성 (예: ``C:\Program Files\ACC``)
* 샘플 데이터 파일도 함께 저장
* 바탕화면 바로가기 생성 (선택사항)

개발자용 설치
--------------

소스코드에서 실행하려면 Python 환경이 필요합니다:

.. code-block:: bash

   # Python 3.8 이상 필요
   pip install PyQt5 matplotlib scipy pandas numpy

   # 또는 requirements.txt 사용
   pip install -r requirements.txt

실행:

.. code-block:: bash

   python acc_gui.py

프로그램 실행
--------------

실행파일 사용
~~~~~~~~~~~~~

1. 다운로드한 ``ACC_v[버전].exe`` 파일을 더블클릭
2. (첫 실행 시) Windows Defender 경고가 나타날 수 있음:

   * "추가 정보" 클릭 → "실행" 선택

3. 프로그램 창이 표시됨

소스코드 실행 (개발자)
~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: bash

   python acc_gui.py

화면 구성
----------

프로그램 실행 시 3열 레이아웃이 표시됩니다:

.. code-block:: text

   ┌─────────────────┬─────────────────┬─────────────────┐
   │  Similarity     │  Dendrograms    │  ACC            │
   │  Matrices       │                 │  Visualization  │
   │  (Left Panel)   │  (Center Panel) │  (Right Panel)  │
   └─────────────────┴─────────────────┴─────────────────┘

**왼쪽 패널**: Similarity Matrix 표시 및 편집

**중앙 패널**: Dendrogram 시각화

**오른쪽 패널**: ACC 동심원 시각화

.. image:: images/01_main_window.png
   :alt: 메인 화면
   :align: center

다음 단계
----------

프로그램 설치가 완료되면 :doc:`getting_started` 로 이동하여 샘플 데이터를 사용해보세요.
