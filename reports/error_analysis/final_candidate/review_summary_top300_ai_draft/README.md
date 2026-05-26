# K-Food Label Review Summary

- reviewed: `reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv`
- total_rows: `300`
- reviewed_count: `300`
- noisy_label_ratio: `0.520000`

## Review Status Counts

| Status | Count |
|---|---:|
| model_error | 144 |
| wrong_label | 126 |
| multi_food | 30 |

## Decision Rule

- Noisy statuses: `wrong_label, ambiguous, multi_food, low_quality, out_of_scope`.
- If noisy statuses >= 10%, prioritize cleaned data retraining.
- If noisy statuses < 5%, prioritize model diversity and ensemble weighting.
