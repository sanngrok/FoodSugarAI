# B3 After Continuation Next Steps Result

작성일: 2026-05-13  
프로젝트: `/Users/sangrok/foodsugar-ai`  
기준 데이터: `data/raw/korean_food_fixed_v1`  
기준 validation: `val`

## 1. 현재 Best 후보 고정

현재 best 후보를 fixed-weight evaluator로 다시 재현했다.

```text
candidate:
  3-model weighted ensemble + hflip

weights:
  food_lewm_b0        = 0.20
  b0_seed123_fixed_v1 = 0.25
  b3_cont_fixed_v1    = 0.55

result:
  top1     = 0.913095
  top3     = 0.979613
  macro_f1 = 0.912846
```

출력:

- `reports/b3/current_best_fixed_weight_hflip`

이전 best도 같은 evaluator로 재현했다.

```text
previous_best:
  food_lewm_b0        = 0.15
  b0_seed7_fixed_v1   = 0.25
  b0_seed123_fixed_v1 = 0.25
  b2_clean_fixed_v1   = 0.35

result:
  top1     = 0.900149
  top3     = 0.974405
  macro_f1 = 0.899900
```

출력:

- `reports/b3/previous_best_b0_b2_fixed_weight_hflip`

## 2. 성능 요약

| Experiment | Data | TTA | Top1 | Top3 | Macro-F1 | Decision |
|---|---|---|---:|---:|---:|---|
| Previous best B0/B2 ensemble | fixed_v1 | hflip | 0.900149 | 0.974405 | 0.899900 | baseline |
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

## 3. Current Best Error Analysis

오류 분석 출력:

- `reports/b3/current_best_error_analysis/low_f1_classes.csv`
- `reports/b3/current_best_error_analysis/low_recall_classes.csv`
- `reports/b3/current_best_error_analysis/low_precision_classes.csv`
- `reports/b3/current_best_error_analysis/top_confusion_pairs.csv`
- `reports/b3/current_best_error_analysis/high_confidence_errors_top300.csv`
- `reports/b3/current_best_error_analysis/hard_class_delta_summary.csv`
- `reports/b3/current_best_error_analysis/current_best_high_conf_review_top300.csv`
- `reports/b3/current_best_error_analysis/contact_sheets_top300`

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

Top confusion pairs:

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

High-confidence error top300의 true_class 집중:

| Class | Count |
|---|---:|
| 곰탕_설렁탕 | 16 |
| 닭볶음탕 | 14 |
| 호박전 | 12 |
| 갈비찜 | 12 |
| 김치찌개 | 11 |
| 갈비구이 | 10 |
| 김치찜 | 10 |
| 닭계장 | 9 |
| 칼국수 | 9 |
| 감자전 | 9 |

## 4. Hard Class Delta

previous best 대비 current best의 hard class 변화:

| Class | Current F1 | Previous F1 | Delta F1 | Errors As True |
|---|---:|---:|---:|---:|
| 곰탕_설렁탕 | 0.801762 | 0.808889 | -0.007127 | 29 |
| 족발 | 0.933333 | 0.933333 | -0.000000 | 8 |
| 보쌈 | 0.914980 | 0.914286 | +0.000694 | 7 |
| 감자전 | 0.872881 | 0.871369 | +0.001512 | 17 |
| 호박전 | 0.888889 | 0.887029 | +0.001860 | 12 |
| 갈비구이 | 0.829694 | 0.824490 | +0.005204 | 25 |
| 김치찌개 | 0.842975 | 0.836066 | +0.006909 | 18 |
| 수제비 | 0.863071 | 0.852174 | +0.010897 | 16 |
| 삼계탕 | 0.901186 | 0.889764 | +0.011422 | 6 |
| 순두부찌개 | 0.880658 | 0.864198 | +0.016460 | 13 |
| 칼국수 | 0.873950 | 0.851240 | +0.022710 | 16 |
| 동태찌개 | 0.837398 | 0.813008 | +0.024390 | 17 |
| 삼겹살 | 0.828194 | 0.801724 | +0.026470 | 26 |
| 갈비찜 | 0.878661 | 0.850000 | +0.028661 | 15 |
| 된장찌개 | 0.927660 | 0.897119 | +0.030541 | 11 |
| 갈비탕 | 0.904564 | 0.872428 | +0.032136 | 11 |
| 라볶이 | 0.927419 | 0.894309 | +0.033110 | 5 |
| 라면 | 0.913793 | 0.823009 | +0.090784 | 14 |

해석:

