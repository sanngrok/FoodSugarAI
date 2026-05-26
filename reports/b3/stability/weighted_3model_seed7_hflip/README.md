# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.05`
- b0_seed123_fixed_v1: `0.35`
- b3_probe_fixed_v1: `0.6`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.4`
- b3_probe_fixed_v1: `0.5`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9125000238418579 | 0.9776785969734192 | 0.9124162875337837 |
| best | evaluation | 0.9092261791229248 | 0.9764881134033203 | 0.908908505644756 |
| best | full | 0.9108631014823914 | 0.9770833253860474 | 0.910713609306059 |
| simple_avg | calibration | 0.9083333611488342 | 0.9782738089561462 | 0.9081765730808419 |
| simple_avg | evaluation | 0.9053571224212646 | 0.9782738089561462 | 0.9050772814364715 |
| simple_avg | full | 0.906845211982727 | 0.9782738089561462 | 0.9066856865751445 |
| diagnostic_full_best | full | 0.911309540271759 | 0.9764881134033203 | 0.9110894033795439 |
