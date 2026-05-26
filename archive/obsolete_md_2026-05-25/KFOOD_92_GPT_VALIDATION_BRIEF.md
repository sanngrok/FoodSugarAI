# K-Food 92% 프로젝트 진행상황 검증용 브리프

작성일: 2026-05-09  
작업 경로: `/Users/sangrok/foodsugar-ai`

이 문서는 현재까지 Codex가 진행한 K-Food 분류 실험/분석 결과를 GPT 또는 다른 검증자에게 넘겨 재검토하기 위한 요약이다.  
핵심 검증 포인트는 `현재 90% 달성 수치가 신뢰 가능한가`, `split leakage 가능성이 있는가`, `다음 액션 우선순위가 맞는가`이다.

---

## 1. 현재 목표

K-Food 56-class 이미지 분류 모델의 validation top1을 92%에 가깝게 끌어올리는 것이 목표다.

현재까지 확인된 best:

| 기준 | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| Best single model | 0.879757 | 0.962212 | 0.879561 |
| Simple ensemble | 0.899232 | 0.976059 | 0.899126 |
| Weighted ensemble, calibration 기준 | 0.900661 | 0.976773 | 0.900545 |
| Weighted ensemble, diagnostic full-best | 0.901465 | 0.976059 | 0.901325 |

보수적으로 채택 가능한 현재 best는 calibration 기준 weighted ensemble:

```text
top1 = 0.900661
macro_f1 = 0.900545
92%까지 남은 gap = 약 1.9339%p
```

주의:

```text
diagnostic full-best는 full validation을 보고 weight를 고른 값이라 validation peeking 위험이 있다.
따라서 최종 채택 기준으로 쓰면 안 되고, 개선 가능성 참고용으로만 봐야 한다.
```

---

## 2. 데이터셋 현황

현재 주로 사용하는 데이터:

| Dataset | Train | Val | Classes |
|---|---:|---:|---:|
| `data/raw/korean_food` | 26,880 | 6,720 | 56 |
| `data/raw/korean_food_1000` | 44,769 | 11,194 | 56 |
| `data/raw/korean_food_smoke` | 1,344 | 336 | 56 |

현재 평가는 대부분 `data/raw/korean_food_1000/val` 기준이다.

---

## 3. 주요 모델 결과

### 3.1 B0 baseline

기존 운영/기준 모델:

```text
checkpoint: data/models/efficientnet_korean_b0_val08275.pt
classes: data/models/korean_food_classes.json
metadata: data/models/korean_food_model_meta.json
```

`korean_food_1000/val`에서 hflip TTA 평가:

| Metric | Value |
|---|---:|
| Top1 | 0.873504 |
| Top3 | 0.964713 |
| Macro-F1 | 0.873296 |

Report:

```text
reports/production_validation/b0_on_1000val_hflip/
```

주의:

```text
이 B0 baseline은 old split 기반 학습 모델이므로,
new validation과 filename-level overlap이 있는지 검증이 필요했다.
```

---

### 3.2 Food-LeWM B0

Food-LeWM pretraining 후 classifier fine-tuning:

```text
pretrain checkpoint: data/models/food_lewm_b0_pretrain_3ep.pt
classifier checkpoint: data/models/food_lewm_b0_classifier_3ep_ft10.pt
classes: data/models/food_lewm_b0_classes_3ep_ft10.json
metadata: data/models/food_lewm_b0_meta_3ep_ft10.json
```

`korean_food_1000/val` hflip:

| Metric | Value |
|---|---:|
| Top1 | 0.869484 |
| Top3 | 0.961408 |
| Macro-F1 | 0.869524 |

결론:

```text
현재 설정의 Food-LeWM 3ep pretraining은 supervised-only보다 낮았다.
B2-LeWM은 지금 당장 진행하지 않는 것이 맞다.
```

---

### 3.3 B0 supervised-only

LeWM checkpoint 없이 같은 wrapper 구조로 supervised-only fine-tuning:

```text
checkpoint: data/models/food_lewm_b0_supervised_only_ft10.pt
classes: data/models/food_lewm_b0_supervised_only_classes_ft10.json
metadata: data/models/food_lewm_b0_supervised_only_meta_ft10.json
```

`korean_food_1000/val` hflip:

| Metric | Value |
|---|---:|
| Top1 | 0.879757 |
| Top3 | 0.962212 |
| Macro-F1 | 0.879561 |

결론:

```text
현재 best single model이다.
```

---

## 4. Ensemble 결과

### 4.1 Simple average ensemble

모델:

```text
1. b0_baseline
2. food_lewm_b0
3. b0_supervised_only
```

Report:

```text
reports/ensemble/b0_baseline_plus_food_lewm_b0_plus_supervised_only_hflip/
```

