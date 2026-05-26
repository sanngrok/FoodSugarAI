# K-Food Classification 현재 진행상황 정리

작성일: 2026-05-13  
프로젝트 경로: `/Users/sangrok/foodsugar-ai`  
기준 데이터셋: `data/raw/korean_food_fixed_v1`  
기준 validation split: `val`  
클래스 수: 56  
Train / Val: 49,243 / 6,720

## 1. 전체 결론

현재 최고 성능은 **B3 continuation 3-model weighted ensemble + hflip**이다.

```text
Current best:
  top1     = 0.913095
  top3     = 0.979613
  macro_f1 = 0.912846

Weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55
```

이전 best였던 B0/B2 ensemble 대비:

```text
Previous best top1 = 0.900149
Current best top1  = 0.913095
Improvement        = +0.012946
```

92%까지 남은 gap:

```text
0.920000 - 0.913095 = 0.006905
약 0.69%p
```

현재 판단:

```text
B3 continuation은 성공.
fivefold TTA는 실패.
plus4 추가 fine-tuning도 실패 신호.
B3 full 25epoch는 즉시 진행하지 않고 보류.
다음 우선순위는 high-confidence error / hard-pair 검수.
```

## 2. 보호해야 할 파일

운영/기존 후보 파일은 덮어쓰지 않는다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt

data/models/food_lewm_b0_classifier_3ep_ft10.pt
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
data/models/efficientnet_korean_b3_probe_fixed_v1.pt
data/models/efficientnet_korean_b3_cont_fixed_v1.pt
```

현재 best B3 continuation 파일:

```text
data/models/efficientnet_korean_b3_cont_fixed_v1.pt
data/models/korean_food_classes_b3_cont_fixed_v1.json
data/models/korean_food_model_meta_b3_cont_fixed_v1.json
```

## 3. 실험 흐름 요약

### 3.1 fixed_v1 기준 정리

`korean_food_fixed_v1`를 기준 split으로 사용했다.

```text
train = 49,243
val   = 6,720
classes = 56
```

class order는 train/val/model classes 간 일치하도록 확인했다.

### 3.2 B0/B2 이전 best

이전 best는 B0-family + B2 clean fixed_v1 weighted ensemble이었다.

```text
Previous best:
  top1     = 0.900149
  top3     = 0.974405
  macro_f1 = 0.899900
```

구성:

```text
food_lewm_b0        = 0.15
b0_seed7_fixed_v1   = 0.25
b0_seed123_fixed_v1 = 0.25
b2_clean_fixed_v1   = 0.35
```

재현 리포트:

```text
reports/b3/previous_best_b0_b2_fixed_weight_hflip
```

### 3.3 B3 probe

B3 probe는 fixed_v1에서 timeboxed로 수행했다.

```text
B3 probe single hflip:
  top1     = 0.888839
  top3     = 0.972321
  macro_f1 = 0.888701

B3 probe 3-model weighted ensemble:
  top1     = 0.911310
  top3     = 0.976488
  macro_f1 = 0.911089
```

판정:

```text
B3는 단일 모델로도 유효했고,
ensemble member로는 이전 best를 크게 넘겼다.
```

### 3.4 B3 continuation

B3 probe checkpoint에서 low-lr continuation을 수행했다.

원래 10epoch 계획이었으나, 2026-05-12에 epoch 6 validation까지 진행 후 사용자가 요청해 중단했다.

best checkpoint는 epoch 6에서 저장되었다.

```text
checkpoint:
  data/models/efficientnet_korean_b3_cont_fixed_v1.pt

epoch:
  6

none TTA:
  top1     = 0.893155
  top3     = 0.972470
  macro_f1 = 0.892909

hflip:
  top1     = 0.895982
  top3     = 0.974107
  macro_f1 = 0.895791
