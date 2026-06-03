# FoodSugar AI Web App Wellness Design Update

작성일: 2026-05-31  
범위: `frontend/` 웹앱 UI/UX 개선  
상태: 테스트 및 빌드 통과

---

## 1. 작업 목표

이번 작업의 목표는 기존 FoodSugar AI 웹앱을 의료기기 느낌이 아니라, 프리미엄 웰니스 대시보드에 가깝게 개선하는 것이었다.

참고 방향은 Levels, Signos, January AI, MyFitnessPal, Noom, Lingo 스타일의 공통 패턴을 따랐다.

- 음식 사진 업로드를 첫 흐름으로 강조
- 분석 결과가 실제 모델 결과인지 데모 데이터인지 명확히 표시
- 음식 분류 confidence가 낮을 때 음식 확인 단계를 제공
- 90분 혈당 예측은 단일 수치보다 범위와 불확실성을 먼저 보여줌
- CGM 차트에 목표 범위 band와 예측 구간 band를 표시
- 기록 화면에 주간 인사이트 카드 추가
- 설정 화면에 앱이 하는 일과 하지 않는 일을 명확히 안내
- 모든 혈당 관련 표현은 참고용, 비진단, 비치료 문구 유지

---

## 2. 수정 원칙

이번 변경에서는 아래 영역을 건드리지 않았다.

- 기존 음식분류 모델
- classifier 학습 코드
- 모델 checkpoint
- `data/models/`
- `src/classifier/`
- backend 모델 로직
- ensemble weight

변경 범위는 프론트엔드 UI와 프론트엔드 테스트로 제한했다.

---

## 3. 주요 변경사항

### 3.1 HomePage 개선

수정 파일:

- `frontend/src/pages/HomePage.tsx`
- `frontend/src/data/mockData.ts`

변경 내용:

- 첫 화면에서 음식 사진 업로드가 시작점이라는 점을 더 분명하게 유지했다.
- 데모 시나리오 버튼 3개를 추가했다.
  - 비빔밥 식사
  - 가벼운 단백질 식사
  - 간식 이후 흐름
- 각 버튼에는 간단한 태그와 설명을 붙여 웰니스 앱의 scenario entry 느낌을 강화했다.

목적:

- 사용자가 앱을 열자마자 “음식 사진을 먼저 올리는 앱”임을 이해하도록 개선
- 데모 앱 검수 시 실제 기능 흐름을 빠르게 파악할 수 있도록 보조

---

### 3.2 결과 출처 배지 추가

수정/추가 파일:

- `frontend/src/components/ResultSourceBadge.tsx`
- `frontend/src/components/FoodPreviewCard.tsx`
- `frontend/src/pages/AnalysisPage.tsx`
- `frontend/src/pages/PredictionPage.tsx`

변경 내용:

- 결과가 backend 실제 응답인지, mock fallback인지 구분하는 배지를 추가했다.
- 표시 문구:
  - `실제 모델 결과`
  - `데모 데이터`

목적:

- 실제 모델 출력과 데모 fallback을 사용자가 혼동하지 않도록 함
- 제출/시연 시 “현재 표시 중인 결과의 출처”를 명확히 설명 가능

---

### 3.3 음식 확인 카드 추가

추가 파일:

- `frontend/src/components/FoodConfirmationCard.tsx`

수정 파일:

- `frontend/src/pages/AnalysisPage.tsx`
- `frontend/src/data/mockData.ts`

변경 내용:

- 음식 분류 confidence가 낮은 경우를 대비한 음식 확인 UI를 추가했다.
- 현재 데모 옵션:
  - 비빔밥
  - 덮밥
  - 채소 비빔밥
- confidence가 높을 때는 “해당 음식으로 분석했다”는 확인 카드로 동작한다.
- confidence가 낮을 때는 “음식명을 먼저 확인해주세요” 문구를 보여준다.

목적:

- MyFitnessPal의 verified food confirmation 패턴 반영
- 음식명 오류가 혈당 위험도/영양성분 해석에 영향을 줄 수 있음을 자연스럽게 안내
- 진단적 경고가 아니라 식습관 참고 흐름으로 유지

---

### 3.4 PredictionPage 90분 예측 UX 강화

수정 파일:

- `frontend/src/pages/PredictionPage.tsx`
- `frontend/src/components/GlucosePredictionCards.tsx`

변경 내용:

- 90분 예측을 별도 강조 카드로 분리했다.
- `104~205 mg/dL`처럼 범위를 먼저 보여주도록 구성했다.
- `불확실성 높음`을 함께 표시했다.
- 90분 예측은 단일 수치보다 가능한 범위를 먼저 확인하라는 문구를 추가했다.

목적:

- 90분 예측의 불확실성을 UI 구조 자체에서 드러냄
- 과도하게 정확한 혈당 예측처럼 보이지 않도록 조정
- “range-first / uncertainty-first” 기준 충족

---

### 3.5 GlucoseChart 개선

수정 파일:

- `frontend/src/components/GlucoseChart.tsx`

변경 내용:

- CGM 예측 그래프에 목표 범위 band를 명확히 표시했다.
  - 목표 범위: `70~180 mg/dL`
- 예측 interval band를 별도 시각 요소로 추가했다.
- tooltip에 참고 수치와 예측 범위를 함께 표시하도록 개선했다.
- 차트 상단에 다음 라벨을 추가했다.
  - `목표 범위 70~180 mg/dL`
  - `예측 범위 band`

목적:

- Levels/Lingo 스타일의 glucose graph 패턴 반영
- 사용자가 point estimate보다 range와 trend를 먼저 보게 함
- CGM-style time and range visualization 기준 충족

---

### 3.6 HistoryPage 주간 인사이트 추가

수정 파일:

- `frontend/src/pages/HistoryPage.tsx`
- `frontend/src/data/mockData.ts`

변경 내용:

- 기존 summary card 아래에 주간 인사이트 섹션을 추가했다.
- 현재 카드:
  - 식후 피크 패턴
  - 안정적인 선택
  - 주의해서 볼 구간
- 기록 화면 하단에도 safety notice를 유지했다.

목적:

- 단순 기록 목록이 아니라 웰니스 대시보드처럼 보이게 개선
- Lingo의 weekly insight snapshot 패턴 반영
- “최근 식사와 혈당 흐름을 돌아보는 화면”으로 의미 강화

---

### 3.7 SettingsPage 안전/한계 안내 추가

수정 파일:

- `frontend/src/pages/SettingsPage.tsx`

변경 내용:

- “이 앱이 하는 일 / 하지 않는 일” 섹션을 추가했다.

하는 일:

- 음식 사진을 바탕으로 음식명과 영양성분 요약
- CGM 흐름이 있을 때 30분, 60분, 90분 혈당 변화 가능성 범위 표시
- 저혈당/고혈당 가능성 신호를 식습관 관리 참고 정보로 표시

하지 않는 일:

- 질병 여부 판단 또는 의료 결정 대체
- 약물, 인슐린, 치료 계획에 대한 지시 제공
- 긴급 상황 판단 또는 실제 CGM 측정값 대체

목적:

- non-medical safety UX 강화
- 앱의 역할과 한계를 사용자가 명확히 이해하도록 함

---

## 4. 안전 문구 정책

이번 UI 변경에서는 혈당 관련 결과를 의료 진단처럼 보이지 않게 조정했다.

유지한 표현 방향:

- `참고용`
- `가능성`
- `가능성 신호`
- `범위`
- `불확실성`
- `실제 측정값과 함께 확인`

피한 표현:

- 혈당을 정확히 예측한다는 표현
- 저혈당/고혈당을 확정하는 표현
- 인슐린 또는 약물 조절을 지시하는 표현
- 진단 또는 치료에 사용한다는 표현

---

## 5. 추가된 테스트

추가 파일:

- `frontend/src/test/wellnessDashboard.test.tsx`

수정 파일:

