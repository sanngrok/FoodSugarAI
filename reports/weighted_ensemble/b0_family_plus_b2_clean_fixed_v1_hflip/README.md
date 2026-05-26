# Cached Weighted Ensemble Sweep

- cache: `reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/logits_cache.pt`
- data_dir: `data/raw/korean_food_fixed_v1`
- tta: `hflip`

## Best Weights

- b0_baseline: `0.0`
- food_lewm_b0: `0.15`
- b0_supervised_only: `0.0`
- b0_supervised_seed7_fixed_v1: `0.25`
- b0_supervised_seed123_fixed_v1: `0.25`
- b2_clean_fixed_v1: `0.35`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9074404835700989 | 0.9797618985176086 | 0.9073892135846305 |
| best | evaluation | 0.8928571343421936 | 0.9690476059913635 | 0.8922512258473223 |
| best | full | 0.9001488089561462 | 0.9744047522544861 | 0.8998998525372074 |
| simple_avg | calibration | 0.8999999761581421 | 0.9794642925262451 | 0.9000094511825292 |
| simple_avg | evaluation | 0.8883928656578064 | 0.9702380895614624 | 0.8877888232056127 |
| simple_avg | full | 0.8941964507102966 | 0.9748511910438538 | 0.8940156152331689 |
| diagnostic_full_best | full | 0.9007440209388733 | 0.9741071462631226 | 0.9004867754779857 |
