# K-Food Label Review Summary

- reviewed: `reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_AI_DRAFT.csv`
- total_rows: `300`
- reviewed_count: `300`
- noisy_label_ratio: `0.626667`

## Review Status Counts

| Status | Count |
|---|---:|
| wrong_label | 129 |
| model_error | 112 |
| ambiguous | 34 |
| multi_food | 23 |
| bad_crop | 2 |

## Decision Rule

- Noisy statuses: `wrong_label, ambiguous, multi_food, bad_crop, class_definition_overlap, low_quality, out_of_scope, unclear`.
- If noisy statuses >= 10%, prioritize cleaned data retraining.
- If noisy statuses < 5%, prioritize model diversity and ensemble weighting.
