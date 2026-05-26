# K-Food Label Patch Impact Audit

- data_dir: `data/raw/korean_food_fixed_v1`
- patch_rows: `23`
- train_affected: `23`
- val_affected: `0`

## Per Action

| Split | Action | Count |
|---|---|---:|
| train | relabel | 14 |
| train | remove | 9 |

## Judgment

- If validation affected rows are used for `val_cleaned`, report it separately from `val_original_fixed`.
- If train affected rows dominate, retraining on cleaned train is the main test.
