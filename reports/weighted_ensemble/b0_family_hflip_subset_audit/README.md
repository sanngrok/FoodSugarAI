# Cached Ensemble Subset Evaluation

- cache: `reports/weighted_ensemble/b0_family_hflip/logits_cache.pt`
- class_filename_overlaps: `reports/split_leakage_audit/all_class_filename_overlaps.csv`

## Subset Counts

| Subset | Count | Ratio |
|---|---:|---:|
| full | 11194 | 1.000000 |
| old_train_filename_overlap_new_val | 4474 | 0.399678 |
| old_val_filename_overlap_new_val | 6720 | 0.600322 |
| minus_old_train_filename_overlap | 6720 | 0.600322 |
| minus_old_train_and_old_val_filename_overlap | 0 | 0.000000 |

## Weighted Selected Metrics

| Subset | Count | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|---:|
| full | 11194 | 0.900661 | 0.976773 | 0.900545 |
| old_train_filename_overlap_new_val | 4474 | 0.928923 | 0.987483 | 0.928789 |
| old_val_filename_overlap_new_val | 6720 | 0.881845 | 0.969643 | 0.881695 |
| minus_old_train_filename_overlap | 6720 | 0.881845 | 0.969643 | 0.881695 |
| minus_old_train_and_old_val_filename_overlap | 0 | 0.000000 | 0.000000 | 0.000000 |

## Ensemble Comparison On Key Subsets

| Ensemble | Full Top1 | Old-Train-Overlap Top1 | Minus-Old-Train Top1 |
|---|---:|---:|---:|
| simple_average | 0.899232 | 0.916853 | 0.887500 |
| weighted_selected | 0.900661 | 0.928923 | 0.881845 |
| diagnostic_full_best | 0.901465 | 0.924899 | 0.885863 |
| single_b0_baseline | 0.873504 | 0.938757 | 0.830060 |
| single_food_lewm_b0 | 0.869484 | 0.869692 | 0.869345 |
| single_b0_supervised_only | 0.879757 | 0.879079 | 0.880208 |

## Best Weight Sweep By Subset

| Subset | Top1 | Top3 | Macro-F1 | Weights |
|---|---:|---:|---:|---|
| full | 0.901465 | 0.976059 | 0.901325 | b0_baseline=0.45, food_lewm_b0=0.2, b0_supervised_only=0.35 |
| minus_old_train_filename_overlap | 0.890476 | 0.969940 | 0.890290 | b0_baseline=0.05, food_lewm_b0=0.45, b0_supervised_only=0.5 |
| old_train_filename_overlap_new_val | 0.939204 | 0.991059 | 0.939139 | b0_baseline=0.85, food_lewm_b0=0.15, b0_supervised_only=0.0 |
| old_val_filename_overlap_new_val | 0.890476 | 0.969940 | 0.890290 | b0_baseline=0.05, food_lewm_b0=0.45, b0_supervised_only=0.5 |

## Interpretation

- `old_train_filename_overlap_new_val` is the highest-risk subset for models trained on the old train split.
- `minus_old_train_filename_overlap` is the more conservative validation view for any ensemble containing the old B0 baseline.
- If the overlap subset is much easier than the minus-overlap subset, current full-val numbers should be treated as optimistic.
