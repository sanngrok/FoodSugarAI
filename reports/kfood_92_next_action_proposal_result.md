# K-Food 92% Next Action Proposal Result

작성일: 2026-05-09

## 1. 이번 실행 요약

`/Users/sangrok/Desktop/CODEX_KFOOD_92_NEXT_ACTION_PROPOSAL.md`의 우선순위에 따라 먼저 긴 학습이 아닌 검증/분석/ensemble weight 단계부터 진행했다.

완료한 작업:

- split leakage audit 스크립트 작성 및 실행
- high-confidence error 300개 검수용 sheet 생성
- label review summary 스크립트 작성
- hard class / hard pair report 생성
- weighted ensemble sweep 스크립트 작성 및 실행
- 최종 결과 리포트 작성
- 기존 테스트 확인: `python3 -m pytest tests/ -q` -> 18 passed

아직 진행하지 않은 긴 학습:

- B0 supervised-only seed 7 / seed 123 추가 학습
- B2 clean supervised 학습
- B2 ensemble 평가
- B2 fine-tuning
- B2-LeWM

이유: 제안서의 핵심 문장대로 `split 검증 -> high-confidence error 300개 검수 -> weighted ensemble sweep`을 먼저 완료했다. B0 seed와 B2는 시간이 긴 다음 실행 단위로 남겨두는 것이 좋다.

---

## 2. 생성/수정한 스크립트

새로 추가:

- `scripts/audit_kfood_splits.py`
- `scripts/prepare_label_review_sheet.py`
- `scripts/summarize_label_review.py`
- `scripts/build_hard_class_report.py`
- `scripts/eval_weighted_ensemble_sweep.py`

핵심 산출물:

- `reports/split_leakage_audit/`
- `reports/error_analysis/final_candidate/review_sheet_top300.csv`
- `reports/hard_class_report/`
- `reports/weighted_ensemble/b0_family_hflip/`
- `reports/kfood_92_next_action_proposal_result.md`

---

## 3. Split Leakage Audit 결과

실행:

```bash
python3 scripts/audit_kfood_splits.py \
  --old-data-dir data/raw/korean_food \
  --new-data-dir data/raw/korean_food_1000 \
  --output-dir reports/split_leakage_audit
```

Split counts:

| Split | Count |
|---|---:|
| old_train | 26,880 |
| old_val | 6,720 |
| new_train | 44,769 |
| new_val | 11,194 |

Overlap summary:

| Pair | Resolved Path Unique | Class+Filename Unique |
|---|---:|---:|
| old_train__old_val | 0 | 0 |
| old_train__new_train | 0 | 22,406 |
| old_train__new_val | 0 | 4,474 |
| old_val__new_train | 0 | 0 |
| old_val__new_val | 0 | 6,720 |
| new_train__new_val | 0 | 0 |

해석:

- `resolved_path` 기준 직접 overlap은 0이다.
- 하지만 `class+filename` 기준으로 `old_train -> new_val` 4,474건이 잡혔다.
- 이는 파일이 복사/재구성되어 실제 경로는 다르지만 동일 class/filename 이미지가 새 validation에 들어간 가능성을 의미한다.
- 따라서 기존 old split으로 학습된 B0 baseline을 새 validation에서 평가할 때 일부 성능 inflate 가능성이 있다.
- 현재 best ensemble에는 B0 baseline이 포함되어 있으므로, 최종 운영 판단 전에는 fixed clean validation 또는 label/image identity audit가 추가로 필요하다.

관련 파일:

- `reports/split_leakage_audit/overlap_summary.json`
- `reports/split_leakage_audit/old_train_new_val_overlap.csv`
- `reports/split_leakage_audit/all_class_filename_overlaps.csv`
- `reports/split_leakage_audit/README.md`

---

## 4. High-Confidence Error 300개 검수 준비

입력:

- `reports/error_analysis/final_candidate/high_confidence_errors_top300.csv`

출력:

- `reports/error_analysis/final_candidate/review_sheet_top300.csv`

행 수:

- 300개 sample + header = 301 lines

Review sheet columns:

| Column | Purpose |
|---|---|
| rank | confidence 순위 |
| image_path | 검수할 이미지 경로 |
| true_label | 현재 정답 label |
| pred_label | 모델 예측 label |
| confidence | 모델 confidence |
| top3 | top-3 예측 |
| review_status | 검수자가 채울 상태 |
| corrected_label | 정정 label |
| review_note | 검수 메모 |
| action | remove/relabel/keep 등 |

권장 `review_status` 값:

