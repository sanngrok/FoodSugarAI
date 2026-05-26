# Human Review Next Actions

작성일: 2026-05-13  
상태: `waiting_for_human_review`

## 1. 지금 채워야 할 파일

### A. High-confidence top300 검수

이미지로 확인할 contact sheet:

```text
reports/current_best/error_analysis/contact_sheets_top300/
```

작성 시작 파일:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
```

작성 완료 후 저장할 파일명:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

필수 컬럼:

```text
image_path
true_label
pred_label
confidence
review_status
corrected_label
action
review_note
```

### B. Train hard-pair 후보 검수

이미지로 확인할 contact sheet:

```text
reports/current_best/hard_class_report/train_contact_sheets/
```

작성 시작 파일:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
```

작성 완료 후 저장할 파일명:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

필수 컬럼:

```text
image_path
current_label
candidate_label
review_status
corrected_label
action
review_note
```

## 2. 기준 문서

검수 전에 아래 문서를 먼저 본다.

```text
reports/current_best/hard_pair_class_definition.md
```

## 3. review_status 값

High-confidence top300:

```text
model_error
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
unclear
```

Train hard-pair:

```text
correct
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
unclear
```

## 4. action 값

```text
keep
relabel
remove
needs_class_definition
needs_more_data
```

## 5. 빠른 판단 기준

```text
model_error:
  라벨은 맞고 모델이 틀림. action=keep.

wrong_label:
  라벨이 명확히 틀림. corrected_label을 채우고 action=relabel.

ambiguous:
  사람이 봐도 애매함. action=needs_class_definition 또는 remove.

multi_food:
  여러 음식이 같이 있어 대표 라벨이 애매함. action=remove 또는 needs_class_definition.

bad_crop:
  음식이 작거나 핵심 단서가 가림. action=remove.

class_definition_overlap:
  클래스 기준 자체가 겹침. action=needs_class_definition.

unclear:
  판단 불가. action=remove 또는 needs_more_data.
```

## 6. 검수 완료 후 Codex가 실행할 명령

High-confidence 검수 요약:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv \
  --output-dir reports/current_best/error_analysis/review_summary_high_conf_top300
```

Train hard-pair patch 생성:

```bash
python3 scripts/build_kfood_label_patch.py \
  --reviewed reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv \
  --patch-output data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude-output data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --report-output reports/current_best/hard_class_report/train_hard_pair_patch_v2_summary.md
```

Patch impact audit:

```bash
python3 scripts/audit_label_patch_impact.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --patch data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --output-dir reports/current_best/hard_class_report/train_hard_pair_patch_impact
```

## 7. 분기 기준

```text
label_boundary_noise >= 20%:
  hard-pair cleaning 우선.

label_boundary_noise 10~20%:
  cleaning과 B3 full 분리 실험.

label_boundary_noise < 10% and model_error majority:
  B3 full 25epoch 검토.
```

