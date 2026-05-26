# FoodSugar AI Long-Horizon Glucose Forecasting Upgrade Result - 2026-05-24

## Scope

이번 단계는 60분/90분 장기 혈당 예측을 더 안전하게 해석하기 위해 long-window feature, IOB/COB proxy, prediction interval, patient-specific analysis를 추가한 연구용 upgrade다.

기존 K-Food 음식분류 모델, ensemble weight, classifier checkpoint, `src/classifier/`, `data/models/`는 수정하지 않았다. 기존 validation/test 분리와 safety UX 원칙도 유지했다.

## Implemented

1. IOB/COB proxy feature 추가
   - `time_since_last_meal`
   - `time_since_last_bolus`
   - `meal_bolus_gap_minutes`
   - `carbs_decay_*`
   - `carbs_on_board_proxy`
   - `insulin_decay_*`
   - `insulin_on_board_proxy`
   - `carb_insulin_ratio_proxy`
   - `net_glucose_pressure_proxy`

2. Horizon long-window glucose feature 추가
   - `glucose_slope_60m`
   - `glucose_slope_120m`
   - `glucose_volatility_120m`
   - `glucose_volatility_180m`
   - `glucose_mean_120m`
   - `glucose_mean_180m`
   - `recent_low_event_count_180m`
   - `recent_high_event_count_180m`
   - `time_since_last_low`
   - `time_since_last_high`

3. Long-horizon model training
   - `--long-horizon-upgrade` flag 추가
   - metadata model type: `enriched_long_horizon`
   - feature count: `66`

4. Prediction interval / uncertainty 추가
   - validation residual 기반 p90 interval 생성
   - API 응답 필드 추가:
     - `prediction_intervals_mg_dl`
     - `uncertainty_level`
     - `uncertainty_message`

5. Patient-specific analysis 추가
   - global vs calibrated patient별 비교
   - horizon별 patient gain
   - worst 60/90 patient 진단용 리포트

6. Range weighted / low-high tradeoff 리포트 생성
   - 위험 구간 성능 확인용 리포트

## Generated Reports

- `reports/glucose_forecasting/iob_cob_feature_audit.csv`
- `reports/glucose_forecasting/iob_cob_feature_summary.json`
- `reports/glucose_forecasting/horizon_feature_set_comparison.csv`
- `reports/glucose_forecasting/long_window_feature_importance.csv`
- `reports/glucose_forecasting/long_window_model_metrics.csv`
- `reports/glucose_forecasting/patient_specific_vs_global.csv`
- `reports/glucose_forecasting/horizon_patient_gain.csv`
- `reports/glucose_forecasting/worst_patient_60_90_diagnosis.csv`
- `reports/glucose_forecasting/patient_specific_summary.md`
- `reports/glucose_forecasting/prediction_interval_metrics.csv`
- `reports/glucose_forecasting/conformal_coverage_report.csv`
- `reports/glucose_forecasting/uncertainty_by_horizon.csv`
- `reports/glucose_forecasting/range_weighted_model_comparison.csv`
- `reports/glucose_forecasting/low_high_tradeoff_report.csv`
- `data/processed/glucose_models_enriched/prediction_intervals.json`

## Final Test Metrics

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| long-horizon enriched raw | 13.027 | 22.704 | 29.721 |
| long-horizon enriched calibrated | 12.998 | 22.633 | 29.606 |

이전 validation-fix 단계의 calibrated MAE는 대략 30m `12.947`, 60m `22.635`, 90m `29.696`이었다. 이번 long-horizon feature는 90m calibrated MAE를 소폭 개선했고, 60m은 거의 동률, 30m은 소폭 나빠졌다. 따라서 장기 예측은 단일 수치 개선보다 uncertainty/interval 제공 쪽의 의미가 더 크다.

## Prediction Interval

| Horizon | Observed Coverage | Mean Interval Width | Uncertainty |
|---:|---:|---:|---|
| 30m | 0.919 | 64.487 | high |
| 60m | 0.915 | 107.109 | high |
| 90m | 0.912 | 136.114 | high |

90분 예측은 interval width가 넓기 때문에 단일 수치보다 범위와 주의 신호 중심으로 제시해야 한다.

## Safety Notes

- IOB/COB feature는 의료용 IOB/COB 계산이 아니라 예측용 proxy다.
- 인슐린 용량 계산, 약물 조절, 치료 결정에 사용하면 안 된다.
- 60분/90분 예측은 불확실성이 높으므로 참고용 범위와 가능성 신호로만 표시한다.
- 모든 혈당 관련 결과는 의료 진단이나 치료 지침이 아니다.

## Verification

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting \
  --use-validation-selection \
  --long-horizon-upgrade

python3 scripts/validate_glucose_artifacts.py \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting

python3 -m pytest tests/ -q
```

Result:

```text
artifact_validation: pass
leakage_audit: pass
63 passed in 5.77s
```

## Interpretation

이번 단계로 FoodSugar AI 혈당 모델은 다음 방향으로 정리할 수 있다.

- 30분: 수치 예측 중심
- 60분: 수치 + 위험 가능성 + 불확실성 표시
- 90분: 범위 예측 + 위험 가능성 + 높은 불확실성 표시

장기 horizon에서는 MAE만으로 운영성을 판단하기보다 interval width, event recall/precision, patient별 편차를 함께 봐야 한다.
