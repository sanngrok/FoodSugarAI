# FoodSugar AI Analyze API Glucose Risk Integration Update

작성일: 2026-06-05  
작업 범위: `/predict/analyze` 통합 API 혈당 위험도 개선, K-Food GI proxy 보강, 프론트 위험도 표시 우선순위 변경  
상태: 테스트 및 빌드 통과

---

## 1. 작업 배경

이전 테스트에서 `/predict/analyze` 통합 API는 이미지 분류 자체는 잘 동작했지만, 아래 음식들이 모두 혈당 위험도 `낮음`으로 표시되는 문제가 있었다.

```text
비빔밥
김밥
떡볶이
라면
후라이드치킨
피자
```

반면 `/predict/glucose-risk` 단독 API는 영양성분을 직접 넣었을 때 다음처럼 잘 구분했다.

```text
bibimbap_like      → 주의
high_sugar_drink  → 높음
very_high_carb    → 높음
```

따라서 문제의 핵심은 모델 분류가 아니라, `/predict/analyze` 통합 응답과 프론트 표시 로직이 기존 legacy `risk_label`에 의존하고 있었던 점이었다.

---

## 2. 수정 원칙

이번 작업에서는 아래 항목을 수정하지 않았다.

```text
기존 음식분류 모델
classifier checkpoint
data/models/
src/classifier/
classifier training code
ensemble weight
```

변경한 범위는 다음으로 제한했다.

```text
API response schema
/predict/analyze response composition
K-Food nutrition GI proxy mapping
frontend risk display priority
tests
```

---

## 3. 핵심 변경 요약

### 변경 전

`/predict/analyze` 응답 구조:

```json
{
  "classification": {},
  "nutrition": {},
  "risk": {}
}
```

프론트 표시 기준:

```text
risk.risk_label 우선 사용
```

문제:

- legacy `risk`는 현재 API 설정상 XGBoost가 아니라 rule-based fallback을 사용한다.
- K-Food nutrition DB의 `glycemic_index`가 대부분 기본값 `50`이었다.
- 그래서 비빔밥, 떡볶이, 라면 같은 음식도 통합 분석에서는 낮음으로 표시되는 경향이 있었다.

### 변경 후

`/predict/analyze` 응답 구조:

```json
{
  "classification": {},
  "nutrition": {},
  "risk": {},
  "glucose_risk": {
    "score": 0,
    "level": "낮음 | 주의 | 높음",
    "factors": {},
    "reference_notice": "",
    "risk_interpretation": "",
    "safety_warning": ""
  }
}
```

프론트 표시 기준:

```text
glucose_risk.level / glucose_risk.score 우선 사용
fallback으로만 risk.risk_label 사용
```

---

## 4. Backend 변경사항

### 4.1 FullAnalysisResponse에 glucose_risk 추가

수정 파일:

```text
api/schemas/models.py
```

변경 내용:

```python
class FullAnalysisResponse(BaseModel):
    classification: ClassificationResponse
    nutrition: NutritionInput | None
    risk: RiskResponse
    glucose_risk: GlucoseRiskResponse | None = None
```

의도:

- 기존 `risk` 필드는 유지해서 API 호환성을 보존한다.
- 새 점수 기반 결과는 `glucose_risk`로 별도 추가한다.

---

### 4.2 /predict/analyze에서 glucose_risk 계산 추가

수정 파일:

```text
api/routers/predict.py
```

변경 내용:

- 기존에는 음식 분류 후 `predictor.predict()` 결과만 `risk`로 내려줬다.
- 이제 nutrition 정보가 있으면 `score_glucose_risk()`를 추가 호출한다.
- 결과를 `GlucoseRiskResponse`로 변환해 `glucose_risk` 필드에 포함한다.

흐름:

```text
image
→ classification
→ get_nutrition(food_key)
→ legacy risk
→ score_glucose_risk(nutrition_info, portion_g)
→ response.glucose_risk
```

---

### 4.3 legacy risk label을 위험 대신 높음으로 변경

수정 파일:

```text
config/settings.py
src/predictor/sugar_predictor.py
api/main.py
```

변경 전:

```text
낮음 / 주의 / 위험
```

변경 후:

```text
낮음 / 주의 / 높음
```

이유:

- 앱이 의료 진단처럼 보이지 않게 하기 위해 `위험`보다 완화된 웰니스 표현인 `높음`을 사용한다.
- 사용자 요청에 따라 문구를 `위험` 대신 `높음/주의/낮음`으로 유지한다.

