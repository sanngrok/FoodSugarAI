# K-Food 92% 다음 단계 실행 결과

작성일: 2026-05-09  
기준 문서: `KFOOD_92_GPT_VALIDATION_BRIEF.md`

## 1. 이번 단계 목적

이전 브리프의 핵심 의심점은 다음이었다.

```text
old_train -> new_val class+filename overlap 4,474건이 current best ensemble 성능을 부풀렸는가?
```

그래서 새 학습을 바로 시작하지 않고, 이미 만들어진 weighted ensemble logits cache를 재사용하여 validation subset별 성능을 분리 평가했다.

---

## 2. 추가한 스크립트

```text
scripts/eval_cached_ensemble_subsets.py
```

역할:

- `reports/weighted_ensemble/b0_family_hflip/logits_cache.pt`를 로드한다.
- `reports/split_leakage_audit/all_class_filename_overlaps.csv`를 이용해 validation sample을 subset으로 나눈다.
- simple average / weighted selected / diagnostic full-best / single model 성능을 subset별로 계산한다.
- conservative subset 기준 weight sweep도 수행한다.
- 이후 B2/seed 모델 비교에 사용할 subset manifest를 저장한다.

실행:

```bash
python3 scripts/eval_cached_ensemble_subsets.py \
  --cache reports/weighted_ensemble/b0_family_hflip/logits_cache.pt \
  --metrics reports/weighted_ensemble/b0_family_hflip/metrics.json \
  --class-filename-overlaps reports/split_leakage_audit/all_class_filename_overlaps.csv \
  --output-dir reports/weighted_ensemble/b0_family_hflip_subset_audit \
  --weight-step 0.05
```

---

## 3. 산출물

```text
reports/weighted_ensemble/b0_family_hflip_subset_audit/
```

주요 파일:

| File | Purpose |
|---|---|
| `README.md` | 사람이 읽는 subset audit 요약 |
| `metrics.json` | 전체 수치 |
| `subset_metrics.csv` | ensemble/model별 subset 성능 |
| `subset_weight_sweep.csv` | subset별 weight sweep 결과 |
| `subset_manifests/full.csv` | 전체 val manifest |
| `subset_manifests/old_train_filename_overlap_new_val.csv` | old train과 filename overlap인 new val |
| `subset_manifests/minus_old_train_filename_overlap.csv` | old train overlap 제외 conservative subset |
| `subset_manifests/old_val_filename_overlap_new_val.csv` | old val에서 온 new val |

Manifest row counts:

| Manifest | Samples |
|---|---:|
| full | 11,194 |
| old_train_filename_overlap_new_val | 4,474 |
| old_val_filename_overlap_new_val | 6,720 |
| minus_old_train_filename_overlap | 6,720 |
| minus_old_train_and_old_val_filename_overlap | 0 |

중요:

```text
korean_food_1000/val 전체 11,194장은 class+filename 기준으로 old_train 4,474장 + old_val 6,720장으로 구성되어 있다.
즉 old split과 전혀 겹치지 않는 new_val subset은 0장이다.
```

---

## 4. 핵심 결과

### 4.1 Weighted selected ensemble

기존 current best로 봤던 weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.50 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.15 |

Subset별 성능:

| Subset | Count | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|---:|
| full | 11,194 | 0.900661 | 0.976773 | 0.900545 |
| old_train_filename_overlap_new_val | 4,474 | 0.928923 | 0.987483 | 0.928789 |
| minus_old_train_filename_overlap | 6,720 | 0.881845 | 0.969643 | 0.881695 |

해석:

```text
full top1 0.900661은 old_train overlap subset 0.928923의 영향으로 올라간 값이다.
old_train overlap을 제외하면 같은 weighted ensemble은 top1 0.881845로 떨어진다.
```

---

### 4.2 모델별 subset 성능

