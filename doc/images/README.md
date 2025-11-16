# ACC 매뉴얼 이미지

이 디렉토리에는 사용자 매뉴얼에 포함될 스크린샷 이미지들이 저장됩니다.

## 필요한 이미지 목록

### 1. 메인 화면 (01_main_window.png)
- **크기**: 1800x900 (전체 화면)
- **내용**: 프로그램 초기 실행 화면
- **촬영 방법**:
  1. ACC 프로그램 실행
  2. 전체 창 캡처 (Alt+PrtScn 또는 스크린샷 도구)
  3. `01_main_window.png`로 저장

---

### 2. 샘플 데이터 로드 완료 (02_sample_loaded.png)
- **크기**: 1800x900 (전체 화면)
- **내용**: 샘플 CSV 두 개 로드 후 화면
- **촬영 방법**:
  1. `data/sample_subordinate.csv` 로드
  2. `data/sample_inclusive.csv` 로드
  3. Dendrogram이 자동으로 표시된 상태
  4. 전체 창 캡처

---

### 3. ACC 생성 완료 (03_acc_generated.png)
- **크기**: 1800x900 (전체 화면)
- **내용**: ACC 생성 후 완성된 동심원
- **촬영 방법**:
  1. "Generate ACC Visualization" 버튼 클릭
  2. 완성된 ACC가 자동으로 표시된 상태
  3. 전체 창 캡처

---

### 4. Matrix 편집 (04_matrix_editing.png)
- **크기**: 600x400 (Matrix 영역만 확대)
- **내용**: Matrix 테이블 편집 및 툴팁
- **촬영 방법**:
  1. Subordinate Matrix의 한 셀을 더블클릭하여 편집 모드
  2. 회색 셀(대각선 또는 Lower triangle)에 마우스 올려 툴팁 표시
  3. Matrix 영역만 확대하여 캡처

---

### 5. Dendrogram 단계별 보기 (05_dendrogram_steps.png)
- **크기**: 600x500 (Dendrogram 영역만)
- **내용**: 중간 단계의 Dendrogram
- **촬영 방법**:
  1. Dendrogram 슬라이더를 중간 위치로 이동 (예: Step 3/5)
  2. 일부는 파란색, 일부는 회색인 상태
  3. 단계 컨트롤과 Dendrogram 영역 캡처

---

### 6. ACC 시각화 상세 (06_acc_detail.png)
- **크기**: 800x800 (ACC 영역만)
- **내용**: ACC 동심원 시각화 확대
- **촬영 방법**:
  1. ACC 생성 완료 후
  2. 오른쪽 패널의 ACC 시각화 영역만 확대하여 캡처
  3. 범례(legend)가 명확히 보이도록

---

### 7. ACC2 Interactive Features (07_acc2_interactive.png)
- **크기**: 800x800 (ACC2 영역만)
- **내용**: Merge point hover 툴팁
- **촬영 방법**:
  1. "Generate ACC2" 버튼 클릭
  2. 빨간색 merge point에 마우스 올리기
  3. 노란색 툴팁이 표시된 상태에서 캡처

---

### 8. 이미지 저장 - 우클릭 메뉴 (08_save_image_menu.png)
- **크기**: 400x300 (메뉴 주변)
- **내용**: 우클릭 컨텍스트 메뉴
- **촬영 방법**:
  1. Dendrogram 또는 ACC 영역에서 우클릭
  2. 컨텍스트 메뉴가 표시된 상태
  3. 메뉴와 주변 영역 캡처

---

### 9. 이미지 저장 - 파일 대화상자 (09_save_dialog.png)
- **크기**: 700x500 (대화상자)
- **내용**: 파일 저장 대화상자
- **촬영 방법**:
  1. "Save Image As..." 선택
  2. 저장 대화상자가 나타난 상태
  3. 기본 파일명과 형식 선택 드롭다운이 보이도록

---

### 10. CSV 파일 오류 메시지 (10_csv_error.png)
- **크기**: 500x300 (오류 대화상자)
- **내용**: CSV 검증 오류 메시지
- **촬영 방법**:
  1. 일부러 잘못된 CSV 파일 생성 (대칭성 위반 등)
  2. 로드 시도
  3. 오류 대화상자 캡처

---

## 촬영 가이드라인

### 해상도 및 품질
- **DPI**: 96-144 (화면 해상도)
- **형식**: PNG (무손실)
- **색상**: RGB

### 스타일
- 깔끔한 배경 (불필요한 창 닫기)
- 마우스 커서 포함 (hover, click 상태 표시 시)
- 충분한 여백 (필요한 요소가 잘리지 않도록)

### 도구
- **Windows**: Snipping Tool, Snip & Sketch, PrtScn
- **macOS**: Cmd+Shift+4
- **Linux**: GNOME Screenshot, Spectacle

### 파일명 규칙
- 번호 2자리 + 설명 (예: `01_main_window.png`)
- 소문자와 언더스코어 사용
- 공백 없음

---

## 이미지 추가 후 확인사항

✅ 모든 이미지가 `images/` 디렉토리에 저장되었는지 확인
✅ 파일명이 매뉴얼의 markdown 링크와 일치하는지 확인
✅ 이미지가 너무 크지 않은지 확인 (각 이미지 < 1MB 권장)
✅ 이미지가 명확하고 읽기 쉬운지 확인

---

## 작업 체크리스트

- [ ] 01_main_window.png
- [ ] 02_sample_loaded.png
- [ ] 03_acc_generated.png
- [ ] 04_matrix_editing.png
- [ ] 05_dendrogram_steps.png
- [ ] 06_acc_detail.png
- [ ] 07_acc2_interactive.png
- [ ] 08_save_image_menu.png
- [ ] 09_save_dialog.png
- [ ] 10_csv_error.png

---

**참고**: 이미지가 준비되면 USER_MANUAL.md를 열어서 이미지가 제대로 표시되는지 확인하세요.
