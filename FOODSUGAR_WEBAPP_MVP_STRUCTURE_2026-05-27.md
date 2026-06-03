# FoodSugar AI Web MVP 구조 정리 - 2026-05-27

## 0. 요약

현재 `webapp` 브랜치에서 FoodSugar AI 웹 MVP를 `frontend/` 폴더로 새로 구현했다.

이번 웹앱 작업의 원칙:

- 기존 K-Food classifier 수정 없음
- 기존 model checkpoint 수정 없음
- `data/models/` 수정 없음
- classifier/training code 수정 없음
- backend는 건드리지 않고 frontend/demo integration 중심으로 구현
- backend API 연결 실패 시 mock fallback으로 데모 UI가 계속 동작
- 혈당 관련 결과는 모두 의료 진단/치료가 아니라 식습관 관리 참고용으로 표현

현재 로컬 URL:

```text
http://127.0.0.1:5173/
```

---

## 1. 기술 스택

```text
Vite
React
TypeScript
Tailwind CSS
Recharts
lucide-react
```

주요 설정 파일:

```text
frontend/package.json
frontend/index.html
frontend/vite.config.ts
frontend/tsconfig.json
frontend/tailwind.config.js
frontend/postcss.config.js
```

---

## 2. Frontend 폴더 구조

핵심 소스 구조:

```text
frontend/
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── styles.css
    ├── vite-env.d.ts
    ├── lib/
    │   └── api.ts
    ├── data/
    │   └── mockData.ts
    ├── components/
    │   ├── AppShell.tsx
    │   ├── BottomNav.tsx
    │   ├── HeaderBar.tsx
    │   ├── SafetyNotice.tsx
    │   ├── UploadPanel.tsx
    │   ├── FoodPreviewCard.tsx
    │   ├── NutritionCard.tsx
    │   ├── GlucoseRiskCard.tsx
    │   ├── GlucosePredictionCards.tsx
    │   ├── GlucoseChart.tsx
    │   ├── RiskSignalCard.tsx
    │   └── HistoryList.tsx
    └── pages/
        ├── HomePage.tsx
        ├── AnalysisPage.tsx
        ├── PredictionPage.tsx
        ├── HistoryPage.tsx
        └── SettingsPage.tsx
```

생성된 빌드 산출물:

```text
frontend/dist/
```

설치된 의존성:

```text
frontend/node_modules/
```

---

## 3. 앱 전체 흐름

앱 상태 관리는 `frontend/src/App.tsx`에서 local state로 처리한다.

페이지 상태:

```ts
type PageKey = "home" | "analysis" | "prediction" | "history" | "settings";
```

사용자 흐름:

```text
1. HomePage
   음식 이미지 업로드

2. analyzeFoodImage(file)
   backend /predict/analyze 호출 시도
   실패하면 mockAnalysis 사용

3. AnalysisPage
   음식명, 신뢰도, 영양성분, 혈당 부담 참고 점수 표시

4. predictGlucose(samplePayload)
   backend /predict/cgm-forecast-enriched-events 호출 시도
   실패하면 mockPrediction 사용

5. PredictionPage
   30/60/90분 혈당 변화 가능성, 예측 범위, 불확실성, 가능성 신호 표시

6. HistoryPage / SettingsPage
   데모 기록, 서비스 설명, 안전 문구 표시
```

---

## 4. 페이지별 역할

### 4.1 HomePage

파일:

```text
frontend/src/pages/HomePage.tsx
```

역할:

- FoodSugar AI 소개
- 음식 사진 업로드
- preview 표시
- 분석 시작 버튼 제공

사용 컴포넌트:

```text
UploadPanel
```

### 4.2 AnalysisPage

파일:

```text
frontend/src/pages/AnalysisPage.tsx
```

역할:

- 업로드 이미지 또는 mock food preview 표시
- 예측 음식명 표시
- classification confidence 표시
- 영양성분 표시
- 혈당 부담 참고 점수 표시
- 안전 문구 표시
- 혈당 예측 화면으로 이동

사용 컴포넌트:

```text
FoodPreviewCard
NutritionCard
GlucoseRiskCard
SafetyNotice
```

### 4.3 PredictionPage

파일:

```text
frontend/src/pages/PredictionPage.tsx
```

역할:

