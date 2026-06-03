# FoodSugar AI Web App Visual Redesign Update

작성일: 2026-06-02  
범위: `frontend/` 웹앱 시각 디자인 재개선  
상태: 테스트 및 빌드 통과

---

## 1. 작업 배경

이전 2026-05-31 작업에서는 기능 요소와 안전 문구는 추가되었지만, 실제 화면을 봤을 때 기존 디자인과 크게 달라 보이지 않는 문제가 있었다.

따라서 이번 작업은 단순한 문구/카드 추가가 아니라, 사용자가 첫 화면을 열었을 때 바로 “디자인이 바뀌었다”고 느낄 수 있도록 화면 구조와 시각 계층을 다시 잡는 것을 목표로 진행했다.

---

## 2. 수정 원칙

이번 작업에서도 기존 모델과 학습 코드는 건드리지 않았다.

수정하지 않은 영역:

```text
config/kfood_production_ensemble_config.json
src/classifier/
data/models/
기존 classifier training code
기존 model checkpoint
기존 ensemble weight
backend model logic
```

실제 변경 범위:

```text
frontend/src/
```

---

## 3. 핵심 디자인 방향

이번 재디자인의 핵심은 아래 네 가지였다.

1. 첫 화면을 단순 업로드 페이지가 아니라 프리미엄 웰니스 앱의 시작 화면처럼 보이게 한다.
2. 음식 분석/혈당 예측 결과가 “카드 나열”이 아니라 상단 요약 대시보드 구조로 보이게 한다.
3. 예시 데이터와 실제 분석 결과가 헷갈리지 않도록 명확히 구분한다.
4. 기존 warm cream / green 디자인 시스템은 유지하되, `forest` 색상을 더 적극적으로 사용해 대비를 만든다.

---

## 4. 주요 변경사항

### 4.1 AppShell 레이아웃 변경

수정 파일:

```text
frontend/src/components/AppShell.tsx
```

변경 내용:

- 기존에는 전체가 같은 cream 배경 안에 header/main/nav가 단순히 배치되어 있었다.
- 이번에는 header를 별도 상단 bar처럼 분리했다.
- 전체 max width를 `max-w-6xl`에서 `max-w-7xl`로 넓혔다.
- main 영역 여백을 조정해 대시보드 느낌을 강화했다.

효과:

- 앱 전체가 더 넓고 현대적인 dashboard layout처럼 보인다.
- header와 content 영역이 시각적으로 구분된다.

---

### 4.2 HeaderBar 개선

수정 파일:

```text
frontend/src/components/HeaderBar.tsx
```

변경 내용:

- 로고 영역을 더 진한 `forest` 색상으로 변경했다.
- `FoodSugar AI` 텍스트를 더 굵고 크게 조정했다.
- 오른쪽에 `Wellness` 상태 pill과 `분석 기록` 버튼을 넣었다.
- 모바일에서는 오른쪽 보조 영역이 숨겨지도록 처리했다.

효과:

- 기존보다 브랜드 헤더 느낌이 강해졌다.
- 웰니스 앱이라는 포지셔닝이 더 명확해졌다.

---

### 4.3 HomePage 대형 히어로 재구성

수정 파일:

```text
frontend/src/pages/HomePage.tsx
```

변경 내용:

- HomePage를 기존 2-column 설명 + 업로드 패널 구조에서 대형 히어로 섹션으로 변경했다.
- 왼쪽에는 큰 headline, 설명, 데모 시나리오, 3-step flow를 배치했다.
- 오른쪽에는 `Today scan` 스타일의 mock preview 패널을 추가했다.
- mock preview 안에는 음식 분석 카드와 90분 예상 범위 카드가 들어간다.

추가된 시각 요소:

```text
사진 스캔 → 음식 확인 → 범위 예측
```

오른쪽 예시 카드 내용:

```text
음식: 비빔밥
탄수: 85g
단백질: 22g
섬유: 6g
90분 예상 범위: 104~205
불확실성 높음
```

효과:

- 첫 화면이 기존보다 훨씬 완성된 앱처럼 보인다.
- 사용자가 앱의 흐름을 한눈에 이해할 수 있다.

---

### 4.4 예시 미리보기 혼동 방지 표시 추가

수정 파일:

```text
frontend/src/pages/HomePage.tsx
```

변경 배경:

- 사용자가 홈 오른쪽 preview card를 보고 “이 화면은 실제 결과인가?”라고 물었다.
- 실제 분석 결과가 아니라 고정 mock preview이기 때문에 명확한 표시가 필요했다.

