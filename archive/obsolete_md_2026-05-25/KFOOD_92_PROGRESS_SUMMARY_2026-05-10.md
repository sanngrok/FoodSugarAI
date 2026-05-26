# K-Food 92% 프로젝트 진행상황 요약

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

이 문서는 K-Food 56-class 분류 성능을 92%에 가깝게 올리기 위해 지금까지 진행한 데이터 검증, 모델 학습, ensemble 실험, 현재 best, 다음 액션을 정리한 것이다.

---

## 1. 최종 요약

초기에는 `korean_food_1000/val` 전체 기준으로 weighted ensemble top1 `0.900661`까지 확인했지만, 이후 split leakage audit에서 기존 B0 baseline이 학습한 old train 이미지와 filename-level로 겹치는 validation subset이 성능을 크게 부풀린다는 사실을 확인했다.

따라서 현재는 `korean_food_fixed_v1` split을 만들고, 이 split 기준으로 보수적 성능을 다시 보고 있다.

현재 보수적 best:

```text
Model/Ensemble: 6-model weighted ensemble including B2 clean fixed_v1
Data: data/raw/korean_food_fixed_v1
TTA: hflip
Top1: 0.900149
Top3: 0.974405
Macro-F1: 0.899900
92%까지 남은 gap: 약 1.9851%p
```

현재 best single:

```text
Model: B0 supervised-only seed123 fixed_v1
Data: data/raw/korean_food_fixed_v1
TTA: hflip
Top1: 0.886012
Top3: 0.965327
Macro-F1: 0.885791
```

핵심 결론:

```text
1. 기존 full-val 90%는 낙관적 수치였다.
2. fixed_v1 기준으로 다시 보니 현재 best는 89.82%다.
3. B0 seed 추가 효과는 반복됐다.
4. B2 clean supervised 단독 성능은 약했지만, ensemble diversity로는 소폭 개선을 만들었다.
```

---

## 2. 데이터셋 현황

기존 데이터:

| Dataset | Train | Val | Classes | Notes |
|---|---:|---:|---:|---|
| `data/raw/korean_food` | 26,880 | 6,720 | 56 | old split |
| `data/raw/korean_food_1000` | 44,769 | 11,194 | 56 | 확장 split, 초기 평가 기준 |
| `data/raw/korean_food_smoke` | 1,344 | 336 | 56 | smoke test |

새로 만든 보수적 split:

| Dataset | Train | Val | Classes | Notes |
|---|---:|---:|---:|---|
| `data/raw/korean_food_fixed_v1` | 49,243 | 6,720 | 56 | old_train overlap 제거 val |

`fixed_v1` 생성 정책:

```text
train = korean_food_1000/train + old_train_filename_overlap_new_val 4,474장
val = minus_old_train_filename_overlap 6,720장
```

관련 파일:

```text
data/raw/korean_food_fixed_v1/
data/raw/korean_food_fixed_v1/split_meta.json
data/raw/korean_food_fixed_v1/train_manifest.csv
data/raw/korean_food_fixed_v1/val_manifest.csv
```

---

## 3. Split Leakage / Overlap 분석

초기 `korean_food_1000/val` audit 결과:

| Pair | Resolved Path Unique | Class+Filename Unique |
|---|---:|---:|
| old_train__new_val | 0 | 4,474 |
| old_val__new_val | 0 | 6,720 |
| new_train__new_val | 0 | 0 |

중요한 발견:

```text
korean_food_1000/val 11,194장은 class+filename 기준으로
old_train 4,474장 + old_val 6,720장으로 구성되어 있었다.
old split과 전혀 겹치지 않는 new validation subset은 0장이다.
```

B0 baseline subset별 성능:

| Model | Full Top1 | Old-Train-Overlap Top1 | Minus-Old-Train Top1 |
|---|---:|---:|---:|
| B0 baseline | 0.873504 | 0.938757 | 0.830060 |

해석:

```text
B0 baseline은 old_train overlap subset에서 비정상적으로 높고,
old_train overlap을 제거하면 0.830060까지 떨어진다.
따라서 B0 baseline 포함 full-val ensemble 성능은 낙관적으로 해석해야 한다.
```

`fixed_v1` audit 결과:

| Pair | Class+Filename Unique |
|---|---:|
| old_train__fixed_v1_val | 0 |
| fixed_v1_train__fixed_v1_val | 0 |
| old_val__fixed_v1_val | 6,720 |

해석:

