# FoodSugar AI Glucose Range-Aware Calibration 결과

- 작성일: 2026-05-21
- 작업 범위: CGM forecasting 개선
- 보호 범위: 기존 음식분류 모델, K-Food ensemble, classifier checkpoint, 기존 `/predict/cgm-forecast` 동작 유지
- 상태: range-aware calibration, hypo/hyper event classifier, enriched API schema, patient-specific evaluation 추가 완료

## 1. 핵심 요약

기존 enriched CGM 모델은 전체 MAE는 history-only보다 개선했지만, low/high glucose 구간에서 bias가 있었다.

관찰된 bias:

- low glucose: 실제보다 높게 예측하는 경향
- high glucose: 실제보다 낮게 예측하는 경향

이번 작업에서 추가한 것:

1. range-aware calibration
2. hypo/hyper event classifier
3. enriched CGM forecast API
4. patient-specific evaluation 리포트 강화
5. 기존 `/predict/cgm-forecast` lazy cache 유지 및 enriched cache 확장
6. 의료 안전 문구 강화

## 2. 수정/추가된 주요 파일

### 코드

```text
src/glucose/constants.py
src/glucose/forecasting.py
scripts/train_glucose_forecaster.py
api/schemas/models.py
api/routers/predict.py
config/settings.py
```

### 테스트

```text
tests/test_api.py
tests/test_glucose_forecasting_eval.py
```

### 생성/갱신 산출물

```text
data/processed/glucose_models_enriched/range_calibrators.json
data/processed/glucose_models_enriched/glucose_event_hypo_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_90m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_90m.joblib
reports/glucose_forecasting/range_calibration_table.csv
reports/glucose_forecasting/metrics_calibrated_vs_raw.csv
reports/glucose_forecasting/event_classifier_metrics.csv
reports/glucose_forecasting/per_patient_metrics.csv
reports/glucose_forecasting/per_patient_horizon_metrics.csv
reports/glucose_forecasting/per_glucose_range_metrics.csv
```

## 3. Range-Aware Calibration

구현 위치:

`src/glucose/forecasting.py`

추가 함수:

- `fit_range_calibrators`
- `apply_range_calibration`
- `save_range_calibrators`
- `load_range_calibrators`
- `load_range_calibrators_cached`

방식:

1. enriched train prediction에서 horizon별/predicted-range별 residual을 계산한다.
2. predicted range는 inference 시점에도 알 수 있는 `raw prediction` 기준으로 나눈다.
3. test/inference에서는 `calibrated = raw_prediction - mean_error`를 적용한다.

Calibration table:

`reports/glucose_forecasting/range_calibration_table.csv`

예시:

| Horizon | Predicted range | Mean error |
|---:|---|---:|
| 30m | high | `-0.599` |
| 30m | low | `2.653` |
| 30m | normal | `0.247` |
| 60m | high | `-1.959` |
| 60m | low | `11.683` |
| 90m | high | `-4.205` |
| 90m | low | `13.384` |

## 4. Raw Enriched vs Calibrated 성능

리포트:

`reports/glucose_forecasting/metrics_calibrated_vs_raw.csv`

| Model | Horizon | MAE | RMSE | R2 | MAE vs history |
|---|---:|---:|---:|---:|---:|
| enriched | 30m | `12.923` | `18.342` | `0.9068` | `4.01%` |
| enriched_calibrated | 30m | `12.896` | `18.331` | `0.9069` | `4.21%` |
| enriched | 60m | `22.564` | `30.821` | `0.7380` | `5.78%` |
| enriched_calibrated | 60m | `22.492` | `30.787` | `0.7386` | `6.08%` |
| enriched | 90m | `29.585` | `39.652` | `0.5692` | `4.75%` |
| enriched_calibrated | 90m | `29.458` | `39.603` | `0.5702` | `5.16%` |

결론:

