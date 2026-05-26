# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.4`
- b3_probe_fixed_v1: `0.5`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.4`
- b3_probe_fixed_v1: `0.5`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9172618985176086 | 0.981249988079071 | 0.9172033152760297 |
| best | evaluation | 0.9053571224212646 | 0.9717261791229248 | 0.9046963322904661 |
| best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
| simple_avg | calibration | 0.9104166626930237 | 0.9821428656578064 | 0.910447812017621 |
| simple_avg | evaluation | 0.9032738208770752 | 0.9744047522544861 | 0.9027561830319907 |
| simple_avg | full | 0.906845211982727 | 0.9782738089561462 | 0.9066856865751445 |
| diagnostic_full_best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
