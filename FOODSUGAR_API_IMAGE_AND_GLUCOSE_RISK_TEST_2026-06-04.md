# FoodSugar AI API Image Classification and Glucose Risk Test

작성일: 2026-06-04  
테스트 위치: `/Users/sangrok/foodsugar-ai`  
테스트 목적: 이미지 음식 분류와 혈당 위험도 예측이 실제 API에서 정상 동작하는지 확인

---

## 1. 테스트 요약

이번 테스트에서는 FastAPI backend를 실제로 실행한 뒤 아래 항목을 확인했다.

1. backend server가 정상 실행되는지
2. 운영 음식 분류 ensemble이 로드되는지
3. `/predict/analyze` 통합 API가 이미지 업로드를 받아 음식 분류, 영양성분 조회, 혈당 위험도 예측까지 반환하는지
4. `/predict/classify`가 56개 K-Food 클래스에 대해 정상 분류하는지
5. `/predict/risk`, `/predict/glucose-risk`가 영양성분 기반 혈당 위험도를 낮음/주의/높음 또는 위험으로 구분하는지

---

## 2. 서버 실행

처음에는 `uvicorn` 명령이 shell PATH에 없어서 실패했다.

```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000
```

결과:

```text
zsh:1: command not found: uvicorn
```

이후 아래 명령으로 정상 실행했다.

```bash
python3 -m uvicorn api.main:app --host 127.0.0.1 --port 8000
```

---

## 3. 서버 로딩 상태

서버 startup 로그에서 운영 ensemble config가 정상 로드됨을 확인했다.

사용 config:

```text
config/kfood_production_ensemble_config.json
```

운영 후보 모델:

```text
kfood_92_hflip_7model_weighted_2026_05_16
```

config에 기록된 검증 성능:

```text
top1: 0.9202380952380952
top3: 0.9794642857142857
macro_f1: 0.9200379850437458
correct: 6184
num_samples: 6720
```

실제 startup 로그상 로드된 ensemble member:

```text
food_lewm_b0
b0_seed123_fixed_v1
b3_full_fixed_v1
b0_seed7_fixed_v1
b3_probe_fixed_v1
b3_cont_fixed_v1
b0_supervised_only
```

서버 health check:

```json
{
  "status": "ok",
  "version": "0.1.0",
  "classifier_ready": true,
  "predictor_ready": true
}
```

---

## 4. 중요한 확인사항

현재 backend 설정에서는 XGBoost 혈당 위험도 모델을 eager load하지 않도록 되어 있다.

startup 로그:

```text
XGBoost 모델 로드를 비활성화했습니다. 규칙 기반 fallback을 사용합니다.
```

현재 설정:

```python
use_xgboost_predictor_model: bool = False
```

즉, 이번 API 테스트에서 `/predict/analyze`와 `/predict/risk`가 사용한 위험도 예측기는 학습된 XGBoost 모델이 아니라 규칙 기반 fallback이다.

단, 별도 Python direct test에서는 `SugarPredictor(use_model=True)`로 XGBoost 모델 파일이 로드되는 것도 확인했다.

---

## 5. `/predict/analyze` 통합 API 테스트

테스트 목적:

```text
이미지 업로드 → 음식 분류 → 영양 DB 조회 → 혈당 위험도 예측
```

테스트 데이터:

```text
data/raw/korean_food_fixed_v1/val
```

테스트 클래스:

```text
비빔밥
김밥
떡볶이
라면
후라이드치킨
피자
```

portion:

```text
150 g
```

결과 요약:

```text
6 / 6 정답
```

상세 결과:

| 기대 클래스 | 예측 클래스 | confidence | 혈당 위험도 | 비고 |
|---|---:|---:|---|---|
| 비빔밥 | 비빔밥 | 0.9091 | 낮음 | 정답 |
| 김밥 | 김밥 | 0.8505 | 낮음 | 정답 |
| 떡볶이 | 떡볶이 | 0.9170 | 낮음 | 정답 |
| 라면 | 라면 | 0.6635 | 낮음 | 정답 |
| 후라이드치킨 | 후라이드치킨 | 0.9618 | 낮음 | 정답 |
| 피자 | 피자 | 0.9295 | 낮음 | 정답 |

대표 top-3 예시:

비빔밥:

```text
1. 비빔밥 0.9091
2. 불고기 0.0208
3. 알밥 0.0115
```

떡볶이:

```text
1. 떡볶이 0.9170
2. 라볶이 0.0166
3. 만두 0.0059
```

피자:

```text
1. 피자 0.9295
2. 파전 0.0058
3. 김치전 0.0050
```

판단:

- 통합 API에서 음식 분류는 정상 동작했다.
- 테스트한 6개 음식 모두 정답이었다.
- confidence도 라면을 제외하면 대부분 0.85 이상으로 안정적이었다.

---

## 6. `/predict/classify` 56클래스 Smoke Test

테스트 목적:

운영 ensemble이 API 경로에서 전체 K-Food 56개 클래스에 대해 정상적으로 동작하는지 빠르게 확인한다.

테스트 방식:

```text
data/raw/korean_food_fixed_v1/val
```

각 클래스에서 첫 번째 이미지 1장씩 선택했다.

총 샘플 수:

```text
56
```

결과:

```text
정답: 51
오답: 5
accuracy: 0.9107
elapsed_sec: 7.08
```

오답 목록:

| 기대 클래스 | 예측 클래스 | confidence | top-3 |
|---|---|---:|---|
| 갈비찜 | 족발 | 0.1561 | 족발, 양념치킨, 김치볶음밥 |
| 갈비탕 | 삼계탕 | 0.4154 | 삼계탕, 갈비탕, 곰탕_설렁탕 |
| 김치찌개 | 짬뽕 | 0.8163 | 짬뽕, 김치찌개, 수제비 |
| 된장찌개 | 불고기 | 0.3754 | 불고기, 된장찌개, 비빔밥 |
| 삼겹살 | 갈비구이 | 0.2468 | 갈비구이, 양념치킨, 삼겹살 |

낮은 confidence 정답 사례:

| 클래스 | confidence | top-3 |
|---|---:|---|
| 감자탕 | 0.6922 | 감자탕, 불고기, 된장찌개 |
| 라면 | 0.6635 | 라면, 라볶이, 짬뽕 |
| 라볶이 | 0.6342 | 라볶이, 떡볶이, 갈비찜 |
| 찜닭 | 0.6939 | 찜닭, 갈비찜, 닭볶음탕 |

판단:

- 56개 클래스 smoke test에서 91.07%가 나왔다.
- 운영 config에 기록된 전체 validation top1 92.02%와 비슷한 수준이다.
- 따라서 API에서 운영 ensemble이 정상적으로 연결되어 동작한다고 볼 수 있다.
- 단, 이 테스트는 각 클래스 1장씩만 본 smoke test이며 전체 성능 평가를 대체하지는 않는다.

---

## 7. 혈당 위험도 단독 API 테스트

테스트 endpoint:

```text
POST /predict/risk
POST /predict/glucose-risk
```

테스트 목적:

영양성분을 직접 입력했을 때 혈당 위험도가 낮음/주의/위험 또는 낮음/주의/높음으로 구분되는지 확인한다.

테스트 케이스:

```text
low_carb_chicken
bibimbap_like
high_sugar_drink
very_high_carb
```

---

### 7.1 `/predict/risk` 결과

현재 API 설정상 규칙 기반 fallback 사용.

| 케이스 | 결과 | risk_level | 설명 |
|---|---|---:|---|
| low_carb_chicken | 낮음 | 0 | 저탄수/고단백 식사 |
| bibimbap_like | 주의 | 1 | 고탄수 비빔밥형 식사 |
| high_sugar_drink | 위험 | 2 | 고당 음료 |
| very_high_carb | 위험 | 2 | 대용량 고탄수 식사 |

판단:

- 영양성분을 직접 넣으면 위험도가 낮음/주의/위험으로 구분된다.
- 규칙 기반 fallback도 기본적인 구분 능력은 있다.

---

### 7.2 `/predict/glucose-risk` 결과

`/predict/glucose-risk`는 0-100 점수 기반 참고용 혈당 위험도 점수를 반환한다.

| 케이스 | score | level |
|---|---:|---|
| low_carb_chicken | 10.69 | 낮음 |
| bibimbap_like | 52.44 | 주의 |
| high_sugar_drink | 92.50 | 높음 |
| very_high_carb | 80.60 | 높음 |

