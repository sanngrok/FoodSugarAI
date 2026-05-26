# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.2`
- b0_seed123_fixed_v1: `0.25`
- b3_cont_fixed_v1: `0.55`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.2`
- b0_seed123_fixed_v1: `0.25`
- b3_cont_fixed_v1: `0.55`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9199404716491699 | 0.9833333492279053 | 0.9199314885099781 |
| best | evaluation | 0.90625 | 0.9758928418159485 | 0.9056277084724039 |
| best | full | 0.913095235824585 | 0.9796130657196045 | 0.9128455016622887 |
| simple_avg | calibration | 0.9110119342803955 | 0.9818452596664429 | 0.9110988057321353 |
| simple_avg | evaluation | 0.9059523940086365 | 0.9735119342803955 | 0.9054067726168809 |
| simple_avg | full | 0.9084821343421936 | 0.9776785969734192 | 0.9083362427186924 |
| diagnostic_full_best | full | 0.913095235824585 | 0.9796130657196045 | 0.9128455016622887 |
