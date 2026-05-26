# K-Food Current Progress GPT Validation Brief

작성일: 2026-05-14  
프로젝트 경로: `/Users/sangrok/foodsugar-ai`  
목적: 현재까지의 K-Food 56-class 분류 실험 진행 상황을 외부 GPT에게 검증받기 위한 브리프

## 1. 한 줄 결론

현재 최고 성능은 `fixed_v1` validation 기준 **B3 continuation 3-model weighted ensemble + hflip**이며, `top1=0.913095`까지 도달했다.  
다만 92%까지 남은 gap은 약 `0.006905`이고, 남은 오류가 label noise / class boundary / hard pair 성격이 강해서 **B3 full 장기학습보다 검수와 cleaning 판단이 우선**인 상태다.

## 2. 현재 Best

기준 데이터셋:

```text
/Users/sangrok/foodsugar-ai/data/raw/korean_food_fixed_v1
```

validation split:

```text
val
```

현재 best 결과 경로:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/fixed_weight_3model_hflip
```

모델 구성:

| Name | Checkpoint | Model | Image Size | Weight |
|---|---|---:|---:|---:|
| `food_lewm_b0` | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` | EfficientNet-B0 | 224 | 0.20 |
| `b0_seed123_fixed_v1` | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` | EfficientNet-B0 | 224 | 0.25 |
| `b3_cont_fixed_v1` | `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` | EfficientNet-B3 | 300 | 0.55 |

성능:

```text
top1     = 0.9130952380952381
top3     = 0.9796130952380953
macro_f1 = 0.9128455016622887
samples  = 6,720
classes  = 56
tta      = hflip
```

이전 best:

```text
B0/B2 weighted ensemble top1 = 0.900149
current best top1            = 0.913095
gain                         = +0.012946
```

목표까지 남은 gap:

```text
92%까지 = 0.006905
94%까지 = 0.026905
```

## 3. 지금까지의 큰 흐름

1. `fixed_v1` 기준으로 B0 / Food-LeWM / B2 계열을 실험했고, 이전 best는 약 `0.900149`였다.
2. 이후 B3 probe / continuation을 timeboxed 방식으로 진행했다.
3. B3 continuation checkpoint가 ensemble diversity member로 강하게 작동하면서 current best가 `0.913095`까지 상승했다.
4. 추가 실험 중 fivefold TTA는 `0.907292` 수준으로 하락했고, plus4 추가 fine-tuning도 `0.891220` 하락 신호가 있었다.
5. 따라서 현재 판단은 **B3 continuation은 성공했지만, 무작정 B3 full 25epoch로 가기 전에 오류/라벨 검수 판단이 필요하다**는 것이다.

## 4. 현재 오류 분석 결과

오류 분석 경로:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis
```

주요 산출물:

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
suggested_data_actions.md
```

low-F1 class 상위:

| Class | Precision | Recall | F1 |
|---|---:|---:|---:|
| 곰탕_설렁탕 | 0.850467 | 0.758333 | 0.801762 |
| 닭볶음탕 | 0.849558 | 0.800000 | 0.824034 |
| 삼겹살 | 0.878505 | 0.783333 | 0.828194 |
| 갈비구이 | 0.871560 | 0.791667 | 0.829694 |
| 동태찌개 | 0.817460 | 0.858333 | 0.837398 |
| 김치찌개 | 0.836066 | 0.850000 | 0.842975 |
| 수제비 | 0.859504 | 0.866667 | 0.863071 |
| 닭계장 | 0.880342 | 0.858333 | 0.869198 |
| 감자전 | 0.887931 | 0.858333 | 0.872881 |
| 칼국수 | 0.881356 | 0.866667 | 0.873950 |

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

해석:

```text
남은 오류는 단순 model capacity 부족이라기보다
class boundary, label ambiguity, multi-food crop, hard-pair confusion 성격이 강함.
```

## 5. 검수 자료 생성 상태

### 5.1 High-confidence top300

검수 원본 CSV:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/current_best_high_conf_review_top300.csv
```

사람 검수 템플릿:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_TEMPLATE.csv
```

contact sheet:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/contact_sheets_top300/review_sheet_001.jpg
...
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/contact_sheets_top300/review_sheet_012.jpg
```

AI visual draft 검수본:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_AI_DRAFT.csv
```

AI visual draft summary:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/current_best_high_conf_top300_ai_draft_review_summary.md
```