```text
fixed_v1 val은 B0 baseline old_train과 겹치지 않는다.
fixed_v1 train/val 간 class+filename overlap도 없다.
따라서 기존 korean_food_1000 full-val보다 더 보수적인 평가 기준이다.
```

관련 산출물:

```text
reports/split_leakage_audit/
reports/weighted_ensemble/b0_family_hflip_subset_audit/
reports/fixed_v1_split_audit/
```

---

## 4. 주요 스크립트 추가 현황

추가한 분석/실험 스크립트:

| Script | Purpose |
|---|---|
| `scripts/audit_kfood_splits.py` | old/new split overlap audit |
| `scripts/prepare_label_review_sheet.py` | high-confidence error 검수 sheet 생성 |
| `scripts/summarize_label_review.py` | 검수 완료 CSV 요약 |
| `scripts/build_hard_class_report.py` | hard class / hard pair report 생성 |
| `scripts/eval_weighted_ensemble_sweep.py` | logits cache 생성 + weighted ensemble sweep |
| `scripts/eval_cached_ensemble_subsets.py` | cached logits subset별 성능 분석 |
| `scripts/build_kfood_fixed_split.py` | fixed_v1 split 생성 |
| `scripts/append_model_to_logits_cache.py` | 기존 logits cache에 새 모델 logits 추가 |
| `scripts/sweep_cached_ensemble_weights.py` | cached logits weight sweep |

기존에 추가/수정된 모델 관련 스크립트:

| Script / Module | Purpose |
|---|---|
| `scripts/pretrain_food_lewm.py` | Food-LeWM pretraining |
| `scripts/train_food_lewm_classifier.py` | Food-LeWM wrapper classifier 학습, supervised-only 지원 |
| `scripts/eval_kfood_any_model.py` | plain timm / Food-LeWM 모델 공통 평가 |
| `scripts/eval_kfood_ensemble.py` | multi-model ensemble 평가 |
| `scripts/analyze_kfood_errors.py` | error analysis |
| `src/classifier/food_classifier.py` | timm classifier + Food-LeWM wrapper 로딩 지원 |
| `src/classifier/food_lewm_model.py` | Food-LeWM classifier wrapper |
| `src/classifier/lewm_sigreg.py` | LeWM / SigReg 구성 요소 |

이번 B2 단계에서 추가 보강한 로딩 호환:

```text
src/classifier/food_classifier.py
```

내용:

```text
efficientnet_korean_b2_clean_fixed_v1.pt 같은 모델명이
korean_food_classes_b2_clean_fixed_v1.json /
korean_food_model_meta_b2_clean_fixed_v1.json companion 파일을 찾도록 보강했다.
```

---

## 5. 모델 실험 결과 요약

### 5.1 기존 B0 baseline

Checkpoint:

```text
data/models/efficientnet_korean_b0_val08275.pt
```

`korean_food_1000/val` hflip:

| Top1 | Top3 | Macro-F1 |
|---:|---:|---:|
| 0.873504 | 0.964713 | 0.873296 |

`fixed_v1` hflip:

| Top1 | Macro-F1 |
|---:|---:|
| 0.830060 | 0.829779 |

해석:

```text
B0 baseline은 old_train overlap 영향을 크게 받는다.
fixed_v1에서는 단일 모델로 약하다.
ensemble에서는 weight를 낮게 제한하는 것이 맞다.
```

---

### 5.2 Food-LeWM B0

Checkpoint:

```text
data/models/food_lewm_b0_classifier_3ep_ft10.pt
```

`korean_food_1000/val` hflip:

| Top1 | Top3 | Macro-F1 |
|---:|---:|---:|
| 0.869484 | 0.961408 | 0.869524 |

`fixed_v1` hflip:

| Top1 | Macro-F1 |
|---:|---:|
| 0.869345 | 0.869215 |

해석:

```text
현재 설정의 LeWM 3ep pretraining은 supervised-only보다 낮다.
B2-LeWM은 보류가 맞다.
```

---

### 5.3 B0 supervised-only 기존 모델

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_ft10.pt
```

`korean_food_1000/val` hflip:

| Top1 | Top3 | Macro-F1 |
|---:|---:|---:|
| 0.879757 | 0.962212 | 0.879561 |

`fixed_v1` hflip:

| Top1 | Macro-F1 |
|---:|---:|
| 0.880208 | 0.880076 |

해석:

```text
old_train overlap에 크게 흔들리지 않는 안정적인 B0 계열 후보다.
```

---

### 5.4 B0 supervised-only seed7 fixed_v1

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt
```

