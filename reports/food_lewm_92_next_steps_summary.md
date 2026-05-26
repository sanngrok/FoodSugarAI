# Food-LeWM 92% Next Steps Summary

## Current Status

- Best single model: `B0 supervised-only ft10 hflip` top1=`0.879757`, macro_f1=`0.879561`
- Best ensemble model: `B0 baseline + Food-LeWM B0 + B0 supervised-only` hflip top1=`0.899232`, macro_f1=`0.899126`
- 92% gap from best ensemble: `2.08%p`

## Performance Table

| Experiment | Model | Pretrain | Data | TTA | Ensemble | Top1 | Top3 | Macro-F1 |
|---|---|---|---|---|---|---:|---:|---:|
| B0 baseline on 1000val | efficientnet_b0 | none | old train / 1000 val | hflip | no | 0.873504 | 0.964713 | 0.873296 |
| B0 supervised-only | B0 Food-LeWM arch | ImageNet | korean_food_1000 | hflip | no | 0.879757 | 0.962212 | 0.879561 |
| B0-LeWM 3ep ft10 | B0 Food-LeWM | LeWM 3ep | korean_food_1000 | hflip | no | 0.869484 | 0.961408 | 0.869524 |
| B2 clean | efficientnet_b2 | none | korean_food_1000 | hflip | no | TBD | TBD | TBD |
| B2-LeWM | B2 Food-LeWM | 3ep | korean_food_1000 | hflip | no | TBD | TBD | TBD |
| Best ensemble | B0/B0-LeWM/Supervised | mixed | korean_food_1000 | hflip | yes | 0.899232 | 0.976059 | 0.899126 |

## Key Findings

1. Same-validation B0 baseline is top1 `0.873504`, so the old 0.8275 score should not be used as the direct comparison baseline for `korean_food_1000/val`.
2. Food-LeWM B0 3ep ft10 is top1 `0.869484`, which is `-0.004020` vs same-validation B0 hflip.
3. Supervised-only is top1 `0.879757`, which is `+0.010273` over Food-LeWM B0. Current 3ep LeWM pretraining did not help relative to ImageNet supervised-only fine-tuning.
4. Ensemble top1 `0.899232` improves over best single by `+0.019475`.

## Error Analysis

- Error analysis output: `reports/error_analysis/final_candidate`
- High-confidence review candidates: `300` images
- Current low-F1 classes are mostly soup/stew/tang, grilled/meat, and visually similar noodle/pancake classes.

Top low-F1 classes from final ensemble:

| class_name | f1 | precision | recall | support |
| --- | --- | --- | --- | --- |
| 동태찌개 | 0.798165 | 0.737288 | 0.870000 | 200 |
| 갈비찜 | 0.816626 | 0.799043 | 0.835000 | 200 |
| 김치찌개 | 0.817955 | 0.815920 | 0.820000 | 200 |
| 갈비구이 | 0.824691 | 0.814634 | 0.835000 | 200 |
| 삼겹살 | 0.827586 | 0.876404 | 0.783920 | 199 |
| 라면 | 0.834646 | 0.873626 | 0.798995 | 199 |
| 닭볶음탕 | 0.835897 | 0.857895 | 0.815000 | 200 |
| 곰탕_설렁탕 | 0.839895 | 0.883978 | 0.800000 | 200 |
| 닭갈비 | 0.842365 | 0.830097 | 0.855000 | 200 |
| 불고기 | 0.843434 | 0.852041 | 0.835000 | 200 |
| 칼국수 | 0.846348 | 0.852792 | 0.840000 | 200 |
| 김치찜 | 0.851385 | 0.857868 | 0.845000 | 200 |
| 수제비 | 0.860825 | 0.883598 | 0.839196 | 199 |
| 닭계장 | 0.861538 | 0.884211 | 0.840000 | 200 |
| 감자탕 | 0.865672 | 0.861386 | 0.870000 | 200 |

## Next Actions

1. Do not promote operational files yet without explicit user approval.
2. Treat B0 supervised-only as the best single candidate for now.
3. Use the 3-model ensemble as the current best evaluation candidate.
4. Review `reports/error_analysis/final_candidate/high_confidence_errors_top300.csv` for label/data issues.
5. Continue with B2 clean and B2-LeWM only after deciding whether the added training time is worthwhile.

## One-Line Conclusion

Current best is the 3-model hflip ensemble with top1=0.899232, macro_f1=0.899126. Same-validation B0 hflip is 0.873504, so the ensemble improves by 2.57%p. The remaining gap to 92% is 2.08%p, and the next bottleneck appears to be data/label/class-confusion cleanup plus model diversity rather than the current B0 LeWM pretraining recipe.