---

### 4.4 serving_advice 문구 완화

수정 파일:

```text
src/predictor/sugar_predictor.py
```

변경 전에는 아래와 같은 문구가 있었다.

```text
혈당 급상승 위험이 높습니다.
섭취를 피하거나...
식후 운동을 권장합니다.
```

변경 후:

```text
혈당 상승 가능성 신호가 높은 편입니다.
단일 판단이 아니라 실제 측정값과 함께 참고하세요.
```

의도:

- 진단/치료/행동 지시처럼 보이는 표현을 줄인다.
- 혈당 관련 결과는 계속 참고용/가능성 신호 중심으로 유지한다.

---

## 5. K-Food GI Proxy Mapping 보강

수정 파일:

```text
src/nutrition/nutrition_db.py
```

추가한 내용:

```python
KFOOD_GI_PROXY: dict[str, float] = {
    ...
}
```

적용 대상:

```text
K-Food 56개 class 전체
```

적용 방식:

- 원본 `data/processed/kfood_nutrition_db.json`은 수정하지 않았다.
- DB 로드 시 `glycemic_index`가 기본값 `50.0`인 경우에만 proxy 값을 적용한다.
- 원본에 65처럼 별도 값이 들어있는 경우는 그대로 유지한다.

예시:

| 음식 | 기존 GI | proxy 적용 후 GI |
|---|---:|---:|
| 비빔밥 | 50 | 68 |
| 김밥 | 50 | 62 |
| 떡볶이 | 50 | 78 |
| 라면 | 50 | 72 |
| 피자 | 50 | 62 |
| 후라이드치킨 | 50 | 45 |

의도:

- 모든 음식이 기본 GI 50에 묶여 낮음으로 쏠리는 문제를 완화한다.
- 혈당 위험도 score가 탄수화물, 당류, portion, GI proxy를 함께 반영하도록 한다.

주의:

- 이 GI 값은 의료 측정값이 아니라 웰니스 앱용 proxy다.
- 실제 개인 혈당 반응은 CGM/측정값과 함께 참고해야 한다.

---

## 6. Frontend 변경사항

### 6.1 AnalysisResult 타입 확장

수정 파일:

```text
frontend/src/data/mockData.ts
```

추가 필드:

```ts
glucoseRiskScore?: number;
glucoseRiskFactors?: Record<string, number>;
```

라벨 타입 변경:

```ts
glucoseRiskLevel: "낮음" | "주의" | "높음";
```

---

### 6.2 API parsing에서 glucose_risk 우선 사용

수정 파일:

```text
frontend/src/lib/api.ts
```

변경 전:

```ts
glucoseRiskLevel: normalizeRiskLevel(risk.risk_label)
```

변경 후:

```ts
glucoseRiskLevel: normalizeRiskLevel(glucoseRisk.level || risk.risk_label)
glucoseRiskScore: Math.round(glucoseRisk.score)
glucoseRiskFactors: glucoseRisk.factors
```

즉, `/predict/analyze` 응답에 `glucose_risk`가 있으면 프론트는 legacy `risk_label`보다 score 기반 결과를 우선 표시한다.

---

### 6.3 GlucoseRiskCard에 score 표시 추가

수정 파일:

```text
frontend/src/components/GlucoseRiskCard.tsx
```

추가 표시:

```text
영양성분 기반 42/100점
```

또한 score bar를 추가했다.

의도:

- 단순 `낮음/주의/높음` 라벨만 보여주는 대신, 사용자가 0~100 참고 점수를 같이 볼 수 있게 한다.
- 기존 risk label보다 glucose_risk score 결과를 우선 표시한다는 점을 UI에서도 드러낸다.

---

## 7. 실제 API 확인 결과

테스트 서버:

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

테스트 endpoint:

```text
POST /predict/analyze
```

테스트 데이터:

```text
data/raw/korean_food_fixed_v1/val
```

portion:

```text
150g
```

결과:

| 음식 | 예측 음식 | legacy risk | glucose_risk score | glucose_risk level | 적용 GI |
|---|---|---|---:|---|---:|
| 비빔밥 | 비빔밥 | 주의 | 41.98 | 주의 | 68 |
| 떡볶이 | 떡볶이 | 주의 | 59.65 | 주의 | 78 |
| 라면 | 라면 | 주의 | 45.28 | 주의 | 72 |
| 피자 | 피자 | 낮음 | 32.53 | 낮음 | 62 |

