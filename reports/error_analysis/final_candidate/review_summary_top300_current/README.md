# K-Food Label Review Summary

- reviewed: `reports/error_analysis/final_candidate/review_sheet_top300.csv`
- total_rows: `300`
- reviewed_count: `0`
- noisy_label_ratio: `0.000000`

## Review Status Counts

| Status | Count |
|---|---:|
| blank | 300 |

## Decision Rule

- Noisy statuses: `wrong_label, ambiguous, multi_food, low_quality, out_of_scope`.
- If noisy statuses >= 10%, prioritize cleaned data retraining.
- If noisy statuses < 5%, prioritize model diversity and ensemble weighting.
