# B3 Timeboxed Fixed_v1 Result

- 작성일: 2026-05-11
- 작업 경로: `/Users/sangrok/foodsugar-ai`
- 계획 파일: `/Users/sangrok/Downloads/CODEX_TIMEBOXED_B3_FIXED_V1_PLAN.md`
- 목적: cleaned train을 기다리지 않고 `fixed_v1` 그대로 EfficientNet-B3 probe를 학습해, B3가 current best ensemble에 diversity member로 기여하는지 확인한다.

## 1. 선택 이유

기존 cleaned 방향은 train label review가 충분히 확정되지 않아 보류 중이다.

- AI draft patch는 train보다 val에 더 많이 걸렸다.
- train affected는 49장 수준으로 작았다.
- 따라서 cleaned split을 만들면 재학습 개선 실험보다 validation correction 실험이 될 위험이 컸다.

이번 실험은 label-cleaning 실험이 아니다. `fixed_v1` 그대로 B3 backbone diversity를 확인하는 timeboxed probe다.

## 2. 안전 규칙

아래 운영/기준 파일은 덮어쓰지 않았다.

- `data/models/efficientnet_korean.pt`
- `data/models/korean_food_classes.json`
- `data/models/korean_food_model_meta.json`
- `data/models/efficientnet_korean_b0_val08275.pt`
- 기존 B0/B2 후보 checkpoint들
- `data/raw/korean_food_fixed_v1`

B3 probe는 별도 파일로 저장했다.

- checkpoint: `data/models/efficientnet_korean_b3_probe_fixed_v1.pt`
- classes: `data/models/korean_food_classes_b3_probe_fixed_v1.json`
- metadata: `data/models/korean_food_model_meta_b3_probe_fixed_v1.json`
- train report: `reports/b3/b3_probe_fixed_v1`

## 3. Preflight

확인 결과:

- MPS built: `True`
- MPS available: `True`
- fixed_v1 train: `49,243`
- fixed_v1 val: `6,720`
- classes: `56`
- train/val class order match: `True`
- required B0/B2 models: all present
- B3 target output files: not present before training

## 4. B3 Probe 학습 설정

학습 명령은 계획서의 B3 probe 설정을 따랐다.

| Item | Value |
|---|---:|
| data | `data/raw/korean_food_fixed_v1` |
| model | `efficientnet_b3` |
| image_size | `300` |
| epochs | `10` |
| batch_size | `8` |
| grad_accum_steps | `4` |
| effective batch | `32` |
| warmup_epochs | `2` |
| lr | `5e-5` |
| head_lr | `3e-4` |
| weight_decay | `1e-4` |
| label_smoothing | `0.05` |
| randaugment | `N=2, M=7` |
| random_erasing_p | `0.1` |
| drop_rate | `0.1` |
| drop_path_rate | `0.1` |
| CutMix | OFF |

## 5. 학습 로그 요약

best checkpoint는 epoch 9에서 저장됐다.

| Epoch | Train Acc | Val Top1 | Val Top3 | Macro-F1 |
|---:|---:|---:|---:|---:|
| 1 | 0.280690 | 0.516518 | 0.738095 | 0.508093 |
| 2 | 0.474220 | 0.594643 | 0.806250 | 0.587728 |
| 3 | 0.674878 | 0.818452 | 0.940625 | 0.818132 |
| 4 | 0.771338 | 0.850000 | 0.955655 | 0.849803 |
| 5 | 0.816888 | 0.865923 | 0.963839 | 0.865243 |
| 6 | 0.846313 | 0.873661 | 0.966369 | 0.873385 |
| 7 | 0.864793 | 0.881845 | 0.966667 | 0.881498 |
| 8 | 0.876490 | 0.882887 | 0.970089 | 0.882512 |
| 9 | 0.883232 | 0.886012 | 0.971429 | 0.885830 |
| 10 | 0.889406 | 0.885417 | 0.971726 | 0.885336 |

학습 중 MPS OOM은 발생하지 않았다. 다만 후반부에 macOS/MPS 스케줄링 지연이 길게 발생해 wall time이 크게 늘었다.

## 6. B3 Probe 단일 평가

평가 파일:

- none: `reports/b3/eval_b3_probe_fixed_v1_none`
- hflip: `reports/b3/eval_b3_probe_fixed_v1_hflip`

| Experiment | Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---:|---:|
| B3 probe single | fixed_v1 | none | 0.886012 | 0.971429 | 0.885830 |
| B3 probe single | fixed_v1 | hflip | 0.888839 | 0.972321 | 0.888701 |

