# Ensemble Fine Weight Sweep - 2026-05-16

## Summary

3-model hflip ensemble의 weight를 더 촘촘하게 탐색했다.

결론:

- 기존 `0.05` step 대비 성능은 올랐다.
- 최고 full validation top1은 `0.919792`, 즉 **91.9792%**다.
- 92% 기준에는 약 `0.0208%p`, 샘플 기준 약 2장 부족하다.
- 현재 validation split에서 weight 조정만으로 92%를 넘기는 것은 어려워 보인다.

## Base Ensemble

```text
models:
  food_lewm_b0
  b0_seed123_fixed_v1
  b3_full_fixed_v1
tta: hflip
data_dir: data/raw/korean_food_fixed_v1
val_subdir: val
num_samples: 6720
```

## Results

| Search | Weights | top1 | Correct | top3 | macro_f1 | Notes |
|---|---|---:|---:|---:|---:|---|
| step 0.05 | `0.20 / 0.25 / 0.55` | 0.919196 | about 6179 | 0.979613 | 0.919031 | previous best official |
| step 0.025 | `0.125 / 0.300 / 0.575` | 0.919494 | about 6180 | 0.979464 | 0.919254 | improved |
| step 0.01 | `0.120 / 0.290 / 0.590` | 0.919792 | 6181 | 0.979464 | 0.919568 | best official calibration sweep |
| local 0.001 | `0.121 / 0.284 / 0.595` | 0.919792 | 6181 | 0.979762 | 0.919553 | top1 unchanged, top3 slightly higher |
| global 0.002 | `0.112 / 0.290 / 0.598` | 0.919792 | 6181 | 0.979315 | 0.919563 | top1 unchanged |

## Best Recommendation

공식 candidate로는 `step 0.01` 결과를 추천한다.

```text
food_lewm_b0:        0.12
b0_seed123_fixed_v1: 0.29
b3_full_fixed_v1:    0.59
tta:                 hflip
top1:                0.919792
top3:                0.979464
macro_f1:            0.919568
```

이전 best 대비:

```text
previous top1: 0.919196
new top1:      0.919792
gain:          +0.000595
```

92%까지 남은 gap:

```text
target: 0.920000
best:   0.919792
gap:    0.000208
```

샘플 수 기준:

```text
current correct: 6181 / 6720
92% threshold:  6183 / 6720 수준
gap:            약 2 samples
```

## Output Paths

```text
reports/b3/weighted_ensemble_3model_b3_full_hflip_step0025
reports/b3/weighted_ensemble_3model_b3_full_hflip_step001
reports/b3/weighted_ensemble_3model_b3_full_hflip_step0005
reports/b3/weighted_ensemble_3model_b3_full_hflip_local001
reports/b3/weighted_ensemble_3model_b3_full_hflip_global002
```

## Decision

이번 fine weight sweep만으로는 92%를 넘기지 못했다.

다음 92% 달성 후보는 weight 조정이 아니라 다음 중 하나가 더 현실적이다.

1. 새 best 기준 high-confidence error 2-3장 이상 수정 가능한지 확인.
2. B3 full seed variation 추가 학습 후 ensemble diversity 확보.
3. hard-pair / label noise patch를 반영한 cleaned train split 실험.
4. 운영 latency를 허용한다면 TTA 확장 실험.
