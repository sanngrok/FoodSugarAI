# FoodSugar AI 현재 진행상황 정리 - 2026-05-31

## 0. 한 줄 요약

FoodSugar AI는 현재 **K-Food 음식 이미지 분류 92.02% 운영 후보**, **영양성분 기반 혈당 부담 참고 기능**, **OhioT1DM 기반 30/60/90분 CGM 혈당 변화 예측**, **Safe Wellness Pilot 문서/안전 테스트**, **Vite React 웹 MVP**까지 연결된 상태다.

현재 작업 브랜치:

```text
webapp
```

현재 핵심 방향:

```text
모델 추가 개발보다 웹 MVP 안정화, 실제 FastAPI 연동 검수, mock fallback, 90분 불확실성 UX, 프론트 안전 테스트를 우선한다.
```

혈당 관련 결과는 모두 **의료 진단이나 치료 지침이 아닌 식습관 관리 참고용**이다.

---

## 1. K-Food 음식 이미지 분류 상태

### 1.1 최종 운영 후보

현재 음식 이미지 분류 운영 후보:

```text
kfood_92_hflip_7model_weighted_2026_05_16
```

운영 config:

```text
config/kfood_production_ensemble_config.json
```

검증 기준:

```text
data/raw/korean_food_fixed_v1/val
```

검증 성능:

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| TTA | `hflip` |

### 1.2 Ensemble 구성

| Model | Weight | Checkpoint |
|---|---:|---|
| `food_lewm_b0` | `0.14236057323734336` | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| `b3_full_fixed_v1` | `0.52949003398239` | `data/models/efficientnet_korean_b3_full_fixed_v1.pt` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` | `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` | `data/models/efficientnet_korean_b3_probe_fixed_v1.pt` |
| `b3_cont_fixed_v1` | `0.00496452020109459` | `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` |
| `b0_supervised_only` | `0.0033210487744569726` | `data/models/food_lewm_b0_supervised_only_ft10.pt` |

### 1.3 주의점

현재 92.02%는 `fixed_v1/val` 기준 verified best이다. 다만 ensemble weight가 같은 validation split에서 탐색되었기 때문에, 별도 holdout 또는 실제 사용자 이미지에서 추가 검증이 필요하다.

---

## 2. 음식 영양성분 및 혈당 부담 참고 기능

음식 분류 결과를 nutrition DB와 연결했다.

흐름:

```text
음식 이미지
-> K-Food classifier
-> 음식명
-> nutrition DB
-> 칼로리/탄수화물/당류/단백질/지방/식이섬유/GI
-> 혈당 부담 참고 점수
```

주요 파일:

```text
src/nutrition/nutrition_db.py
src/predictor/sugar_predictor.py
src/glucose/risk.py
data/processed/kfood_nutrition_db.json
```

현재 운영 기본값:

```text
settings.use_xgboost_predictor_model = False
```

이유:

- K-Food classifier 안정성을 우선
- XGBoost eager loading과 torch/MPS 충돌 가능성 회피
- rule-based fallback으로도 혈당 부담 참고 점수 제공 가능

---

## 3. OhioT1DM CGM 혈당 예측 상태

### 3.1 데이터

원본:

```text
/Users/sangrok/Downloads/OhioT1DM
```

변환 결과:

```text
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
```

대략적인 데이터 규모:

| 항목 | 값 |
|---|---:|
| total rows | 약 `166,533` |
| train rows | 약 `134,790` |
| test rows | 약 `31,743` |
| patients | `12` |
| years | `2018`, `2020` |
| glucose range | `40-400 mg/dL` |

### 3.2 최신 모델

모델 타입:

```text
enriched_long_horizon
```

모델 artifact:

```text
data/processed/glucose_models_enriched/glucose_forecast_30m.joblib
data/processed/glucose_models_enriched/glucose_forecast_60m.joblib
data/processed/glucose_models_enriched/glucose_forecast_90m.joblib
```

feature 수:

```text
66
```

최신 calibrated MAE:

| Horizon | MAE |
|---:|---:|
| 30m | `12.998` |
| 60m | `22.633` |
| 90m | `29.606` |

### 3.3 Prediction interval

| Horizon | Observed Coverage | Mean Width | Uncertainty |
|---:|---:|---:|---|
| 30m | `0.919` | `64.487` | high |
| 60m | `0.915` | `107.109` | high |
| 90m | `0.912` | `136.114` | high |

해석:

- 30분: 참고용 수치 예측 중심
- 60분: 수치 + 범위 + 가능성 신호
- 90분: 단일 숫자보다 범위 + 높은 불확실성 중심

---

## 4. Safe Wellness Pilot 정리 상태

혈당 기능은 의료 판단 도구가 아니라 **웰니스/식습관 관리 보조 기능**으로 포지셔닝했다.

생성 문서:

```text
docs/GLUCOSE_PRODUCT_POSITIONING.md
docs/GLUCOSE_SAFETY_WORDING_GUIDE.md
docs/PILOT_STUDY_PROTOCOL.md
docs/PILOT_USER_CONSENT_DRAFT.md
docs/PILOT_DATA_SCHEMA.md
docs/GLUCOSE_DATA_GOVERNANCE.md
docs/GLUCOSE_PRIVACY_SECURITY_CHECKLIST.md
docs/GLUCOSE_LOGGING_POLICY.md
docs/GLUCOSE_UX_SPEC.md
docs/GLUCOSE_API_RESPONSE_EXAMPLES.md
docs/EXTERNAL_VALIDATION_PLAN.md
docs/KOREAN_FOOD_CGM_VALIDATION_PLAN.md
```

안전 원칙:

```text
1. 혈당 결과는 참고용
2. 의료 진단/치료 지침 아님
3. 저혈당/고혈당은 가능성 신호로만 표현
4. 90분 예측은 범위와 불확실성 중심
5. 실제 측정값과 증상을 우선 확인
6. 의료진과 상의 안내
```

---

## 5. FastAPI Backend 상태

진입점:

```text
api/main.py
```

실행 명령:

```bash
cd /Users/sangrok/foodsugar-ai
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

