# Train Hard-Class Review Sheet

- data_dir: `data/raw/korean_food_fixed_v1`
- output_csv: `reports/b3/current_best_hard_class_report/train_hard_review_candidates.csv`
- num_samples: `300`
- seed: `42`

## Source Counts

| Source | Count |
|---|---:|
| hard_pair_true_side | 120 |
| hard_pair_pred_side | 120 |
| hard_class_extra | 60 |

## Top Class Counts

| Class | Count |
|---|---:|
| 갈비구이 | 29 |
| 닭볶음탕 | 22 |
| 곰탕_설렁탕 | 18 |
| 삼겹살 | 18 |
| 김치찌개 | 17 |
| 감자전 | 14 |
| 칼국수 | 14 |
| 닭계장 | 14 |
| 떡갈비 | 12 |
| 수제비 | 10 |
| 동태찌개 | 10 |
| 호박전 | 8 |
| 김치찜 | 8 |
| 삼계탕 | 8 |
| 갈비찜 | 8 |
| 양념치킨 | 8 |
| 보쌈 | 8 |
| 찜닭 | 8 |
| 갈비탕 | 4 |
| 떡볶이 | 4 |
| 라볶이 | 4 |
| 물냉면 | 4 |
| 비빔냉면 | 4 |
| 순두부찌개 | 4 |
| 후라이드치킨 | 4 |
| 감자탕 | 4 |
| 약식 | 4 |
| 잡곡밥 | 4 |
| 잔치국수 | 4 |
| 족발 | 4 |

## Important

This sheet samples fixed_v1 train images around hard classes and hard pairs.
Rows are candidates for human review, not confirmed label errors.

```json
{
  "data_dir": "data/raw/korean_food_fixed_v1",
  "output_csv": "reports/b3/current_best_hard_class_report/train_hard_review_candidates.csv",
  "num_samples": 300,
  "max_samples": 300,
  "seed": 42,
  "source_counts": {
    "hard_pair_true_side": 120,
    "hard_pair_pred_side": 120,
    "hard_class_extra": 60
  },
  "top_class_counts": {
    "갈비구이": 29,
    "닭볶음탕": 22,
    "곰탕_설렁탕": 18,
    "삼겹살": 18,
    "김치찌개": 17,
    "감자전": 14,
    "칼국수": 14,
    "닭계장": 14,
    "떡갈비": 12,
    "수제비": 10,
    "동태찌개": 10,
    "호박전": 8,
    "김치찜": 8,
    "삼계탕": 8,
    "갈비찜": 8,
    "양념치킨": 8,
    "보쌈": 8,
    "찜닭": 8,
    "갈비탕": 4,
    "떡볶이": 4,
    "라볶이": 4,
    "물냉면": 4,
    "비빔냉면": 4,
    "순두부찌개": 4,
    "후라이드치킨": 4,
    "감자탕": 4,
    "약식": 4,
    "잡곡밥": 4,
    "잔치국수": 4,
    "족발": 4
  },
  "note": "Train-focused review candidates only; not a model prediction result."
}
```