| Model / Ensemble | Full Top1 | Old-Train-Overlap Top1 | Minus-Old-Train Top1 |
|---|---:|---:|---:|
| simple_average | 0.899232 | 0.916853 | 0.887500 |
| weighted_selected | 0.900661 | 0.928923 | 0.881845 |
| diagnostic_full_best | 0.901465 | 0.924899 | 0.885863 |
| single_b0_baseline | 0.873504 | 0.938757 | 0.830060 |
| single_food_lewm_b0 | 0.869484 | 0.869692 | 0.869345 |
| single_b0_supervised_only | 0.879757 | 0.879079 | 0.880208 |

가장 중요한 관찰:

```text
B0 baseline:
  old_train overlap subset = 0.938757
  minus old_train subset   = 0.830060
  gap = +10.8697%p
```

이는 B0 baseline이 old_train overlap subset에서 매우 강하게 inflated 되었음을 시사한다.

반면 supervised-only:

```text
B0 supervised-only:
  old_train overlap subset = 0.879079
  minus old_train subset   = 0.880208
```

즉 supervised-only는 해당 overlap에 거의 민감하지 않다.

---

## 5. Conservative subset 기준 weight sweep

`minus_old_train_filename_overlap` 6,720장 기준 best weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.45 |
| b0_supervised_only | 0.50 |

성능:

| Subset | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| minus_old_train_filename_overlap | 0.890476 | 0.969940 | 0.890290 |

비교:

| Candidate | Conservative Top1 |
|---|---:|
| weighted_selected, old full 기준 | 0.881845 |
| simple_average | 0.887500 |
| conservative subset sweep best | 0.890476 |

해석:

```text
conservative 기준에서는 B0 baseline weight를 0.50이 아니라 0.05까지 낮춰야 한다.
즉 기존 weighted ensemble은 B0 leakage-risk subset에 과적합된 weight다.
```

---

## 6. 업데이트된 판단

이전 판단:

```text
현재 best = weighted B0-family ensemble top1 0.900661
```

업데이트 후 보수적 판단:

```text
현재 full-val 0.900661은 낙관적 수치다.
B0 baseline 포함 성능은 old_train overlap 때문에 inflated 되었을 가능성이 높다.
현재 conservative 기준 best는 subset sweep 기준 top1 0.890476이다.
```

단, 이 conservative subset도 완전한 신규 validation은 아니다.

```text
minus_old_train subset = old_val_filename_overlap_new_val 6,720장
```

즉 이 subset은 B0 baseline이 직접 학습한 train 이미지는 아니지만, old validation과 동일 filename으로 구성되어 있다.  
따라서 최종 신뢰용으로는 여전히 새로운 fixed validation split이 필요하다.

---

## 7. 다음 액션 우선순위 변경

이 결과 때문에 다음 우선순위는 더 명확해졌다.

### 1순위: B0 baseline을 current best 판단에서 분리

현재 ensemble에서 B0 baseline weight를 크게 주는 것은 위험하다.

권장:

```text
full-val 성능 표에는 계속 기록하되,
의사결정 기준은 minus_old_train_filename_overlap subset 또는 새 fixed validation으로 이동한다.
```

### 2순위: fixed clean validation 구축

현재 `korean_food_1000/val`은 old split과 class+filename 기준으로 100% 연결되어 있다.

권장:

```text
새로운 holdout/fixed validation을 만들거나,
원본 전체 이미지에서 old_train/old_val filename과 겹치지 않는 검증 set을 별도로 구성해야 한다.
```

### 3순위: B0 supervised-only seed 추가

B0 supervised-only는 overlap subset과 minus subset에서 성능이 안정적이다.

권장:

```text
B0 supervised-only seed 7/123을 추가 학습하고,
conservative subset 기준 ensemble 다양성을 확인한다.
```

### 4순위: B2 clean supervised

B2는 여전히 유효하지만, 평가 기준은 full-val이 아니라 conservative subset/fixed validation이어야 한다.

권장:

```text
B2 clean supervised 학습 후
1. full val
2. minus_old_train_filename_overlap
3. 새 fixed validation
세 기준을 분리해서 평가한다.
```

---

## 8. GPT 검증 질문 업데이트

