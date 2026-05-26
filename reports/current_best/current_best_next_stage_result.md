# Current Best Review And Decision Result

작성일: 2026-05-13  
프로젝트: `/Users/sangrok/foodsugar-ai`  
현재 best: B3 continuation 3-model weighted ensemble + hflip

## 1. 현재 Best 요약

```text
3-model weighted ensemble + hflip

Models:
  food_lewm_b0
  b0_seed123_fixed_v1
  b3_cont_fixed_v1

Weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

Metrics:
  top1     = 0.913095
  top3     = 0.979613
  macro_f1 = 0.912846
```

이전 best 대비:

```text
previous top1 = 0.900149
current top1  = 0.913095
improvement   = +0.012946
```

목표까지 남은 gap:

```text
92%까지 = 0.006905
94%까지 = 0.026905
```

## 2. 이번 단계에서 수행한 작업

### 2.1 Preflight

확인 완료:

```text
data/raw/korean_food_fixed_v1/train exists
data/raw/korean_food_fixed_v1/val exists
current best checkpoints exist
reports/current_best/fixed_weight_3model_hflip exists
error analysis exists
review templates exist
classes = 56
train = 49,243
val = 6,720
```

### 2.2 Human review 입력 상태 확인

아직 사람이 검수한 완료본은 없다.

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
  missing

reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
  missing
```

따라서 아래 작업은 실행하지 않았다.

```text
high-confidence review summary
train hard-pair patch 생성
patch impact audit
cleaned_train_v1 생성
B3 full 25epoch
```

### 2.3 Train hard-pair 후보 보정

점검 중 `reports/current_best/hard_class_report/train_hard_review_candidates.csv`가 header만 있는 상태임을 발견했다.

조치:

```text
reports/current_best/hard_class_report/hard_classes.csv 재생성
reports/current_best/hard_class_report/hard_pairs.csv 재생성
reports/current_best/hard_class_report/train_hard_review_candidates.csv 재생성
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv 재생성
reports/current_best/hard_class_report/train_contact_sheets/ 재생성
```

보정 후 상태:

```text
hard_classes.csv                       19 lines including header
hard_pairs.csv                         31 lines including header
train_hard_review_candidates.csv       301 lines including header
reviewed_train_hard_pair_candidates_TEMPLATE.csv 301 lines including header
train_contact_sheets                   12 sheets
```

### 2.4 Human review next action 문서 작성

생성:

```text
reports/current_best/HUMAN_REVIEW_NEXT_ACTIONS.md
```

포함 내용:

```text
1. 어떤 CSV를 채워야 하는지
2. 어떤 contact sheets를 봐야 하는지
3. review_status / action 값 설명
4. 완료 후 저장할 파일명
5. 완료 후 Codex가 실행할 명령
6. 다음 분기 기준
```

### 2.5 스크립트 호환 보강

수정:

```text
scripts/build_kfood_label_patch.py
scripts/summarize_label_review.py
```

변경 내용:

```text
build_kfood_label_patch.py:
  true_label뿐 아니라 current_label도 old_label로 인식하도록 보강.
  class_definition_overlap도 remove 계열로 처리.

summarize_label_review.py:
  bad_crop, class_definition_overlap, unclear를 noisy status에 포함.
  review_counts.json 출력 추가.
  wrong_label_cases.csv 출력 추가.
  ambiguous_cases.csv 출력 추가.
  remove_candidates.csv 출력 추가.
  class_definition_overlap_cases.csv 출력 추가.
  label_audit_summary.md 출력 추가.
```

목적:

```text
사람 검수 완료 후 high-conf review와 train hard-pair review를 같은 흐름으로 안전하게 처리하기 위함.
```

### 2.6 Safe runner 작성

생성:

```text
scripts/run_current_best_review_and_decision.py
```

역할:

```text
1. high-conf reviewed 파일이 있으면 summary 실행
2. train reviewed 파일이 있으면 patch / exclude 생성
3. patch 생성 시 impact audit 실행
4. 현재 decision 상태를 JSON/MD로 기록
```

안전 제한:

```text
B3 full training은 자동 실행하지 않음.
cleaned_train_v1도 자동 생성하지 않음.
사람 검수 파일이 없으면 waiting_for_human_review로 멈춤.
```

실행 결과:

```text
reports/current_best/review_and_decision_status.md
reports/current_best/review_and_decision_status.json
```

현재 상태:

```text
decision = waiting_for_human_review
high_conf_review_exists = false
train_review_exists = false
```

## 3. 현재 검수 대상

### 3.1 High-confidence top300

검수할 이미지:

```text
reports/current_best/error_analysis/contact_sheets_top300/
```

작성할 템플릿:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
```

