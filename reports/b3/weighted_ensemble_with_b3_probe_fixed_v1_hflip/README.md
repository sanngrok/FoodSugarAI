# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.1`
- b0_seed7_fixed_v1: `0.0`
- b0_seed123_fixed_v1: `0.4`
- b2_clean_fixed_v1: `0.0`
- b3_probe_fixed_v1: `0.5`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed7_fixed_v1: `0.0`
- b0_seed123_fixed_v1: `0.4`
- b2_clean_fixed_v1: `0.0`
- b3_probe_fixed_v1: `0.5`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9172618985176086 | 0.981249988079071 | 0.9172033152760297 |
| best | evaluation | 0.9053571224212646 | 0.9717261791229248 | 0.9046963322904661 |
| best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
| simple_avg | calibration | 0.9077380895614624 | 0.9824404716491699 | 0.9077044975286176 |
| simple_avg | evaluation | 0.9005952477455139 | 0.9735119342803955 | 0.9000224568658461 |
| simple_avg | full | 0.9041666388511658 | 0.9779762029647827 | 0.9039832441643447 |
| diagnostic_full_best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
