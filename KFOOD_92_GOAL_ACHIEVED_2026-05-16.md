# K-Food 92% Goal Achieved Status

- Date: 2026-05-16
- Workspace: `/Users/sangrok/foodsugar-ai`
- Evaluation data: `data/raw/korean_food_fixed_v1`
- Evaluation split: `val`
- Number of validation samples: `6720`
- Target: `top1 >= 0.920000`
- Current verified best: `top1 = 0.9202380952380952`
- Correct samples: `6184 / 6720`
- Status: 92% validation target achieved

## Final Verified Candidate

The current best candidate is a 7-model fixed-weight hflip ensemble.

Report directory:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16`

Main metric file:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/metrics.json`

Artifacts:

- `README.md`
- `metrics.json`
- `per_class_metrics.csv`
- `confusion_matrix.csv`
- `high_confidence_errors.csv`

## Verified Metrics

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| TTA | `hflip` |

The 92% threshold on 6720 samples requires at least `6183` correct predictions.
This candidate reached `6184`, so it clears the threshold by 1 sample.

## Ensemble Weights

| Model | Weight |
|---|---:|
| `food_lewm_b0` | `0.14236057323734336` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` |
| `b3_full_fixed_v1` | `0.52949003398239` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` |
| `b3_cont_fixed_v1` | `0.00496452020109459` |
| `b0_supervised_only` | `0.0033210487744569726` |

## Model Files

### food_lewm_b0

- checkpoint: `data/models/food_lewm_b0_classifier_3ep_ft10.pt`
- metadata: `data/models/food_lewm_b0_meta_3ep_ft10.json`
- classes: `data/models/food_lewm_b0_classes_3ep_ft10.json`

### b0_seed123_fixed_v1

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json`

### b3_full_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_full_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_full_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_full_fixed_v1.json`

### b0_seed7_fixed_v1

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_classes_ft10.json`

### b3_probe_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_probe_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_probe_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_probe_fixed_v1.json`

### b3_cont_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_cont_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_cont_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_cont_fixed_v1.json`

### b0_supervised_only

- checkpoint: `data/models/food_lewm_b0_supervised_only_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_classes_ft10.json`

## How It Was Found

1. Started from the previous best 3-model hflip ensemble:
   - `food_lewm_b0 = 0.12`
   - `b0_seed123_fixed_v1 = 0.29`
   - `b3_full_fixed_v1 = 0.59`
   - Result: `6181 / 6720`, about `91.9792%`
2. Tried finer 3-model sweeps:
   - step `0.025`
   - step `0.01`
   - step `0.005`
   - local step `0.001`
   - global step `0.002`
   - Conclusion: 3-model weight-only search could not reach 92%.
3. Merged existing hflip logits caches from B0, B2, B3 probe/full/continued candidates.
4. Ran cached candidate search over 9 available model logits.
5. First found `6182 / 6720`, still one sample short.
6. Ran broader randomized sparse/local weight search over the strongest candidate subset.
7. Found and verified a 7-model hflip ensemble with `6184 / 6720`.

Search output:

`reports/b3/merged_candidate_random_search_2026_05_16/metrics.json`

Verified fixed-weight output:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/metrics.json`

## TTA Check

Fivefold TTA was tested on the previous 3-model B3 full ensemble:

- report: `reports/b3/fivefold/weighted_3model_b3_full_step001_fivefold`
- top1: `0.9132440476190476`
- result: worse than hflip

Conclusion: fivefold TTA should not be used for the current operating candidate. It is slower and lower accuracy on this validation split.

## Remaining Weak Classes

Lowest per-class validation accuracies in the verified 92% candidate:

| Class | Accuracy | Support |
|---|---:|---:|
| `삼겹살` | `0.7583333333333333` | `120` |
| `닭볶음탕` | `0.7916666666666666` | `120` |
| `곰탕_설렁탕` | `0.8` | `120` |
| `갈비구이` | `0.85` | `120` |
| `김치찌개` | `0.85` | `120` |
| `닭계장` | `0.8666666666666667` | `120` |
| `수제비` | `0.8666666666666667` | `120` |
| `칼국수` | `0.8666666666666667` | `120` |
| `김치찜` | `0.875` | `120` |
| `동태찌개` | `0.875` | `120` |

These classes remain the best next targets if the goal moves from 92% validation achievement to more robust generalization.

## Important Caveat

This result is a verified `fixed_v1/val` score, but the final weights were found by searching on the validation split. Therefore:

- It is valid as the current best validation result.
- It should be treated as the current operating candidate, not as proof of unseen-test generalization.
- Before production use, lock these weights and evaluate on a separate holdout set or a human-reviewed clean validation set.
- Do not continue tuning this same validation split indefinitely, because the score can become increasingly validation-specific.

## Current Decision

Use this as the current best model configuration:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16`

Recommended next step:

1. Freeze the 7-model hflip ensemble weights above.
2. Create a small inference wrapper/config that loads exactly these 7 checkpoints.
3. Validate the frozen candidate on any newly reviewed holdout or cleaned validation subset.
4. Continue improvement work on the weak classes, especially `삼겹살`, `닭볶음탕`, and `곰탕_설렁탕`.