완료 후 저장:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

### 3.2 Train hard-pair candidates

검수할 이미지:

```text
reports/current_best/hard_class_report/train_contact_sheets/
```

작성할 템플릿:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
```

완료 후 저장:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

### 3.3 검수 기준

기준 문서:

```text
reports/current_best/hard_pair_class_definition.md
reports/current_best/HUMAN_REVIEW_NEXT_ACTIONS.md
```

review_status:

```text
model_error
correct
wrong_label
ambiguous
multi_food
bad_crop
class_definition_overlap
unclear
```

action:

```text
keep
relabel
remove
needs_class_definition
needs_more_data
```

## 4. 분기 판단

현재는 사람 검수 전이므로 확정 분기 불가.

현재 provisional 판단:

```text
남은 오류는 model capacity 단독 문제보다
class boundary / label ambiguity / crop ambiguity 성격이 강함.
```

검수 후 분기:

```text
label_boundary_noise >= 20%:
  hard-pair cleaning 우선

label_boundary_noise 10~20%:
  cleaning과 B3 full 분리 실험

label_boundary_noise < 10% and model_error majority:
  B3 full 25epoch 검토
```

train patch 기준:

```text
train affected >= 300:
  cleaned_train_v1 생성 가치 높음

train affected 100~300:
  B0 seed123 1회 재학습으로 확인 가능

train affected < 100:
  cleaning 효과 제한적
```

## 5. B3 Full 25epoch 여부

현재 결정:

```text
B3 full 25epoch는 보류.
```

이유:

```text
1. 사람 검수 완료본이 아직 없음.
2. high-confidence error의 label/class-boundary 비율을 아직 계산할 수 없음.
3. train hard-pair patch 규모도 아직 계산할 수 없음.
4. current best는 이미 91.31%까지 올라왔고 plus4/fivefold는 하락했음.
5. 장시간 full run은 검수 결과 이후 결정하는 것이 안전함.
```

## 6. 현재 운영 후보

운영 후보는 유지한다.

```text
3-model weighted ensemble + hflip

Models:
  data/models/food_lewm_b0_classifier_3ep_ft10.pt
  data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
  data/models/efficientnet_korean_b3_cont_fixed_v1.pt

Weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

Metrics:
  top1     = 0.913095
  top3     = 0.979613
  macro_f1 = 0.912846
```

운영화 전 남은 작업:

```text
1. ensemble inference wrapper
2. model metadata 통합
3. class order 검증
4. single B3 vs 3-model ensemble latency benchmark
5. memory benchmark
6. API /predict end-to-end test
7. rollback path 정리
```

## 7. 다음 액션

사람이 먼저 할 일:

```text
1. reports/current_best/error_analysis/contact_sheets_top300/ 확인
2. reviewed_current_best_high_conf_top300_TEMPLATE.csv 작성
3. reviewed_current_best_high_conf_top300.csv로 저장
4. reports/current_best/hard_class_report/train_contact_sheets/ 확인
5. reviewed_train_hard_pair_candidates_TEMPLATE.csv 작성
6. reviewed_train_hard_pair_candidates.csv로 저장
```

그 다음 Codex가 할 일:

```bash
python3 scripts/run_current_best_review_and_decision.py \
  --summarize-if-available \
  --build-patch-if-available
```

이후:

```text
1. label_boundary_noise 계산
2. patch impact audit 확인
3. cleaned_train_v1 vs B3 full 분기 결정
4. 필요 시 cleaned_train_v1 생성 또는 B3 full 장시간 실험
```

## 8. 검증

실행 완료:

```bash
python3 -m py_compile scripts/analyze_kfood_errors.py scripts/eval_fixed_weight_ensemble.py scripts/build_hard_class_report.py scripts/prepare_label_review_sheet.py scripts/build_label_review_contact_sheets.py scripts/build_train_hard_review_sheet.py scripts/summarize_label_review.py scripts/build_kfood_label_patch.py scripts/audit_label_patch_impact.py scripts/run_current_best_review_and_decision.py
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

현재 실행 중인 학습/평가 프로세스:

```text
없음
```
