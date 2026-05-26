# FoodSugar AI 모델 학습 과정 전체 정리 - 2026-05-24

## 개요

이 프로젝트의 모델 학습은 크게 3개 축으로 나뉜다.

1. K-Food 음식 이미지 분류 모델
2. 영양성분 기반 혈당 위험도 모델
3. OhioT1DM CGM 기반 혈당 예측 모델

현재 운영 후보의 핵심은 다음 두 가지다.

- 음식 이미지 분류: K-Food 56-class 7-model hflip weighted ensemble
- 혈당 예측: OhioT1DM 기반 enriched long-horizon CGM forecasting + hypo/hyper event classifier

혈당 관련 출력은 모두 참고용이며 의료 진단이나 치료 지침이 아니다.

---

## 1. K-Food 음식 이미지 분류 모델

### 목적

음식 이미지를 입력받아 한국 음식 56개 class 중 하나로 분류한다.

### 데이터

최종 기준 데이터:

```text
data/raw/korean_food_fixed_v1
```

구조:

```text
train/
val/
```

검증 기준:

```text
validation split: data/raw/korean_food_fixed_v1/val
validation samples: 6,720
classes: 56
```

### 최종 운영 후보

최종 운영 후보는 단일 모델이 아니라 7개 모델을 합친 weighted ensemble이다.

설정 파일:

```text
config/kfood_production_ensemble_config.json
```

후보명:

```text
kfood_92_hflip_7model_weighted_2026_05_16
```

성능:

| Metric | Value |
|---|---:|
| top1 | 0.920238 |
| top3 | 0.979464 |
| macro_f1 | 0.920038 |
| correct | 6184 / 6720 |
| TTA | hflip |

### Ensemble 구성

| Model | Weight | Checkpoint |
|---|---:|---|
| food_lewm_b0 | 0.142361 | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` |
| b0_seed123_fixed_v1 | 0.256735 | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| b3_full_fixed_v1 | 0.529490 | `data/models/efficientnet_korean_b3_full_fixed_v1.pt` |
| b0_seed7_fixed_v1 | 0.062120 | `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |
| b3_probe_fixed_v1 | 0.001008 | `data/models/efficientnet_korean_b3_probe_fixed_v1.pt` |
| b3_cont_fixed_v1 | 0.004965 | `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` |
| b0_supervised_only | 0.003321 | `data/models/food_lewm_b0_supervised_only_ft10.pt` |

### 학습 및 탐색 흐름

1. K-Food 56-class split을 구성했다.
2. EfficientNet-B0/B2/B3 계열 모델을 학습했다.
3. Food-LeWM B0와 supervised-only B0 seed 모델을 학습했다.
4. B3 probe, continuation, full 25epoch 모델을 학습했다.
5. 각 모델의 hflip logits를 cache했다.
6. validation split에서 ensemble weight search를 수행했다.
7. 최종 7-model hflip weighted ensemble이 top1 92.02%를 달성했다.

중요 caveat:

```text
ensemble weight는 fixed_v1 validation split에서 탐색되었으므로,
현재 결과는 “운영 후보”이지 unseen test 일반화의 최종 증명은 아니다.
```

---

## 2. EfficientNet-B3 Full 학습

### 목적

B0 계열보다 큰 backbone을 학습해 ensemble diversity와 성능을 높인다.

### 데이터

```text
data/raw/korean_food_fixed_v1
```

### 학습 설정

| 항목 | 값 |
|---|---|
| model | efficientnet_b3 |
| image_size | 300 |
| epochs | 25 |
| batch_size | 8 |
| grad_accum_steps | 4 |
| lr | 3e-5 |
| head_lr | 3e-4 |
| warmup_epochs | 2 |
| label_smoothing | 0.05 |
| weight_decay | 0.0001 |
| randaugment | n=2, m=7 |
| random_erasing_p | 0.1 |
| device | MPS |

### 산출물

```text
checkpoint: data/models/efficientnet_korean_b3_full_fixed_v1.pt
metadata:   data/models/korean_food_model_meta_b3_full_fixed_v1.json
classes:    data/models/korean_food_classes_b3_full_fixed_v1.json
report:     reports/b3/b3_full_fixed_v1
```

### 결과

| 평가 | top1 | top3 | macro_f1 |
|---|---:|---:|---:|
| train-time val | 0.903423 | 0.973065 | 0.903170 |
| hflip eval | 0.904315 | 0.974554 | 0.904010 |