결과:

| Metric | Value |
|---|---:|
| Top1 | 0.899232 |
| Top3 | 0.976059 |
| Macro-F1 | 0.899126 |

---

### 4.2 Weighted ensemble sweep

새 스크립트:

```text
scripts/eval_weighted_ensemble_sweep.py
```

Report:

```text
reports/weighted_ensemble/b0_family_hflip/
```

설정:

```text
models: B0 baseline + Food-LeWM B0 + B0 supervised-only
TTA: hflip
weight_step: 0.05
calibration_ratio: 0.5
seed: 42
calibration samples: 5,600
evaluation samples: 5,594
total val samples: 11,194
```

Calibration 기준 선택 weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.50 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.15 |

결과:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.899643 | 0.977500 | 0.899444 |
| evaluation | 0.901680 | 0.976046 | 0.901579 |
| full | 0.900661 | 0.976773 | 0.900545 |

Simple average와 비교:

| Ensemble | Full Top1 | Full Top3 | Full Macro-F1 |
|---|---:|---:|---:|
| simple average | 0.899232 | 0.976059 | 0.899126 |
| weighted selected | 0.900661 | 0.976773 | 0.900545 |

개선:

```text
Top1 +0.1429%p
Macro-F1 +0.1419%p
```

Diagnostic full-best:

| Model | Weight |
|---|---:|
| b0_baseline | 0.45 |
| food_lewm_b0 | 0.20 |
| b0_supervised_only | 0.35 |

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| full | 0.901465 | 0.976059 | 0.901325 |

검증자에게 확인받고 싶은 점:

```text
1. calibration 기준 selected weight를 현재 best로 채택해도 되는가?
2. evaluation top1이 simple average보다 약간 낮지 않고 오히려 높거나 유사한지 확인.
3. full-best weight는 peeking이므로 참고용으로만 둔 판단이 맞는가?
```

---

## 5. Split Leakage Audit

새 스크립트:

```text
scripts/audit_kfood_splits.py
```

실행:

```bash
python3 scripts/audit_kfood_splits.py \
  --old-data-dir data/raw/korean_food \
  --new-data-dir data/raw/korean_food_1000 \
  --output-dir reports/split_leakage_audit
```

결과:

| Pair | Resolved Path Unique | Class+Filename Unique |
|---|---:|---:|
| old_train__old_val | 0 | 0 |
| old_train__new_train | 0 | 22,406 |
| old_train__new_val | 0 | 4,474 |
| old_val__new_train | 0 | 0 |
| old_val__new_val | 0 | 6,720 |
| new_train__new_val | 0 | 0 |

해석:

```text
resolved_path 기준 직접 overlap은 0이다.
하지만 class+filename 기준 old_train -> new_val overlap이 4,474건이다.
```

검증자에게 확인받고 싶은 점:

```text
1. 이 상황을 leakage risk로 보는 것이 맞는가?
2. 기존 B0 baseline이 old split으로 학습되었다면,
   new_val 평가에서 inflated score 가능성이 있다고 봐야 하는가?
3. 최종 성능 확정 전 fixed clean validation split을 따로 만드는 것이 맞는가?
```

중요:

```text
current best ensemble에는 B0 baseline이 포함되어 있다.
따라서 filename-level overlap risk가 있다면 현재 ensemble 수치도 보수적으로 해석해야 한다.
```

관련 파일:

```text
reports/split_leakage_audit/overlap_summary.json
reports/split_leakage_audit/all_class_filename_overlaps.csv
reports/split_leakage_audit/old_train_new_val_overlap.csv
reports/split_leakage_audit/README.md
```

---

## 6. Error Analysis / Hard Classes

기존 error analysis:

```text
reports/error_analysis/final_candidate/
```

새 hard class report:

```text
scripts/build_hard_class_report.py
reports/hard_class_report/
```

Top hard classes:

| Class | F1 | Recall | High-Conf Errors |
|---|---:|---:|---:|
| 동태찌개 | 0.798165 | 0.870000 | 4 |
| 갈비찜 | 0.816626 | 0.835000 | 8 |
| 김치찌개 | 0.817955 | 0.820000 | 8 |
| 갈비구이 | 0.824691 | 0.835000 | 7 |
| 삼겹살 | 0.827586 | 0.783920 | 6 |
| 라면 | 0.834646 | 0.798995 | 11 |
| 닭볶음탕 | 0.835897 | 0.815000 | 15 |
| 곰탕_설렁탕 | 0.839895 | 0.800000 | 15 |

Top hard pairs:

| True | Pred | Count | True Accuracy |
|---|---|---:|---:|
| 곰탕_설렁탕 | 갈비탕 | 13 | 0.800 |
| 김치찌개 | 동태찌개 | 13 | 0.820 |
| 호박전 | 감자전 | 12 | 0.875 |
| 감자전 | 호박전 | 11 | 0.880 |
| 갈비구이 | 갈비찜 | 10 | 0.835 |
| 곰탕_설렁탕 | 삼계탕 | 10 | 0.800 |
| 비빔냉면 | 물냉면 | 10 | 0.905 |
| 삼겹살 | 갈비구이 | 10 | 0.783920 |
| 칼국수 | 수제비 | 10 | 0.840 |

해석:

```text
1. 찌개/탕/면류는 broth-only, crop, ingredient visibility 문제가 커 보인다.
2. 고기류는 구이/찜/보쌈/족발 경계가 애매하다.
3. 전류와 냉면류는 class boundary 검수가 필요하다.
```

검증자에게 확인받고 싶은 점:

```text
hard class 정리와 label review를 B2 학습보다 먼저 하는 판단이 맞는가?
```

---

## 7. High-Confidence Error 300개 검수 준비

입력:

```text
reports/error_analysis/final_candidate/high_confidence_errors_top300.csv
```

생성한 검수 sheet:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
```

행 수:

```text
300 samples + header = 301 lines
```

검수자가 채울 column:

```text
review_status
corrected_label
review_note
action
```

추천 review_status:

```text
correct
wrong_label
ambiguous
multi_food
bad_crop
unclear
```

검수 완료 후 저장할 파일명:

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

요약 스크립트:

```text
scripts/summarize_label_review.py
```

실행:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/error_analysis/final_candidate/reviewed_top300.csv \
  --output-dir reports/error_analysis/final_candidate/review_summary_top300
```

아직 사람이 검수한 `reviewed_top300.csv`는 없다.

판단 규칙:

```text
wrong_label + ambiguous + multi_food >= 10%:
  cleaned_v1 split 재학습 우선

wrong_label + ambiguous + multi_food < 5%:
  model diversity / ensemble weighting 우선
```

---

## 8. 테스트 및 검증

