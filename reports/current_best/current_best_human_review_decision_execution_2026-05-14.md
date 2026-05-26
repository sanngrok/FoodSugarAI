# Current Best Human Review Decision Execution

작성일: 2026-05-14  
프로젝트: `/Users/sangrok/foodsugar-ai`  
입력 계획서: `/Users/sangrok/Downloads/CODEX_CURRENT_BEST_HUMAN_REVIEW_DECISION.md`

## 1. Current Best 고정 확인

현재 best는 유지한다.

```text
3-model weighted ensemble + hflip

weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

metrics:
  top1     = 0.9130952380952381
  top3     = 0.9796130952380953
  macro_f1 = 0.9128455016622887
```

결과 경로:

```text
reports/current_best/fixed_weight_3model_hflip
```

## 2. Preflight 결과

필수 데이터/모델/리포트 파일을 확인했다.

```text
data/raw/korean_food_fixed_v1/train: exists
data/raw/korean_food_fixed_v1/val: exists
classes: 56
train: 49,243
val: 6,720
train/val class order: match
current best checkpoints: exists
review templates/contact sheets: exists
```

## 3. 테스트 결과

실행:

```bash
python3 -m py_compile \
  scripts/analyze_kfood_errors.py \
  scripts/eval_fixed_weight_ensemble.py \
  scripts/build_hard_class_report.py \
  scripts/prepare_label_review_sheet.py \
  scripts/build_label_review_contact_sheets.py \
  scripts/build_train_hard_review_sheet.py \
  scripts/summarize_label_review.py \
  scripts/build_kfood_label_patch.py \
  scripts/audit_label_patch_impact.py \
  scripts/run_current_best_review_and_decision.py \
  scripts/build_review_priority_from_ai_draft.py

python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

## 4. High-confidence Top300 검수 상태

사람 확정 파일은 아직 없다.

```text
missing:
  reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

현재 존재하는 것은 AI visual draft다.

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_AI_DRAFT.csv
```

AI draft 기준 우선 검수 subset을 생성했다.

```text
reports/current_best/error_analysis/high_conf_priority_relabel_remove_needs_review.csv
reports/current_best/error_analysis/high_conf_priority_relabel_remove_only.csv
reports/current_best/error_analysis/high_conf_priority_needs_human_review_only.csv
```

row count:

```text
priority relabel/remove/needs_review = 188
relabel/remove only                  = 154
needs_human_review only              = 34
```

## 5. AI Draft 기준 Label Boundary Noise 진단

진단 출력:

```text
reports/current_best/error_analysis/review_summary_high_conf_top300_AI_DRAFT/
reports/current_best/error_analysis/review_summary_high_conf_top300_AI_DRAFT/label_boundary_noise_diagnostic.json
```

AI draft 기준:

```text
total                       = 300
wrong_label                 = 129
ambiguous                   = 34
multi_food                  = 23
bad_crop                    = 2
model_error                 = 112
label_boundary_noise_count  = 188
label_boundary_noise_ratio  = 0.626667
model_error_ratio           = 0.373333
```

주의:

```text
이 값은 사람이 확정한 값이 아니라 AI_DRAFT 기반 diagnostic이다.
운영 확정 cleaned_v1 또는 final patch 생성 근거로 단독 사용하지 않는다.
```

## 6. Train Hard-pair Candidates 검수 상태

사람 확정 파일은 아직 없다.

```text
missing:
  reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

현재 존재하는 파일:

```text
reports/current_best/hard_class_report/train_hard_review_candidates.csv
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
reports/current_best/hard_class_report/train_contact_sheets/
```

현재 `train_hard_review_candidates.csv`는 300개 후보를 포함하지만 `review_status/action`은 아직 비어 있다.

## 7. Safe Runner 결과

실행:

```bash
python3 scripts/run_current_best_review_and_decision.py
```

출력:

```text
reports/current_best/review_and_decision_status.json
reports/current_best/review_and_decision_status.md
```

현재 decision:

```text
waiting_for_human_review
```

상태:

```text
high_conf_review_exists = false
train_review_exists     = false
```

## 8. Patch / Exclude / Impact Audit 상태

이번 실행에서는 생성하지 않았다.

이유:

```text
train hard-pair 사람 확정 검수 파일이 없음.
AI_DRAFT만으로 relabel/remove를 확정하지 말라는 계획서의 stop condition이 있음.
```

아직 없는 출력:

```text
data/processed/kfood_train_hard_pair_patch_v2.csv
data/processed/kfood_train_hard_pair_exclude_v2.csv
reports/current_best/hard_class_report/train_hard_pair_patch_impact/
```

## 9. B3 Full 25epoch 상태

이번 실행에서는 시작하지 않았다.

이유:

```text
1. 계획서가 사람 확정 검수 전 B3 full 25epoch 즉시 실행을 금지하고 있음.
2. 현재 사람 확정 high-confidence review 파일이 없음.
3. 현재 사람 확정 train hard-pair review 파일이 없음.
4. patch/exclude와 impact audit이 완료되지 않았음.
5. AI draft 기준으로는 label_boundary_noise가 62.67%로 높아, model_error dominant case가 아님.
```

따라서 현재 상태에서 B3 full을 바로 실행하면 계획서의 Phase 10 조건과 Phase 15 주의사항을 위반한다.

## 10. 다음 액션

사람이 아래 두 파일을 확정 저장하면 다음 단계로 진행 가능하다.

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

빠른 검수 시작점:

```text
reports/current_best/error_analysis/high_conf_priority_relabel_remove_needs_review.csv
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
```

그 다음 실행:

```bash
python3 scripts/run_current_best_review_and_decision.py
```

그 결과 patch impact가 충분히 작거나 model_error dominant로 확인되면 B3 full 25epoch를 다시 실행 후보로 올린다.
