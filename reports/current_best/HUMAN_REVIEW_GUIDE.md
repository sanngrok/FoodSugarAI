# Current Best Human Review Guide

작성일: 2026-05-13

## 검수 대상

1. High-confidence validation error review

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
reports/current_best/error_analysis/contact_sheets_top300/
```

검수 완료 후 저장할 파일:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

2. Train hard-pair review

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
reports/current_best/hard_class_report/train_contact_sheets/
```

검수 완료 후 저장할 파일:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

## 기준 문서

검수 전 아래 문서를 먼저 본다.

```text
reports/current_best/hard_pair_class_definition.md
```

## review_status 값

High-confidence validation review:

```text
model_error
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
unclear
```

Train hard-pair review:

```text
correct
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
```

## action 값

```text
keep
relabel
remove
needs_class_definition
needs_more_data
```

## 검수 판단

model_error:

- 현재 라벨은 맞다.
- 모델 예측이 틀렸다.
- action은 보통 `keep`.

wrong_label:

- 현재 라벨이 명확히 틀렸다.
- corrected_label을 채운다.
- action은 `relabel`.

ambiguous:

- 사람이 봐도 두 클래스 사이가 애매하다.
- action은 `needs_class_definition` 또는 `remove`.

multi_food:

- 여러 음식이 함께 있고 대표 라벨이 애매하다.
- action은 `remove` 또는 `needs_class_definition`.

bad_crop:

- 음식이 너무 작거나 핵심 단서가 가려졌다.
- action은 `remove`.

class_definition_overlap:

- 클래스 정의 자체가 겹쳐서 한 이미지에 대해 일관된 결정이 어렵다.
- action은 `needs_class_definition`.

unclear:

- 이미지 품질/맥락상 판단이 불가능하다.
- action은 `remove` 또는 `needs_more_data`.

## 다음 자동 처리

검수 완료 파일이 생기면 다음을 실행한다.

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv \
  --output-dir reports/current_best/error_analysis/review_summary_high_conf_top300
```

train hard-pair review가 완료되면 patch 후보를 만든다.

```bash
python3 scripts/build_kfood_label_patch.py \
  --reviewed reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv \
  --patch-output data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude-output data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --report-output reports/current_best/hard_class_report/train_hard_pair_patch_v2_summary.md
```

이후 impact audit:

```bash
python3 scripts/audit_label_patch_impact.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --patch data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --output-dir reports/current_best/hard_class_report/train_hard_pair_patch_impact
```

