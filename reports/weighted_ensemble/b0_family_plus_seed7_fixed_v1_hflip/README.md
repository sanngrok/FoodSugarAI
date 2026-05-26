# K-Food Weighted Ensemble Sweep

- data_dir: `data/raw/korean_food_fixed_v1`
- tta: `hflip`
- weight_step: `0.05`
- num_samples: `6720`

## Best Weights

- b0_baseline: `0.05`
- food_lewm_b0: `0.35`
- b0_supervised_only: `0.2`
- b0_supervised_seed7_fixed_v1: `0.4`

## Diagnostic Full-Best Weights

- b0_baseline: `0.05`
- food_lewm_b0: `0.35`
- b0_supervised_only: `0.05`
- b0_supervised_seed7_fixed_v1: `0.55`

## Metrics

| Ensemble | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| best | calibration | 0.8991071581840515 | 0.9767857193946838 | 0.8991265339719509 |
| best | evaluation | 0.8863095045089722 | 0.96875 | 0.8857529236262939 |
| best | full | 0.8927083611488342 | 0.9727678298950195 | 0.8925763253293015 |
| simple_avg | calibration | 0.8928571343421936 | 0.976190447807312 | 0.8928499324169914 |
| simple_avg | evaluation | 0.8872023820877075 | 0.9675595164299011 | 0.8866604217360461 |
| simple_avg | full | 0.890029788017273 | 0.971875011920929 | 0.8898324363599402 |
| diagnostic_full_best | full | 0.8936011791229248 | 0.9723214507102966 | 0.8934422899580639 |
