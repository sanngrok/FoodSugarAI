# Production Validation on korean_food_1000/val

Same-validation comparison between the original B0 baseline and Food-LeWM B0 candidate.

| Model | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| B0 baseline | none | 0.867876 | 0.962301 | 0.867653 |
| B0 baseline | hflip | 0.873504 | 0.964713 | 0.873296 |
| Food-LeWM B0 3ep ft10 | none | 0.867965 | 0.961587 | 0.868040 |
| Food-LeWM B0 3ep ft10 | hflip | 0.869484 | 0.961408 | 0.869524 |

## Deltas

- B0 hflip TTA gain: +0.005628
- Food-LeWM hflip TTA gain: +0.001519
- Food-LeWM vs B0, no TTA: +0.000089
- Food-LeWM vs B0, hflip: -0.004020

## Interpretation

- The old `0.8275` B0 score was measured on `data/raw/korean_food/val`, not `data/raw/korean_food_1000/val`.
- On the same `korean_food_1000/val`, the original B0 baseline is much stronger than the old score suggests.
- Food-LeWM B0 is roughly tied with B0 without TTA, but below B0 hflip in this same-validation comparison.
- Next step: supervised-only ablation to separate data/recipe effects from LeWM pretraining effects.
