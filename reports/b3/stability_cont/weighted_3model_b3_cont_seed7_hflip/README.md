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
| best | calibration | 0.9160714149475098 | 0.9794642925262451 | 0.9158736939349151 |
| best | evaluation | 0.9101190567016602 | 0.9797618985176086 | 0.9097491539811361 |
| best | full | 0.913095235824585 | 0.9796130657196045 | 0.9128455016622887 |
| simple_avg | calibration | 0.9098214507102966 | 0.9773809313774109 | 0.9097370335385219 |
| simple_avg | evaluation | 0.9071428775787354 | 0.9779762029647827 | 0.9068866982679129 |
| simple_avg | full | 0.9084821343421936 | 0.9776785969734192 | 0.9083362427186924 |
| diagnostic_full_best | full | 0.913095235824585 | 0.9796130657196045 | 0.9128455016622887 |
