데이터 형식
===========

CSV 파일 형식
--------------

Similarity matrix CSV는 다음 규칙을 따라야 합니다:

기본 구조
~~~~~~~~~

.. code-block:: csv

   ,J,T,Y,N,O,Q
   J,1.0,0.9,0.8,0.4,0.35,0.36
   T,0.9,1.0,0.8,0.38,0.33,0.34
   Y,0.8,0.8,1.0,0.37,0.32,0.33
   N,0.4,0.38,0.37,1.0,0.75,0.75
   O,0.35,0.33,0.32,0.75,1.0,0.85
   Q,0.36,0.34,0.33,0.75,0.85,1.0

필수 조건
~~~~~~~~~

1. **첫 행**: 컬럼 헤더 (라벨 이름)
2. **첫 열**: 로우 인덱스 (라벨 이름, 헤더와 동일 순서)
3. **대각선**: 모든 값이 1.0
4. **대칭성**: matrix[i][j] == matrix[j][i]
5. **값 범위**: 0.0 ~ 1.0
6. **라벨 일치**: Subordinate와 Inclusive matrix가 동일한 라벨 사용

잘못된 예시
~~~~~~~~~~~

.. code-block:: csv

   # ❌ 첫 행 누락
   J,1.0,0.9,0.8
   T,0.9,1.0,0.8

.. code-block:: csv

   # ❌ 대칭성 위반
   ,J,T
   J,1.0,0.9
   T,0.8,1.0  ← 0.9여야 함

.. code-block:: csv

   # ❌ 범위 초과
   ,J,T
   J,1.0,1.5  ← 1.0 초과
   T,1.5,1.0

.. code-block:: csv

   # ❌ 대각선이 1.0이 아님
   ,J,T
   J,0.9,0.8  ← 1.0이어야 함
   T,0.8,1.0

.. image:: images/10_csv_error.png
   :alt: CSV 오류 메시지
   :align: center

데이터 준비 가이드
------------------

Excel에서 CSV 생성
~~~~~~~~~~~~~~~~~~~

1. Excel에서 similarity matrix 작성
2. 첫 행과 첫 열에 동일한 라벨 입력
3. 대각선을 1.0으로 설정
4. 대칭 값 입력 (수식 사용 가능: ``=INDEX($B$2:$G$7, COLUMN()-1, ROW()-1)``)
5. "다른 이름으로 저장" → "CSV (쉼표로 분리)" 선택

Python으로 생성
~~~~~~~~~~~~~~~

.. code-block:: python

   import pandas as pd
   import numpy as np

   # 라벨 정의
   labels = ['J', 'T', 'Y', 'N', 'O', 'Q']

   # 빈 매트릭스 생성 (대각선 1.0)
   n = len(labels)
   matrix = np.eye(n)

   # 상삼각 값 입력 (예시)
   matrix[0, 1] = 0.9  # J-T
   matrix[0, 2] = 0.8  # J-Y
   # ... 추가 값 입력

   # 대칭화
   matrix = matrix + matrix.T - np.diag(np.diag(matrix))

   # DataFrame 생성 및 저장
   df = pd.DataFrame(matrix, index=labels, columns=labels)
   df.to_csv('subordinate.csv')

데이터 검증
-----------

CSV 파일 로드 시 자동으로 다음 사항을 검증합니다:

* ✓ 파일 형식 (CSV)
* ✓ 대칭성
* ✓ 대각선 값 (1.0)
* ✓ 값 범위 (0.0 ~ 1.0)
* ✓ 라벨 일치 (Subordinate ↔ Inclusive)

오류 발생 시 상세한 메시지가 표시됩니다.

검증 오류 메시지 예시
~~~~~~~~~~~~~~~~~~~~~

.. code-block:: text

   Invalid Similarity Matrix

   Matrix is not symmetric: matrix[0,1]=0.900000 but matrix[1,0]=0.800000

   Requirements:
   - Diagonal values must be 1.0
   - Matrix must be symmetric (matrix[i,j] = matrix[j,i])
   - All values should be between 0.0 and 1.0

다음 단계
----------

데이터 형식을 이해했다면 :doc:`visualization` 으로 이동하여 시각화 해석 방법을 확인하세요.
