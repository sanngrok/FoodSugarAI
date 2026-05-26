# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.025`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.225`
- b0_seed123_fixed_v1: `0.2`
- b3_cont_fixed_v1: `0.575`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.025`
- b0_seed123_fixed_v1: `0.45`
- b3_cont_fixed_v1: `0.525`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9202380776405334 | 0.9830357432365417 | 0.9202998947743473 |
| best | evaluation | 0.9047619104385376 | 0.9750000238418579 | 0.9041692649489121 |
| best | full | 0.9125000238418579 | 0.9790178537368774 | 0.9122724567856147 |
| simple_avg | calibration | 0.9110119342803955 | 0.9818452596664429 | 0.9110988057321353 |
| simple_avg | evaluation | 0.9059523940086365 | 0.9735119342803955 | 0.9054067726168809 |
| simple_avg | full | 0.9084821343421936 | 0.9776785969734192 | 0.9083362427186924 |
| diagnostic_full_best | full | 0.9135416746139526 | 0.9776785969734192 | 0.9133391703428108 |