- calibration은 전체 MAE를 소폭 개선했다.
- 특히 60분/90분에서 개선폭이 더 크다.
- 단, low/high range bias가 완전히 해결되지는 않았다.

## 5. Low/High Range Bias 변화

리포트:

`reports/glucose_forecasting/per_glucose_range_metrics.csv`

주요 비교:

| Model | Horizon | Range | MAE | Mean error |
|---|---:|---|---:|---:|
| enriched | 30m | low | `15.161` | `14.745` |
| enriched_calibrated | 30m | low | `14.471` | `13.697` |
| enriched | 30m | high | `15.475` | `-7.485` |
| enriched_calibrated | 30m | high | `15.424` | `-6.991` |
| enriched | 90m | low | `47.239` | `47.239` |
| enriched_calibrated | 90m | low | `45.619` | `45.619` |
| enriched | 90m | high | `38.641` | `-32.366` |
| enriched_calibrated | 90m | high | `38.307` | `-30.216` |

해석:

- calibration이 bias를 줄이긴 했지만, 90분 low/high 구간은 여전히 어렵다.
- low glucose는 여전히 높게 예측되는 경향이 크다.
- high glucose는 여전히 낮게 예측되는 경향이 크다.
- 다음 단계는 range-specific loss, threshold-aware classifier 보조, 또는 low/high 구간 전용 보정이 필요하다.

## 6. Hypo/Hyper Event Classifier

구현 위치:

`src/glucose/forecasting.py`

추가 함수:

- `train_event_classifiers`
- `evaluate_event_classifiers`
- `save_event_classifiers`
- `load_event_classifiers`
- `load_event_classifiers_cached`

저장 모델:

```text
data/processed/glucose_models_enriched/glucose_event_hypo_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_90m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_90m.joblib
```

평가 리포트:

`reports/glucose_forecasting/event_classifier_metrics.csv`

| Event | Horizon | Positive rate | Accuracy | Precision | Recall | F1 | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|---:|
| hyper | 30m | `0.350` | `0.921` | `0.900` | `0.871` | `0.885` | `0.975` |
| hyper | 60m | `0.350` | `0.860` | `0.834` | `0.751` | `0.790` | `0.928` |
| hyper | 90m | `0.351` | `0.813` | `0.787` | `0.640` | `0.706` | `0.872` |
| hypo | 30m | `0.027` | `0.980` | `0.731` | `0.424` | `0.537` | `0.985` |
| hypo | 60m | `0.028` | `0.974` | `0.587` | `0.153` | `0.242` | `0.945` |
| hypo | 90m | `0.028` | `0.972` | `0.540` | `0.080` | `0.139` | `0.891` |

해석:

- hyper classifier는 30/60/90분 모두 비교적 안정적이다.
- hypo classifier는 positive rate가 낮아서 recall이 낮다.
- 특히 60/90분 hypo recall은 운영 경고용으로 부족하다.
- 다음 단계에서는 hypo class weighting 또는 threshold tuning이 필요하다.

## 7. Enriched API Schema

추가 endpoint:

```text
POST /predict/cgm-forecast-enriched
```

기존 endpoint:

```text
POST /predict/cgm-forecast
```

기존 endpoint는 유지했다.

새 enriched 입력:

```text
readings: 최근 CGM readings, 최소 13개
event_features:
  carbs_current
  carbs_last_30m
  carbs_last_60m
  carbs_last_120m
  carbs_last_180m
  bolus_current
  bolus_last_30m
  bolus_last_60m
  bolus_last_120m
  bolus_last_180m
  basal_current
  basal_mean_60m
  basal_mean_120m
  exercise_active
  exercise_last_60m
  exercise_last_120m
  sleep_indicator
  hypo_event_current
  gsr_current
  skin_temperature_current
  acceleration_current
  patient_id_numeric
```

새 enriched 응답:

```text
predictions_mg_dl
calibrated_predictions_mg_dl
event_probabilities
horizons_minutes
reference_notice
risk_interpretation
safety_warning
```

