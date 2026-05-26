# K-Food Current Best 91.31% 이후 진행상황

작성일: 2026-05-13  
프로젝트 경로: `/Users/sangrok/foodsugar-ai`  
기준 데이터셋: `data/raw/korean_food_fixed_v1`  
현재 최고 후보: B3 continuation 3-model weighted ensemble + hflip

## 1. 현재 결론

현재 최고 성능은 아래 조합이다.

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
Previous best top1 = 0.900149
Current best top1  = 0.913095
Improvement        = +0.012946
```

목표까지 남은 gap:

```text
92%까지 = 0.006905
94%까지 = 0.026905
```

현재 판단:

```text
B3 continuation은 성공.
fivefold TTA는 실패.
plus4 추가 fine-tuning도 실패 신호.
B3 full 25epoch는 검수 전까지 보류.
다음 핵심은 high-confidence error / hard-pair 사람 검수.
```

## 2. 이번 단계에서 완료한 작업

### 2.1 Current best 표준 경로 고정

기존 `reports/b3/...`에 있던 current best를 플랜 기준 표준 경로인 `reports/current_best/...` 아래에 다시 재현했다.

출력:

```text
reports/current_best/fixed_weight_3model_hflip
```

결과:

```text
top1     = 0.913095
top3     = 0.979613
macro_f1 = 0.912846
```

검증:

```text
기존 B3 continuation ensemble 결과와 동일하게 재현됨.
class order / checkpoint / metadata / TTA / weight normalization 문제 없음.
```

### 2.2 Current best 오류 분석 생성

출력:

```text
reports/current_best/error_analysis
```

생성 파일:

```text
low_f1_classes.csv
low_recall_classes.csv
low_precision_classes.csv
top_confusion_pairs.csv
high_confidence_errors_top300.csv
current_best_high_conf_review_top300.csv
reviewed_current_best_high_conf_top300_TEMPLATE.csv
contact_sheets_top300/
hard_class_delta_summary.csv
README.md
```

핵심 low-F1 class:

| Class | F1 | Precision | Recall |
|---|---:|---:|---:|
| 곰탕_설렁탕 | 0.801762 | 0.850467 | 0.758333 |
| 닭볶음탕 | 0.824034 | 0.849558 | 0.800000 |
| 삼겹살 | 0.828194 | 0.878505 | 0.783333 |
| 갈비구이 | 0.829694 | 0.871560 | 0.791667 |
| 동태찌개 | 0.837398 | 0.817460 | 0.858333 |
| 김치찌개 | 0.842975 | 0.836066 | 0.850000 |
| 수제비 | 0.863071 | 0.859504 | 0.866667 |
| 닭계장 | 0.869198 | 0.880342 | 0.858333 |
| 감자전 | 0.872881 | 0.887931 | 0.858333 |
| 칼국수 | 0.873950 | 0.881356 | 0.866667 |

핵심 confusion pair:

| True | Pred | Count |
|---|---|---:|
| 감자전 | 호박전 | 12 |
| 곰탕_설렁탕 | 갈비탕 | 9 |
| 김치찜 | 김치찌개 | 8 |
| 칼국수 | 수제비 | 8 |
| 곰탕_설렁탕 | 삼계탕 | 7 |
| 떡볶이 | 라볶이 | 7 |
| 호박전 | 감자전 | 7 |
| 갈비찜 | 닭볶음탕 | 6 |
| 김치찌개 | 동태찌개 | 6 |
| 물냉면 | 비빔냉면 | 6 |
| 순두부찌개 | 김치찌개 | 6 |
| 양념치킨 | 후라이드치킨 | 6 |

해석:

```text
남은 오류는 model capacity 단독 문제라기보다
class boundary / label ambiguity / crop ambiguity 성격이 강함.
```

### 2.3 High-confidence error top300 검수 자료 생성

검수 대상 CSV:

```text
reports/current_best/error_analysis/current_best_high_conf_review_top300.csv
```

사람 검수용 템플릿:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
```

Contact sheets:

```text
reports/current_best/error_analysis/contact_sheets_top300/
```

검수 완료 후 저장해야 할 파일:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

### 2.4 Hard-pair class definition 작성

검수 기준 문서:

```text
reports/current_best/hard_pair_class_definition.md
```

포함한 주요 pair:

```text
곰탕_설렁탕 vs 갈비탕 / 삼계탕
김치찌개 vs 동태찌개 vs 순두부찌개 vs 된장찌개
감자전 vs 호박전 vs 파전
칼국수 vs 수제비
갈비구이 vs 갈비찜 vs 삼겹살
물냉면 vs 비빔냉면
떡볶이 vs 라볶이
양념치킨 vs 후라이드치킨
족발 vs 보쌈
```

목적:

```text
검수자가 이미지별로 wrong_label / ambiguous / model_error를 일관되게 판단할 수 있게 기준 고정.
```

### 2.5 Train hard-pair review 자료 생성

출력:

```text
reports/current_best/hard_class_report
```

생성 파일:

```text
hard_classes.csv
hard_pairs.csv
train_hard_review_candidates.csv
reviewed_train_hard_pair_candidates_TEMPLATE.csv
train_contact_sheets/
train_hard_review_candidates.md
README.md
```

검수 완료 후 저장해야 할 파일:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

### 2.6 Human review guide 작성

검수 안내 문서:

```text
reports/current_best/HUMAN_REVIEW_GUIDE.md
```

