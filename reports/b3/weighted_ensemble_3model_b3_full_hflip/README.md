# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.2`
- b0_seed123_fixed_v1: `0.25`
- b3_full_fixed_v1: `0.55`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.3`
- b3_full_fixed_v1: `0.6`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9238095283508301 | 0.9845238327980042 | 0.9237767062004201 |
| best | evaluation | 0.9145833253860474 | 0.9747023582458496 | 0.9141813923563752 |
| best | full | 0.9191964268684387 | 0.9796130657196045 | 0.9190306146989915 |
| simple_avg | calibration | 0.9157738089561462 | 0.9824404716491699 | 0.9158467198718055 |
| simple_avg | evaluation | 0.9092261791229248 | 0.9744047522544861 | 0.9087515697348483 |
| simple_avg | full | 0.9125000238418579 | 0.9784226417541504 | 0.91236189246482 |
| diagnostic_full_best | full | 0.9193452596664429 | 0.9788690209388733 | 0.919121813223318 |