- `correct`
- `wrong_label`
- `ambiguous`
- `multi_food`
- `bad_crop`
- `unclear`

검수 결과 파일을 아래 경로로 저장하면 summary 스크립트를 바로 실행할 수 있다.

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

Summary 실행:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/error_analysis/final_candidate/reviewed_top300.csv \
  --output-dir reports/error_analysis/final_candidate/review_summary_top300
```

현재는 사람이 채운 reviewed file이 아직 없으므로 검수 요약 수치는 미산출이다.

---

## 5. Hard Class / Hard Pair 분석 결과

실행:

```bash
python3 scripts/build_hard_class_report.py \
  --error-dir reports/error_analysis/final_candidate \
  --output-dir reports/hard_class_report
```

Hard class count:

- 16 classes

Top hard classes:

| Class | F1 | Recall | High-Conf Errors | Action |
|---|---:|---:|---:|---|
| 동태찌개 | 0.798165 | 0.870000 | 4 | broth-only 이미지 검수, 특징 재료 중심 보강 |
| 갈비찜 | 0.816626 | 0.835000 | 8 | high-confidence error 검수, clean example 보강 |
| 김치찌개 | 0.817955 | 0.820000 | 8 | broth-only 이미지 검수, 특징 재료 중심 보강 |
| 갈비구이 | 0.824691 | 0.835000 | 7 | high-confidence error 검수, clean example 보강 |
| 삼겹살 | 0.827586 | 0.783920 | 6 | high-confidence error 검수, clean example 보강 |
| 라면 | 0.834646 | 0.798995 | 11 | high-confidence error 검수, clean example 보강 |
| 닭볶음탕 | 0.835897 | 0.815000 | 15 | broth-only 이미지 검수, 특징 재료 중심 보강 |
| 곰탕_설렁탕 | 0.839895 | 0.800000 | 15 | broth-only 이미지 검수, 특징 재료 중심 보강 |

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

- 찌개/탕/면류처럼 국물 색과 구도에 의존하는 class가 약하다.
- 구이/찜/고기류는 plating과 crop ambiguity가 주요 병목이다.
- 전류, 냉면류, 족발/보쌈류는 class boundary 검수가 우선이다.

관련 파일:

- `reports/hard_class_report/hard_classes.csv`
- `reports/hard_class_report/hard_pairs.csv`
- `reports/hard_class_report/README.md`

---

## 6. Weighted Ensemble Sweep 결과

실행:

```bash
python3 scripts/eval_weighted_ensemble_sweep.py \
  --data-dir data/raw/korean_food_1000 \
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
  --tta hflip \
  --batch-size 128 \
  --num-workers 0 \
  --weight-step 0.05 \
  --calibration-ratio 0.5 \
  --seed 42 \
  --output-dir reports/weighted_ensemble/b0_family_hflip