```

판정:

```text
B3 probe hflip 0.888839 → B3 continuation hflip 0.895982
single 기준 +0.007143 개선.
계획서 기준 B3 continuation hflip >= 0.895 조건 충족.
```

리포트:

```text
reports/b3/b3_cont_fixed_v1
reports/b3/eval_b3_cont_fixed_v1_none
reports/b3/eval_b3_cont_fixed_v1_hflip
```

### 3.5 B3 continuation ensemble

B3 probe를 B3 continuation으로 교체해 3-model weighted ensemble을 평가했다.

구성:

```text
food_lewm_b0
b0_seed123_fixed_v1
b3_cont_fixed_v1
```

best weights:

```text
food_lewm_b0        = 0.20
b0_seed123_fixed_v1 = 0.25
b3_cont_fixed_v1    = 0.55
```

결과:

```text
top1     = 0.913095
top3     = 0.979613
macro_f1 = 0.912846
```

리포트:

```text
reports/b3/weighted_ensemble_3model_b3_cont_hflip
reports/b3/current_best_fixed_weight_hflip
```

### 3.6 Ensemble stability

calibration seed를 바꿔 안정성을 확인했다.

| Seed | Step | Weights | Top1 | Top3 | Macro-F1 |
|---:|---:|---|---:|---:|---:|
| 42 | 0.05 | `0.20 / 0.25 / 0.55` | 0.913095 | 0.979613 | 0.912846 |
| 7 | 0.05 | `0.20 / 0.25 / 0.55` | 0.913095 | 0.979613 | 0.912846 |
| 123 | 0.05 | `0.25 / 0.30 / 0.45` | 0.912202 | 0.978869 | 0.911994 |
| 42 | 0.025 | `0.225 / 0.20 / 0.575` | 0.912500 | 0.979018 | 0.912272 |

판정:

```text
B3 continuation weight가 0.45~0.575로 안정적으로 높다.
0.025 step은 최고점을 갱신하지 못했다.
현재 best는 0.20 / 0.25 / 0.55 조합이다.
```

### 3.7 fivefold TTA

B3 continuation ensemble에 fivefold TTA를 적용했다.

```text
hflip ensemble:
  top1     = 0.913095
  top3     = 0.979613
  macro_f1 = 0.912846

fivefold ensemble:
  top1     = 0.907292
  top3     = 0.979018
  macro_f1 = 0.907179