hflip 평가:

| Data | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| fixed_v1 | 0.880357 | 0.965179 | 0.880014 |

해석:

```text
seed7 단일 모델은 기존 supervised-only와 거의 비슷하다.
단일 성능 개선은 작지만 weighted ensemble에는 소폭 기여했다.
```

---

### 5.5 B0 supervised-only seed123 fixed_v1

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
```

hflip 평가:

| Data | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| fixed_v1 | 0.886012 | 0.965327 | 0.885791 |

해석:

```text
seed123은 seed7보다 단일 hflip 기준 +0.5655%p 높다.
현재 best single model이다.
seed 추가 학습 효과는 반복됐다.
```

---

### 5.6 B2 clean supervised fixed_v1

기준 문서:

```text
/Users/sangrok/Desktop/CODEX_B2_CLEAN_SUPERVISED_FIXED_V1_PLAN.md
```

Checkpoint:

```text
data/models/efficientnet_korean_b2_clean_fixed_v1.pt
```

학습 설정:

```text
model_name=efficientnet_b2
image_size=260
epochs=20 planned
batch_size=32
grad_accum_steps=2
lr=5e-5
weight_decay=1e-4
label_smoothing=0.05
randaugment_n=2
randaugment_m=7
random_erasing_p=0.1
drop_rate=0.1
drop_path_rate=0.1
```

학습 진행:

| Epoch | Val Top1 | Val Top3 | Macro-F1 | Seconds |
|---:|---:|---:|---:|---:|
| 1 | 0.096577 | 0.219048 | 0.094726 | 210.83 |
| 2 | 0.222619 | 0.408036 | 0.214998 | 211.07 |
| 3 | 0.786458 | 0.926339 | 0.786383 | 2248.29 |
| 4 | 0.833929 | 0.953125 | 0.833526 | 16772.22 |

중단 사유:

```text
epoch 4 이후 epoch 5가 batch 900/1539까지 진행됐지만,
MPS full fine-tuning 속도가 지나치게 느려져 실행 가능성이 낮다고 판단하고 중단했다.
best checkpoint는 epoch 4 기준으로 보존했다.
```

평가 결과:

| TTA | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| none | 0.833929 | 0.953125 | 0.833526 |
| hflip | 0.835714 | 0.954762 | 0.835308 |

산출물:

```text
data/models/efficientnet_korean_b2_clean_fixed_v1.pt
data/models/korean_food_classes_b2_clean_fixed_v1.json
data/models/korean_food_model_meta_b2_clean_fixed_v1.json
reports/b2/b2_clean_fixed_v1/
reports/b2/eval_b2_clean_fixed_v1_none/
reports/b2/eval_b2_clean_fixed_v1_hflip/
```

해석:

```text
B2 single hflip 0.835714로 계획서 기준 <0.85 weak 구간이다.
단독 모델로는 채택하기 어렵지만, backbone diversity 후보로 ensemble 효과는 확인했다.
```

---

## 6. Ensemble 결과 요약

### 6.1 초기 full-val 3-model weighted ensemble

데이터:

```text
data/raw/korean_food_1000
```

모델:

```text
b0_baseline
food_lewm_b0
b0_supervised_only
```

결과:

| Ensemble | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| weighted selected | 0.900661 | 0.976773 | 0.900545 |

주의:

```text
이 수치는 old_train filename overlap 영향으로 낙관적이다.
현재 best로 보지 않는다.
```

---

### 6.2 Conservative subset 3-model sweep

Subset:

```text
minus_old_train_filename_overlap
```

Best weights:

| Model | Weight |
|---|---:|
| b0_baseline | 0.05 |
| food_lewm_b0 | 0.45 |
| b0_supervised_only | 0.50 |

결과:

| Top1 | Top3 | Macro-F1 |
|---:|---:|---:|
| 0.890476 | 0.969940 | 0.890290 |

---

### 6.3 4-model weighted ensemble

데이터:

```text
data/raw/korean_food_fixed_v1
```

모델:

```text
b0_baseline
food_lewm_b0
b0_supervised_only
b0_supervised_seed7_fixed_v1
```

Best weights:

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

---

### 6.4 5-model weighted ensemble

데이터:

```text
data/raw/korean_food_fixed_v1
```

모델:

```text
b0_baseline
food_lewm_b0
b0_supervised_only
b0_supervised_seed7_fixed_v1
b0_supervised_seed123_fixed_v1
```

Best weights:

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
| full | 0.893601 | 0.972619 | 0.893388 |

해석:

```text
seed123 추가 후 5-model weighted ensemble은 4-model 대비 +0.5506%p 개선했다.
seed 추가 효과는 ensemble에서도 반복됐다.
현재 fixed_v1 기준 best는 5-model weighted ensemble이다.
```

---

### 6.5 6-model weighted ensemble with B2

데이터:

```text
data/raw/korean_food_fixed_v1
```

모델:

```text
b0_baseline
food_lewm_b0
b0_supervised_only
b0_supervised_seed7_fixed_v1
b0_supervised_seed123_fixed_v1
b2_clean_fixed_v1
```

Best weights:

| Model | Weight |
|---|---:|
| b0_baseline | 0.00 |
| food_lewm_b0 | 0.15 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.25 |
| b0_supervised_seed123_fixed_v1 | 0.25 |
| b2_clean_fixed_v1 | 0.35 |

결과:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.907440 | 0.979762 | 0.907389 |
| evaluation | 0.892857 | 0.969048 | 0.892251 |
| full | 0.900149 | 0.974405 | 0.899900 |

Diagnostic full-best:

| Top1 | Top3 | Macro-F1 |
|---:|---:|---:|
| 0.900744 | 0.974107 | 0.900487 |

비교:

| Candidate | Full Top1 | Full Macro-F1 |
|---|---:|---:|
| 5-model weighted ensemble | 0.898214 | 0.897979 |
| 6-model weighted ensemble selected by calibration | 0.900149 | 0.899900 |
| 6-model diagnostic full-best | 0.900744 | 0.900487 |

해석:

```text
B2 단독은 약하지만, 6-model weighted ensemble에서는 full top1 기준 +0.1935%p 개선했다.
다만 evaluation split top1은 5-model 0.893750보다 6-model 0.892857이 낮으므로,
개선은 작고 보수적으로 해석해야 한다.
```

산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/logits_cache.pt
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/metrics.json
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/sweep_results.csv
```

