# K-Food Label Patch v1 Summary

- reviewed: `reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv`
- patch_output: `data/processed/kfood_train_hard_pair_patch_v2.csv`
- exclude_output: `data/processed/kfood_train_hard_pair_exclude_v2.csv`
- reviewed_rows: `300`
- patch_rows: `23`
- exclude_rows: `9`
- skipped_rows: `0`

## Action Counts

| Action | Count |
|---|---:|
| relabel | 14 |
| remove | 9 |

## Status Counts

| Status | Count |
|---|---:|
| ambiguous | 2 |
| multi_food | 7 |
| wrong_label | 14 |

```json
{
  "reviewed": "reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv",
  "patch_output": "data/processed/kfood_train_hard_pair_patch_v2.csv",
  "exclude_output": "data/processed/kfood_train_hard_pair_exclude_v2.csv",
  "reviewed_rows": 300,
  "patch_rows": 23,
  "exclude_rows": 9,
  "skipped_rows": 0,
  "action_counts": {
    "relabel": 14,
    "remove": 9
  },
  "status_counts": {
    "wrong_label": 14,
    "ambiguous": 2,
    "multi_food": 7
  },
  "new_label_counts": {
    "호박전": 4,
    "감자전": 1,
    "김치찌개": 1,
    "라볶이": 2,
    "떡볶이": 1,
    "순두부찌개": 1,
    "감자탕": 1,
    "blank": 9,
    "갈비탕": 1,
    "수제비": 2
  },
  "skipped": []
}
```
