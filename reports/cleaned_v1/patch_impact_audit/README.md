# K-Food Label Patch Impact Audit

- data_dir: `data/raw/korean_food_fixed_v1`
- patch_rows: `156`
- train_affected: `49`
- val_affected: `107`

## Per Action

| Split | Action | Count |
|---|---|---:|
| train | relabel | 42 |
| train | remove | 7 |
| val | relabel | 84 |
| val | remove | 23 |

## Judgment

- If validation affected rows are used for `val_cleaned`, report it separately from `val_original_fixed`.
- If train affected rows dominate, retraining on cleaned train is the main test.