## 8. Safety 문구 강화

수정 파일:

`src/glucose/constants.py`

추가 문구:

- `GLUCOSE_REFERENCE_NOTICE`
- `GLUCOSE_RISK_INTERPRETATION`
- `GLUCOSE_SAFETY_WARNING`

모든 glucose 관련 API response에 포함:

- `/predict/risk`
- `/predict/glucose-risk`
- `/predict/cgm-forecast`
- `/predict/cgm-forecast-enriched`

주의:

- 진단/치료/인슐린 용량 권고 표현은 사용하지 않는다.
- 결과는 참고용이라는 표현을 유지한다.

## 9. Patient-Specific Evaluation

기존 patient별 리포트는 유지하고, calibrated model까지 포함되도록 재생성했다.

리포트:

```text
reports/glucose_forecasting/per_patient_metrics.csv
reports/glucose_forecasting/per_patient_horizon_metrics.csv
reports/glucose_forecasting/worst_patients.csv
reports/glucose_forecasting/best_patients.csv
```

포함 model type:

- persistence
- history
- enriched
- enriched_calibrated

다음 분석 포인트:

- enriched_calibrated가 특정 patient에서만 좋아지는지 확인
- hypo/hyper event probability가 patient별로 편향되는지 확인
- worst patient에 대해 meal/bolus 기록 품질 확인

## 10. Cache 개선

기존:

- `/predict/cgm-forecast`는 forecast model lazy cache 사용

추가:

- forecast metadata cache
- range calibrator cache
- hypo/hyper event classifier cache

추가 함수:

```text
load_forecast_metadata_cached
load_range_calibrators_cached
load_event_classifiers_cached
clear_forecast_model_cache
```

테스트로 확인:

- forecast model은 두 번째 요청부터 재로드하지 않음
- calibrator/event classifier도 cache 재사용
- missing model directory는 503 유지

## 11. 테스트 결과

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
39 passed in 7.90s
```

추가/갱신 테스트:

```text
tests/test_api.py
tests/test_glucose_forecasting_eval.py
```

검증 항목:

- 기존 `/predict/cgm-forecast` 유지
- 새 `/predict/cgm-forecast-enriched` 응답
- calibrated predictions 포함
- hypo/hyper event probabilities 포함
- safety 문구 포함
- model cache 재사용
- calibrator/event classifier cache 재사용
- calibration/report 파일 생성 확인

## 12. 남은 과제

### 12.1 Hypo recall 개선

현재 hypo classifier는 ROC-AUC는 높지만 recall이 낮다.

다음 후보:

- decision threshold 낮추기
- class weight가 가능한 classifier로 교체
- low glucose sample oversampling
- low range 전용 classifier

### 12.2 Range-specific calibration 강화

현재 calibration은 predicted range 기준 평균 residual 보정이다.

다음 후보:

- horizon + patient + predicted range calibration
- quantile calibration
- low/high 전용 isotonic regression
- risk-zone-aware post-processing

### 12.3 Enriched API UX

새 endpoint는 enriched feature를 직접 받는다.

운영 UX에서는 사용자가 직접 `carbs_last_60m` 같은 feature를 넣기 어렵다.

다음 후보:

- raw meal/bolus/basal event list를 받는 schema
- API 내부에서 rolling feature 생성
- CGM 앱 연동 포맷 설계

## 13. 최종 판단

이번 작업으로 전체 MAE 개선뿐 아니라 low/high glucose bias를 관찰하고 보정하는 기반이 생겼다.

완료:

- range-aware calibration
- calibrated model metric report
- hypo/hyper event classifier
- event classifier metric report
- enriched API schema/endpoint
- patient-specific evaluation 유지/확장
- 기존 `/predict/cgm-forecast` 호환 유지
- 테스트 통과

아직 운영 확정 단계는 아니다.

특히 hypo recall과 90분 low/high range error는 추가 개선이 필요하다.
