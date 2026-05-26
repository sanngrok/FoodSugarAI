# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_1000`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `11194`

## Best Weights

- b0_baseline: `0.5`
- food_lewm_b0: `0.35`
- b0_supervised_only: `0.15`

## Diagnostic Full-Best Weights

- b0_baseline: `0.45`
- food_lewm_b0: `0.2`
- b0_supervised_only: `0.35`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.8996428847312927 | 0.9775000214576721 | 0.8994444904603414 |
| best | evaluation | 0.9016803503036499 | 0.9760457873344421 | 0.9015790339280235 |
| best | full | 0.900661051273346 | 0.9767732620239258 | 0.9005454101987682 |
| simple_avg | calibration | 0.8964285850524902 | 0.9766071438789368 | 0.8962644722264479 |
| simple_avg | evaluation | 0.9020379185676575 | 0.9755094647407532 | 0.9019521520038278 |
| simple_avg | full | 0.8992317318916321 | 0.9760586023330688 | 0.8991260984446873 |
| diagnostic_full_best | full | 0.9014650583267212 | 0.9760586023330688 | 0.9013247392109426 |