B3 full은 단일 모델로 90%를 넘겼고, 최종 ensemble에서 가장 큰 weight를 받았다.

---

## 3. Food-LeWM 계열

### 목적

K-Food 이미지 도메인에서 더 좋은 representation을 만들기 위해 self-supervised pretraining을 실험했다.

### Self-supervised pretraining

스크립트:

```text
scripts/pretrain_food_lewm.py
```

방식:

```text
image view A -> encoder -> z_a -> predictor -> z_b_hat
image view B -> encoder -> z_b -> predictor -> z_a_hat

loss = 0.5 * (MSE(z_b_hat, z_b) + MSE(z_a_hat, z_a))
     + lambda_sigreg * SIGReg(z_a, z_b)
```

핵심 구성:

- two-view augmentation
- latent prediction
- SIGReg anti-collapse regularization
- EfficientNet encoder

대표 pretrain checkpoint:

```text
data/models/food_lewm_b0_pretrain_3ep.pt
```

### Supervised fine-tuning

스크립트:

```text
scripts/train_food_lewm_classifier.py
```

지원 모드:

1. LeWM checkpoint를 로드해서 fine-tuning
2. LeWM checkpoint 없이 ImageNet pretrained encoder로 supervised-only fine-tuning

주요 augmentation:

- RandomResizedCrop
- HorizontalFlip
- ColorJitter
- RandomErasing

loss:

```text
CrossEntropyLoss + label smoothing
```

optimizer:

```text
AdamW + cosine scheduler
```

### 주요 모델

| 모델 | 데이터 | 설명 | checkpoint |
|---|---|---|---|
| food_lewm_b0 | K-Food 1000/fixed 계열 | LeWM pretrain 후 fine-tuning | `food_lewm_b0_classifier_3ep_ft10.pt` |
| b0_supervised_only | K-Food 1000/fixed 계열 | ImageNet pretrained에서 바로 fine-tuning | `food_lewm_b0_supervised_only_ft10.pt` |
| b0_seed123_fixed_v1 | fixed_v1 | seed 123 supervised-only | `food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| b0_seed7_fixed_v1 | fixed_v1 | seed 7 supervised-only | `food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |

### 해석

LeWM pretraining 자체가 항상 supervised-only보다 좋았던 것은 아니다. 실제 성능 향상은 다음 요소들이 합쳐진 결과다.

- split 정리
- fine-tuning recipe 개선
- hflip TTA
- 여러 모델 ensemble
- B3 full 추가

하지만 Food-LeWM B0는 최종 ensemble에서 diversity member로 유용했다.

---

## 4. 영양성분 기반 혈당 위험도 모델

### 목적

음식의 영양성분을 기반으로 혈당 위험도를 낮음/주의/위험으로 분류한다.

### 모델

```text
XGBClassifier
```

학습 스크립트:

```text
src/predictor/train_predictor.py
```

추론 래퍼:

```text
src/predictor/sugar_predictor.py
```

모델 파일:

```text
data/models/xgboost_sugar.pkl
```

### 입력 feature

| Feature |
|---|
| calories |
| carbs |
| sugar |
| protein |
| fat |
| fiber |
| glycemic_index |

### 출력 label

| Label | 의미 |
|---:|---|
| 0 | 낮음 |
| 1 | 주의 |
| 2 | 위험 |

### 학습 데이터

기본 학습은 `NUTRITION_DB` 기반 synthetic data로 수행한다.

생성 방식:

1. 음식별 영양정보를 가져온다.
2. sugar, glycemic_index, carbs 기준 rule로 pseudo label 생성
3. portion/noise augmentation 적용
4. XGBoost로 3-class classification 학습

실제 CSV가 있으면 `--data` 옵션으로 학습 가능하다.

### 학습 설정

| 항목 | 값 |
|---|---|
| n_estimators | 300 |
| max_depth | 5 |
| learning_rate | 0.05 |
| subsample | 0.8 |
| colsample_bytree | 0.8 |
| eval_metric | mlogloss |
| CV | Stratified 5-Fold |
| metric | F1-macro |
| sample_weight | balanced |

### 운영상 주의

현재 API에서는 안정성을 위해 XGBoost model load를 기본적으로 끄고 rule-based fallback을 사용할 수 있게 했다.

```text
settings.use_xgboost_predictor_model = False
```

---

## 5. OhioT1DM CGM 혈당 예측 모델

