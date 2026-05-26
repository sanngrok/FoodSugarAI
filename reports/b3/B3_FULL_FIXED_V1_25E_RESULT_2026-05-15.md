# B3 Full Fixed_v1 25epoch Result - 2026-05-15

## Summary

- 요청대로 `efficientnet_b3` full training을 중단 없이 25epoch까지 완료했다.
- 데이터는 `data/raw/korean_food_fixed_v1`, 기준 검증 split은 `val`이다.
- 기존 운영 best 파일은 덮어쓰지 않았고, B3 full 전용 파일로만 저장했다.
- 최종 best single은 epoch 25에서 갱신되었다.

## Training Config

- Model: `efficientnet_b3`
- Image size: `300`
- Epochs: `25`
- Batch size: `8`
- Grad accumulation: `4`
- LR: `3e-5`
- Head LR: `3e-4`
- Warmup epochs: `2`
- TTA during training validation: none
- Device: MPS
- Checkpoint: `data/models/efficientnet_korean_b3_full_fixed_v1.pt`
- Metadata: `data/models/korean_food_model_meta_b3_full_fixed_v1.json`
- Classes: `data/models/korean_food_classes_b3_full_fixed_v1.json`
- Report dir: `reports/b3/b3_full_fixed_v1`

## Best Single Result

| Eval | top1 | top3 | macro_f1 | Notes |
|---|---:|---:|---:|---|
| train-time val | 0.903423 | 0.973065 | 0.903170 | best epoch 25 |
| hflip eval | 0.904315 | 0.974554 | 0.904010 | `reports/b3/eval_b3_full_fixed_v1_hflip` |

## Important Epochs

| Epoch | val_top1 | macro_f1 | Notes |
|---:|---:|---:|---|
| 10 | 0.886607 | 0.886431 | 기존 B3 장기학습 초반 기준 |
| 16 | 0.898958 | 0.898693 | 90% 직전 |
| 19 | 0.900446 | 0.900224 | single 90% 첫 돌파 |
| 20 | 0.902381 | 0.902122 | 큰 폭 갱신 |
| 21 | 0.903274 | 0.903046 | 기존 best 갱신 |
| 25 | 0.903423 | 0.903170 | 최종 best checkpoint 저장 |

## Ensemble Results

| Ensemble | Weights | top1 | top3 | macro_f1 | Decision |
|---|---|---:|---:|---:|---|
| 3-model hflip | `food_lewm_b0=0.20`, `b0_seed123_fixed_v1=0.25`, `b3_full_fixed_v1=0.55` | 0.919196 | 0.979613 | 0.919031 | best candidate |
| 4-model hflip | `food_lewm_b0=0.15`, `b0_seed123_fixed_v1=0.20`, `b3_cont_fixed_v1=0.25`, `b3_full_fixed_v1=0.40` | 0.917857 | 0.979911 | 0.917632 | 3-model보다 낮음 |

## Comparison

- Previous current best:
  - `reports/current_best/fixed_weight_3model_hflip`
  - top1 `0.913095`
  - macro_f1 `0.912846`
- New best candidate:
  - `reports/b3/weighted_ensemble_3model_b3_full_hflip`
  - top1 `0.919196`
  - macro_f1 `0.919031`
- Improvement over previous current best:
  - top1: `+0.006101`
  - macro_f1: about `+0.006185`

## Output Files

- Training metrics: `reports/b3/b3_full_fixed_v1/metrics.json`
- Training log: `reports/b3/b3_full_fixed_v1/train_log.csv`
- Single hflip eval: `reports/b3/eval_b3_full_fixed_v1_hflip/metrics.json`
- 3-model ensemble: `reports/b3/weighted_ensemble_3model_b3_full_hflip/metrics.json`
- 4-model ensemble: `reports/b3/weighted_ensemble_4model_b3_cont_full_hflip/metrics.json`

## Current Decision

- B3 full 25epoch는 성공 실험으로 판단한다.
- 운영 후보는 우선 `3-model hflip ensemble`이 가장 강하다.
- 4-model에서 B3 continuation을 추가하면 full top1이 낮아져서, 현 시점에서는 B3 continuation을 운영 후보에 넣지 않는 쪽이 낫다.

## Next Recommended Steps

1. `reports/b3/weighted_ensemble_3model_b3_full_hflip`를 새 current best 후보로 고정한다.
2. hard class / high confidence error를 새 best 기준으로 다시 뽑는다.
3. top300 사람 검수 결과와 label noise 분석을 새 best 기준으로 갱신한다.
4. 운영 후보로 올리기 전 latency와 모델 수를 같이 검토한다.