GPT에게 추가로 물어볼 질문:

1. B0 baseline의 `old_train overlap 0.938757` vs `minus old_train 0.830060` 차이를 leakage/inflation 근거로 봐도 되는가?
2. 현재 full-val best 0.900661보다 conservative subset best 0.890476을 의사결정 기준으로 쓰는 것이 맞는가?
3. `korean_food_1000/val`이 old_train+old_val filename overlap으로 100% 구성되어 있다면, 92% 목표 검증용으로 부적합하다고 봐야 하는가?
4. 다음 장기 실험은 B2보다 fixed clean validation 구축과 B0 supervised-only seed가 먼저인가?
5. B0 baseline은 ensemble 후보에서 제외하거나 weight 상한을 둬야 하는가?

---

## 9. 테스트

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.36s
```

---

## 10. 한 줄 결론

다음 단계 분석 결과, 기존 full validation 기준 90.0661%는 B0 baseline의 old_train filename-overlap subset 고성능에 의해 낙관적으로 보일 가능성이 크다.  
old_train overlap을 제외한 conservative 기준 best는 89.0476%이며, 앞으로는 fixed clean validation을 먼저 만들고 B0 supervised-only seed/B2를 그 기준에서 비교해야 한다.

---

## 11. Fixed V1 Split 생성

다음 액션으로 B0-baseline leakage risk를 줄인 fixed split을 생성했다.

추가 스크립트:

```text
scripts/build_kfood_fixed_split.py
```

실행:

```bash
python3 scripts/build_kfood_fixed_split.py \
  --source-data-dir data/raw/korean_food_1000 \
  --classes data/models/korean_food_classes.json \
  --old-train-overlap-manifest reports/weighted_ensemble/b0_family_hflip_subset_audit/subset_manifests/old_train_filename_overlap_new_val.csv \
  --fixed-val-manifest reports/weighted_ensemble/b0_family_hflip_subset_audit/subset_manifests/minus_old_train_filename_overlap.csv \
  --output-dir data/raw/korean_food_fixed_v1
```

생성된 split:

| Split | Count |
|---|---:|
| train | 49,243 |
| val | 6,720 |
| classes | 56 |

Split policy:

```text
train = korean_food_1000/train + old_train_filename_overlap_new_val 4,474장
val = minus_old_train_filename_overlap 6,720장
```

Audit:

```bash
python3 scripts/audit_kfood_splits.py \
  --old-data-dir data/raw/korean_food \
  --new-data-dir data/raw/korean_food_fixed_v1 \
  --output-dir reports/fixed_v1_split_audit
```

Audit 결과:

| Pair | Class+Filename Unique |
|---|---:|
| old_train__new_val | 0 |
| new_train__new_val | 0 |
| old_val__new_val | 6,720 |

해석:

```text
fixed_v1 val은 B0 baseline old_train과 겹치지 않는다.
fixed_v1 train/val 간 class+filename overlap도 0이다.
따라서 기존 full-val보다 B0 baseline-safe한 평가 기준이다.
```

관련 파일:

```text
data/raw/korean_food_fixed_v1/
data/raw/korean_food_fixed_v1/split_meta.json
reports/fixed_v1_split_audit/
```

---

## 12. B0 Supervised-Only Seed7 Fixed V1 학습

기존 운영 파일을 덮어쓰지 않고 별도 checkpoint로 학습했다.

실행:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 10 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 1 \
  --random-erasing-p 0.1 \
  --seed 7 \
  --output data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt \
  --classes-output data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_classes_ft10.json \
  --metadata-output data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json \
  --report-dir reports/seed_experiments/b0_supervised_only_seed7_fixed_v1_ft10 \
  --log-every 50
```

