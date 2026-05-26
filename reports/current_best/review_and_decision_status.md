# Current Best Review And Decision Status

- high_conf_review_exists: `True`
- train_review_exists: `True`
- high_conf_label_boundary_ratio: `0.6266666666666667`
- train_patch_rows: `23`
- decision: `label_hard_pair_cleaning_first`

## High-Confidence Review Status Counts

| Status | Count |
|---|---:|
| wrong_label | 129 |
| model_error | 112 |
| ambiguous | 34 |
| multi_food | 23 |
| bad_crop | 2 |

## Train Review Status Counts

| Status | Count |
|---|---:|
| correct | 277 |
| wrong_label | 14 |
| multi_food | 7 |
| ambiguous | 2 |

## Notes

- This runner does not start B3 full training.
- This runner does not create cleaned_train_v1.
- Missing human review files keep the decision in a waiting state.
