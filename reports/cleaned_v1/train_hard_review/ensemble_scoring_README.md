# Train Review Ensemble Scoring

- review_csv: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- output_csv: `reports/cleaned_v1/train_hard_review/train_hard_review_scored.csv`
- suspects_output: `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`
- tta: `hflip`
- suspect_threshold: `0.8`
- num_rows: `500`
- num_suspects: `7`

## Important

`model_suspect` rows are not confirmed label errors. They require visual/human review before relabel/remove patching.

```json
{
  "review_csv": "reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv",
  "output_csv": "reports/cleaned_v1/train_hard_review/train_hard_review_scored.csv",
  "suspects_output": "reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv",
  "weights_json": "reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/metrics.json",
  "tta": "hflip",
  "suspect_threshold": 0.8,
  "num_rows": 500,
  "num_suspects": 7,
  "prefilled_existing_ai_patch_rows": 49,
  "models": [
    {
      "name": "b0_baseline",
      "checkpoint": "data/models/efficientnet_korean_b0_val08275.pt",
      "metadata": "data/models/korean_food_model_meta.json",
      "weight": 0.0,
      "image_size": 224
    },
    {
      "name": "food_lewm_b0",
      "checkpoint": "data/models/food_lewm_b0_classifier_3ep_ft10.pt",
      "metadata": "data/models/food_lewm_b0_meta_3ep_ft10.json",
      "weight": 0.15,
      "image_size": 224
    },
    {
      "name": "b0_supervised_only",
      "checkpoint": "data/models/food_lewm_b0_supervised_only_ft10.pt",
      "metadata": "data/models/food_lewm_b0_supervised_only_meta_ft10.json",
      "weight": 0.0,
      "image_size": 224
    },
    {
      "name": "b0_supervised_seed7_fixed_v1",
      "checkpoint": "data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt",
      "metadata": "data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json",
      "weight": 0.25,
      "image_size": 224
    },
    {
      "name": "b0_supervised_seed123_fixed_v1",
      "checkpoint": "data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt",
      "metadata": "data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json",
      "weight": 0.25,
      "image_size": 224
    },
    {
      "name": "b2_clean_fixed_v1",
      "checkpoint": "data/models/efficientnet_korean_b2_clean_fixed_v1.pt",
      "metadata": "data/models/korean_food_model_meta_b2_clean_fixed_v1.json",
      "weight": 0.35,
      "image_size": 260
    }
  ]
}
```