- 현재 혈당 기준값 표시
- 30분 예측 표시
- 60분 예측 범위 표시
- 90분 예측은 단일 숫자보다 범위와 불확실성 중심으로 표시
- Recharts 기반 혈당 변화 그래프 표시
- 저혈당/고혈당 가능성 신호 표시
- 안전 문구 표시

사용 컴포넌트:

```text
GlucosePredictionCards
GlucoseChart
RiskSignalCard
SafetyNotice
```

중요한 UX 원칙:

```text
90분 예측은 큰 단일 숫자 카드로 강조하지 않는다.
90분은 "예상 범위", "불확실성", "참고용" 메시지를 우선 표시한다.
```

### 4.4 HistoryPage

파일:

```text
frontend/src/pages/HistoryPage.tsx
```

역할:

- mock 식사 기록 리스트 표시
- 주간 평균 혈당, 혈당 변동성, 가장 높은 시간대 표시

사용 컴포넌트:

```text
HistoryList
```

### 4.5 SettingsPage

파일:

```text
frontend/src/pages/SettingsPage.tsx
```

역할:

- FoodSugar AI 서비스 소개
- CGM 연결 상태 mock 표시
- 데이터 처리 안내
- 개인정보/로그 원칙 안내
- 모델 한계 표시
- 안전 문구 표시

---

## 5. 주요 컴포넌트

### AppShell

파일:

```text
frontend/src/components/AppShell.tsx
```

역할:

- 전체 배경/레이아웃
- HeaderBar
- BottomNav
- page content wrapper

### HeaderBar

파일:

```text
frontend/src/components/HeaderBar.tsx
```

역할:

- FoodSugar AI 로고 영역
- 분석 기록 버튼

### BottomNav

파일:

```text
frontend/src/components/BottomNav.tsx
```

역할:

- 홈 / 분석 / 예측 / 기록 / 설정 이동
- local state 기반 client routing

### SafetyNotice

파일:

```text
frontend/src/components/SafetyNotice.tsx
```

역할:

- 모든 혈당 관련 화면에 참고용/비의료 문구 표시

문구:

```text
본 결과는 의료 진단이나 치료 목적이 아닌 식습관 관리 참고용입니다.
저혈당 또는 고혈당 증상이 있으면 실제 측정값을 확인하고 의료진과 상의하세요.
```

### UploadPanel

파일:

```text
frontend/src/components/UploadPanel.tsx
```

역할:

- 이미지 drag/drop
- 파일 선택
- preview
- 분석 시작 버튼

### GlucosePredictionCards

파일:

```text
frontend/src/components/GlucosePredictionCards.tsx
```

역할:

- 30/60/90분 예측 카드 표시

표시 정책:

```text
30분: 숫자 중심
60분: 범위 + 참고 수치
90분: 범위 + 불확실성 중심
```

### GlucoseChart

파일:

```text
frontend/src/components/GlucoseChart.tsx
```

역할:

- Recharts 기반 혈당 변화 가능성 그래프
- 현재 / 30분 / 60분 / 90분 / 120분 축
- 목표 범위 70~180 mg/dL 영역 표시
- 예측 범위 band 표시
- 예측 line 표시

### RiskSignalCard

파일:

```text
frontend/src/components/RiskSignalCard.tsx
```

역할:

- 저혈당 가능성 신호
- 고혈당 가능성 신호

금지 표현:

```text
저혈당입니다
고혈당입니다
```

---

## 6. API 연결 구조

파일:

```text
frontend/src/lib/api.ts
```