AI draft 검수 결과:

```text
총 후보              = 300
relabel             = 129
keep/model_error    = 112
remove              = 25
needs_human_review  = 34
```

review_status counts:

```text
wrong_label = 129
model_error = 112
ambiguous   = 34
multi_food  = 23
bad_crop    = 2
```

중요 제한:

```text
이 검수본은 사람이 확정한 파일이 아니라 Codex가 contact sheet를 보고 만든 AI visual draft다.
운영 확정 cleaned_v1 생성에는 바로 사용하면 안 된다.
사람이 relabel/remove/needs_human_review 행을 재확인해야 한다.
```

### 5.2 Train hard-pair candidates

검수 후보 경로:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/hard_class_report/train_hard_review_candidates.csv
```

사람 검수 템플릿:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates_TEMPLATE.csv
```

contact sheet:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/hard_class_report/train_contact_sheets/review_sheet_001.jpg
...
/Users/sangrok/foodsugar-ai/reports/current_best/hard_class_report/train_contact_sheets/review_sheet_012.jpg
```

현재 상태:

```text
train_hard_review_candidates.csv rows = 300
review_status/action은 아직 비어 있음
AI draft 검수는 아직 완료하지 않음
사람 확정 검수 파일도 아직 없음
```

## 6. 스크립트/자동화 상태

검수 후 실행할 safe runner:

```text
/Users/sangrok/foodsugar-ai/scripts/run_current_best_review_and_decision.py
```

관련 스크립트:

```text
/Users/sangrok/foodsugar-ai/scripts/summarize_label_review.py
/Users/sangrok/foodsugar-ai/scripts/build_kfood_label_patch.py
/Users/sangrok/foodsugar-ai/scripts/audit_label_patch_impact.py
```

현재 safe runner 상태 파일:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/review_and_decision_status.json
/Users/sangrok/foodsugar-ai/reports/current_best/review_and_decision_status.md
```

현재 decision:

```text
waiting_for_human_review
```

주의:

```text
safe runner는 사람 확정 파일명인 reviewed_current_best_high_conf_top300.csv,
reviewed_train_hard_pair_candidates.csv를 기준으로 판단한다.
따라서 AI_DRAFT 파일은 존재하지만 현재 decision은 여전히 waiting_for_human_review가 맞다.
```

## 7. 아직 하지 않은 작업

아래 작업은 아직 보류 중이다.

```text
1. high-confidence top300 사람 확정 검수
2. train hard-pair candidates 사람 확정 검수
3. high-confidence review summary 생성
4. train hard-pair patch / exclude 생성
5. patch impact audit
6. cleaned_train_v1 또는 cleaned_v1_candidate 생성 여부 결정
7. cleaned/fixed 기준 current best 재평가
8. B0 seed123 / seed7 재학습 여부 결정
9. B3 full 25epoch 여부 결정
10. 운영용 ensemble inference wrapper / latency benchmark
```

## 8. 현재 보류 판단

B3 full 25epoch는 아직 실행하지 않는 것이 현재 판단이다.

이유:

```text
1. current best가 이미 0.913095로 높다.
2. 추가 TTA와 추가 fine-tuning에서 하락 신호가 있었다.
3. 오류 분석상 남은 gap은 hard-pair / label-boundary 쪽에 집중되어 있다.
4. AI draft 기준으로도 wrong_label + ambiguous + multi_food + bad_crop 비율이 높다.
5. 사람 검수 없이 장시간 full training을 돌리면 개선 원인을 분리하기 어렵다.
```

## 9. 추천 다음 단계 초안

현재 권장 순서:

```text
1. AI_DRAFT high-confidence top300에서 relabel/remove/needs_human_review만 사람이 빠르게 재확인
2. train hard-pair candidates도 같은 기준으로 사람 또는 보수적 AI draft 검수
3. 사람 확정 파일명으로 저장
4. run_current_best_review_and_decision.py 실행
5. patch impact audit 결과 확인
6. train 영향이 충분하면 cleaned_candidate 생성
7. cleaned_candidate에서 B0 seed123만 먼저 재학습
8. B0 seed123이 기존 대비 유지/상승하면 seed7 및 ensemble sweep
9. label cleaning 효과가 약하면 B3 full 25epoch를 별도 장시간 실험으로 검토
```

