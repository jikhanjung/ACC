변경 이력
=========

Version 2.0 (2025-11-15)
-------------------------

사용자 경험 개선
~~~~~~~~~~~~~~~~

* Matrix 로드 후 dendrogram 자동으로 마지막 단계 표시
* ACC 생성 후 완성된 시각화 자동 표시
* 우클릭으로 이미지 저장 기능 (PNG/PDF/SVG)
* Dendrogram Y축 라벨을 오른쪽으로 이동

문서화
~~~~~~

* 포괄적인 사용자 매뉴얼 작성 (1,141줄)
* Sphinx 기반 HTML 문서 (reStructuredText)
* GitHub Pages 자동 배포
* ACC 약어 정확히 수정 (Area Affinity in Concentric Circles)
* Matrix 편집 UI 상세 설명
* 10개 스크린샷 이미지 추가

ACC2 알고리즘
~~~~~~~~~~~~~

* Interactive features (merge point hover, branch swap)
* 향상된 동심원 라벨링
* Merge point 클릭으로 branch swap 가능
* 툴팁으로 클러스터 정보 표시

시각화 개선
~~~~~~~~~~~

* ACC1 area 색상을 동심원 색상과 일치
* 무지개 colormap 적용
* 각 area가 속한 global_sim 레벨을 색상으로 표시

데이터 검증
~~~~~~~~~~~

* CSV 파일 검증 강화
* 비대칭 matrix 감지 및 오류 메시지
* 대각선 값 검증
* 값 범위 검증 (0.0 ~ 1.0)
* 상세한 오류 위치 및 값 표시

UI 개선
~~~~~~~

* Navigation 버튼 추가 (⏮ ⏭)
* 단계별 시각화 제어 향상
* Matrix 테이블 툴팁 추가
* 이미지 저장 대화상자 개선

Version 1.0 (2025-11-13)
-------------------------

초기 릴리스
~~~~~~~~~~~

* 기본 ACC 알고리즘 구현
* PyQt5 기반 GUI 구현
* CSV matrix 입력 지원
* Dendrogram 단계별 시각화
* 동심원 기반 ACC 시각화
* Local/Global similarity 통합
* Matrix 편집 기능
* 기본 이미지 저장 기능

핵심 기능
~~~~~~~~~

* Hierarchical clustering (scipy)
* Procrustes superimposition
* 극좌표 변환 및 시각화
* 3열 레이아웃 (Matrix / Dendrogram / ACC)
* 단계별 슬라이더 제어

데이터 지원
~~~~~~~~~~~

* CSV 파일 입력/출력
* Dictionary 기반 similarity matrix
* 6개 샘플 데이터 포함 (J, T, Y, N, O, Q)

기술 스택
~~~~~~~~~

* Python 3.8+
* PyQt5
* NumPy, SciPy, Pandas
* Matplotlib

알려진 제한사항
~~~~~~~~~~~~~~~

* 대규모 데이터 (50+ 영역) 성능 저하
* 동영상 저장 미지원
* 다국어 미지원 (한글만)

향후 계획
---------

Version 2.1 (예정)
~~~~~~~~~~~~~~~~~~

* 키보드 단축키 지원

  * Ctrl+S: 이미지 저장
  * Ctrl+O: CSV 로드
  * Space: 다음 단계

* 배치 저장

  * 모든 단계를 한 번에 이미지로 저장
  * ZIP 파일로 압축

* 이미지 옵션

  * DPI 선택 (150/300/600)
  * 이미지 크기 조정
  * 배경 투명/불투명 선택

Version 3.0 (장기)
~~~~~~~~~~~~~~~~~~

* 다국어 지원 (영어, 한국어)
* 동영상 저장 기능
* 웹 기반 버전
* API 서버 제공
* 실시간 협업 기능

기여
----

이 프로젝트에 기여하고 싶으신가요?

1. GitHub 저장소 Fork
2. Feature branch 생성
3. 변경사항 commit
4. Pull request 제출

자세한 내용은 GitHub의 ``CONTRIBUTING.md`` 참조.

라이선스
--------

MIT License

Copyright (c) 2025 ACC Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
