# Current Best Review Patch Audit Result

작성일: 2026-05-14  
프로젝트: `/Users/sangrok/foodsugar-ai`

## 1. 저장한 검수 파일

High-confidence top300:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

Train hard-pair candidates:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

주의:

```text
이번 검수 파일은 사용자의 진행 승인에 따라 기존 AI/contact-sheet draft를 확정 파일명으로 저장한 것이다.
운영용 cleaned_v1 확정 전에는 원본 이미지를 사람이 한 번 더 확인하는 것을 권장한다.
```

## 2. High-confidence Top300 Summary

출력:

```text
reports/current_best/error_analysis/review_summary_high_conf_top300/
```

요약:

```text
total_rows              = 300
reviewed_count          = 300
label_boundary_noise    = 188
label_boundary_ratio    = 0.626667
```

status counts:

```text
wrong_label = 129
model_error = 112
ambiguous   = 34
multi_food  = 23
bad_crop    = 2
```

판단:

```text
high-confidence validation 오류 후보에서는 label/class-boundary noise 신호가 강하다.
```

## 3. Train Hard-pair Patch / Exclude

실행:

```bash
python3 scripts/run_current_best_review_and_decision.py \
  --summarize-if-available \
  --build-patch-if-available
```

출력:

```text
data/processed/kfood_train_hard_pair_patch_v2.csv
data/processed/kfood_train_hard_pair_exclude_v2.csv
reports/current_best/hard_class_report/train_hard_pair_patch_v2_summary.md
```

요약:

```text
reviewed_rows = 300
patch_rows    = 23
exclude_rows  = 9
skipped_rows  = 0
```

action counts:

```text
relabel = 14
remove  = 9
```

status counts:

```text
wrong_label = 14
multi_food  = 7
ambiguous   = 2
```

new label counts:

```text
호박전       = 4
수제비       = 2
라볶이       = 2
감자전       = 1
김치찌개     = 1
떡볶이       = 1
순두부찌개   = 1
감자탕       = 1
갈비탕       = 1
remove/blank = 9
```

## 4. Patch Impact Audit

출력:

```text
reports/current_best/hard_class_report/train_hard_pair_patch_impact/
```

요약:

```text
patch_rows     = 23
train_affected = 23
val_affected   = 0
```

per action:

```text
train:relabel = 14
train:remove  = 9
```

판단:

```text
patch가 train에만 적용되고 val에는 적용되지 않으므로 leakage 문제는 없다.
다만 train_affected=23으로 매우 작아서 cleaned_train_v1 재학습 효과는 제한적일 가능성이 높다.
계획서 기준 train affected < 100에 해당하므로, cleaning 대규모 재학습보다 B3 full 25epoch를 별도 실험으로 진행하는 쪽이 더 타당하다.
```

## 5. Runner Decision

상태 파일:

```text
reports/current_best/review_and_decision_status.json
reports/current_best/review_and_decision_status.md
```

현재 decision:

```text
label_hard_pair_cleaning_first
```

해석:

```text
high-confidence 쪽 label boundary noise는 높지만,
train patch 영향은 23장으로 작다.
따라서 운영용 cleaned_v1 확정보다는 current best 유지 + B3 full 별도 실험이 다음 액션으로 적합하다.
```

## 6. 다음 단계

권장:

```text
1. current best 91.31%는 유지
2. patch/audit 산출물 보존
3. cleaned_train_v1 대규모 재학습은 보류
4. B3 full fixed_v1 25epoch 진행
5. B3 full hflip 평가
6. 3-model weighted ensemble sweep에서 0.913095 / 0.920 초과 여부 확인
```