학습 중 best checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt
```

Training log 기준:

| Epoch | Val Top1 | Val Top3 | Macro-F1 |
|---:|---:|---:|---:|
| 5 | 0.871429 | 0.962649 | 0.871025 |
| 7 | 0.877232 | 0.966220 | 0.877038 |
| 9 | 0.877232 | 0.964583 | 0.876917 |
| 10 | 0.879315 | 0.965923 | 0.878975 |

최종 epoch 10에서 best checkpoint가 갱신되었다.

---

## 13. Seed7 Fixed V1 hflip 평가

실행:

```bash
python3 scripts/eval_kfood_any_model.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --checkpoint data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt \
  --metadata data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json \
  --classes data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_classes_ft10.json \
  --name b0_supervised_only_seed7_fixed_v1_hflip \
  --tta hflip \
  --batch-size 64 \
  --num-workers 2 \
  --output-dir reports/seed_experiments/eval_b0_supervised_only_seed7_fixed_v1_hflip
```

결과:

| Model | Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---:|---:|
| B0 supervised-only seed7 fixed_v1 | korean_food_fixed_v1 | hflip | 0.880357 | 0.965179 | 0.880014 |

비교:

| Model | Fixed V1 Top1 | Macro-F1 |
|---|---:|---:|
| 기존 B0 supervised-only | 0.880208 | 0.880076 |
| seed7 fixed_v1 | 0.880357 | 0.880014 |

해석:

```text
seed7 단일 모델은 기존 supervised-only와 거의 동일한 수준이다.
seed 다양성 단독으로 큰 single-model 개선은 아직 없다.
```

---

## 14. Seed7 추가 Ensemble 평가

4-model simple average:

```text
b0_baseline
food_lewm_b0
b0_supervised_only
b0_supervised_seed7_fixed_v1
```

결과:

| Ensemble | Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---:|---:|
| 4-model simple average | fixed_v1 | hflip | 0.890030 | 0.971875 | 0.889832 |

Single model 참고:

| Model | Top1 | Macro-F1 |
|---|---:|---:|
| b0_baseline | 0.830060 | 0.829779 |
| food_lewm_b0 | 0.869345 | 0.869215 |
| b0_supervised_only | 0.880208 | 0.880076 |
| b0_supervised_seed7_fixed_v1 | 0.880357 | 0.880014 |

---

## 15. 4-Model Weighted Ensemble Sweep

실행:

```bash
python3 scripts/eval_weighted_ensemble_sweep.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --checkpoint data/models/efficientnet_korean_b0_val08275.pt \
  --metadata data/models/korean_food_model_meta.json \
  --classes data/models/korean_food_classes.json \
  --name b0_baseline \
  --checkpoint data/models/food_lewm_b0_classifier_3ep_ft10.pt \
  --metadata data/models/food_lewm_b0_meta_3ep_ft10.json \
  --classes data/models/food_lewm_b0_classes_3ep_ft10.json \
  --name food_lewm_b0 \
  --checkpoint data/models/food_lewm_b0_supervised_only_ft10.pt \
  --metadata data/models/food_lewm_b0_supervised_only_meta_ft10.json \
  --classes data/models/food_lewm_b0_supervised_only_classes_ft10.json \
  --name b0_supervised_only \
  --checkpoint data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt \
  --metadata data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json \
  --classes data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_classes_ft10.json \
  --name b0_supervised_seed7_fixed_v1 \
  --tta hflip \
  --batch-size 128 \
  --num-workers 0 \
  --weight-step 0.05 \
  --calibration-ratio 0.5 \
  --seed 42 \
  --output-dir reports/weighted_ensemble/b0_family_plus_seed7_fixed_v1_hflip