주요 endpoint:

```text
GET  /health
POST /predict/analyze
POST /predict/glucose-risk
POST /predict/cgm-forecast
POST /predict/cgm-forecast-enriched
POST /predict/cgm-forecast-enriched-events
```

최근 실제 연동 확인:

```text
GET /health
status: ok
classifier_ready: true
predictor_ready: true
```

```text
POST /predict/analyze
result: success
classification fields: food_key, food_name_ko, confidence, top5
nutrition: present
risk_label: present
reference_notice: 참고용 문구 포함
```

```text
POST /predict/cgm-forecast-enriched-events
result: success
horizons: [30, 60, 90]
prediction_intervals_mg_dl: present
event_probabilities: present
90m uncertainty_message: present
reference_notice: 참고용 문구 포함
```

---

## 6. 최근 API 연결부 최소 수정

실제 프론트-백엔드 연동 중 발견한 문제:

```text
long-horizon glucose regressor는 66개 feature를 사용한다.
기존 event classifier는 39개 feature로 학습되어 있었다.
API가 동일한 66-feature matrix를 event classifier에 넣으면서 422가 발생했다.
```

수정 파일:

```text
src/glucose/forecasting.py
```

수정 내용:

- event classifier에 `n_features_in_`이 있으면 해당 feature 수만큼 prefix feature만 사용
- event classifier가 현재 입력보다 더 많은 feature를 요구하면 해당 classifier만 skip
- 회귀 예측, interval, uncertainty는 유지

추가 테스트:

```text
tests/test_glucose_event_classifier_feature_compat.py
```

검증:

```text
python3 -m pytest tests/test_glucose_event_classifier_feature_compat.py tests/test_glucose_forecasting_eval.py tests/test_api.py -q
20 passed
```

전체 backend test:

```text
python3 -m pytest tests/ -q
73 passed
```

---

## 7. Web MVP 상태

프론트엔드 위치:

```text
frontend/
```

실행 명령:

```bash
cd /Users/sangrok/foodsugar-ai/frontend
npm run dev -- --port 5173
```

접속 URL:

```text
http://127.0.0.1:5173/
```

기술 스택:

```text
Vite
React
TypeScript
Tailwind CSS
Recharts
lucide-react
Vitest
Testing Library
```

페이지:

```text
HomePage
AnalysisPage
PredictionPage
HistoryPage
SettingsPage
```

핵심 흐름:

```text
음식 업로드
-> /predict/analyze 호출
-> 실패 시 mockAnalysis fallback
-> 음식 분석/영양성분/혈당 부담 표시
-> /predict/cgm-forecast-enriched-events 호출
-> 실패 시 mockPrediction fallback
-> 30/60/90분 예측, interval, uncertainty, risk signal 표시
```

---

## 8. Frontend 구조

핵심 파일:

```text
frontend/src/App.tsx
frontend/src/lib/api.ts
frontend/src/data/mockData.ts
frontend/src/styles.css
```

컴포넌트:

```text
frontend/src/components/AppShell.tsx
frontend/src/components/HeaderBar.tsx
frontend/src/components/BottomNav.tsx
frontend/src/components/SafetyNotice.tsx
frontend/src/components/UploadPanel.tsx
frontend/src/components/FoodPreviewCard.tsx
frontend/src/components/NutritionCard.tsx
frontend/src/components/GlucoseRiskCard.tsx
frontend/src/components/GlucosePredictionCards.tsx
frontend/src/components/GlucoseChart.tsx
frontend/src/components/RiskSignalCard.tsx
frontend/src/components/HistoryList.tsx
```

API 연결:

```text
frontend/src/lib/api.ts
```

