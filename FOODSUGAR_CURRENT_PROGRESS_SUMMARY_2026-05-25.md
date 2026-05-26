# FoodSugar AI 현재 진행상황 정리 - 2026-05-25

## 0. 요약

FoodSugar AI 프로젝트는 현재 크게 두 축으로 진행되어 있다.

1. **K-Food 음식 이미지 분류**
   - 목표였던 92% validation top1을 달성했다.
   - 현재 운영 후보는 `7-model hflip weighted ensemble`이다.
   - 운영용 config와 FastAPI 로딩 구조까지 정리되어 있다.

2. **혈당/CGM 기능 추가**
   - 음식 영양성분 기반 혈당 위험도 참고 기능을 추가했다.
   - OhioT1DM XML 데이터를 CGM 시계열 CSV로 변환했다.
   - 30분/60분/90분 혈당 예측 모델을 학습했다.
   - low/high glucose bias 대응을 위해 calibration, event classifier, prediction interval, patient-specific evaluation까지 추가했다.

혈당 관련 출력은 모두 **참고용 정보**이며, 의료 진단/치료/약물 조절 지침으로 사용하면 안 된다.

---

## 1. K-Food 음식 분류 현재 상태

### 1.1 목표 달성 상태

- 목표: K-Food 56-class 음식 이미지 분류 `top1 >= 92%`
- 기준 데이터: `data/raw/korean_food_fixed_v1/val`
- validation sample 수: `6,720`
- class 수: `56`
- 현재 verified best: `top1 = 0.9202380952380952`
- 정답 수: `6184 / 6720`
- 상태: **92% validation 목표 달성**

### 1.2 현재 운영 후보

운영 후보 이름:

```text
kfood_92_hflip_7model_weighted_2026_05_16
```

운영 config:

```text
config/kfood_production_ensemble_config.json
```

검증 리포트:

```text
reports/b3/verified_92_hflip_7model_weighted_2026_05_16
```

주요 성능:

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| TTA | `hflip` |

### 1.3 Ensemble 구성

| Model | Weight | Checkpoint |
|---|---:|---|
| `food_lewm_b0` | `0.14236057323734336` | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| `b3_full_fixed_v1` | `0.52949003398239` | `data/models/efficientnet_korean_b3_full_fixed_v1.pt` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` | `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` | `data/models/efficientnet_korean_b3_probe_fixed_v1.pt` |
| `b3_cont_fixed_v1` | `0.00496452020109459` | `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` |
| `b0_supervised_only` | `0.0033210487744569726` | `data/models/food_lewm_b0_supervised_only_ft10.pt` |

### 1.4 음식 분류 쪽에서 완료된 작업

- K-Food 56-class fixed split 구성 및 검증
- Food-LeWM B0 pretraining/fine-tuning 실험
- EfficientNet-B0 supervised-only seed 실험
- EfficientNet-B3 probe/continuation/full 25epoch 학습
- hflip TTA 평가
- 3-model ensemble 탐색
- 7-model weighted ensemble 탐색
- 92% 달성 후보 검증
- 운영용 ensemble config 생성
- `EnsembleFoodClassifier` 추가
- FastAPI startup에서 production ensemble 우선 로드하도록 개선
- production config preflight 검증 스크립트 추가
- K-Food 56-class label과 nutrition DB 연결

### 1.5 음식 분류 관련 주의점

현재 92.02%는 `fixed_v1/val`에서 검증된 수치다. 다만 ensemble weight 탐색도 같은 validation split에서 이루어졌기 때문에, 이 수치는 **현재 운영 후보 성능**으로는 의미가 있지만 **완전히 독립적인 unseen test 일반화 증명**은 아니다.

운영 확정 전에 권장되는 추가 확인:

- 별도 holdout 또는 사람 검수 clean validation subset 평가
- 약한 class 중심 오류 검토
- 실제 API inference latency 확인
- 실사용 이미지에서 smoke test

---

## 2. 음식 영양성분/혈당 위험도 기능

### 2.1 목적

기존 음식 분류 결과를 영양성분 DB와 연결해서 음식 기반 혈당 위험도 참고 정보를 제공한다.

흐름:

```text
음식 이미지
-> K-Food classifier
-> 음식명
-> nutrition lookup
-> 혈당 위험도 참고 점수/등급
```

### 2.2 주요 파일

```text
src/nutrition/nutrition_db.py
src/predictor/sugar_predictor.py
src/predictor/train_predictor.py
data/processed/kfood_nutrition_db.json
data/models/xgboost_sugar.pkl
```

### 2.3 구현 내용

- K-Food 56-class label을 nutrition lookup key로 연결
- 기존 `train_data.csv` 기반 exact match 51개 생성
- `곰탕_설렁탕`은 `곰탕`, `설렁탕` 평균값으로 구성
- exact row가 없는 일부 class는 curated alias로 보완
- XGBoost 기반 sugar risk predictor 학습 코드 유지
- API 기본값은 안정성을 위해 rule-based fallback 사용
- `use_xgboost_predictor_model=False` 기본값 적용

### 2.4 주의점

현재 음식 기반 혈당 위험도는 의료적 혈당 반응을 확정하는 모델이 아니다. 음식 영양성분 기반의 참고용 위험도이며, 개인별 인슐린 민감도, 운동, 수면, 스트레스, 약물, 식사 시간 등은 별도 영향을 줄 수 있다.

---

## 3. OhioT1DM CGM 예측 기능

### 3.1 목적

OhioT1DM XML 데이터를 읽어서 CGM 시계열 데이터로 변환하고, 현재/과거 CGM 및 이벤트 정보를 바탕으로 30분/60분/90분 뒤 혈당을 예측한다.

### 3.2 데이터

원본 데이터:

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

### 3.3 학습 명령

최신 long-horizon upgrade 기준 학습 명령:

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting \
  --use-validation-selection \
  --long-horizon-upgrade
```