- B3 continuation ensemble은 대부분 hard class를 개선했다.
- 명확한 악화는 `곰탕_설렁탕` 하나가 가장 크다.
- 여전히 낮은 class는 `곰탕_설렁탕`, `삼겹살`, `갈비구이`, `동태찌개`, `김치찌개`, `칼국수/수제비`, `감자전/호박전`이다.
- 남은 오류는 모델 capacity만의 문제라기보다 class boundary/label ambiguity 성격이 강하다.

## 5. Hard Class / Hard Pair Review 산출물

생성한 hard-class report:

- `reports/b3/current_best_hard_class_report/README.md`
- `reports/b3/current_best_hard_class_report/hard_classes.csv`
- `reports/b3/current_best_hard_class_report/hard_pairs.csv`

생성한 train hard review 후보:

- `reports/b3/current_best_hard_class_report/train_hard_review_candidates.csv`
- `reports/b3/current_best_hard_class_report/train_hard_review_candidates.md`
- `reports/b3/current_best_hard_class_report/train_contact_sheets`

검수 우선순위:

1. `reports/b3/current_best_error_analysis/current_best_high_conf_review_top300.csv`
2. `reports/b3/current_best_error_analysis/contact_sheets_top300`
3. `reports/b3/current_best_hard_class_report/train_hard_review_candidates.csv`
4. `reports/b3/current_best_hard_class_report/train_contact_sheets`

## 6. B3 Full Run 결정

현재 결론: B3 full 25epoch는 즉시 실행하지 않고 보류한다.

이유:

- B3 continuation은 이미 대부분 hard class를 개선했다.
- plus4 추가 fine-tuning은 epoch 1부터 하락했다.
- fivefold TTA도 하락했다.
- 남은 상위 오류가 `전`, `탕/찌개`, `면`, `갈비/삼겹살`, `냉면`, `족발/보쌈`처럼 class boundary가 강한 pair에 집중되어 있다.
- high-confidence error top300도 label/class-boundary 검수 후보로 보는 것이 더 안전하다.

따라서 지금 바로 full 25epoch를 시작하면 장시간 비용 대비 92% 도달 가능성이 불확실하다.

권장 분기:

```text
현재 best ensemble은 운영 후보로 고정한다.
B3 full run은 별도 장시간 실험으로 보류한다.
우선 current best high-confidence top300과 train hard-pair 후보를 검수한다.
검수 후 label noise / class boundary 문제가 적다고 확인되면 B3 full run을 다시 진행한다.
```

## 7. 운영 후보 판단

현재 연구 성능 기준 운영 후보:

```text
3-model weighted ensemble + hflip

food_lewm_b0        0.20
b0_seed123_fixed_v1 0.25
b3_cont_fixed_v1    0.55

top1     0.913095
top3     0.979613
macro_f1 0.912846
```

운영 적용 전 남은 작업:

1. ensemble inference wrapper
2. class order/metadata 통합
3. single B3 vs 3-model ensemble latency benchmark
4. memory benchmark
5. `/predict` end-to-end compatibility test
6. rollback path 정리

## 8. 변경/생성 파일

스크립트 변경:

- `scripts/analyze_kfood_errors.py`
  - `--baseline-eval-dir` 옵션 추가
  - `hard_class_delta_summary.csv` 출력 추가
  - hard class README 섹션 추가

주요 생성 파일:

- `reports/b3/current_best_fixed_weight_hflip`
- `reports/b3/previous_best_b0_b2_fixed_weight_hflip`
- `reports/b3/current_best_error_analysis`
- `reports/b3/current_best_hard_class_report`

## 9. 검증

실행:

```bash
python3 -m py_compile scripts/analyze_kfood_errors.py scripts/eval_fixed_weight_ensemble.py scripts/build_hard_class_report.py scripts/prepare_label_review_sheet.py scripts/build_label_review_contact_sheets.py scripts/build_train_hard_review_sheet.py
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

## 10. 다음 액션

추천 순서:

1. `current_best_high_conf_review_top300.csv` 수동 검수
2. `contact_sheets_top300` 이미지 검수
3. `train_hard_review_candidates.csv` 검수
4. 검수 결과로 label noise 비율 계산
5. hard pair별 class definition 작성
6. cleaned/hard-pair patch 생성 여부 결정
7. 그 이후 B3 full 25epoch 재검토

최종 결론:

```text
현재 best는 B3 continuation 3-model weighted ensemble이다.
top1=0.913095, macro_f1=0.912846, 92%까지 0.6905%p 남았다.
다음 병목은 model capacity 단독보다는 label noise / class boundary / hard pair 문제로 판단된다.
B3 full run은 즉시 진행하지 않고 보류한다.
```