판단:

- B3 hflip `0.888839`로 B3 probe 기준 `>= 0.87` 조건을 충족했다.
- 기존 best single B0 seed123 hflip `0.886012`보다 약간 높다.
- B3는 단일 모델로도 충분히 유효한 후보가 됐다.

## 7. B3 vs Current Ensemble Disagreement

비교 기준:

- target: B3 probe hflip
- current weighted ensemble: 기존 current best의 nonzero weights
  - `food_lewm_b0`: 0.15
  - `b0_seed7_fixed_v1`: 0.25
  - `b0_seed123_fixed_v1`: 0.25
  - `b2_clean_fixed_v1`: 0.35

출력:

- `reports/b3/compare_b3_vs_current/b3_correct_current_wrong.csv`
- `reports/b3/compare_b3_vs_current/current_correct_b3_wrong.csv`
- `reports/b3/compare_b3_vs_current/both_wrong.csv`
- `reports/b3/compare_b3_vs_current/per_class_delta.csv`
- `reports/b3/compare_b3_vs_current/README.md`

요약:

| Metric | Count |
|---|---:|
| B3 correct / current wrong | 201 |
| current correct / B3 wrong | 277 |
| both wrong | 470 |

해석:

- B3 단일은 current ensemble보다 낮지만, current가 틀린 샘플 201개를 맞춘다.
- 이 보완 샘플이 ensemble 성능 개선으로 이어졌다.

class-level로 B3가 current보다 좋은 쪽:

| Class | B3 Acc | Current Acc | Delta |
|---|---:|---:|---:|
| 라면 | 0.850000 | 0.775000 | +0.075000 |
| 곰탕_설렁탕 | 0.800000 | 0.758333 | +0.041667 |
| 약과 | 0.950000 | 0.908333 | +0.041667 |
| 감자전 | 0.900000 | 0.875000 | +0.025000 |
| 불고기 | 0.883333 | 0.858333 | +0.025000 |
| 수제비 | 0.841667 | 0.816667 | +0.025000 |
| 식혜 | 0.975000 | 0.950000 | +0.025000 |
| 한과 | 1.000000 | 0.975000 | +0.025000 |
| 동태찌개 | 0.858333 | 0.833333 | +0.025000 |

class-level로 B3가 current보다 약한 쪽:

| Class | B3 Acc | Current Acc | Delta |
|---|---:|---:|---:|
| 갈비구이 | 0.733333 | 0.841667 | -0.108333 |
| 된장찌개 | 0.841667 | 0.908333 | -0.066667 |
| 김치찌개 | 0.800000 | 0.850000 | -0.050000 |
| 떡볶이 | 0.850000 | 0.900000 | -0.050000 |
| 비빔냉면 | 0.916667 | 0.966667 | -0.050000 |
| 비빔밥 | 0.858333 | 0.908333 | -0.050000 |
| 순두부찌개 | 0.825000 | 0.875000 | -0.050000 |
| 쫄면 | 0.916667 | 0.966667 | -0.050000 |

## 8. B3 포함 Simple Ensemble

구성:

- `food_lewm_b0`
- `b0_seed7_fixed_v1`
- `b0_seed123_fixed_v1` - `b2_clean_fixed_v1`
- `b3_probe_fixed_v1`

출력:

- `reports/b3/ensemble_simple_with_b3_probe_fixed_v1_hflip`

결과:

| Experiment | Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---:|---:|
| current fixed_v1 best | fixed_v1 | hflip | 0.900149 | 0.974405 | 0.899900 |
| B3 probe simple ensemble | fixed_v1 | hflip | 0.904167 | 0.977976 | 0.903983 |

판단:

- 단순 평균만으로 current best 대비 `+0.004018` top1 개선.
- B3는 weighted sweep 없이도 ensemble에 도움을 준다.

## 9. B3 포함 Weighted Ensemble Sweep

출력:

- `reports/b3/weighted_ensemble_with_b3_probe_fixed_v1_hflip`

설정:

- TTA: `hflip`
- calibration_ratio: `0.5`
- weight_step: `0.05`
- seed: `42`

best weights:

| Model | Weight |
|---|---:|
| food_lewm_b0 | 0.10 |
| b0_seed7_fixed_v1 | 0.00 |
| b0_seed123_fixed_v1 | 0.40 |
| b2_clean_fixed_v1 | 0.00 |
| b3_probe_fixed_v1 | 0.50 |

결과:

| Experiment | Split | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| B3 weighted ensemble | calibration | 0.917262 | 0.981250 | 0.917203 |
| B3 weighted ensemble | evaluation | 0.905357 | 0.971726 | 0.904696 |
| B3 weighted ensemble | full | 0.911310 | 0.976488 | 0.911089 |

current best 대비:

- current best top1: `0.900149`
- B3 weighted full top1: `0.911310`
- top1 delta: `+0.011161`

판단:

- B3 weight가 `0.50`으로 매우 높다.
- B3 diversity가 명확하다.
- evaluation split도 `0.905357`로 current best full `0.900149`보다 높다.
- calibration-only overfit으로 보기 어렵다.

## 10. B3 Full Run 여부

B3 full run 조건은 충족했다.

충족 조건:

- B3 probe hflip `0.888839` >= `0.87`
- B3 포함 weighted ensemble `0.911310` > current best `0.900149`
- B3 weight `0.50` >= `0.10`

하지만 이번 실행에서는 B3 full 25epoch는 시작하지 않았다.

이유:

- 10epoch probe만으로도 B3 diversity 가치는 충분히 확인됐다.
- 25epoch full run은 wall time이 매우 길 가능성이 크다.
- 현재 최적 ensemble은 이미 91.13%로 크게 개선됐다.
- 다음 full run은 별도 장시간 실험으로 분리하는 것이 안전하다.

권장:

- 다음 단계에서 `efficientnet_korean_b3_full_fixed_v1.pt`를 별도 경로로 25epoch 실행한다.
- 또는 현 B3 probe를 ensemble 후보로 먼저 stability 검증한다.

## 11. 5-Fold TTA 여부

5-fold TTA는 실행하지 않았다.

이유:

- 현재 평가 스크립트의 주요 경로는 `none`/`hflip` 중심이다.
- 5-fold TTA는 운영 후보 확정 후 최고점 탐색용이다.
- hflip만으로 이미 `0.911310`을 달성했다.

## 12. 92% / 94%까지 남은 Gap

기준:

- current best: `0.900149`
- B3 weighted best: `0.911310`

남은 gap:

| Target | Gap |
|---|---:|
| 92% | 0.008690 |
| 94% | 0.028690 |

## 13. 최종 성능표

| Experiment | Data | TTA | Top1 | Top3 | Macro-F1 | Note |
|---|---|---|---:|---:|---:|---|
| current fixed_v1 best | fixed_v1 | hflip | 0.900149 | 0.974405 | 0.899900 | baseline |
| B3 probe single | fixed_v1 | none | 0.886012 | 0.971429 | 0.885830 | epoch 9 best checkpoint |
| B3 probe single | fixed_v1 | hflip | 0.888839 | 0.972321 | 0.888701 | best single-level candidate |
| B3 probe simple ensemble | fixed_v1 | hflip | 0.904167 | 0.977976 | 0.903983 | current best 초과 |
| B3 probe weighted ensemble | fixed_v1 | hflip | 0.911310 | 0.976488 | 0.911089 | current best 대비 +0.011161 |
| B3 full single | fixed_v1 | hflip | TBD | TBD | TBD | 조건 충족, 미실행 |
| B3 full ensemble | fixed_v1 | hflip | TBD | TBD | TBD | 조건부 다음 단계 |
| final fivefold TTA | fixed_v1 | fivefold | TBD | TBD | TBD | 실험용, 미실행 |

## 14. 검증

실행:

```bash
python3 -m py_compile src/classifier/train_classifier_korean.py scripts/eval_kfood_any_model.py scripts/eval_kfood_ensemble.py scripts/eval_weighted_ensemble_sweep.py scripts/score_review_sheet_with_ensemble.py
python3 -m py_compile scripts/compare_kfood_model_vs_weighted_ensemble.py
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

## 15. 결론

B3 fixed_v1 timeboxed probe는 성공이다.

핵심:

- B3 single hflip: `0.888839`
- B3 simple ensemble: `0.904167`
- B3 weighted ensemble: `0.911310`
- B3 best weight: `0.50`
- current best 대비 top1: `+0.011161`

따라서 B3는 단순히 큰 모델이라서가 아니라, 실제로 기존 B0/B2 ensemble과 다른 오류 패턴을 제공하는 diversity member로 가치가 있다.

다음 권장 액션:

1. B3 포함 weighted ensemble stability를 seed/calibration split 변화로 확인한다.
2. B3 full 25epoch를 별도 장시간 실험으로 실행한다.
3. B3 full이 probe보다 개선되면 full checkpoint로 weighted ensemble을 재평가한다.
4. 이후 92% 근처까지 접근하면 5-fold TTA를 실험용으로만 적용한다.