### 목적

최근 CGM history와 식사/인슐린/운동/수면 event feature를 이용해 30분, 60분, 90분 뒤 혈당을 예측한다.

### 데이터

원본:

```text
/Users/sangrok/Downloads/OhioT1DM
```

변환 스크립트:

```text
scripts/prepare_ohiot1dm_cgm.py
```

변환 결과:

```text
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
```

데이터 요약:

| 항목 | 값 |
|---|---:|
| total CGM rows | 약 166,533 |
| train rows | 134,790 |
| test rows | 31,743 |
| patients | 12 |
| years | 2018, 2020 |
| glucose min/max | 40 / 400 |

### 최신 학습 명령

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting \
  --use-validation-selection \
  --long-horizon-upgrade
```

### Validation/Test 분리

test leakage를 막기 위해 train split 내부를 다시 시간순으로 분리했다.

```text
train split
  ├── train_inner: 모델 학습
  └── validation: model/threshold/calibration 선택

test split
  └── 최종 평가 전용
```

분리 결과:

| 항목 | 값 |
|---|---:|
| train_inner rows | 107,827 |
| validation rows | 26,963 |
| groups | 12 |
| time_order_safe | true |
| test_split_used_for_selection | false |

### 예측 horizon

```text
30분 뒤 glucose
60분 뒤 glucose
90분 뒤 glucose
```

### 모델

horizon별 별도 모델을 학습한다.

```text
HistGradientBoostingRegressor
```

저장 파일:

```text
data/processed/glucose_models_enriched/glucose_forecast_30m.joblib
data/processed/glucose_models_enriched/glucose_forecast_60m.joblib
data/processed/glucose_models_enriched/glucose_forecast_90m.joblib
data/processed/glucose_models_enriched/metadata.joblib
```

최신 metadata:

```text
model_type: enriched_long_horizon
feature_count: 66
```

### 주요 feature

기본 CGM feature:

- glucose_mg_dl
- lag_1, lag_2, lag_3, lag_6, lag_12
- diff_1, diff_3, diff_6
- rolling_mean_3, rolling_mean_6, rolling_mean_12
- rolling_std_6, rolling_std_12
- hour_sin, hour_cos

event/enriched feature:

- carbs_current
- carbs_last_30m, carbs_last_60m, carbs_last_120m, carbs_last_180m
- bolus_current
- bolus_last_30m, bolus_last_60m, bolus_last_120m, bolus_last_180m
- basal_current
- basal_mean_60m, basal_mean_120m
- exercise_active
- exercise_last_60m, exercise_last_120m
- sleep_indicator
- hypo_event_current
- patient_id_numeric

long-horizon feature:

- time_since_last_meal
- time_since_last_bolus
- meal_bolus_gap_minutes
- carbs_on_board_proxy
- insulin_on_board_proxy
- net_glucose_pressure_proxy
- glucose_slope_60m
- glucose_slope_120m
- glucose_volatility_120m
- glucose_volatility_180m
- glucose_mean_120m
- glucose_mean_180m
- recent_low_event_count_180m
- recent_high_event_count_180m
- time_since_last_low
- time_since_last_high

주의:

```text
IOB/COB feature는 의료용 IOB/COB 계산이 아니라 예측용 proxy다.
인슐린 용량 계산이나 치료 결정에 사용하면 안 된다.
```

### 최신 최종 test 성능

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| long-horizon enriched raw | 13.027 | 22.704 | 29.721 |
| long-horizon enriched calibrated | 12.998 | 22.633 | 29.606 |

---

## 6. Hypo/Hyper Event Classifier

### 목적

혈당 수치 예측과 별도로, 저혈당/고혈당 가능성 신호를 예측한다.

### 모델

각 event type과 horizon별 classifier를 학습했다.

```text
hypo 30m
hypo 60m
hypo 90m
hyper 30m
hyper 60m
hyper 90m
```

저장 파일:

```text
glucose_event_hypo_30m.joblib
glucose_event_hypo_60m.joblib
glucose_event_hypo_90m.joblib
glucose_event_hyper_30m.joblib
glucose_event_hyper_60m.joblib
glucose_event_hyper_90m.joblib
```

### 학습 및 선택

후보 모델:

- default HistGradientBoosting
- weighted HistGradientBoosting
- balanced RandomForest
- balanced LogisticRegression

선택 방식:

1. train_inner에서 후보 모델 학습
2. validation에서 모델 family 선택
3. validation에서 threshold 선택
4. test에서 최종 평가

threshold 설정:

```text
data/processed/glucose_models_enriched/event_thresholds.json
```

이 파일에는 다음이 명시되어 있다.

```text
selection_split = validation
evaluation_split = test
```

### 해석

저혈당 60m/90m은 recall을 높게 잡았기 때문에 precision은 낮다. 따라서 API에서는 확정 표현을 쓰지 않는다.

허용 표현:

```text
저혈당 가능성 신호가 감지되었습니다.
고혈당 가능성 신호가 감지되었습니다.
실제 혈당 측정값과 증상을 우선 확인하세요.
```

금지 표현:

```text
저혈당입니다.
고혈당입니다.
인슐린을 조절하세요.
치료하세요.
진단합니다.
```

---

## 7. Calibration, Prediction Interval, Uncertainty

### Range-aware calibration

raw prediction을 그대로 쓰지 않고, train/validation residual 기반으로 predicted range별 보정을 적용했다.

저장:

```text
data/processed/glucose_models_enriched/range_calibrators.json
```

### Prediction interval

validation residual p90 기반 interval을 생성했다.

저장:

```text
data/processed/glucose_models_enriched/prediction_intervals.json
```

리포트:

```text
reports/glucose_forecasting/prediction_interval_metrics.csv
reports/glucose_forecasting/conformal_coverage_report.csv
reports/glucose_forecasting/uncertainty_by_horizon.csv
```

최신 interval 결과:

| Horizon | Observed Coverage | Mean Interval Width | Uncertainty |
|---:|---:|---:|---|
| 30m | 0.919 | 64.487 | high |
| 60m | 0.915 | 107.109 | high |
| 90m | 0.912 | 136.114 | high |

해석:

```text
90분 예측은 interval width가 넓기 때문에 단일 수치보다 범위와 주의 신호 중심으로 제시해야 한다.
```

---

## 8. API에서 사용되는 모델 구조

### 음식 이미지 경로

```text
이미지
-> K-Food 7-model hflip ensemble
-> food label
-> nutrition DB lookup
-> 혈당 위험도 계산
```

### CGM 예측 경로

```text
CGM readings
+ meal / bolus / basal / exercise / sleep events
-> feature engineering
-> 30m/60m/90m HistGradientBoostingRegressor
-> calibration
-> prediction interval
-> hypo/hyper event classifier
-> risk flags + safety message
```

### 주요 endpoint

```text
POST /predict/classify
POST /predict/analyze
POST /predict/risk
POST /predict/glucose-risk
POST /predict/cgm-forecast
POST /predict/cgm-forecast-enriched
POST /predict/cgm-forecast-enriched-events
```

---

## 9. 현재 상태 요약

### 음식 분류

| 항목 | 상태 |
|---|---|
| class 수 | 56 |
| 운영 후보 | 7-model hflip weighted ensemble |
| validation top1 | 0.920238 |
| config 고정 | 완료 |
| production preflight | 완료 |

### 혈당 예측

| 항목 | 상태 |
|---|---|
| 데이터 | OhioT1DM enriched CGM |
| 모델 | horizon별 HistGradientBoostingRegressor |
| event classifier | hypo/hyper x 30/60/90 |
| validation/test 분리 | 완료 |
| leakage audit | pass |
| uncertainty interval | 추가 완료 |
| 안전 문구 | 적용 완료 |

### 최신 테스트

```text
63 passed
```

---

## 10. 최종 해석

이 프로젝트는 처음에는 음식 이미지 분류와 영양성분 기반 위험도 예측 구조였지만, 현재는 다음 구조까지 확장되었다.

```text
음식 이미지
-> 한국 음식 56-class 분류
-> 영양성분 조회
-> 혈당 위험도 참고 점수

CGM history + 식사/인슐린/운동 이벤트
-> 30/60/90분 혈당 변화 예측
-> 저혈당/고혈당 가능성 신호
-> prediction interval + uncertainty
```

음식분류 모델은 92% validation 목표를 달성한 운영 후보가 있고, 혈당 모델은 validation/test 분리와 leakage audit을 통과한 참고용 예측 모델이다.

단, 혈당 모델은 의료기기 수준의 검증 모델이 아니다. 특히 60분/90분 예측은 불확실성이 크므로, 실제 서비스에서는 단일 수치보다 범위와 주의 신호 중심으로 제공해야 한다.