포함 내용:

```text
1. 검수 대상 파일
2. 검수 후 저장할 파일명
3. review_status 기준
4. action 기준
5. 검수 완료 후 실행할 summary / patch / impact audit 명령
```

### 2.7 최종 리포트 작성

이번 단계의 결과 리포트:

```text
reports/current_best/current_best_next_steps_result.md
```

## 3. 아직 실행하지 않은 작업

아래 작업은 사람 검수 결과가 필요해서 아직 실행하지 않았다.

### 3.1 High-confidence review summary

대기 중인 입력:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

입력이 생기면 실행:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv \
  --output-dir reports/current_best/error_analysis/review_summary_high_conf_top300
```

### 3.2 Train hard-pair patch 생성

대기 중인 입력:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

입력이 생기면 실행:

```bash
python3 scripts/build_kfood_label_patch.py \
  --reviewed reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv \
  --patch-output data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude-output data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --report-output reports/current_best/hard_class_report/train_hard_pair_patch_v2_summary.md
```

### 3.3 Patch impact audit

patch/exclude 생성 후 실행:

```bash
python3 scripts/audit_label_patch_impact.py \
  --data-dir data/raw/korean_food_fixed_v1 \
  --patch data/processed/kfood_train_hard_pair_patch_v2.csv \
  --exclude data/processed/kfood_train_hard_pair_exclude_v2.csv \
  --output-dir reports/current_best/hard_class_report/train_hard_pair_patch_impact
```

### 3.4 B3 full 25epoch

현재는 보류.

실행 조건:

```text
high-confidence top300 검수 결과 model_error 비율이 높고,
wrong_label / ambiguous / multi_food / bad_crop / class_definition_overlap 비율이 낮을 때.
```

## 4. 현재 B3 Full 보류 이유

```text
1. B3 continuation은 이미 91.31% current best를 달성했다.
2. fivefold TTA는 0.907292로 하락했다.
3. plus4 추가 fine-tuning도 0.891220으로 하락 신호였다.
4. 남은 오류가 감자전↔호박전, 곰탕_설렁탕↔갈비탕/삼계탕,
   칼국수↔수제비, 김치찌개↔동태찌개 같은 hard-pair에 집중되어 있다.
5. 사람 검수 없이 full 25epoch를 돌리면 장시간 비용 대비 근거가 약하다.
```

## 5. 다음 분기 기준

### Case A. Label / class boundary 문제가 많음

조건:

```text
reviewed high-conf top300에서
wrong_label + ambiguous + multi_food + bad_crop + class_definition_overlap >= 20%
```

진행:

```text
1. hard-pair cleaning 우선
2. train patch / exclude 생성
3. patch impact audit
4. cleaned_train_v1 생성 여부 결정
5. B0 seed123 / seed7 재학습 검토
6. current best ensemble 재평가
```

### Case B. Model error가 대부분임

조건:

```text
model_error가 대부분이고
label/class-boundary noise < 10%
```

진행:

```text
1. B3 full 25epoch 장시간 실험
2. B3 full hflip 평가
3. B3 full 3-model ensemble 평가
4. 0.913095 초과 또는 0.920 달성 여부 확인
```

### Case C. 혼합형

조건:

```text
label 문제와 model error가 모두 의미 있게 존재
```

진행:

```text
1. current best 유지
2. 검수/cleaning과 B3 full을 분리 실험으로 관리
3. patch 규모가 충분할 때 cleaned_train_v1 재학습
4. 장시간 여유가 있을 때 B3 full 별도 진행
```

## 6. 현재 운영 후보

연구 성능 기준 운영 후보:

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
4. latency benchmark
5. memory benchmark
6. API /predict end-to-end test
7. rollback path 정리
```

## 7. 보호 대상 파일

절대 덮어쓰지 않는다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt

data/models/food_lewm_b0_classifier_3ep_ft10.pt
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
data/models/efficientnet_korean_b3_probe_fixed_v1.pt
data/models/efficientnet_korean_b3_cont_fixed_v1.pt
data/models/korean_food_classes_b3_cont_fixed_v1.json
data/models/korean_food_model_meta_b3_cont_fixed_v1.json
```

## 8. 검증

마지막 실행:

```bash
python3 -m py_compile scripts/analyze_kfood_errors.py scripts/eval_fixed_weight_ensemble.py scripts/build_hard_class_report.py scripts/prepare_label_review_sheet.py scripts/build_label_review_contact_sheets.py scripts/build_train_hard_review_sheet.py scripts/summarize_label_review.py scripts/build_kfood_label_patch.py scripts/audit_label_patch_impact.py
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

## 9. 바로 다음 액션

사람이 해야 할 것:

```text
1. reports/current_best/error_analysis/contact_sheets_top300/ 확인
2. reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv 작성
3. 작성 완료본을 reviewed_current_best_high_conf_top300.csv로 저장
4. reports/current_best/hard_class_report/train_contact_sheets/ 확인
5. reviewed_train_hard_pair_candidates_TEMPLATE.csv 작성
6. 작성 완료본을 reviewed_train_hard_pair_candidates.csv로 저장
```

Codex가 다음에 할 것:

```text
1. high-conf 검수 요약
2. label/class-boundary noise 비율 계산
3. train hard-pair patch 생성
4. patch impact audit
5. B3 full vs cleaning 분기 결정
```

