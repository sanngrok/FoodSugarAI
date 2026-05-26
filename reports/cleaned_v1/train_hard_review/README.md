# Train Hard-Class Review Sheet

- data_dir: `data/raw/korean_food_fixed_v1`
- output_csv: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- num_samples: `500`
- seed: `42`

## Source Counts

| Source | Count |
|---|---:|
| hard_pair_pred_side | 178 |
| hard_pair_true_side | 177 |
| hard_class_extra | 96 |
| existing_ai_patch_train_affected | 49 |

## Top Class Counts

| Class | Count |
|---|---:|
| 갈비구이 | 43 |
| 곰탕_설렁탕 | 33 |
| 김치찌개 | 28 |
| 동태찌개 | 27 |
| 칼국수 | 26 |
| 삼겹살 | 23 |
| 갈비찜 | 22 |
| 라면 | 19 |
| 불고기 | 18 |
| 호박전 | 18 |
| 라볶이 | 18 |
| 닭볶음탕 | 16 |
| 갈비탕 | 14 |
| 감자전 | 13 |
| 떡볶이 | 13 |
| 수제비 | 13 |
| 잔치국수 | 13 |
| 삼계탕 | 12 |
| 새우볶음밥 | 12 |
| 족발 | 10 |
| 닭갈비 | 10 |
| 알밥 | 9 |
| 김치볶음밥 | 8 |
| 양념치킨 | 8 |
| 닭계장 | 7 |
| 물냉면 | 7 |
| 보쌈 | 7 |
| 비빔냉면 | 6 |
| 김치찜 | 6 |
| 순두부찌개 | 6 |

## Important

This sheet samples fixed_v1 train images around hard classes and hard pairs.
Rows are candidates for human review, not confirmed label errors.

```json
{
  "data_dir": "data/raw/korean_food_fixed_v1",
  "output_csv": "reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv",
  "num_samples": 500,
  "max_samples": 500,
  "seed": 42,
  "source_counts": {
    "existing_ai_patch_train_affected": 49,
    "hard_pair_true_side": 177,
    "hard_pair_pred_side": 178,
    "hard_class_extra": 96
  },
  "top_class_counts": {
    "갈비구이": 43,
    "곰탕_설렁탕": 33,
    "김치찌개": 28,
    "동태찌개": 27,
    "칼국수": 26,
    "삼겹살": 23,
    "갈비찜": 22,
    "라면": 19,
    "불고기": 18,
    "호박전": 18,
    "라볶이": 18,
    "닭볶음탕": 16,
    "갈비탕": 14,
    "감자전": 13,
    "떡볶이": 13,
    "수제비": 13,
    "잔치국수": 13,
    "삼계탕": 12,
    "새우볶음밥": 12,
    "족발": 10,
    "닭갈비": 10,
    "알밥": 9,
    "김치볶음밥": 8,
    "양념치킨": 8,
    "닭계장": 7,
    "물냉면": 7,
    "보쌈": 7,
    "비빔냉면": 6,
    "김치찜": 6,
    "순두부찌개": 6
  },
  "note": "Train-focused review candidates only; not a model prediction result."
}
```
