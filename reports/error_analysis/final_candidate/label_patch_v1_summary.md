# K-Food Label Patch v1 Summary

- reviewed: `reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv`
- patch_output: `data/processed/kfood_label_patch_v1.csv`
- exclude_output: `data/processed/kfood_exclude_list_v1.csv`
- reviewed_rows: `300`
- patch_rows: `156`
- exclude_rows: `30`
- skipped_rows: `0`

## Action Counts

| Action | Count |
|---|---:|
| relabel | 126 |
| remove | 30 |

## Status Counts

| Status | Count |
|---|---:|
| multi_food | 30 |
| wrong_label | 126 |

```json
{
  "reviewed": "reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv",
  "patch_output": "data/processed/kfood_label_patch_v1.csv",
  "exclude_output": "data/processed/kfood_exclude_list_v1.csv",
  "reviewed_rows": 300,
  "patch_rows": 156,
  "exclude_rows": 30,
  "skipped_rows": 0,
  "action_counts": {
    "relabel": 126,
    "remove": 30
  },
  "status_counts": {
    "wrong_label": 126,
    "multi_food": 30
  },
  "new_label_counts": {
    "비빔냉면": 1,
    "blank": 30,
    "보쌈": 3,
    "불고기": 6,
    "갈비찜": 8,
    "약식": 7,
    "파전": 1,
    "후라이드치킨": 4,
    "수제비": 3,
    "잡곡밥": 2,
    "순두부찌개": 3,
    "잔치국수": 2,
    "쫄면": 7,
    "훈제오리": 1,
    "갈비구이": 5,
    "비빔밥": 3,
    "감자전": 2,
    "짜장면": 3,
    "약과": 1,
    "김치찌개": 1,
    "계란말이": 3,
    "피자": 1,
    "닭갈비": 4,
    "물냉면": 4,
    "떡갈비": 2,
    "라볶이": 5,
    "주먹밥": 2,
    "떡볶이": 5,
    "양념치킨": 3,
    "김치볶음밥": 2,
    "짬뽕": 7,
    "새우볶음밥": 6,
    "된장찌개": 1,
    "알밥": 2,
    "칼국수": 2,
    "식혜": 1,
    "유부초밥": 1,
    "라면": 2,
    "닭볶음탕": 1,
    "호박전": 1,
    "고등어구이": 1,
    "족발": 2,
    "삼겹살": 1,
    "김치찜": 2,
    "감자탕": 1,
    "갈비탕": 1
  },
  "skipped": []
}
```