이전에는 비빔밥/떡볶이/라면까지 모두 낮음으로 표시되는 경향이 있었지만, 이번 변경 후에는 score 기반 결과가 통합 API 응답에 포함되고 프론트 표시 기준도 score 기반 결과를 우선 사용하게 되었다.

---

## 8. 검증 결과

### 8.1 Python 문법 검사

실행:

```bash
python3 -m py_compile \
  api/schemas/models.py \
  api/routers/predict.py \
  src/nutrition/nutrition_db.py \
  src/predictor/sugar_predictor.py \
  config/settings.py
```

결과:

```text
통과
```

---

### 8.2 Backend 전체 테스트

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
74 passed
```

---

### 8.3 Frontend 테스트

실행:

```bash
cd frontend
npm run test
```

결과:

```text
Test Files  3 passed
Tests       12 passed
```

---

### 8.4 Frontend 빌드

실행:

```bash
cd frontend
npm run build
```

결과:

```text
✓ built
```

참고:

- Vite bundle size warning은 계속 존재한다.
- Recharts 등 프론트 번들 크기 때문이며, 이번 기능 변경의 실패는 아니다.

---

## 9. 추가된 테스트

수정 파일:

```text
tests/test_api.py
tests/test_predictor.py
frontend/src/test/apiFallback.test.ts
```

추가/변경된 검증:

1. `/predict/analyze` 응답에 `glucose_risk`가 포함되는지 확인
2. `glucose_risk.level`이 `낮음/주의/높음` 중 하나인지 확인
3. K-Food GI proxy가 56개 class를 모두 커버하는지 확인
4. 프론트가 legacy `risk.risk_label`보다 `glucose_risk.level/score`를 우선 사용하는지 확인

프론트 테스트 핵심:

```text
legacy risk_label = 낮음
glucose_risk.level = 주의
```

이 경우 프론트 결과는 `주의`로 표시되어야 한다.

---

## 10. 변경 파일 목록

Backend:

```text
api/main.py
api/routers/predict.py
api/schemas/models.py
config/settings.py
src/nutrition/nutrition_db.py
src/predictor/sugar_predictor.py
```

Frontend:

```text
frontend/src/components/GlucoseRiskCard.tsx
frontend/src/data/mockData.ts
frontend/src/lib/api.ts
```

Tests:

```text
tests/test_api.py
tests/test_predictor.py
frontend/src/test/apiFallback.test.ts
```

참고:

이전 작업에서 수정된 아래 파일들도 현재 작업트리에 남아 있다.

```text
frontend/src/App.tsx
frontend/src/components/FoodPreviewCard.tsx
frontend/src/pages/AnalysisPage.tsx
```

이 파일들은 backend fallback 실패 시 데모 결과를 실제 분석처럼 보이지 않게 하기 위한 이전 안전 UX 변경이다.

---

## 11. 현재 판단

### 해결된 점

- `/predict/analyze`가 score 기반 `glucose_risk`를 함께 반환한다.
- 프론트가 `glucose_risk`를 우선 표시한다.
- K-Food 56개 class에 GI proxy가 적용된다.
- 비빔밥/떡볶이/라면이 더 이상 무조건 낮음으로만 보이지 않는다.
- `위험` 대신 `높음` 표현을 사용한다.
- 기존 classifier 모델과 checkpoint는 수정하지 않았다.

### 남은 고려사항

- GI proxy는 실제 측정값이 아니라 추정값이므로 추후 근거 표를 따로 정리하면 좋다.
- 운영 배포 전에는 실제 사용자 업로드 이미지와 nutrition DB mapping을 더 넓게 검증해야 한다.
- `/predict/analyze`의 legacy `risk`와 `glucose_risk`가 둘 다 존재하므로, API 문서에서 `glucose_risk`가 표시 우선 결과임을 명시하면 좋다.
- 추후 XGBoost predictor를 다시 활성화할지 여부는 torch/MPS ensemble 충돌 가능성을 별도로 검증한 뒤 결정해야 한다.

---

## 12. 서버 상태

테스트를 위해 backend server를 잠시 실행했다.

테스트 후 서버는 종료했다.

현재 상태:

```text
http://127.0.0.1:8000/health 응답 없음
8000 서버 종료됨
```

