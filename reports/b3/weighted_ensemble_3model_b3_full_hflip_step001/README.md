# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.01`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.12`
- b0_seed123_fixed_v1: `0.29`
- b3_full_fixed_v1: `0.59`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.12`
- b0_seed123_fixed_v1: `0.29`
- b3_full_fixed_v1: `0.59`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9247024059295654 | 0.9839285612106323 | 0.9245879020038519 |
| best | evaluation | 0.9148809313774109 | 0.9750000238418579 | 0.9144232724662749 |
| best | full | 0.9197916388511658 | 0.9794642925262451 | 0.9195684820093929 |
| simple_avg | calibration | 0.9157738089561462 | 0.9824404716491699 | 0.9158467198718055 |
| simple_avg | evaluation | 0.9092261791229248 | 0.9744047522544861 | 0.9087515697348483 |
| simple_avg | full | 0.9125000238418579 | 0.9784226417541504 | 0.91236189246482 |
| diagnostic_full_best | full | 0.9197916388511658 | 0.9794642925262451 | 0.9195684820093929 |
