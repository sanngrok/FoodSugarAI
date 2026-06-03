# FoodSugar AI Web MVP 다음 단계 검증 결과 - 2026-05-27

## Summary

요청한 순서대로 다음 단계를 진행했다.

```text
1. .gitignore 정리
2. 실제 FastAPI 연동 확인
3. mock fallback 검수
4. 90분 UI 문구/구조 검수
5. 프론트 전용 안전 테스트 추가
```

기존 classifier checkpoint, `data/models/`, classifier training code, glucose training code는 수정하지 않았다.

## 1. .gitignore 정리

수정 파일:

```text
.gitignore
```

추가한 제외 항목:

```text
frontend/node_modules/
frontend/dist/
frontend/.npm-cache/
frontend/tsconfig.tsbuildinfo
```

목적:

- frontend dependency, build artifact, local npm cache, TypeScript incremental cache가 git에 올라가지 않도록 정리

## 2. 실제 FastAPI 연동 확인

FastAPI 서버 실행:

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

서버 기동 결과:

```text
production ensemble config 로드 성공
7개 음식 분류 모델 로드 성공
SugarPredictor rule-based fallback 사용
Application startup complete
```

Health check:

```text
GET /health
status: ok
classifier_ready: true
predictor_ready: true
```

음식 분석 endpoint:

```text
POST /predict/analyze
result: success
classification fields: food_key, food_name_ko, confidence, top5
nutrition: present
risk_label: 주의
reference_notice: 참고용 문구 포함
```

혈당 예측 endpoint:

```text
POST /predict/cgm-forecast-enriched-events
result: success
horizons: [30, 60, 90]
prediction_intervals_mg_dl: present
event_probabilities: present
90m uncertainty_message: present
reference_notice: 참고용 문구 포함
```

## 3. API 연결부 최소 수정

실제 연동 중 발견한 문제:

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

- event classifier에 `n_features_in_`이 있으면 해당 feature 수만큼 prefix feature를 사용
- event classifier가 현재 feature보다 더 많은 feature를 요구하면 해당 classifier만 skip
- regression forecast, interval, uncertainty는 유지

추가 테스트:

```text
tests/test_glucose_event_classifier_feature_compat.py
```

검증:

```text
python3 -m pytest tests/test_glucose_event_classifier_feature_compat.py tests/test_glucose_forecasting_eval.py tests/test_api.py -q
20 passed
```

## 4. mock fallback 검수

수정 파일:

```text
frontend/src/data/mockData.ts
```

수정 내용:

- 실제 long-horizon backend가 120/180분 window feature를 만들 수 있도록 sample CGM readings를 `13개`에서 `37개`로 증가

프론트 테스트:

```text
frontend/src/test/apiFallback.test.ts
```

검수 항목:

- `/predict/analyze` 실패 시 mockAnalysis 사용
- `/predict/cgm-forecast-enriched-events` 실패 시 mockPrediction 사용
- mock fallback일 때 `isDemo=true`
- 90분 mock interval과 참고용 메시지 유지

## 5. 90분 UI 문구/구조 검수

프론트 테스트:

```text
frontend/src/test/safetyUi.test.tsx
```

검수 항목:

- 90분 카드에 `104~205 mg/dL` 범위 표시
- `불확실성 높음` 문구 표시
- `범위 우선` badge 표시
- 저혈당/고혈당은 “가능성 신호”로만 표현
- 금지 의료 표현이 UI component에 없음

금지 표현 검색:

```bash
rg -n "혈당을 정확히 예측|저혈당입니다|고혈당입니다|인슐린을 조절|치료에 사용|당뇨병을 진단|약을 조절" frontend/src --glob '!**/test/**'
```

결과:

```text
production frontend source에서 매칭 없음
```

참고:

```text
현재 로컬 환경에는 headless Chrome/Playwright CLI가 없어 자동 스크린샷 검수는 수행하지 못했다.
대신 DOM 기반 frontend test와 실제 in-app browser 화면 확인 대상으로 90분 UI 구조를 고정했다.
```

## 6. 프론트 전용 안전 테스트 추가

추가 파일:

```text
frontend/vitest.config.ts
frontend/src/test/setup.ts
frontend/src/test/apiFallback.test.ts
frontend/src/test/safetyUi.test.tsx
```

추가 script:

```json
"test": "vitest run"
```

프론트 테스트 결과:

```text
npm run test
2 test files passed
5 tests passed
```

프론트 빌드 결과:

```text
npm run build
success
```

주의:

```text
Vite build에서 Recharts 포함으로 500KB chunk size warning이 계속 표시된다.
npm audit moderate vulnerability 2개가 계속 표시된다.
현재 MVP 실행과 build/test를 막지는 않으므로 force fix는 하지 않았다.
```

## 7. 현재 상태

현재 `webapp` 브랜치 변경 범위:

```text
.gitignore
src/glucose/forecasting.py
tests/test_glucose_event_classifier_feature_compat.py
frontend/
FOODSUGAR_FULL_PROJECT_SUBMISSION_DRAFT_2026-05-27.md
FOODSUGAR_WEBAPP_MVP_STRUCTURE_2026-05-27.md
FOODSUGAR_WEBAPP_NEXT_STAGE_VALIDATION_2026-05-27.md
```

핵심 결론:

```text
FastAPI 실제 연동 성공
프론트 mock fallback 테스트 통과
90분 UI safety wording 테스트 통과
frontend build 성공
backend compatibility test 통과
```

