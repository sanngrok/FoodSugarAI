# K-Food Split Leakage Audit

- old_data_dir: `data/raw/korean_food`
- new_data_dir: `data/raw/korean_food_1000`

## Split Counts

| Split | Count |
|---|---:|
| old_train | 26880 |
| old_val | 6720 |
| new_train | 44769 |
| new_val | 11194 |

## Overlap Summary

| Pair | Resolved Unique | Class+Filename Unique |
|---|---:|---:|
| old_train__old_val | 0 | 0 |
| old_train__new_train | 0 | 22406 |
| old_train__new_val | 0 | 4474 |
| old_val__new_train | 0 | 0 |
| old_val__new_val | 0 | 6720 |
| new_train__new_val | 0 | 0 |

## Interpretation

- old_train -> new_val resolved overlap: `0`
- If this value is large, ensembles containing models trained on the old split can be inflated on the new validation split.
- `class_filename` overlap is a softer filename-level check; resolved-path overlap is the stronger leakage signal.