```

설정:

- models: B0 baseline + Food-LeWM B0 + B0 supervised-only
- TTA: hflip
- weight step: 0.05
- validation split: calibration 5,600 / evaluation 5,594
- logits cache: `reports/weighted_ensemble/b0_family_hflip/logits_cache.pt`

Calibration 기준 채택 weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.50 |
| food_lewm_b0 | 0.35 |
| b0_supervised_only | 0.15 |

Calibration 기준 채택 결과:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.899643 | 0.977500 | 0.899444 |
| evaluation | 0.901680 | 0.976046 | 0.901579 |
| full | 0.900661 | 0.976773 | 0.900545 |

단순 평균 baseline:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.896429 | 0.976607 | 0.896264 |
| evaluation | 0.902038 | 0.975509 | 0.901952 |
| full | 0.899232 | 0.976059 | 0.899126 |

Diagnostic full-best:

| Model | Weight |
|---|---:|
| b0_baseline | 0.45 |
| food_lewm_b0 | 0.20 |
| b0_supervised_only | 0.35 |

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| full | 0.901465 | 0.976059 | 0.901325 |

주의:

- 채택 가능한 기준은 calibration에서 선택한 weight다.
- diagnostic full-best는 full validation을 보고 고른 값이므로 최종 모델 선택 기준으로 쓰면 validation peeking 위험이 있다.
- 그래도 weighted ensemble이 단순 평균 대비 개선 여지가 있음을 보여준다.

판단:

```text
weighted ensemble eval/full top1 > 0.899232 이므로 채택 가능.
```

---

## 7. 성능 표

| Experiment | Model | Data | TTA | Ensemble | Top1 | Top3 | Macro-F1 |
|---|---|---|---|---|---:|---:|---:|
| B0 baseline | efficientnet_b0 | korean_food_1000 | hflip | no | 0.873504 | 0.964713 | 0.873296 |
| B0 supervised-only | B0 wrapper | korean_food_1000 | hflip | no | 0.879757 | 0.962212 | 0.879561 |
| Food-LeWM B0 | B0-LeWM | korean_food_1000 | hflip | no | 0.869484 | 0.961408 | 0.869524 |
| Current best simple ensemble | B0+B0LeWM+B0Sup | korean_food_1000 | hflip | yes | 0.899232 | 0.976059 | 0.899126 |
| Weighted ensemble selected | B0+B0LeWM+B0Sup | korean_food_1000 | hflip | yes | 0.900661 | 0.976773 | 0.900545 |
| Weighted ensemble diagnostic full-best | B0+B0LeWM+B0Sup | korean_food_1000 | hflip | yes | 0.901465 | 0.976059 | 0.901325 |
| B2 clean | efficientnet_b2 | korean_food_1000 | hflip | no | TBD | TBD | TBD |
| B0 family + B2 | mixed | korean_food_1000 | hflip | yes | TBD | TBD | TBD |

---

## 8. 현재 Best

보수적 채택 기준:

```text
현재 best는 weighted B0-family ensemble이며 top1=0.900661, macro_f1=0.900545이다.
현재 92%까지 남은 gap은 1.9339%p이다.
다음 병목은 split/filename overlap risk + label noise + hard class confusion이다.
```

Diagnostic full-best 기준:

```text
diagnostic full-best는 top1=0.901465, macro_f1=0.901325이다.
이 경우 92%까지 남은 gap은 1.8535%p이다.
단, full validation을 보고 고른 weight이므로 최종 채택 전 clean/fixed validation으로 재확인이 필요하다.
```

---

## 9. 판단 규칙 적용

### Weighted ensemble

```text
weighted ensemble full top1 = 0.900661
previous simple ensemble top1 = 0.899232
delta = +0.1429%p
```

결론:

```text
weighted ensemble은 채택 가능.
```

### 라벨 검수

아직 사람 검수 결과가 없으므로 판단 보류.

검수 후:

```text
wrong_label + ambiguous + multi_food >= 10%:
  cleaned_v1 split 재학습 우선

wrong_label + ambiguous + multi_food < 5%:
  model diversity / ensemble weighting 우선
```

### B2

아직 미실행.

다음 실행 기준:

```text
B2 clean supervised를 ensemble diversity 목적으로 1회 실행한다.
B2 single hflip >= 85% 또는 ensemble 개선 시 B2 fine-tuning 검토.
B2-LeWM은 아직 보류.
```

---

## 10. 다음 액션

우선순위:

1. `review_sheet_top300.csv`를 사람이 검수하고 `reviewed_top300.csv`로 저장한다.
2. `scripts/summarize_label_review.py`로 label noise 비율을 계산한다.
3. label noise가 높으면 cleaned_v1 split을 만든 뒤 B0 supervised-only를 재학습한다.
4. label noise가 낮으면 B0 seed 7 또는 seed 123 학습을 먼저 진행한다.
5. 그 다음 B2 clean supervised를 ensemble diversity 목적으로 진행한다.
6. B2가 현재 weighted ensemble을 개선하면 B2 fine-tuning을 검토한다.
7. B2-LeWM은 마지막 후보로 유지한다.

추천 다음 명령 1:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/error_analysis/final_candidate/reviewed_top300.csv \
  --output-dir reports/error_analysis/final_candidate/review_summary_top300
```

추천 다음 명령 2:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_1000 \
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
  --output data/models/food_lewm_b0_supervised_only_seed7_ft10.pt \
  --classes-output data/models/food_lewm_b0_supervised_only_seed7_classes_ft10.json \
  --metadata-output data/models/food_lewm_b0_supervised_only_seed7_meta_ft10.json \
  --report-dir reports/seed_experiments/b0_supervised_only_seed7_ft10 \
  --log-every 50
```

---

## 11. 결론

다음 단계의 첫 실행 결과, 단순 평균 ensemble 0.899232에서 weighted ensemble 0.900661로 90% 선을 넘겼다.  
다만 split audit에서 `old_train -> new_val` class+filename overlap 4,474건이 확인되어, 현재 수치는 최종 운영 성능으로 확정하기 전에 clean/fixed validation으로 재검증해야 한다.  

가장 중요한 다음 병목은 B2가 아니라 label review와 hard class 정리다. 그 다음에 B0 seed와 B2 clean supervised를 model diversity 목적으로 추가하는 순서가 맞다.