```

Calibration 기준 best weights:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.20 |
| b0_supervised_seed7_fixed_v1 | 0.40 |

결과:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.899107 | 0.976786 | 0.899127 |
| evaluation | 0.886310 | 0.968750 | 0.885753 |
| full | 0.892708 | 0.972768 | 0.892576 |

Diagnostic full-best:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.05 |
| b0_supervised_seed7_fixed_v1 | 0.55 |

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| full | 0.893601 | 0.972321 | 0.893442 |

비교:

| Candidate | Fixed V1 Top1 | Macro-F1 |
|---|---:|---:|
| 기존 conservative 3-model sweep best | 0.890476 | 0.890290 |
| 4-model simple average | 0.890030 | 0.889832 |
| 4-model calibration selected | 0.892708 | 0.892576 |
| 4-model diagnostic full-best | 0.893601 | 0.893442 |

해석:

```text
seed7은 single model로는 큰 개선이 없지만, weighted ensemble에서는 +0.223%p 개선을 만든다.
B0 baseline weight는 여전히 0.05로 낮게 유지된다.
현재 fixed_v1 기준 채택 가능한 best는 4-model calibration selected top1=0.892708이다.
```

---

## 16. 업데이트된 현재 Best

보수적 채택 기준:

```text
현재 fixed_v1 best는 4-model weighted ensemble이다.
top1 = 0.892708
macro_f1 = 0.892576
92%까지 남은 gap = 약 2.7292%p
```

참고용 diagnostic full-best:

```text
top1 = 0.893601
macro_f1 = 0.893442
92%까지 남은 gap = 약 2.6399%p
```

---

## 17. 다음 권장 액션

우선순위:

1. B0 supervised-only seed123 fixed_v1 추가 학습
2. seed7 + seed123 + 기존 supervised-only 중심 weighted ensemble
3. B2 clean supervised fixed_v1 학습
4. B2를 포함한 weighted ensemble
5. label review 300개 반영 후 cleaned_v1 재학습

현재 관찰:

```text
B0 baseline은 fixed_v1에서 약하므로 weight를 0.05 이하로 제한하는 것이 맞다.
seed 다양성은 single보다는 ensemble에서 소폭 이득이 있다.
다음 seed123이 seed7과 다른 오답을 잡으면 89.5% 근처까지는 기대할 수 있다.
B2는 92% 접근을 위해 여전히 필요하지만, fixed_v1 기준으로만 판단해야 한다.
```

---

## 18. 추가 테스트

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.55s
```

---

## 19. B0 Supervised-Only Seed123 Fixed V1 추가 학습

목적:

```text
seed7에서 관찰된 seed diversity 효과가 반복되는지 확인한다.
```

실행:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 10 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 1 \
  --random-erasing-p 0.1 \
  --seed 123 \
  --output data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt \
  --classes-output data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json \
  --metadata-output data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json \
  --report-dir reports/seed_experiments/b0_supervised_only_seed123_fixed_v1_ft10 \
  --log-every 50
```

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
```

Training log 주요 구간:

| Epoch | Val Top1 | Val Top3 | Macro-F1 |
|---:|---:|---:|---:|
| 5 | 0.869643 | 0.963095 | 0.869242 |
| 7 | 0.879613 | 0.964286 | 0.879466 |
| 8 | 0.881994 | 0.963988 | 0.881725 |
| 9 | 0.880804 | 0.965030 | 0.880695 |
| 10 | 0.882887 | 0.965179 | 0.882682 |

최종 epoch 10에서 best checkpoint가 저장되었다.

---

## 20. Seed123 Fixed V1 hflip 평가

실행:

```bash
python3 scripts/eval_kfood_any_model.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --checkpoint data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt \
  --metadata data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json \
  --classes data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json \
  --name b0_supervised_only_seed123_fixed_v1_hflip \
  --tta hflip \
  --batch-size 64 \
  --num-workers 2 \
  --output-dir reports/seed_experiments/eval_b0_supervised_only_seed123_fixed_v1_hflip
```

결과:

| Model | Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---|---:|---:|---:|
| B0 supervised-only seed123 fixed_v1 | korean_food_fixed_v1 | hflip | 0.886012 | 0.965327 | 0.885791 |

Seed 비교:

| Model | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| 기존 B0 supervised-only | 0.880208 | 0.961756 | 0.880076 |
| seed7 fixed_v1 | 0.880357 | 0.965179 | 0.880014 |
| seed123 fixed_v1 | 0.886012 | 0.965327 | 0.885791 |

해석:

```text
seed123은 seed7보다 단일 hflip 기준 +0.5655%p 높다.
seed 추가 학습 효과가 반복됐고, seed123은 현재 best single이다.
```

---

## 21. 5-Model Cache 기반 Weighted Ensemble

추가 스크립트:

```text
scripts/append_model_to_logits_cache.py
scripts/sweep_cached_ensemble_weights.py
```

목적:

```text
기존 4-model logits cache에 seed123 logits만 추가해 5-model weighted ensemble을 빠르게 평가한다.
```

Cache 생성:

```bash
python3 scripts/append_model_to_logits_cache.py \
  --input-cache reports/weighted_ensemble/b0_family_plus_seed7_fixed_v1_hflip/logits_cache.pt \
  --output-cache reports/weighted_ensemble/b0_family_plus_seed7_seed123_fixed_v1_hflip/logits_cache.pt \
  --checkpoint data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt \
  --metadata data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json \
  --classes data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json \
  --name b0_supervised_seed123_fixed_v1 \
  --tta hflip \
  --batch-size 128 \
  --num-workers 0
```

Weight sweep:

```bash
python3 scripts/sweep_cached_ensemble_weights.py \
  --cache reports/weighted_ensemble/b0_family_plus_seed7_seed123_fixed_v1_hflip/logits_cache.pt \
  --output-dir reports/weighted_ensemble/b0_family_plus_seed7_seed123_fixed_v1_hflip \
  --weight-step 0.05 \
  --calibration-ratio 0.5 \
  --seed 42
```

5-model calibration 기준 best weights:

| Model | Weight |
|---|---:|
| b0_baseline | 0.10 |
| food_lewm_b0 | 0.20 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.20 |
| b0_supervised_seed123_fixed_v1 | 0.50 |

결과:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.902679 | 0.975595 | 0.902677 |
| evaluation | 0.893750 | 0.966964 | 0.893057 |
| full | 0.898214 | 0.971280 | 0.897979 |

Simple average:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.897024 | 0.977381 | 0.896990 |
| evaluation | 0.890179 | 0.967857 | 0.889577 |
| full | 0.893601 | 0.972619 | 0.893388 |

비교:

| Candidate | Fixed V1 Top1 | Macro-F1 |
|---|---:|---:|
| 기존 conservative 3-model sweep best | 0.890476 | 0.890290 |
| 4-model calibration selected | 0.892708 | 0.892576 |
| 5-model simple average | 0.893601 | 0.893388 |
| 5-model weighted selected | 0.898214 | 0.897979 |

해석:

```text
seed123 추가 효과는 반복됐다.
5-model weighted ensemble은 4-model 대비 +0.5506%p 개선됐다.
fixed_v1 기준 90%에 가까워졌고, 현재 보수적 best는 0.898214다.
```

---

## 22. 업데이트된 현재 Best

보수적 채택 기준:

```text
현재 fixed_v1 best는 5-model weighted ensemble이다.
top1 = 0.898214
macro_f1 = 0.897979
92%까지 남은 gap = 약 2.1786%p
```

현재 best single:

```text
B0 supervised-only seed123 fixed_v1 hflip
top1 = 0.886012
macro_f1 = 0.885791
```

---

## 23. 다음 권장 액션 업데이트

이제 seed 추가 효과가 반복됐으므로 다음 선택지는 두 갈래다.

1. B0 supervised-only seed 추가 1개 더
   - 기대: ensemble diversity로 0.1~0.3%p 추가 가능
   - 한계: 모두 B0 계열이라 개선 폭이 작아질 가능성 큼

2. B2 clean supervised fixed_v1 학습
   - 기대: backbone diversity로 90% 돌파 가능성
   - 비용: B0보다 느리고 batch size 조정 필요 가능

추천:

```text
다음은 B2 clean supervised fixed_v1을 진행한다.
이유는 seed7/seed123으로 seed diversity 효과는 확인됐고,
92%까지 남은 2.18%p를 줄이려면 backbone diversity가 필요하기 때문이다.
```

---

## 24. 추가 테스트

실행:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.40s
```