```

판정:

```text
fivefold는 top1 기준 -0.005804 악화.
운영 후보에서 제외.
hflip 유지.
```

### 3.8 plus4 추가 fine-tuning

epoch 6 B3 continuation checkpoint에서 `lr=3e-6`으로 4epoch 추가 학습을 시도했다.

별도 파일로 저장해 기존 best는 보호했다.

```text
data/models/efficientnet_korean_b3_cont_plus4_fixed_v1.pt
data/models/korean_food_model_meta_b3_cont_plus4_fixed_v1.json
reports/b3/b3_cont_plus4_fixed_v1
```

epoch 1 결과:

```text
top1     = 0.891220
top3     = 0.971577
macro_f1 = 0.890778
```

판정:

```text
원본 epoch 6 checkpoint none top1 0.893155보다 낮다.
추가 continuation은 개선 신호가 약해 조기 중단.
운영 후보는 plus4가 아니라 epoch 6 B3 continuation.
```

## 4. Current Best 오류 분석

current best ensemble을 고정 weight evaluator로 재현한 뒤 오류 분석을 수행했다.

분석 리포트:

```text
reports/b3/current_best_error_analysis
reports/b3/current_best_hard_class_report
```

### 4.1 Low-F1 상위 class

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

### 4.2 Top confusion pairs

| True | Pred | Count | True Accuracy |
|---|---|---:|---:|
| 감자전 | 호박전 | 12 | 0.858333 |
| 곰탕_설렁탕 | 갈비탕 | 9 | 0.758333 |
| 김치찜 | 김치찌개 | 8 | 0.875000 |
| 칼국수 | 수제비 | 8 | 0.866667 |
| 곰탕_설렁탕 | 삼계탕 | 7 | 0.758333 |
| 떡볶이 | 라볶이 | 7 | 0.900000 |
| 호박전 | 감자전 | 7 | 0.900000 |
| 갈비찜 | 닭볶음탕 | 6 | 0.875000 |
| 김치찌개 | 동태찌개 | 6 | 0.850000 |
| 물냉면 | 비빔냉면 | 6 | 0.925000 |
| 순두부찌개 | 김치찌개 | 6 | 0.891667 |
| 양념치킨 | 후라이드치킨 | 6 | 0.908333 |

### 4.3 Hard class delta

previous best 대비 current best hard class 변화:

| Class | Current F1 | Previous F1 | Delta |
|---|---:|---:|---:|
| 곰탕_설렁탕 | 0.801762 | 0.808889 | -0.007127 |
| 감자전 | 0.872881 | 0.871369 | +0.001512 |
| 호박전 | 0.888889 | 0.887029 | +0.001860 |
| 갈비구이 | 0.829694 | 0.824490 | +0.005204 |
| 김치찌개 | 0.842975 | 0.836066 | +0.006909 |
| 수제비 | 0.863071 | 0.852174 | +0.010897 |
| 삼계탕 | 0.901186 | 0.889764 | +0.011422 |
| 순두부찌개 | 0.880658 | 0.864198 | +0.016460 |
| 칼국수 | 0.873950 | 0.851240 | +0.022710 |
| 동태찌개 | 0.837398 | 0.813008 | +0.024390 |
| 삼겹살 | 0.828194 | 0.801724 | +0.026470 |
| 갈비찜 | 0.878661 | 0.850000 | +0.028661 |
| 된장찌개 | 0.927660 | 0.897119 | +0.030541 |
| 갈비탕 | 0.904564 | 0.872428 | +0.032136 |
| 라볶이 | 0.927419 | 0.894309 | +0.033110 |
| 라면 | 0.913793 | 0.823009 | +0.090784 |

해석:

```text
B3 continuation ensemble은 대부분 hard class를 개선했다.
명확한 악화는 곰탕_설렁탕 하나가 가장 크다.
남은 오류는 model capacity 단독 문제라기보다 class boundary / label ambiguity 성격이 강하다.
```

## 5. 생성한 검수 자료

### 5.1 Current best high-confidence error top300

CSV:

```text
reports/b3/current_best_error_analysis/current_best_high_conf_review_top300.csv
```

Contact sheets:

```text
reports/b3/current_best_error_analysis/contact_sheets_top300
```

용도:

```text
현재 best ensemble이 높은 confidence로 틀린 val 이미지 300개 검수.
wrong label / ambiguous / multi-food / crop issue / true model error 구분.
```

### 5.2 Train hard-pair review candidates

CSV:

```text
reports/b3/current_best_hard_class_report/train_hard_review_candidates.csv
```

Contact sheets:

```text
reports/b3/current_best_hard_class_report/train_contact_sheets
```

용도:

```text
train split에서 hard class / hard pair 주변 샘플 300개 검수.
cleaned_train_v1 또는 hard-pair patch 생성 여부 판단.
```

## 6. B3 full 25epoch 판단

현재 결론:

```text
B3 full 25epoch는 즉시 실행하지 않고 보류.
```

보류 이유:

```text
1. B3 continuation이 이미 대부분 hard class를 개선했다.
2. plus4 추가 fine-tuning이 하락했다.
3. fivefold TTA도 하락했다.
4. 남은 오류가 class boundary / label ambiguity 쪽에 집중되어 있다.
5. full 25epoch는 장시간 비용이 크며, 지금 바로 92%를 넘길 근거가 부족하다.
```

다시 full run을 고려할 조건:

```text
1. high-confidence top300 검수에서 label/class-boundary 문제가 적다.
2. 남은 오류가 명확히 model capacity / visual detail 문제로 확인된다.
3. 장시간 학습 시간을 확보할 수 있다.
4. epoch 5/10/15 중간 판단 기준을 두고 별도 checkpoint로만 실행한다.
```

## 7. 현재 운영 후보

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

운영 적용 전 필요 작업:

```text
1. ensemble inference wrapper
2. class order / metadata 통합
3. single B3 vs 3-model ensemble latency benchmark
4. memory benchmark
5. /predict end-to-end compatibility test
6. rollback path 정리
```

## 8. 주요 리포트 파일

```text
reports/b3/b3_next_stage_after_probe_result.md
reports/b3/b3_after_continuation_next_steps_result.md
reports/b3/current_best_fixed_weight_hflip
reports/b3/current_best_error_analysis
reports/b3/current_best_hard_class_report
```

## 9. 변경된 스크립트

`scripts/analyze_kfood_errors.py`를 보강했다.

추가 내용:

```text
--baseline-eval-dir 옵션
hard_class_delta_summary.csv 출력
hard class README 섹션
```

## 10. 검증 상태

마지막 검증:

```bash
python3 -m py_compile scripts/analyze_kfood_errors.py scripts/eval_fixed_weight_ensemble.py scripts/build_hard_class_report.py scripts/prepare_label_review_sheet.py scripts/build_label_review_contact_sheets.py scripts/build_train_hard_review_sheet.py
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

## 11. 다음 액션 추천

우선순위:

```text
1. current_best_high_conf_review_top300.csv 수동 검수
2. contact_sheets_top300 이미지 검수
3. train_hard_review_candidates.csv 수동 검수
4. 검수 결과로 label noise 비율 계산
5. hard pair별 class definition 작성
6. cleaned_train_v1 / hard-pair patch 생성 여부 결정
7. cleaned/hard-pair 반영 후 current best ensemble 재평가
8. 그래도 92% 미달이면 B3 full 25epoch 장시간 실험 재검토
9. 운영 후보 적용을 위해 ensemble wrapper / latency / memory / API compatibility 체크
```

핵심 판단:

```text
현재 91.31%까지는 모델/ensemble로 크게 올렸다.
남은 0.69%p는 단순 추가 학습보다 label boundary와 hard-pair 정리가 더 중요해 보인다.
```