기본 backend 주소:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
```

프론트 API 함수:

```ts
analyzeFoodImage(file)
predictGlucose(payload)
getMockAnalysis(imageUrl)
getMockPrediction()
```

---

## 9. Mock fallback 검수

프론트는 backend가 꺼져 있어도 UI가 멈추지 않도록 mock fallback을 사용한다.

테스트 파일:

```text
frontend/src/test/apiFallback.test.ts
```

검수 항목:

- `/predict/analyze` 실패 시 mock analysis 사용
- `/predict/cgm-forecast-enriched-events` 실패 시 mock prediction 사용
- mock fallback일 때 `isDemo=true`
- 90분 mock interval과 참고용 message 유지

실제 long-horizon backend와 맞추기 위해 sample CGM readings를 다음처럼 조정했다.

```text
기존: 13개
현재: 37개
```

이유:

```text
long-horizon feature에서 120/180분 window feature를 만들기 위해 더 긴 recent readings가 필요하다.
```

---

## 10. 90분 UI 안전 검수

90분 예측은 불확실성이 크므로 웹 UI에서 단일 숫자를 크게 강조하지 않는다.

테스트 파일:

```text
frontend/src/test/safetyUi.test.tsx
```

검수 항목:

```text
90분 카드에 104~205 mg/dL 범위 표시
불확실성 높음 문구 표시
범위 우선 badge 표시
저혈당/고혈당은 가능성 신호로 표현
금지 의료 표현 없음
```

금지 표현:

```text
혈당을 정확히 예측
저혈당입니다
고혈당입니다
인슐린을 조절
치료에 사용
당뇨병을 진단
약을 조절
```

production frontend source 검색 결과:

```text
매칭 없음
```

---

## 11. Frontend 검증 상태

프론트 테스트:

```bash
cd /Users/sangrok/foodsugar-ai/frontend
npm run test
```

결과:

```text
2 test files passed
5 tests passed
```

프론트 빌드:

```bash
npm run build
```

결과:

```text
success
```

주의:

```text
Vite build에서 Recharts 포함으로 500KB chunk size warning이 있음.
npm audit moderate vulnerability 2개가 있음.
현재 MVP 실행과 build/test를 막지는 않으므로 force fix는 하지 않음.
```

---

## 12. .gitignore 정리

수정 파일:

```text
.gitignore
```

추가 항목:

```text
frontend/node_modules/
frontend/dist/
frontend/.npm-cache/
frontend/tsconfig.tsbuildinfo
```

목적:

```text
frontend dependency, build artifact, local npm cache, TypeScript incremental cache가 git에 올라가지 않도록 정리
```

---

## 13. 현재 git 상태

현재 `webapp` 브랜치 기준 변경 상태:

```text
M .gitignore
M src/glucose/forecasting.py
M reports/glucose_forecasting/artifact_validation_report.json
M reports/glucose_forecasting/leakage_audit.json
?? FOODSUGAR_FULL_PROJECT_SUBMISSION_DRAFT_2026-05-27.md
?? FOODSUGAR_WEBAPP_MVP_STRUCTURE_2026-05-27.md
?? FOODSUGAR_WEBAPP_NEXT_STAGE_VALIDATION_2026-05-27.md
?? frontend/
?? tests/test_glucose_event_classifier_feature_compat.py
```

참고:

```text
reports/glucose_forecasting/artifact_validation_report.json
reports/glucose_forecasting/leakage_audit.json
```

위 두 파일은 glucose artifact validation 실행 과정에서 갱신된 것으로 보인다.

---

## 14. 최근 생성한 주요 MD

프로젝트 전체 제출용 초안:

```text
FOODSUGAR_FULL_PROJECT_SUBMISSION_DRAFT_2026-05-27.md
```

웹 MVP 구조 정리:

```text
FOODSUGAR_WEBAPP_MVP_STRUCTURE_2026-05-27.md
```

웹 MVP 다음 단계 검증 결과:

```text
FOODSUGAR_WEBAPP_NEXT_STAGE_VALIDATION_2026-05-27.md
```

현재 최신 진행상황:

```text
FOODSUGAR_CURRENT_PROGRESS_SUMMARY_2026-05-31.md
```

---

## 15. 실행 명령 정리

### 서버 종료

```bash
lsof -ti tcp:8000 | xargs -r kill
lsof -ti tcp:5173 | xargs -r kill
```

### Backend 실행

```bash
cd /Users/sangrok/foodsugar-ai
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

### Frontend 실행

```bash
cd /Users/sangrok/foodsugar-ai/frontend
npm run dev -- --port 5173
```

### 접속

```text
http://127.0.0.1:5173/
```

### Backend 확인

```bash
curl http://127.0.0.1:8000/health
```

---

## 16. 다음 단계 추천

현재 모델 개발보다 웹앱 안정화와 제출/시연 준비가 우선이다.

추천 순서:

1. `webapp` 브랜치 변경 파일 리뷰
2. 필요하면 report JSON 변경을 commit에 포함할지 제외할지 결정
3. 실제 브라우저에서 음식 업로드 -> 분석 -> 혈당 예측 flow 수동 검수
4. backend가 꺼졌을 때 mock fallback badge가 보이는지 확인
5. 90분 예측 UI가 숫자보다 범위/불확실성 중심인지 시각 검수
6. `.gitignore` 적용 후 `frontend/node_modules`, `dist`, `.npm-cache`가 git에 안 잡히는지 재확인
7. PR 또는 main merge 전 `npm run test`, `npm run build`, `python3 -m pytest tests/ -q` 재실행

현재 기준으로는 **웹 MVP와 backend 실제 연동 모두 작동 확인된 상태**다.

