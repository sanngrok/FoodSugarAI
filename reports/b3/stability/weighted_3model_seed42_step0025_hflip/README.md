# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- val_subdir: `val`
- tta: `hflip`
- weight_step: `0.025`
- num_samples: `6720`

## Best Weights

- food_lewm_b0: `0.1`
- b0_seed123_fixed_v1: `0.375`
- b3_probe_fixed_v1: `0.525`

## Diagnostic Full-Best Weights

- food_lewm_b0: `0.05`
- b0_seed123_fixed_v1: `0.425`
- b3_probe_fixed_v1: `0.525`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9172618985176086 | 0.981249988079071 | 0.9172258325677215 |
| best | evaluation | 0.9047619104385376 | 0.9723214507102966 | 0.9040909943633031 |
| best | full | 0.9110119342803955 | 0.9767857193946838 | 0.9108117226051048 |
| simple_avg | calibration | 0.9104166626930237 | 0.9821428656578064 | 0.910447812017621 |
| simple_avg | evaluation | 0.9032738208770752 | 0.9744047522544861 | 0.9027561830319907 |
| simple_avg | full | 0.906845211982727 | 0.9782738089561462 | 0.9066856865751445 |
| diagnostic_full_best | full | 0.9114583134651184 | 0.9764881134033203 | 0.9112411205161373 |
