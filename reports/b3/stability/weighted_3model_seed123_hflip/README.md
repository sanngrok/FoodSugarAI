# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.15`
- b0_seed123_fixed_v1: `0.4`
- b3_probe_fixed_v1: `0.45`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.4`
- b3_probe_fixed_v1: `0.5`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9092261791229248 | 0.9767857193946838 | 0.9090445912737274 |
| best | evaluation | 0.911309540271759 | 0.976190447807312 | 0.9110112201057226 |
| best | full | 0.9102678298950195 | 0.9764881134033203 | 0.9100799237537903 |
| simple_avg | calibration | 0.9065476059913635 | 0.9782738089561462 | 0.9063931315190189 |
| simple_avg | evaluation | 0.9071428775787354 | 0.9782738089561462 | 0.9069238278994565 |
| simple_avg | full | 0.906845211982727 | 0.9782738089561462 | 0.9066856865751445 |
| diagnostic_full_best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
