# CGM Final Test Evaluation

- model/threshold selection split: `validation`
- evaluation split: `test`
- test used for selection: `False`
- statement: validation에서 선택한 model family, threshold, calibration strategy를 고정한 뒤 test에서 최종 평가했다.
- selected calibration strategy: `predicted_range_mean_residual`
- reference notice: 이 결과는 참고용이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리 결정은 의료진과 상의하세요.

## Forecast Metrics

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

## Event Metrics

| Event | Horizon | Split | Threshold | Precision | Recall | F1 | PR-AUC | ROC-AUC | FN | FP |
|---|---:|---|---:|---:|---:|---:|---:|---:|---:|---:|
| hyper | 30m | test | 0.50 | 0.901 | 0.868 | 0.884 | 0.958 | 0.975 | 1369 | 989 |
| hyper | 60m | test | 0.50 | 0.831 | 0.744 | 0.785 | 0.883 | 0.927 | 2649 | 1563 |
| hyper | 90m | test | 0.50 | 0.779 | 0.626 | 0.694 | 0.803 | 0.869 | 3870 | 1843 |
| hypo | 30m | test | 0.50 | 0.358 | 0.912 | 0.514 | 0.650 | 0.984 | 70 | 1306 |
| hypo | 60m | test | 0.50 | 0.209 | 0.795 | 0.331 | 0.377 | 0.941 | 168 | 2459 |
| hypo | 90m | test | 0.50 | 0.157 | 0.640 | 0.252 | 0.251 | 0.880 | 300 | 2869 |

## Remaining Limitations

- 90분 저혈당 precision은 낮을 수 있어 운영 UI에서는 가능성/주의 신호로만 표현해야 한다.
- RandomForest probability는 calibrated clinical probability가 아니라 모델 점수로 해석해야 한다.
- 본 결과는 참고용이며 의료 진단이나 치료 지침이 아니다.