### 3.4 모델 구조

예측 모델:

```text
HistGradientBoostingRegressor
```

horizon별 별도 모델:

```text
glucose_forecast_30m.joblib
glucose_forecast_60m.joblib
glucose_forecast_90m.joblib
```

모델 타입:

```text
enriched_long_horizon
```

feature 수:

```text
66
```

### 3.5 주요 feature

기본 CGM feature:

- glucose lag
- glucose diff
- rolling mean/std
- time-of-day sin/cos

enriched event feature:

- carbs
- bolus
- basal
- exercise
- sleep
- patient id numeric

long-horizon proxy feature:

- `time_since_last_meal`
- `time_since_last_bolus`
- `meal_bolus_gap_minutes`
- `carbs_on_board_proxy`
- `insulin_on_board_proxy`
- `carb_insulin_ratio_proxy`
- `net_glucose_pressure_proxy`
- `glucose_slope_60m`
- `glucose_slope_120m`
- `glucose_volatility_120m`
- `glucose_volatility_180m`
- `recent_low_event_count_180m`
- `recent_high_event_count_180m`
- `time_since_last_low`
- `time_since_last_high`

IOB/COB feature는 의료용 IOB/COB 계산이 아니라 예측용 proxy다.

---

## 4. CGM 예측 성능

### 4.1 최신 test MAE

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| long-horizon enriched raw | `13.027` | `22.704` | `29.721` |
| long-horizon enriched calibrated | `12.998` | `22.633` | `29.606` |

해석:

- 30분은 비교적 수치 예측 중심으로 사용 가능
- 60분은 수치 + 위험 가능성 + 불확실성 표시 필요
- 90분은 단일 수치보다 범위/불확실성 중심으로 표시하는 것이 적절

### 4.2 Prediction interval

| Horizon | Observed Coverage | Mean Interval Width | Uncertainty |
|---:|---:|---:|---|
| 30m | `0.919` | `64.487` | high |
| 60m | `0.915` | `107.109` | high |
| 90m | `0.912` | `136.114` | high |

90분 예측은 interval width가 넓기 때문에 정확한 단일 수치처럼 보여주면 안 된다.

### 4.3 Bias 대응

기존 enriched CGM 모델은 전체 MAE는 개선했지만 다음 bias가 있었다.

- low glucose 구간을 실제보다 높게 예측하는 경향
- high glucose 구간을 실제보다 낮게 예측하는 경향

이에 대응해 추가한 것:

- range-aware calibration
- hypo event classifier
- hyper event classifier
- event threshold validation selection
- patient-specific evaluation
- prediction interval / uncertainty message
- leakage audit

---

## 5. Hypo/Hyper Event Classifier

### 5.1 목적

혈당 수치 예측만으로 low/high 위험을 표현하면 bias 문제가 생길 수 있으므로, hypo/hyper 가능성 신호를 별도 classifier로 제공한다.

### 5.2 산출물

모델 파일:

```text
data/processed/glucose_models_enriched/hypo_event_30m.joblib
data/processed/glucose_models_enriched/hypo_event_60m.joblib
data/processed/glucose_models_enriched/hypo_event_90m.joblib
data/processed/glucose_models_enriched/hyper_event_30m.joblib
data/processed/glucose_models_enriched/hyper_event_60m.joblib
data/processed/glucose_models_enriched/hyper_event_90m.joblib
```