실행한 테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.06s
```

새 분석 스크립트들은 실제 실행하여 산출물 생성까지 확인했다.

---

## 9. 운영 파일 보호

다음 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

새 결과는 별도 파일명/별도 report dir에 저장했다.

---

## 10. 아직 하지 않은 것

아직 미진행:

```text
B0 supervised-only seed 7 추가 학습
B0 supervised-only seed 123 추가 학습
B2 clean supervised 학습
B2 추가 ensemble 평가
B2 fine-tuning
B2-LeWM
```

미진행 이유:

```text
제안서의 우선순위가 split 검증 -> high-confidence error 300개 검수 -> weighted ensemble sweep이었기 때문.
긴 학습 전에 현재 수치의 신뢰성과 데이터 병목을 먼저 확인하는 것이 맞다고 판단했다.
```

---

## 11. 다음 액션 제안

추천 순서:

1. `review_sheet_top300.csv`를 사람이 검수하여 `reviewed_top300.csv`로 저장한다.
2. `scripts/summarize_label_review.py`로 label noise 비율을 계산한다.
3. label noise가 높으면 cleaned_v1 split 생성 후 B0 supervised-only 재학습을 우선한다.
4. label noise가 낮으면 B0 seed 7/123 추가 학습을 진행한다.
5. 그 다음 B2 clean supervised를 ensemble diversity 목적으로 진행한다.
6. B2가 ensemble을 개선하면 B2 fine-tuning을 검토한다.
7. B2-LeWM은 마지막 후보로 보류한다.

---

## 12. 검증자에게 묻고 싶은 핵심 질문

1. `old_train -> new_val` class+filename overlap 4,474건을 leakage risk로 보는 것이 맞는가?
2. 이 overlap 때문에 B0 baseline 포함 ensemble 성능을 보수적으로 해석해야 하는가?
3. calibration 기준 weighted ensemble `top1=0.900661`을 현재 best로 채택해도 되는가?
4. diagnostic full-best `top1=0.901465`를 참고용으로만 두는 판단이 맞는가?
5. B2 clean 학습보다 label review / hard class 정리를 먼저 하는 순서가 맞는가?
6. 92%까지 남은 약 1.93%p를 모델 capacity보다 label noise / hard pair / fixed validation 이슈로 먼저 보는 것이 타당한가?

---

## 13. 한 줄 결론

현재 best는 calibration 기준 weighted B0-family ensemble이며 `top1=0.900661`, `macro_f1=0.900545`이다.  
다만 `old_train -> new_val` filename-level overlap 4,474건이 있어 최종 성능 확정 전 clean/fixed validation 재검증이 필요하다.  
다음 병목은 B2 학습 자체보다 label noise, hard class confusion, split leakage risk 정리다.

---

## 14. 다음 단계 실행 결과 업데이트

추가 실행 문서:

```text
KFOOD_92_NEXT_STEP_EXECUTION.md
```

추가 산출물:

```text
scripts/eval_cached_ensemble_subsets.py
reports/weighted_ensemble/b0_family_hflip_subset_audit/
```

핵심 업데이트:

| Model / Ensemble | Full Top1 | Old-Train-Overlap Top1 | Minus-Old-Train Top1 |
|---|---:|---:|---:|
| simple_average | 0.899232 | 0.916853 | 0.887500 |
| weighted_selected | 0.900661 | 0.928923 | 0.881845 |
| diagnostic_full_best | 0.901465 | 0.924899 | 0.885863 |
| single_b0_baseline | 0.873504 | 0.938757 | 0.830060 |
| single_food_lewm_b0 | 0.869484 | 0.869692 | 0.869345 |
| single_b0_supervised_only | 0.879757 | 0.879079 | 0.880208 |

Conservative subset 기준 best weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.45 |
| b0_supervised_only | 0.50 |

Conservative subset best:

```text
minus_old_train_filename_overlap top1 = 0.890476
macro_f1 = 0.890290
```

업데이트된 결론:

```text
기존 full-val 0.900661은 낙관적 수치일 가능성이 크다.
B0 baseline은 old_train overlap subset에서 0.938757, minus-old-train subset에서 0.830060으로 10.87%p 차이가 난다.
앞으로 의사결정 기준은 full-val이 아니라 conservative subset 또는 새 fixed clean validation이어야 한다.
```

---

## 15. Fixed V1 및 Seed7 실행 업데이트

추가 실행 문서:

```text
KFOOD_92_NEXT_STEP_EXECUTION.md
```

Fixed V1 split:

| Split | Count |
|---|---:|
| train | 49,243 |
| val | 6,720 |

Audit:

```text
old_train -> fixed_v1 val class+filename overlap = 0
fixed_v1 train -> fixed_v1 val class+filename overlap = 0
```

B0 supervised-only seed7 fixed_v1 hflip:

| Model | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| seed7 fixed_v1 | 0.880357 | 0.965179 | 0.880014 |

4-model weighted ensemble:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.20 |
| b0_supervised_seed7_fixed_v1 | 0.40 |

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.899107 | 0.976786 | 0.899127 |
| evaluation | 0.886310 | 0.968750 | 0.885753 |
| full | 0.892708 | 0.972768 | 0.892576 |

업데이트된 보수적 best:

```text
fixed_v1 best = 4-model weighted ensemble
top1 = 0.892708
macro_f1 = 0.892576
92%까지 남은 gap = 약 2.7292%p
```

검증 포인트:

```text
calibration/evaluation split 차이가 있다.
따라서 4-model weighted ensemble은 채택 가능 후보지만,
seed123 또는 B2를 추가해 fixed_v1 evaluation split에서도 안정적인 개선이 반복되는지 확인해야 한다.
```

---

## 16. Seed123 반복성 확인 업데이트

추가 실행 결과:

```text
KFOOD_92_NEXT_STEP_EXECUTION.md
```

Seed123 single hflip:

| Model | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| B0 supervised-only seed123 fixed_v1 | 0.886012 | 0.965327 | 0.885791 |

Seed 비교:

| Model | Top1 | Macro-F1 |
|---|---:|---:|
| 기존 B0 supervised-only | 0.880208 | 0.880076 |
| seed7 fixed_v1 | 0.880357 | 0.880014 |
| seed123 fixed_v1 | 0.886012 | 0.885791 |

5-model weighted ensemble:

| Model | Weight |
|---|---:|
| b0_baseline | 0.10 |
| food_lewm_b0 | 0.20 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.20 |
| b0_supervised_seed123_fixed_v1 | 0.50 |

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.902679 | 0.975595 | 0.902677 |
| evaluation | 0.893750 | 0.966964 | 0.893057 |
| full | 0.898214 | 0.971280 | 0.897979 |

업데이트된 보수적 best:

```text
fixed_v1 best = 5-model weighted ensemble
top1 = 0.898214
macro_f1 = 0.897979
92%까지 남은 gap = 약 2.1786%p
```

판단:

```text
seed 추가 학습 효과는 반복됐다.
seed123은 단일 모델에서도 seed7보다 높고,
5-model weighted ensemble은 4-model weighted ensemble 대비 +0.5506%p 개선했다.
다음은 B0 seed를 하나 더 늘리기보다 B2 clean supervised fixed_v1로 backbone diversity를 확인하는 편이 더 타당하다.
```