## 10. GPT에게 검증받고 싶은 질문

1. 현재 `top1=0.913095` 상태에서 B3 full 25epoch보다 label/hard-pair 검수를 우선하는 판단이 타당한가?
2. AI visual draft에서 `relabel=129`, `remove=25`, `needs_human_review=34`, `keep=112`가 나온 상황이면 cleaned candidate 실험을 진행할 근거가 충분한가?
3. 단, 이 AI draft는 validation high-confidence 오류 후보 기반인데, train cleaning으로 일반화해도 되는가? 아니면 train hard-pair 확정 검수가 먼저인가?
4. `val_original_fixed`를 공정 비교 기준으로 유지하고, corrected/cleaned validation은 진단용으로만 보는 원칙이 맞는가?
5. 다음 실험으로 B0 seed123 cleaned_candidate 재학습을 먼저 하는 것이 맞는가, 아니면 B3 full을 병렬/우선으로 돌리는 것이 맞는가?
6. 현재 confusion pair를 보면 클래스 정의 문서부터 더 강화해야 하는 pair는 무엇인가?
7. 운영 후보로 `3-model weighted ensemble + hflip`을 유지할 때 latency / memory 관점에서 반드시 확인해야 할 항목은 무엇인가?

## 11. 보호해야 할 파일

아래 파일은 기존 운영/실험 기준점이므로 덮어쓰지 않아야 한다.

```text
/Users/sangrok/foodsugar-ai/data/models/efficientnet_korean.pt
/Users/sangrok/foodsugar-ai/data/models/korean_food_classes.json
/Users/sangrok/foodsugar-ai/data/models/korean_food_model_meta.json
/Users/sangrok/foodsugar-ai/data/models/efficientnet_korean_b0_val08275.pt
/Users/sangrok/foodsugar-ai/data/models/food_lewm_b0_classifier_3ep_ft10.pt
/Users/sangrok/foodsugar-ai/data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
/Users/sangrok/foodsugar-ai/data/models/efficientnet_korean_b3_probe_fixed_v1.pt
/Users/sangrok/foodsugar-ai/data/models/efficientnet_korean_b3_cont_fixed_v1.pt
/Users/sangrok/foodsugar-ai/data/models/korean_food_classes_b3_cont_fixed_v1.json
/Users/sangrok/foodsugar-ai/data/models/korean_food_model_meta_b3_cont_fixed_v1.json
```

## 12. 검증용 핵심 파일 목록

GPT 검증 시 참고할 파일:

```text
/Users/sangrok/foodsugar-ai/reports/current_best/fixed_weight_3model_hflip/metrics.json
/Users/sangrok/foodsugar-ai/reports/current_best/fixed_weight_3model_hflip/per_class_metrics.csv
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/low_f1_classes.csv
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/top_confusion_pairs.csv
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/reviewed_current_best_high_conf_top300_AI_DRAFT.csv
/Users/sangrok/foodsugar-ai/reports/current_best/error_analysis/current_best_high_conf_top300_ai_draft_review_summary.md
/Users/sangrok/foodsugar-ai/reports/current_best/hard_class_report/train_hard_review_candidates.csv
/Users/sangrok/foodsugar-ai/reports/current_best/hard_pair_class_definition.md
/Users/sangrok/foodsugar-ai/reports/current_best/HUMAN_REVIEW_NEXT_ACTIONS.md
/Users/sangrok/foodsugar-ai/reports/current_best/current_best_next_stage_result.md
```

## 13. 현재 최종 판단

현재는 **운영 후보 성능은 91.31%로 확보**, **92% 달성을 위한 다음 병목은 hard-pair/label cleaning 검증**이라고 보는 것이 가장 타당하다.

B3 full은 완전히 폐기한 것이 아니라, 아래 중 하나가 확인되면 다시 진행한다.

```text
1. high-confidence 검수에서 model_error가 대부분으로 확인됨
2. train cleaning 영향이 너무 작아 cleaned 재학습 실험 가치가 낮음
3. 운영 목표가 latency보다 offline accuracy를 우선함
4. 장시간 학습 리소스를 써도 되는 상황이 됨
```

반대로 AI draft만 믿고 바로 운영용 `cleaned_v1`을 만드는 것은 아직 이르다.  
현재 적절한 명칭은 `cleaned_v1_candidate` 또는 `cleaned_candidate` 실험이다.