선택/평가 리포트:

```text
reports/glucose_forecasting/test_final_event_classifier_metrics.csv
reports/glucose_forecasting/validation_hypo_classifier_model_comparison.csv
reports/glucose_forecasting/validation_hypo_threshold_selection.json
```

### 5.3 원칙

- train_inner로 모델 학습
- validation으로 모델/threshold 선택
- test는 최종 평가에만 사용
- API 문구는 “가능성 신호”로 표현
- 진단/치료/인슐린 조절 지침으로 표현하지 않음

---

## 6. API 현재 상태

### 6.1 주요 endpoint

```text
/predict/classify
/predict/analyze
/predict/risk
/predict/glucose-risk
/predict/cgm-forecast
/predict/cgm-forecast-enriched
/predict/cgm-forecast-enriched-events
```

### 6.2 유지한 호환성

- 기존 음식 분류 모델과 checkpoint는 건드리지 않음
- 기존 ensemble weight는 고정
- 기존 `/predict/cgm-forecast` 동작은 유지
- enriched/event endpoint는 확장 기능으로 추가
- 혈당 관련 응답에는 참고용/비진단성 문구를 유지

---

## 7. 검증 상태

### 7.1 K-Food production config 검증

검증 스크립트:

```bash
python3 scripts/validate_kfood_production_config.py
```

확인 항목:

- config JSON 존재
- 7개 model entry 존재
- checkpoint/metadata/classes 파일 존재
- class count `56`
- class order 일치
- weight sum 정상
- verified top1 `>= 0.92`

### 7.2 Glucose artifact 검증

검증 스크립트:

```bash
python3 scripts/validate_glucose_artifacts.py \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting
```

최근 검증 결과:

```text
artifact_validation: pass
leakage_audit: pass
```

### 7.3 테스트

최근 전체 테스트 결과:

```text
63 passed
```

---

## 8. 현재 가장 중요한 산출물

### 8.1 음식 분류

```text
config/kfood_production_ensemble_config.json
reports/b3/verified_92_hflip_7model_weighted_2026_05_16
KFOOD_92_GOAL_ACHIEVED_2026-05-16.md
KFOOD_PRODUCTION_MODEL_READINESS_2026-05-16.md
```

### 8.2 혈당/CGM

```text
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
data/processed/glucose_models_enriched
reports/glucose_forecasting
FOODSUGAR_GLUCOSE_LONG_HORIZON_UPGRADE_RESULT_2026-05-24.md
FOODSUGAR_MODEL_TRAINING_PROCESS_SUMMARY_2026-05-24.md
```

---

## 9. 남은 작업

### 9.1 운영모델 확정 전 권장 작업

1. K-Food 92% ensemble을 별도 holdout 또는 human-reviewed clean validation subset에서 재평가
2. 약한 class 재검토
   - `삼겹살`
   - `닭볶음탕`
   - `곰탕_설렁탕`
   - `갈비구이`
   - `김치찌개`
3. 실제 FastAPI inference latency 측정
4. production config 기반 end-to-end smoke test
5. 운영 문서에 validation-tuned ensemble이라는 caveat 명시

### 9.2 혈당 기능 쪽 권장 작업

1. CGM 예측 API 응답 문구 최종 점검
2. 90분 예측은 point estimate보다 interval 중심 UI로 표현
3. hypo/hyper event classifier의 precision/recall tradeoff 재검토
4. patient별 성능 편차를 사용자-facing 문구에 반영
5. 실제 앱 화면에서는 “참고용”, “의료 진단 아님”, “치료 결정에 사용하지 말 것” 문구 고정

---

## 10. 현재 결론

현재 프로젝트는 다음 상태로 정리할 수 있다.

- **음식 분류 모델:** 92.02% validation top1을 달성한 7-model hflip weighted ensemble이 현재 best 운영 후보
- **음식-영양 연결:** K-Food 56-class label을 nutrition DB와 연결 완료
- **혈당 위험도:** 영양성분 기반 참고용 risk 기능 구현 완료
- **CGM 예측:** OhioT1DM 기반 30/60/90분 예측 모델 구현 및 검증 완료
- **안전성:** 혈당 관련 결과는 참고용/비진단 문구를 유지하는 방향으로 정리 완료
- **남은 핵심:** 운영 전 독립 holdout 검증, latency 확인, 혈당 UI/문구 최종 안정화

현재 기준으로 FoodSugar AI는 “음식 이미지 -> 음식명 -> 영양성분 -> 혈당 위험도 참고 -> CGM 기반 미래 혈당 참고 예측”까지 연결된 상태다.

