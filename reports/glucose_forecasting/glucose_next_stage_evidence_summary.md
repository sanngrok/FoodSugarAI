# FoodSugar Glucose Evidence Summary

## Raw vs Calibrated MAE

| model_type | horizon_minutes | mae | rmse | r2 |
| --- | --- | --- | --- | --- |
| enriched | 30 | 13.0269 | 18.488 | 0.9053 |
| enriched_calibrated | 30 | 12.9984 | 18.4761 | 0.9054 |
| enriched | 60 | 22.7038 | 31.0421 | 0.734 |
| enriched_calibrated | 60 | 22.6334 | 31.0083 | 0.7346 |
| enriched | 90 | 29.7212 | 39.8638 | 0.5633 |
| enriched_calibrated | 90 | 29.6057 | 39.8308 | 0.564 |

## Selected Hypo Classifier

| horizon_minutes | selected_model | precision | recall | f1 | target_met |
| --- | --- | --- | --- | --- | --- |
| 30 | hist_gradient_boosting_weighted | 0.3304 | 0.8395 | 0.4742 | True |
| 60 | hist_gradient_boosting_weighted | 0.1796 | 0.6536 | 0.2818 | True |
| 90 | hist_gradient_boosting_weighted | 0.1369 | 0.5385 | 0.2183 | True |

## Hyper Classifier

| horizon_minutes | precision | recall | f1 | roc_auc |
| --- | --- | --- | --- | --- |
| 30 | 0.9008 | 0.8677 | 0.8839 | 0.975 |
| 60 | 0.8313 | 0.744 | 0.7852 | 0.9266 |
| 90 | 0.7787 | 0.6263 | 0.6942 | 0.8687 |

## Artifact Validation

- Status: `pass`
- Errors: `0`
- Warnings: `11`

## Leakage Audit

- Threshold selection split: `validation`
- Model selection split: `validation`
- Calibration selection split: `validation`
- Calibration leakage safe: `True`

## API Safety Checklist

- reference_notice/risk_interpretation/safety_warning 유지
- risk_flags와 event_probabilities 반환
- 위험 표현은 확정 진단이 아니라 가능성/주의 신호로 표현
- 음수 carbs/bolus/basal 입력은 Pydantic validation으로 422 처리
- 부족한 CGM readings는 안전한 422 error 처리

## Remaining Limitations

- test set은 model family, threshold, calibration strategy 선택에 사용하지 않고 최종 평가에만 사용한다.
- 90m hypo precision은 낮으므로 운영 UI에서는 경고 강도를 낮추고 실제 측정값 확인을 우선 안내해야 한다.
- RandomForest probability는 calibrated clinical probability가 아니라 모델 점수로 표현해야 한다.
- 모든 결과는 참고용이며 의료 진단이나 치료 지침이 아니다.
