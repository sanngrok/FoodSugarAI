# Cached Ensemble Weight Stability

- cache: `reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/logits_cache.pt`
- weight_step: `0.05`
- calibration_ratio: `0.5`
- seeds: `0, 1, 2, 7, 42, 123`

## Selected Weight Ranges

| Model | Min | Mean | Max |
|---|---:|---:|---:|
| b0_baseline | 0.0000 | 0.0167 | 0.1000 |
| food_lewm_b0 | 0.1500 | 0.1833 | 0.2000 |
| b0_supervised_only | 0.0000 | 0.0000 | 0.0000 |
| b0_supervised_seed7_fixed_v1 | 0.1000 | 0.1750 | 0.2500 |
| b0_supervised_seed123_fixed_v1 | 0.2500 | 0.3417 | 0.5000 |
| b2_clean_fixed_v1 | 0.0000 | 0.2833 | 0.3500 |

## Per-Seed Metrics

| Seed | Full Top1 | Eval Top1 | Full Macro-F1 |
|---:|---:|---:|---:|
| 0 | 0.900298 | 0.899107 | 0.900050 |
| 1 | 0.900149 | 0.903571 | 0.899961 |
| 2 | 0.900149 | 0.895238 | 0.899897 |
| 7 | 0.898214 | 0.894048 | 0.897979 |
| 42 | 0.900149 | 0.892857 | 0.899900 |
| 123 | 0.900149 | 0.899405 | 0.899900 |
