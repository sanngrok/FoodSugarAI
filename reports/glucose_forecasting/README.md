# CGM Forecasting Evaluation

- CGM CSV: `data/processed/ohiot1dm/cgm_timeseries_enriched.csv`
- model_dir: `data/processed/glucose_models_enriched`
- train rows raw: `134790`
- test rows raw: `31743`
- train rows used: `101385`
- test rows used: `29536`
- saved model type: `enriched`
- enriched features detected: `True`
- reference notice: 이 결과는 참고용이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리 결정은 의료진과 상의하세요.

## Metrics

| Model | Horizon | Samples | MAE | RMSE | R2 | MAE vs persistence | MAE vs history |
|---|---:|---:|---:|---:|---:|---:|---:|
| enriched | 30m | 29536 | 13.027 | 18.488 | 0.9053 | 23.08% | 3.69% |
| enriched_calibrated | 30m | 29536 | 12.998 | 18.476 | 0.9054 | 23.25% | 3.90% |
| history | 30m | 29677 | 13.526 | 19.163 | 0.8983 | 20.13% | 0.00% |
| persistence | 30m | 29677 | 16.935 | 23.385 | 0.8486 | 0.00% | -25.21% |
| enriched | 60m | 29536 | 22.704 | 31.042 | 0.7340 | 20.35% | 4.88% |
| enriched_calibrated | 60m | 29536 | 22.633 | 31.008 | 0.7346 | 20.59% | 5.18% |
| history | 60m | 29677 | 23.869 | 32.411 | 0.7103 | 16.26% | 0.00% |
| persistence | 60m | 29677 | 28.503 | 38.506 | 0.5911 | 0.00% | -19.41% |
| enriched | 90m | 29536 | 29.721 | 39.864 | 0.5633 | 19.66% | 4.35% |
| enriched_calibrated | 90m | 29536 | 29.606 | 39.831 | 0.5640 | 19.97% | 4.73% |
| history | 90m | 29677 | 31.074 | 41.219 | 0.5344 | 16.00% | 0.00% |
| persistence | 90m | 29677 | 36.993 | 49.254 | 0.3352 | 0.00% | -19.05% |

## Interpretation

These models forecast CGM values 30, 60, and 90 minutes ahead from recent CGM history and optional event features.
They are for reference and product experimentation only, not medical diagnosis or treatment guidance.

## Additional Reports

- `metrics_baseline_vs_enriched.csv`
- `metrics_calibrated_vs_raw.csv`
- `range_calibration_table.csv`
- `range_specific_calibration_comparison.csv`
- `range_specific_calibration_table.csv`
- `calibration_strategy_selection.json`
- `event_classifier_metrics.csv`
- `hypo_classifier_model_comparison.csv`
- `hypo_classifier_selected_models.json`
- `hypo_threshold_sweep.csv`
- `hypo_threshold_selection.json`
- `per_patient_metrics.csv`
- `per_patient_horizon_metrics.csv`
- `per_patient_event_metrics.csv`
- `per_patient_calibration_gain.csv`
- `patient_data_quality_audit.csv`
- `worst_patient_diagnostic_report.csv`
- `worst_patients.csv`
- `best_patients.csv`
- `per_glucose_range_metrics.csv`
- `hypoglycemia_case_errors.csv`
- `hyperglycemia_case_errors.csv`
