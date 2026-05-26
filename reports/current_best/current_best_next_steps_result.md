# Current Best 91.31% Next Steps Result

작성일: 2026-05-13  
프로젝트: `/Users/sangrok/foodsugar-ai`  
기준 데이터셋: `data/raw/korean_food_fixed_v1`  
현재 best: B3 continuation 3-model weighted ensemble + hflip

## 1. 현재 Best 고정

플랜의 표준 출력 경로로 current best를 재현했다.

```text
output:
  reports/current_best/fixed_weight_3model_hflip

models:
  food_lewm_b0
  b0_seed123_fixed_v1
  b3_cont_fixed_v1

weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

tta:
  hflip
```

결과:

```text
top1     = 0.913095
top3     = 0.979613
macro_f1 = 0.912846
```

이전 best 재현값:

```text
previous best:
  top1     = 0.900149
  top3     = 0.974405
  macro_f1 = 0.899900
```

개선폭:

```text
top1 +0.012946
```

## 2. 성능표

| Experiment | Data | TTA | Top1 | Top3 | Macro-F1 | Decision |
|---|---|---|---:|---:|---:|---|
| Previous best | fixed_v1 | hflip | 0.900149 | 0.974405 | 0.899900 | baseline |
| B3 probe ensemble | fixed_v1 | hflip | 0.911310 | 0.976488 | 0.911089 | improved |
| B3 continuation single | fixed_v1 | hflip | 0.895982 | 0.974107 | 0.895791 | valid |
| B3 continuation ensemble | fixed_v1 | hflip | 0.913095 | 0.979613 | 0.912846 | current best |
| B3 continuation fivefold | fixed_v1 | fivefold | 0.907292 | 0.979018 | 0.907179 | rejected |
| B3 cont plus4 | fixed_v1 | none | 0.891220 | 0.971577 | 0.890778 | rejected |
| B3 full ensemble | fixed_v1 | hflip | TBD | TBD | TBD | deferred |

92%까지 남은 gap:

```text
0.920000 - 0.913095 = 0.006905
```

94%까지 남은 gap:

```text
0.940000 - 0.913095 = 0.026905
```

## 3. 오류 분석

표준 출력 경로:

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

Low-F1 상위 class:

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

주요 confusion pair:

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

판단:

```text
남은 오류는 model capacity 단독 문제보다 class boundary / label ambiguity 성격이 강하다.
```

## 4. High-Confidence Error 검수 준비

검수 입력:

```text
reports/current_best/error_analysis/current_best_high_conf_review_top300.csv
reports/current_best/error_analysis/contact_sheets_top300/
```

사람 검수용 템플릿:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
```

검수 완료 후 저장할 파일:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
```

검수 status:

```text
model_error
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

현재는 사람이 검수한 파일이 아직 없으므로 review summary는 실행하지 않았다.

## 5. Hard Pair Class Definition

작성 완료:

```text
reports/current_best/hard_pair_class_definition.md
```

포함한 pair:

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

용도:

```text
high-confidence top300 검수와 train hard-pair 검수 기준 통일.
```

## 6. Train Hard-Pair Review 준비

출력 경로:

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

검수 완료 후 저장할 파일:

```text
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
```

현재는 사람이 검수한 파일이 아직 없으므로 patch 생성과 impact audit은 실행하지 않았다.

## 7. B3 Full Run 여부

현재 결정:

```text
B3 full 25epoch는 즉시 실행하지 않고 보류.
```

보류 이유:

```text
1. B3 continuation은 이미 current best까지 개선했다.
2. fivefold TTA는 악화됐다.
3. plus4 low-lr fine-tuning도 악화 신호였다.
4. current best의 남은 오류가 hard-pair / class-boundary 문제에 집중되어 있다.
5. high-confidence top300 검수 결과 없이 full run을 돌리면 장시간 비용 대비 판단 근거가 약하다.
```

B3 full run을 다시 고려할 조건:

```text
reviewed high-conf top300에서 model_error가 대부분이고,
wrong_label + ambiguous + multi_food + bad_crop + class_definition_overlap 비율이 낮을 때.
```

## 8. 운영 후보

현재 연구 성능 기준 운영 후보:

```text
3-model weighted ensemble + hflip

models:
  data/models/food_lewm_b0_classifier_3ep_ft10.pt
  data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
  data/models/efficientnet_korean_b3_cont_fixed_v1.pt

weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

metrics:
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

## 9. Human Review Guide

생성 완료:

```text
reports/current_best/HUMAN_REVIEW_GUIDE.md
```

이 파일에는 검수 대상, 저장할 reviewed 파일명, status/action 기준, 검수 후 실행할 요약/patch/audit 명령을 정리했다.

## 10. 다음 액션

사람 검수 필요:

```text
1. reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
   를 복사/수정해 reviewed_current_best_high_conf_top300.csv로 저장

2. reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
   를 복사/수정해 reviewed_train_hard_pair_candidates.csv로 저장
```

검수 후 자동 실행:

```text
1. high-conf review summary
2. train hard-pair patch 생성
3. patch impact audit
4. label/hard-pair cleaning 우선인지 B3 full run 우선인지 재판단
```

## 11. 최종 결론

```text
현재 최고 정확도는 91.31%다.
B3 continuation은 성공했고, current best는 표준 경로에 고정 재현했다.
fivefold TTA와 plus4 fine-tuning은 실패했으므로 제외한다.
남은 0.69%p는 무작정 추가 학습보다 high-confidence error와 hard-pair 검수가 먼저다.
B3 full 25epoch는 검수 결과가 나오기 전까지 보류한다.
```