기본 API 주소:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
```

구현된 함수:

```ts
analyzeFoodImage(file: File): Promise<AnalysisResult>
predictGlucose(payload: CGMForecastPayload): Promise<GlucosePredictionResult>
getMockAnalysis(imageUrl?: string): AnalysisResult
getMockPrediction(): GlucosePredictionResult
```

사용 endpoint:

```text
POST /predict/analyze
POST /predict/cgm-forecast-enriched-events
```

fallback 정책:

```text
backend가 꺼져 있거나 요청이 실패하면 mock data를 반환한다.
UI는 멈추지 않고 분석/예측 화면을 계속 보여준다.
mock fallback일 때 isDemo=true로 표시한다.
```

---

## 7. Mock Data 구조

파일:

```text
frontend/src/data/mockData.ts
```

주요 type:

```ts
AnalysisResult
GlucosePredictionResult
CGMForecastPayload
PageKey
```

mock 음식 분석:

```text
음식명: 비빔밥
신뢰도: 92%
칼로리: 560 kcal
탄수화물: 85 g
당류: 8 g
단백질: 22 g
지방: 15 g
식이섬유: 6 g
혈당 위험도: 높음
예상 혈당 상승 가능성: +48 mg/dL
피크 예상 시간: 식후 60분
```

mock CGM 예측:

```text
현재 혈당: 112 mg/dL
30분: 138 mg/dL, 범위 120~152
60분: 160 mg/dL, 범위 126~176
90분: 142 mg/dL, 범위 104~205, 불확실성 높음
```

---

## 8. 디자인 방향

현재 UI는 FoodSugar AI의 safe wellness positioning에 맞춰 병원/의료기기 느낌보다 식습관 관리 앱 느낌으로 구성했다.

색상:

```text
background: cream #F8F6EC
surface/card: #FFFDF5
primary green: #1F7A43
dark green: #123524
soft green: #E8F3E8
border: #D8E8D2
warning cream/orange: #FFF8E8 / #F97316
```

스타일:

```text
따뜻한 크림 배경
세이지/포레스트 그린 포인트
둥근 카드
부드러운 그림자
큰 숫자와 짧은 설명
하단 탭 내비게이션
반응형 중앙 레이아웃
```

---

## 9. 안전 UX 원칙

웹앱에서 지킨 원칙:

```text
1. 혈당 관련 결과는 참고용이라고 표시한다.
2. 의료 진단이나 치료 지침이라고 말하지 않는다.
3. 저혈당/고혈당은 확정 표현이 아니라 가능성 신호로 표현한다.
4. 90분 예측은 단일 수치보다 범위와 불확실성을 우선 표시한다.
5. 실제 측정값과 증상을 우선 확인하라고 안내한다.
6. backend 오류 시 mock fallback으로 UI가 계속 동작한다.
7. 음식 인식 confidence가 낮으면 음식명 확인을 유도한다.
```

금지 표현 검색에서 제외한 문구:

```text
혈당을 정확히 예측
저혈당입니다
고혈당입니다
인슐린을 조절
치료에 사용
당뇨병을 진단
약을 조절
```

---

## 10. 실행 방법

frontend 폴더로 이동:

```bash
cd /Users/sangrok/foodsugar-ai/frontend
```

의존성 설치:

```bash
npm install --cache ./.npm-cache
```

개발 서버 실행:

```bash
npm run dev -- --port 5173
```

브라우저 접속:

```text
http://127.0.0.1:5173/
```

빌드:

```bash
npm run build
```

---

## 11. 검증 결과

설치:

```text
npm install --cache ./.npm-cache
success
```

빌드:

```text
npm run build
success
```

dev server:

```text
VITE ready
Local: http://127.0.0.1:5173/
```

HTTP 확인:

```text
curl -I http://127.0.0.1:5173/
HTTP/1.1 200 OK
```

주의:

```text
npm install 시 moderate vulnerability 2개가 보고됨.
Recharts 포함으로 build 시 500KB chunk size warning이 있음.
현재 MVP 실행과 빌드를 막지는 않으므로 force fix는 하지 않음.
```

---

## 12. 현재 변경 범위

현재 변경은 `frontend/` 새 폴더 중심이다.

수정하지 않은 것:

```text
config/kfood_production_ensemble_config.json
src/classifier/
data/models/
기존 classifier checkpoint
기존 ensemble weight
기존 classifier training code
기존 glucose training code
```

현재 git 상태상 새 변경:

```text
?? frontend/
```

---

## 13. 다음 단계 추천

1. `.gitignore`에 frontend build/cache 관련 항목 정리 여부 결정
   - `frontend/node_modules/`
   - `frontend/dist/`
   - `frontend/.npm-cache/`
   - `frontend/tsconfig.tsbuildinfo`
2. 실제 backend 서버와 연결해서 `/predict/analyze` 동작 확인
3. 실제 backend 서버와 연결해서 `/predict/cgm-forecast-enriched-events` 동작 확인
4. 이미지 업로드 후 mock fallback badge가 보이는지 사용자 테스트
5. 90분 예측 UI가 숫자보다 범위/불확실성 중심으로 보이는지 시각 검수
6. 웹앱 전용 lint/test 추가 여부 결정

