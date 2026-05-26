# FoodSugar AI Glucose Validation Leakage Fix Result - 2026-05-22

## Scope

이번 단계의 목표는 test split을 이용한 threshold/model selection 가능성을 제거하고, validation/test가 분리된 신뢰 가능한 평가 흐름으로 바꾸는 것이었다.

기존 K-Food 음식분류 모델, production ensemble config, classifier checkpoint, `src/classifier/`, `data/models/`는 수정하지 않았다.

## Implemented

1. Time-based validation split 생성
   - train split 내부에서 환자/연도/source 기준 시간순 80/20 분리
   - 앞 80%: `train_inner`
   - 뒤 20%: `validation`
   - test split은 selection에 사용하지 않음

2. Validation-based hypo model family selection
   - 후보 모델을 `train_inner`에서 학습
   - `validation`에서만 후보 선택
   - 선택 기준: recall target 충족, PR-AUC, F1, false negative 최소화

3. Validation-based threshold selection
   - threshold 후보: `0.50, 0.40, 0.30, 0.25, 0.20, 0.15, 0.10`
   - `validation`에서 threshold 선택
   - 선택된 threshold를 고정하고 test에서 최종 평가

4. Validation-based calibration selection
   - calibration strategy를 validation에서 선택
   - 선택된 strategy: `predicted_range_mean_residual`
   - test에서는 고정된 strategy로 최종 평가

5. Final test evaluation 재생성
   - validation에서 선택된 model/threshold/calibration을 고정한 뒤 test에서 평가
   - evidence summary에 `test used for selection: False` 명시

6. Leakage audit 강화
   - `event_thresholds.json.selection_split == validation`
   - `event_thresholds.json.evaluation_split == test`
   - selected model JSON의 `selection_split == validation`
   - calibration selection JSON의 `selection_split == validation`
   - 이전 test-based selection warning 제거

## Generated Files

### Validation Split

- `data/processed/ohiot1dm/cgm_train_inner_enriched.csv`
- `data/processed/ohiot1dm/cgm_validation_enriched.csv`
- `data/processed/ohiot1dm/cgm_test_enriched.csv`
- `reports/glucose_forecasting/validation_split_audit.csv`
- `reports/glucose_forecasting/validation_split_summary.json`

### Validation Selection

- `reports/glucose_forecasting/validation_hypo_classifier_model_comparison.csv`
- `reports/glucose_forecasting/validation_hypo_classifier_selected_models.json`
- `reports/glucose_forecasting/validation_hypo_threshold_sweep.csv`
- `reports/glucose_forecasting/validation_hypo_threshold_selection.json`
- `reports/glucose_forecasting/validation_calibration_strategy_comparison.csv`
- `reports/glucose_forecasting/validation_calibration_strategy_selection.json`

### Final Test Evaluation

- `reports/glucose_forecasting/test_final_metrics.csv`
- `reports/glucose_forecasting/test_final_event_classifier_metrics.csv`
- `reports/glucose_forecasting/test_final_range_metrics.csv`
- `reports/glucose_forecasting/test_final_per_patient_metrics.csv`
- `reports/glucose_forecasting/test_calibration_final_evaluation.csv`
- `reports/glucose_forecasting/test_final_evidence_summary.md`

## Key Validation Results

Validation split:

```text
train_inner rows: 107,827
validation rows: 26,963
groups: 12
time_order_safe: true
test_split_used_for_selection: false
```

Leakage audit:

```text
status: pass
threshold_selection_split: validation
model_selection_split: validation
calibration_selection_split: validation
evaluation_split: test
calibration_leakage_safe: true
issues: none
```

Artifact validation:

```text
status: pass
errors: 0
warnings: 11
```

남은 warning은 test leakage가 아니라 90m hypo precision 낮음, calibration/patient audit의 권장 상세 컬럼 부족에 대한 개선 권고다.

## Final Test Metrics

### Forecast MAE

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| enriched raw | 12.974 | 22.712 | 29.827 |
| enriched calibrated | 12.947 | 22.635 | 29.696 |

### Final Event Metrics on Test

| Event | Horizon | Precision | Recall | F1 | PR-AUC | ROC-AUC |
|---|---:|---:|---:|---:|---:|---:|
| hypo | 30m | 0.494 | 0.811 | 0.614 | 0.673 | 0.985 |
| hypo | 60m | 0.214 | 0.800 | 0.337 | 0.424 | 0.944 |
| hypo | 90m | 0.159 | 0.632 | 0.254 | 0.276 | 0.886 |
| hyper | 30m | 0.900 | 0.869 | 0.884 | 0.958 | 0.975 |
| hyper | 60m | 0.836 | 0.745 | 0.788 | 0.884 | 0.927 |
| hyper | 90m | 0.779 | 0.623 | 0.692 | 0.803 | 0.869 |

## Interpretation

이제 발표/보고서에는 다음과 같이 말할 수 있다.

```text
저혈당/고혈당 가능성 판단 모델은 validation set에서 threshold와 model family를 선택하고,
test set에서는 고정된 설정으로 최종 평가하였다.
따라서 test set은 모델 선택에 사용되지 않았다.
```

주의할 점:

- 60m/90m hypo recall은 높아졌지만 precision은 낮다.
- 특히 90m hypo는 오경고 가능성이 있으므로 UI에서는 “가능성/주의 신호”로만 표현해야 한다.
- RandomForest probability는 calibrated clinical probability가 아니라 모델 점수로 해석해야 한다.
- 모든 혈당 관련 결과는 참고용이며 의료 진단이나 치료 지침이 아니다.

## Tests

실행:

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting \
  --use-validation-selection

python3 scripts/validate_glucose_artifacts.py \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting

python3 -m pytest tests/ -q
```

결과:

```text
53 passed in 5.35s
```
