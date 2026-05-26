# FoodSugar AI Glucose Next Stage Result - 2026-05-21

## Scope

기존 K-Food 음식분류 모델, production ensemble config, classifier checkpoint, `src/classifier/`, `data/models/`는 수정하지 않았다.

이번 단계는 enriched CGM 모델의 low/high glucose bias를 줄이고, 저혈당/고혈당 이벤트 판단을 API 응답에 더 명확히 붙이는 작업이다. 모든 혈당 관련 API 응답에는 참고용/비의료진단 문구와 의료진 상담 문구를 유지했다.

## Implemented

1. Range-aware calibration 유지 및 리포트 확장
   - `range_calibrators.json` 저장
   - raw vs calibrated MAE 비교 리포트 생성
   - calibration strategy 선택 JSON 생성

2. Hypoglycemia event classifier 개선
   - 기본 HistGradientBoosting 대비 class-weighted 후보 비교
   - 후보: default HGB, weighted HGB, balanced RandomForest, balanced LogisticRegression
   - 30/60/90분 모두 `random_forest_balanced` 선택

3. Hypo threshold sweep
   - threshold: `0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10`
   - 이번 결과에서는 세 horizon 모두 threshold `0.50`이 recall target을 만족하면서 F1이 가장 좋아 선택됨

4. Raw-event enriched API 추가
   - 기존 `/predict/cgm-forecast` 동작 유지
   - 기존 `/predict/cgm-forecast-enriched` 동작 유지
   - 신규 `POST /predict/cgm-forecast-enriched-events` 추가
   - raw `readings`, `meals`, `bolus`, `basal`, `exercise`, `sleep_indicator`, `biosignals`를 받아 내부에서 enriched rolling feature 생성

5. Patient-specific evaluation 추가
   - patient별 event metrics
   - patient별 calibration gain
   - patient data quality audit
   - worst patient diagnostic report 생성

## Key Metrics

### Raw vs Calibrated Forecast MAE

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| enriched raw | 12.923 | 22.564 | 29.585 |
| enriched calibrated | 12.896 | 22.492 | 29.458 |

Calibration은 전체 MAE를 크게 바꾸지는 않지만 30/60/90분 모두 소폭 개선했다.

### Hypo Classifier Result

| Horizon | Selected Model | Precision | Recall | F1 | Target Met |
|---:|---|---:|---:|---:|---|
| 30m | random_forest_balanced | 0.492 | 0.806 | 0.611 | yes |
| 60m | random_forest_balanced | 0.353 | 0.604 | 0.445 | yes |
| 90m | random_forest_balanced | 0.275 | 0.364 | 0.313 | yes |

기존 enriched classifier 대비 low glucose recall이 크게 개선되어, 저혈당 쪽을 더 보수적으로 잡는 방향으로 개선되었다.

### Hyper Classifier Result

| Horizon | Precision | Recall | F1 | ROC-AUC |
|---:|---:|---:|---:|---:|
| 30m | 0.900 | 0.871 | 0.885 | 0.975 |
| 60m | 0.834 | 0.751 | 0.790 | 0.928 |
| 90m | 0.787 | 0.640 | 0.706 | 0.872 |

## Generated Artifacts

- `data/processed/glucose_models_enriched/event_thresholds.json`
- `reports/glucose_forecasting/hypo_threshold_sweep.csv`
- `reports/glucose_forecasting/hypo_threshold_selection.json`
- `reports/glucose_forecasting/hypo_classifier_model_comparison.csv`
- `reports/glucose_forecasting/hypo_classifier_selected_models.json`
- `reports/glucose_forecasting/range_specific_calibration_comparison.csv`
- `reports/glucose_forecasting/range_specific_calibration_table.csv`
- `reports/glucose_forecasting/calibration_strategy_selection.json`
- `reports/glucose_forecasting/per_patient_event_metrics.csv`
- `reports/glucose_forecasting/per_patient_calibration_gain.csv`
- `reports/glucose_forecasting/patient_data_quality_audit.csv`
- `reports/glucose_forecasting/worst_patient_diagnostic_report.csv`

## Changed Code

- `src/glucose/forecasting.py`
  - event threshold loader/cache
  - risk flag generation
  - raw event to enriched feature conversion
  - enriched forecast result risk flags

- `scripts/train_glucose_forecaster.py`
  - hypo threshold sweep
  - class-weighted hypo classifier comparison/selection
  - patient-specific event/calibration/data-quality reports

- `api/schemas/models.py`
  - raw meal/bolus/basal/exercise request schema
  - enriched event response schema
  - safety/reference fields 유지

- `api/routers/predict.py`
  - `/predict/cgm-forecast-enriched-events` 추가
  - enriched endpoint risk flags 연결

## Verification

```bash
python3 -m py_compile src/glucose/forecasting.py scripts/train_glucose_forecaster.py api/schemas/models.py api/routers/predict.py tests/test_api.py tests/test_glucose_forecasting_eval.py
python3 scripts/train_glucose_forecaster.py --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv --model-dir data/processed/glucose_models_enriched --report-dir reports/glucose_forecasting
python3 -m pytest tests/ -q
```

Result:

```text
41 passed in 2.74s
```

## Decision Notes

- 저혈당 recall 목표는 모두 달성했다.
- 전체 CGM forecast MAE는 calibration으로 소폭 개선했다.
- 90분 저혈당 precision은 낮은 편이므로 운영 UI에서는 “위험 확정”이 아니라 “가능성/주의 신호”로 표현해야 한다.
- 이 모델은 참고용 예측이며 의료 진단이나 치료 지침이 아니다.