추가 문구:

```text
예시 미리보기
실제 분석 결과 아님
아래 값은 화면 구성을 보여주는 데모 예시입니다.
```

효과:

- mock preview와 실제 분석 결과를 구분할 수 있다.
- 데모/제출 화면에서 오해 가능성을 줄였다.

---

### 4.5 UploadPanel을 Scan Workspace 형태로 변경

수정 파일:

```text
frontend/src/components/UploadPanel.tsx
```

변경 내용:

- 기존에는 업로드 박스와 버튼이 단순히 위아래로 배치되어 있었다.
- 이번에는 왼쪽 업로드 영역 + 오른쪽 작업 패널 구조로 변경했다.
- 오른쪽 패널에 `Scan workspace` 제목을 추가했다.
- `갤러리에서 선택`, `분석 시작하기` 버튼을 오른쪽 작업 패널에 배치했다.
- 촬영 체크 리스트를 추가했다.

촬영 체크:

```text
밝은 조명
음식 전체 노출
한 끼 단위 사진
```

효과:

- 업로드 영역이 단순 form이 아니라 실제 앱의 scan workflow처럼 보인다.
- Food scan first UX가 더 명확해졌다.

---

### 4.6 AnalysisPage 상단 대시보드화

수정 파일:

```text
frontend/src/pages/AnalysisPage.tsx
```

변경 내용:

- 기존에는 제목과 버튼만 있는 단순 header였다.
- 이번에는 어두운 `forest` 배경의 상단 분석 결과 hero section을 추가했다.
- 오른쪽에 현재 인식 음식과 분류 신뢰도를 요약하는 panel을 넣었다.

표시 내용:

```text
현재 인식 음식
비빔밥
분류 신뢰도 92%
```

효과:

- 분석 결과 화면이 카드 나열보다 dashboard result처럼 보인다.
- 음식 분석 결과가 더 강하게 눈에 들어온다.

---

### 4.7 NutritionCard 시각 계층 개선

수정 파일:

```text
frontend/src/components/NutritionCard.tsx
```

변경 내용:

- `Nutrition map` header를 추가했다.
- 총 열량을 상단 강조 영역으로 분리했다.
- 세부 영양소는 작은 metric grid로 배치했다.
- 기존 모든 영양소가 동일한 카드로 보이던 문제를 줄였다.

효과:

- 칼로리와 세부 영양소 사이의 정보 계층이 명확해졌다.
- 대시보드 카드처럼 보이는 정도가 개선되었다.

---

### 4.8 GlucoseRiskCard 시각 개선

수정 파일:

```text
frontend/src/components/GlucoseRiskCard.tsx
```

변경 내용:

- 혈당 부담 참고 점수 아래에 low/medium/high bar를 추가했다.

표시 구조:

```text
낮음 | 보통 | 높음
```

효과:

- Noom 스타일의 단순 color-coded guidance에 더 가까워졌다.
- 위험도 텍스트만 있는 것보다 사용자가 빠르게 이해하기 쉽다.

---

### 4.9 PredictionPage 상단 90분 범위 대시보드 추가

수정 파일:

```text
frontend/src/pages/PredictionPage.tsx
```

변경 내용:

- 기존에는 일반 title 아래에 예측 카드가 나열되어 있었다.
- 이번에는 `forest` 배경의 상단 hero dashboard를 추가했다.
- 오른쪽에 90분 예상 범위를 크게 보여주는 panel을 넣었다.

표시 내용:

```text
90분 예상 범위
104~205
mg/dL · 불확실성 높음
```

효과:

- 90분 예측이 단일 값이 아니라 range-first로 보인다.
- CGM 예측 화면의 첫인상이 더 강해졌다.

---

### 4.10 HistoryList 밀도 개선

수정 파일:

```text
frontend/src/components/HistoryList.tsx
```

변경 내용:

- 기존 기록 item은 단순 horizontal card였다.
- 이번에는 desktop에서 grid layout으로 바꿨다.
- `혈당 영향` 값을 별도 column처럼 분리했다.

효과:

- 기록 화면이 더 dashboard/table hybrid 느낌으로 보인다.
- 반복 기록을 스캔하기 쉬워졌다.

---

### 4.11 BottomNav 디자인 변경

수정 파일:

```text
frontend/src/components/BottomNav.tsx
```

변경 내용:

- 기존에는 완전히 둥근 pill nav였다.
- 이번에는 더 넓은 rounded rectangle 앱 네비 형태로 변경했다.
- 버튼 높이와 active state를 조정했다.

효과:

- mobile wellness app navigation에 더 가까운 인상을 준다.

---

## 5. 안전/비의료 UX 유지

이번 디자인 재작업에서도 혈당 관련 문구는 기존 안전 원칙을 유지했다.

유지한 표현:

```text
참고용
가능성
가능성 신호
예상 범위
불확실성
실제 측정값과 함께 확인
```

피한 표현:

```text
저혈당입니다
고혈당입니다
혈당을 정확히 예측
인슐린을 조절
치료에 사용
당뇨병을 진단
약을 조절
```

코드 검색 결과, 위 금지 표현은 테스트 파일의 forbidden wording 목록 외 실제 UI 문구에는 사용되지 않았다.

---

## 6. 검증 결과

실행 위치:

```bash
cd /Users/sangrok/foodsugar-ai/frontend
```

테스트:

```bash
npm run test
```

결과:

```text
Test Files  3 passed
Tests       11 passed
```

빌드:

```bash
npm run build
```

결과:

```text
✓ built
```

참고:

- Vite build에서 chunk size warning은 계속 표시된다.
- 원인은 Recharts 등 프론트 번들 크기이며, 현재 기능 동작에는 영향이 없다.

---

## 7. 브라우저 확인 결과

확인 URL:

```text
http://127.0.0.1:5173/
```

브라우저에서 확인한 항목:

```text
HomePage:
- 대형 hero 표시
- 예시 미리보기 카드 표시
- 실제 분석 결과 아님 배지 표시
- Scan workspace 표시
- 사진 스캔 / 음식 확인 / 범위 예측 flow 표시

AnalysisPage:
- 어두운 상단 분석 결과 panel 표시
- 현재 인식 음식 panel 표시
- Wellness summary 표시
- Nutrition map 표시

PredictionPage:
- 어두운 상단 예측 panel 표시
- 90분 예상 범위 강조 표시
- 90분 범위 우선 예측 카드 표시
- 예측 범위 band 표시

HistoryPage:
- 주간 인사이트 표시
- 혈당 영향 column 표시
```

---

## 8. 현재 변경 파일 목록

이번 시각 재디자인에서 수정된 주요 파일:

```text
frontend/src/components/AppShell.tsx
frontend/src/components/HeaderBar.tsx
frontend/src/components/UploadPanel.tsx
frontend/src/components/NutritionCard.tsx
frontend/src/components/GlucoseRiskCard.tsx
frontend/src/components/HistoryList.tsx
frontend/src/components/BottomNav.tsx
frontend/src/pages/HomePage.tsx
frontend/src/pages/AnalysisPage.tsx
frontend/src/pages/PredictionPage.tsx
```

이전 5/31 작업에서 추가되어 이번 디자인의 기반이 된 파일:

```text
frontend/src/components/FoodConfirmationCard.tsx
frontend/src/components/ResultSourceBadge.tsx
frontend/src/components/GlucoseChart.tsx
frontend/src/pages/HistoryPage.tsx
frontend/src/pages/SettingsPage.tsx
frontend/src/test/wellnessDashboard.test.tsx
```

---

## 9. 현재 상태 요약

현재 웹앱은 이전보다 시각적으로 더 명확한 프리미엄 웰니스 대시보드 형태에 가까워졌다.

특히 달라진 점:

- 첫 화면이 더 이상 단순 업로드 폼처럼 보이지 않는다.
- 오른쪽 preview가 앱의 결과 형태를 보여주되, 예시임을 명확히 표시한다.
- 분석/예측 화면 상단에 강한 dashboard hero가 생겼다.
- 90분 예측이 더 명확하게 range-first로 보인다.
- 기록 화면은 insight와 기록 table이 함께 있는 구조에 가까워졌다.

---

## 10. 다음 개선 후보

아직 남은 개선 후보:

1. HomePage demo scenario 버튼을 실제 mock scenario state 전환과 연결
2. FoodConfirmationCard에서 선택한 음식명을 실제 analysis state에 반영
3. 실제 업로드 이미지가 들어갔을 때 Home preview와 Analysis preview 간 시각 연동
4. PredictionPage chart를 더 촘촘한 time-series 기반으로 확장
5. Recharts lazy loading 또는 manual chunk 분리로 bundle size warning 완화
6. 모바일 화면에서 hero preview card의 높이와 간격 추가 검수