- `frontend/src/test/setup.ts`

테스트 내용:

- HomePage가 food scan first 구조를 유지하는지 확인
- 데모 시나리오 버튼이 표시되는지 확인
- `데모 데이터` / `실제 모델 결과` 출처 배지가 표시되는지 확인
- 음식 확인 카드가 표시되는지 확인
- CGM chart에 목표 범위와 예측 범위 band 라벨이 있는지 확인
- HistoryPage에 주간 인사이트 카드가 표시되는지 확인
- SettingsPage에 “하는 일 / 하지 않는 일” 섹션이 표시되는지 확인

테스트 환경 보완:

- Recharts의 `ResponsiveContainer`가 jsdom에서 동작하도록 `ResizeObserver` mock을 추가했다.

---

## 6. 검증 결과

실행 위치:

```bash
cd frontend
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

- Vite build 중 bundle size warning이 표시되었지만 빌드는 성공했다.
- warning 원인은 Recharts 등을 포함한 프론트 번들 크기이며, 현재 MVP 기능에는 치명적 문제는 아니다.

---

## 7. 브라우저 확인

확인 URL:

```text
http://127.0.0.1:5173/
```

브라우저에서 확인한 항목:

- HomePage 음식 사진 업로드 heading 표시
- HomePage 데모 시나리오 버튼 3개 표시
- AnalysisPage 음식 확인 카드 표시
- AnalysisPage 데모 데이터 배지 표시
- PredictionPage 90분 범위 우선 예측 카드 표시
- PredictionPage 예측 범위 band 라벨 표시
- PredictionPage 가능성 신호 표시
- HistoryPage 주간 인사이트 표시
- SettingsPage “이 앱이 하는 일 / 하지 않는 일” 표시

---

## 8. 현재 UX 기준 충족 여부

### Food scan first

충족.

- 첫 화면이 음식 사진 업로드 중심이다.
- 데모 시나리오 버튼이 HomePage에 노출된다.

### Wellness dashboard result

충족.

- AnalysisPage와 HistoryPage가 영양 요약, 위험도, 주간 인사이트 카드 중심으로 구성된다.
- warm cream / green 디자인 시스템을 유지했다.

### CGM-style time and range visualization

충족.

- PredictionPage에서 시간대별 혈당 변화 가능성을 보여준다.
- GlucoseChart에 목표 범위 band와 예측 interval band가 들어갔다.
- 60분/90분은 단일 수치보다 범위 중심으로 표시된다.

### Non-medical safety UX

충족.

- 혈당 관련 페이지에 참고용 safety notice를 유지했다.
- 90분 예측은 범위와 불확실성을 먼저 보여준다.
- 저혈당/고혈당 관련 표현은 `가능성 신호`로 유지했다.

---

## 9. 변경 파일 목록

주요 수정/추가 파일:

```text
frontend/src/components/FoodConfirmationCard.tsx
frontend/src/components/FoodPreviewCard.tsx
frontend/src/components/GlucoseChart.tsx
frontend/src/components/ResultSourceBadge.tsx
frontend/src/data/mockData.ts
frontend/src/pages/AnalysisPage.tsx
frontend/src/pages/HistoryPage.tsx
frontend/src/pages/HomePage.tsx
frontend/src/pages/PredictionPage.tsx
frontend/src/pages/SettingsPage.tsx
frontend/src/test/setup.ts
frontend/src/test/wellnessDashboard.test.tsx
```

---

## 10. 다음 개선 후보

현재 MVP 수준에서는 디자인/안전 UX 기준을 충족했다.

다음 단계에서 고려할 수 있는 개선:

- demo scenario 버튼을 실제 mock state 전환과 연결
- 음식 확인 카드에서 사용자가 선택한 음식명이 분석 결과에 반영되도록 상태 연결
- PredictionPage 차트를 더 정교한 time-series 데이터 기반으로 확장
- 모바일에서 chart tooltip/legend 시각 검수
- bundle size warning 완화를 위한 chart lazy loading 또는 manual chunk 분리