판단:

- 점수 기반 API는 직관적으로 잘 구분된다.
- 특히 고당 음료와 대용량 탄수 식사를 높은 위험도로 판단했다.
- 비빔밥형 고탄수 식사는 `주의`로 분류되었다.

---

## 8. XGBoost Direct Load 비교

API는 현재 XGBoost를 비활성화하고 있지만, 직접 Python에서 `SugarPredictor(use_model=True)`를 실행하면 모델 파일은 로드된다.

비교 결과:

| 케이스 | 규칙 기반 fallback | XGBoost direct |
|---|---|---|
| low_carb_chicken | 낮음 | 낮음 |
| bibimbap_like | 주의 | 주의 |
| high_sugar_drink | 위험 | 위험 |
| very_high_carb | 위험 | 주의 |

판단:

- XGBoost 모델 파일 자체는 존재하고 로드 가능하다.
- 현재 운영 API에서는 macOS torch/MPS ensemble inference와의 충돌 가능성을 피하기 위해 XGBoost loading이 꺼져 있다.
- 위험도 결과를 운영 UI에서 더 적극적으로 활용하려면 XGBoost 활성화 여부를 별도 검증해야 한다.

---

## 9. 발견된 문제점

### 9.1 통합 이미지 분석의 혈당 위험도 낮음 쏠림

`/predict/analyze`에서 테스트한 6개 음식은 모두 혈당 위험도가 `낮음`으로 나왔다.

대상:

```text
비빔밥
김밥
떡볶이
라면
후라이드치킨
피자
```

가능한 원인:

1. 현재 API가 XGBoost가 아니라 규칙 기반 fallback을 사용한다.
2. K-Food 영양 DB의 `glycemic_index`가 대부분 기본값 `50`이다.
3. 영양 DB 값이 per 100g 기준이며, portion scaling 이후에도 sugar/GI 기준이 보수적으로 적용된다.
4. `risk_label`과 `/glucose-risk` score API가 서로 다른 기준을 사용한다.

판단:

- 이미지 분류는 정상.
- 혈당 위험도 단독 API도 정상적으로 구분.
- 그러나 이미지 통합 분석에서 실제 음식별 위험도가 낮게 나오는 경향은 개선 필요.

---

## 10. 최종 판단

### 이미지 분류

상태:

```text
정상
```

근거:

- 운영 7-model ensemble이 정상 로드됨.
- `/predict/analyze` 샘플 6개 중 6개 정답.
- `/predict/classify` 56클래스 smoke test 51/56 정답, 91.07%.
- 운영 config의 전체 validation 92.02%와 유사.

### 혈당 위험도 예측

상태:

```text
부분 정상 / 통합 분석 개선 필요
```

근거:

- 영양성분 직접 입력 시 낮음/주의/위험 또는 낮음/주의/높음 구분 가능.
- `/glucose-risk` 0-100 score는 직관적으로 작동.
- 하지만 `/predict/analyze` 통합 결과는 실제 음식 이미지 샘플에서 모두 `낮음`으로 나옴.

---

## 11. 권장 다음 작업

1. `/predict/analyze` 응답에 기존 `risk` 외에 `/glucose-risk` 점수 기반 결과도 함께 포함할지 검토한다.
2. K-Food nutrition DB의 `glycemic_index` 기본값 50을 음식별 추정값으로 보강한다.
3. 운영 환경에서 `use_xgboost_predictor_model=True`를 켰을 때 torch/MPS ensemble과 충돌이 없는지 별도 테스트한다.
4. 위험도 문구는 현재보다 더 non-medical하게 다듬는다.
   - 예: `위험` → `높음`
   - 예: `혈당 급상승 위험` → `혈당 상승 가능성 신호`
5. 통합 분석 화면에서는 낮은 confidence 음식 분류 결과에 대해 음식 확인 단계를 반드시 거치게 한다.
6. 56개 클래스 전체 validation API benchmark를 필요 시 별도 script로 자동화한다.

---

## 12. 테스트 후 처리

테스트를 위해 실행한 backend server는 확인 후 종료했다.

종료 상태:

```text
Application shutdown complete.
Finished server process.
```

