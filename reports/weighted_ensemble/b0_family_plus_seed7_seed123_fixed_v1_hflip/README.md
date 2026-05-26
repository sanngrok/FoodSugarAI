# Cached Weighted Ensemble Sweep

- cache: `reports/weighted_ensemble/b0_family_plus_seed7_seed123_fixed_v1_hflip/logits_cache.pt`
- data_dir: `data/raw/korean_food_fixed_v1`
- tta: `hflip`

## Best Weights

- b0_baseline: `0.1`
- food_lewm_b0: `0.2`
- b0_supervised_only: `0.0`
- b0_supervised_seed7_fixed_v1: `0.2`
- b0_supervised_seed123_fixed_v1: `0.5`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.9026785492897034 | 0.975595235824585 | 0.902676835982211 |
| best | evaluation | 0.893750011920929 | 0.9669643044471741 | 0.893056842170292 |
| best | full | 0.8982142806053162 | 0.9712797403335571 | 0.8979793158403641 |
| simple_avg | calibration | 0.8970237970352173 | 0.9773809313774109 | 0.8969901388430311 |
| simple_avg | evaluation | 0.8901785612106323 | 0.9678571224212646 | 0.8895767890261916 |
| simple_avg | full | 0.8936011791229248 | 0.9726190567016602 | 0.8933875364431442 |
| diagnostic_full_best | full | 0.8982142806053162 | 0.9712797403335571 | 0.8979793158403641 |
