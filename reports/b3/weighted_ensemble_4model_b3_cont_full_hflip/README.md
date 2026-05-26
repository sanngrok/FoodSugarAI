# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.15`
- b0_seed123_fixed_v1: `0.2`
- b3_cont_fixed_v1: `0.25`
- b3_full_fixed_v1: `0.4`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.3`
- b3_cont_fixed_v1: `0.0`
- b3_full_fixed_v1: `0.6`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.925000011920929 | 0.9845238327980042 | 0.9249302893101577 |
| best | evaluation | 0.9107142686843872 | 0.9752976298332214 | 0.910215146260738 |
| best | full | 0.9178571701049805 | 0.9799107313156128 | 0.9176322396953402 |
| simple_avg | calibration | 0.9202380776405334 | 0.9839285612106323 | 0.9202583785808743 |
| simple_avg | evaluation | 0.9095237851142883 | 0.975595235824585 | 0.9090113854000685 |
| simple_avg | full | 0.9148809313774109 | 0.9797618985176086 | 0.9146952726160517 |
| diagnostic_full_best | full | 0.9193452596664429 | 0.9788690209388733 | 0.919121813223318 |