---

## 7. 현재 성능 리더보드

보수적 fixed_v1 기준:

| Rank | Experiment | Top1 | Top3 | Macro-F1 |
|---:|---|---:|---:|---:|
| 1 | 6-model weighted ensemble with B2 | 0.900149 | 0.974405 | 0.899900 |
| 2 | 5-model weighted ensemble | 0.898214 | 0.971280 | 0.897979 |
| 3 | 6-model simple average | 0.894196 | 0.974851 | 0.894016 |
| 4 | 5-model simple average | 0.893601 | 0.972619 | 0.893388 |
| 5 | 4-model weighted ensemble | 0.892708 | 0.972768 | 0.892576 |
| 6 | 3-model conservative sweep | 0.890476 | 0.969940 | 0.890290 |
| 7 | B0 supervised-only seed123 | 0.886012 | 0.965327 | 0.885791 |
| 8 | B0 supervised-only seed7 | 0.880357 | 0.965179 | 0.880014 |
| 9 | B0 supervised-only existing | 0.880208 | 0.961756 | 0.880076 |
| 10 | Food-LeWM B0 | 0.869345 | - | 0.869215 |
| 11 | B2 clean supervised fixed_v1 | 0.835714 | 0.954762 | 0.835308 |
| 12 | B0 baseline | 0.830060 | - | 0.829779 |

---

## 8. Error Analysis / Hard Classes

Hard class report:

```text
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

| True | Pred | Count |
|---|---|---:|
| 곰탕_설렁탕 | 갈비탕 | 13 |
| 김치찌개 | 동태찌개 | 13 |
| 호박전 | 감자전 | 12 |
| 감자전 | 호박전 | 11 |
| 갈비구이 | 갈비찜 | 10 |
| 곰탕_설렁탕 | 삼계탕 | 10 |
| 비빔냉면 | 물냉면 | 10 |
| 삼겹살 | 갈비구이 | 10 |
| 칼국수 | 수제비 | 10 |

해석:

```text
찌개/탕/면류는 broth-only, crop, ingredient visibility 문제가 크다.
고기류는 구이/찜/보쌈/족발 경계가 애매하다.
전류와 냉면류는 class boundary 검수가 필요하다.
```

---

## 9. High-Confidence Error 검수 준비

검수용 sheet:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
```

행 수:

```text
300 samples + header = 301 lines
```

아직 사람이 검수한 파일은 없음:

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

