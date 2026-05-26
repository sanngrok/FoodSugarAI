# B0 LeWM Ablation Summary

| Experiment | Pretrain | Data | Epochs | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---|---:|---:|---:|
| B0 baseline on 1000val | none | old 600 train / 1000 val | old | hflip | 0.873504 | 0.964713 | 0.873296 |
| B0 supervised-only | ImageNet | korean_food_1000 | 10 | hflip | 0.879757 | 0.962212 | 0.879561 |
| B0-LeWM 3ep ft10 | LeWM 3ep | korean_food_1000 | 10 | hflip | 0.869484 | 0.961408 | 0.869524 |

## Deltas

- LeWM pretraining effect vs supervised-only: -0.010273 top1
- Data/recipe/wrapper effect vs B0 baseline: +0.006253 top1
- Food-LeWM vs B0 baseline: -0.004020 top1
- B0 hflip TTA effect: +0.005628 top1
- Food-LeWM hflip TTA effect: +0.001519 top1

## Interpretation

- On `korean_food_1000/val`, the original B0 baseline is already strong.
- The strongest current single model is B0 supervised-only with the Food-LeWM wrapper/recipe, not the LeWM-pretrained checkpoint.
- In this ablation, the LeWM 3epoch pretraining hurts relative to ImageNet supervised-only fine-tuning by about 1.03%p top1.
- The practical gain appears to come from the 1000/class split, fine-tuning recipe, wrapper head, and TTA rather than the current LeWM pretraining configuration.
