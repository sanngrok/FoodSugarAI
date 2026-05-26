# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.25`
- b0_seed123_fixed_v1: `0.3`
- b3_cont_fixed_v1: `0.45`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.2`
- b0_seed123_fixed_v1: `0.25`
- b3_cont_fixed_v1: `0.55`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9127976298332214 | 0.9785714149475098 | 0.9126341551290044 |
| best | evaluation | 0.9116071462631226 | 0.9791666865348816 | 0.9112972854158546 |
| best | full | 0.9122023582458496 | 0.9788690209388733 | 0.911993857593109 |
| simple_avg | calibration | 0.9083333611488342 | 0.9779762029647827 | 0.9082201269101792 |
| simple_avg | evaluation | 0.9086309671401978 | 0.9773809313774109 | 0.9084264362272416 |
| simple_avg | full | 0.9084821343421936 | 0.9776785969734192 | 0.9083362427186924 |
| diagnostic_full_best | full | 0.913095235824585 | 0.9796130657196045 | 0.9128455016622887 |