검수 완료 후 실행:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/error_analysis/final_candidate/reviewed_top300.csv \
  --output-dir reports/error_analysis/final_candidate/review_summary_top300
```

---

## 10. 운영 파일 보호

다음 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

새 학습 결과는 별도 파일명으로 저장했다.

---

## 11. 주요 산출물 경로

진행 문서:

```text
KFOOD_92_GPT_VALIDATION_BRIEF.md
KFOOD_92_NEXT_STEP_EXECUTION.md
KFOOD_92_PROGRESS_SUMMARY_2026-05-10.md
reports/kfood_92_next_action_proposal_result.md
```

데이터:

```text
data/raw/korean_food_fixed_v1/
```

모델:

```text
data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
data/models/efficientnet_korean_b2_clean_fixed_v1.pt
```

평가/ensemble:

```text
reports/seed_experiments/eval_b0_supervised_only_seed7_fixed_v1_hflip/
reports/seed_experiments/eval_b0_supervised_only_seed123_fixed_v1_hflip/
reports/weighted_ensemble/b0_family_plus_seed7_fixed_v1_hflip/
reports/weighted_ensemble/b0_family_plus_seed7_seed123_fixed_v1_hflip/
reports/b2/b2_clean_fixed_v1/
reports/b2/eval_b2_clean_fixed_v1_none/
reports/b2/eval_b2_clean_fixed_v1_hflip/
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/
```

분석:

```text
reports/split_leakage_audit/
reports/fixed_v1_split_audit/
reports/weighted_ensemble/b0_family_hflip_subset_audit/
reports/hard_class_report/
reports/error_analysis/final_candidate/
```

---

## 12. 테스트

가장 최근 테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 1.84s
```

---

## 13. 현재 판단

### 13.1 Leakage 판단

```text
korean_food_1000 full-val 90% 수치는 더 이상 current best로 보지 않는다.
B0 baseline이 old_train overlap subset에서 과도하게 높은 성능을 보였기 때문이다.
```

### 13.2 Seed 효과 판단

```text
seed7은 단일 성능 개선은 작았지만 ensemble에 기여했다.
seed123은 단일 모델과 ensemble 모두에서 개선을 만들었다.
따라서 seed diversity 효과는 반복됐다.
```

### 13.3 LeWM 판단

```text
현재 LeWM 3ep 설정은 supervised-only보다 낮다.
B2-LeWM은 보류한다.
```

### 13.4 B2 판단

```text
B2 clean supervised는 단독 top1 0.835714로 약하다.
하지만 6-model weighted ensemble에서는 full top1을 0.898214에서 0.900149로 올렸다.
B2는 단독 모델이 아니라 diversity member로만 의미가 있다.
```

### 13.5 B0 baseline 판단

```text
B0 baseline은 fixed_v1에서 단일 top1 0.830060으로 낮다.
하지만 weighted ensemble에서는 0.05~0.10 정도의 낮은 weight로 약간 기여한다.
높은 weight를 주면 leakage-risk 방향으로 끌릴 수 있다.
```

---

## 14. 다음 액션

추천 우선순위:

1. B2 clean supervised를 길게 재개할지 판단
2. label review 300개 수동 검수
3. label noise가 높으면 cleaned_v1 split 재학습
4. B0 seed 추가 1개 또는 B2 재학습 설정 개선
5. hard class 중심 class-boundary/데이터 보강

현재 B2 이후 판단:

```text
B2는 ensemble diversity로 소폭 이득을 줬지만, epoch 4 기준 단독 성능은 낮다.
full fine-tuning 속도가 지나치게 느려서 그대로 20epoch를 밀기보다
학습 설정/장치/재개 전략을 먼저 조정하는 것이 낫다.
```

B2 성공 기준:

```text
B2 single fixed_v1 hflip >= 0.87:
  ensemble 후보로 강하게 채택

B2 single fixed_v1 hflip 0.85~0.87:
  ensemble improvement 여부로 판단

B2 single fixed_v1 hflip < 0.85:
  실제 결과 0.835714. 단독 채택은 보류하고 ensemble member로만 유지
```

---

## 15. 한 줄 결론

현재 보수적 best는 `fixed_v1` 기준 B2를 포함한 6-model weighted ensemble이며 `top1=0.900149`, `macro_f1=0.899900`이다.  
B2 단독은 약하지만 ensemble diversity로는 소폭 효과가 있었고, 92%까지 남은 gap은 약 1.99%p다.
