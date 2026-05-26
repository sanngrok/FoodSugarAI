# K-Food Cleanup Sequence Status

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

## 1. 현재 실행 상태

사용자가 지정한 10단계 순서를 기준으로 현재 가능한 작업을 진행했다.

| Step | 작업 | 상태 | 결과 |
|---:|---|---|---|
| 1 | `review_sheet_top300.csv` 수동 검수 | AI draft 완료 | 300/300 row 채움 |
| 2 | label noise 비율 계산 | 완료 | noisy_label_ratio=0.520000 |
| 3 | hard class / hard pair 기준 정리 | 완료 | 아래 기준표 정리 |
| 4 | cleaned_v1 생성 여부 결정 | 조건부 생성 권장 | AI draft 기준 52% noise |
| 5 | cleaned_v1 또는 fixed_v1에서 현재 best ensemble 재평가 | fixed_v1 완료 | 6-model weighted top1=0.900149 |
| 6 | cleaned_v1이 생기면 B0 seed123 / B0 seed ensemble 재학습 | 대기 | cleaned_v1 생성 이후 진행 |
| 7 | B2 현재 checkpoint diversity member 유지 | 완료 | ensemble 후보로 유지 |
| 8 | B2 재학습/fine-tuning 결정 | 대기 | cleaned_v1 결과 이후 결정 |
| 9 | ensemble weight 안정성 검증 | 완료 | 6 seeds stability 확인 |
| 10 | 운영 후보 선택 | 임시 후보 선정 | 최종은 label review 이후 확정 |

---

## 2. Label Review 진행 방법

검수 대상 CSV:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
```

검수용 contact sheets:

```text
reports/error_analysis/final_candidate/contact_sheets/
```

생성된 파일:

```text
review_sheet_001.jpg
review_sheet_002.jpg
...
review_sheet_012.jpg
```

각 CSV row의 빈 칸을 다음 규칙으로 채운다.

| Column | 값 |
|---|---|
| `review_status` | `model_error`, `wrong_label`, `ambiguous`, `multi_food`, `low_quality`, `out_of_scope` |
| `corrected_label` | `wrong_label`이면 올바른 class명 입력, 아니면 비워도 됨 |
| `review_note` | 헷갈린 이유, visible ingredient, crop 문제 등 |
| `action` | `keep`, `relabel`, `remove`, `collect_more`, `boundary_rule` |

Noise로 계산하는 status:

```text
wrong_label
ambiguous
multi_food
low_quality
out_of_scope
```

집계 명령:

```bash
python3 scripts/summarize_label_review.py \
  --reviewed reports/error_analysis/final_candidate/review_sheet_top300.csv \
  --output-dir reports/error_analysis/final_candidate/review_summary_top300
```

현재 상태:

```text
reviewed_count=300
reviewed_ratio=1.0
noisy_label_ratio=0.520000
```

주의:

```text
현재 값은 AI visual draft 기준이다.
사람 검수 없이 바로 cleaned_v1을 확정 운영 기준으로 쓰기보다는
cleaned_v1 실험 후보 생성 기준으로 사용하는 것이 적절하다.
```

AI draft 산출물:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
reports/error_analysis/final_candidate/review_sheet_top300_unreviewed_backup.csv
reports/error_analysis/final_candidate/review_summary_top300/
```

AI draft 집계:

| Status | Count |
|---|---:|
| model_error | 144 |
| wrong_label | 126 |
| multi_food | 30 |

| Action | Count |
|---|---:|
| keep | 144 |
| relabel | 126 |
| remove | 30 |

---

## 3. Hard Class 기준

현재 low-F1 / high-confusion 기준으로 우선 검수할 class:

| Group | Classes | 주요 기준 |
|---|---|---|
| 찌개/탕 | 동태찌개, 김치찌개, 순두부찌개, 된장찌개, 감자탕 | 국물 색만 보이면 `ambiguous`; 주재료가 보여야 유지 |
| 곰탕류 | 곰탕_설렁탕, 갈비탕, 삼계탕 | 고기 부위/뼈/닭 형태가 안 보이면 `ambiguous` |
| 고기류 | 갈비구이, 갈비찜, 삼겹살, 보쌈, 족발 | 조리법이 구이/찜/수육인지 시각적으로 불명확하면 `ambiguous` |
| 면류 | 라면, 라볶이, 칼국수, 수제비, 잔치국수 | 면 굵기/국물/떡/어묵 등 핵심 단서가 보여야 유지 |
| 전류 | 감자전, 호박전, 파전 | 재료 texture가 안 보이면 `ambiguous` |
| 냉면류 | 물냉면, 비빔냉면 | 육수/양념장이 안 보이면 `ambiguous` |

---

## 4. Hard Pair 기준

우선 boundary rule이 필요한 pair:

| True | Pred | 기준 |
|---|---|---|
| 곰탕_설렁탕 | 갈비탕 | 갈비뼈/갈비 형태가 보이면 갈비탕, 아니면 곰탕_설렁탕 또는 ambiguous |
| 곰탕_설렁탕 | 삼계탕 | 닭 한 마리/닭뼈 형태가 명확하면 삼계탕 |
| 김치찌개 | 동태찌개 | 생선 살/동태 단서가 보이면 동태찌개, 김치/돼지고기 중심이면 김치찌개 |
| 호박전 | 감자전 | 호박 단면/초록 테두리 visible이면 호박전, 감자채/감자전 texture면 감자전 |
| 갈비구이 | 갈비찜 | 양념구이/그릴 자국이면 갈비구이, 국물/찜 양념/당면/채소 동반이면 갈비찜 |
| 삼겹살 | 갈비구이 | 삼겹 지방층이 명확하면 삼겹살, 뼈/갈비 형태면 갈비구이 |
| 비빔냉면 | 물냉면 | 빨간 양념 비빔 상태면 비빔냉면, 육수 중심이면 물냉면 |
| 칼국수 | 수제비 | 긴 면이면 칼국수, 뜯은 반죽 조각이면 수제비 |
| 떡볶이 | 라볶이 | 라면 사리가 명확하면 라볶이, 떡 중심이면 떡볶이 |
| 족발 | 보쌈 | 껍질/윤기/족발 형태면 족발, 삶은 수육 단면 중심이면 보쌈 |

---

## 5. Cleaned_v1 생성 결정 규칙

검수 완료 후 noisy ratio 기준:

| Noisy Ratio | 결정 |
|---:|---|
| `< 5%` | cleaned_v1 생성보다 model diversity / ensemble tuning 우선 |
| `5% ~ 10%` | hard class 중심 부분 clean set 생성 검토 |
| `>= 10%` | cleaned_v1 생성 후 재학습 우선 |

추가 조건:

```text
특정 hard pair에서 wrong_label/ambiguous가 집중되면 전체 ratio가 10% 미만이어도
해당 class pair 중심 cleaned_v1_partial 또는 class-boundary rule 문서를 만든다.
```

현재 결정:

```text
AI draft 기준 noisy_label_ratio=52%로 10% 기준을 크게 초과한다.
따라서 cleaned_v1 실험 split 생성은 권장한다.
단, 이 값은 high-confidence error top300에 대한 표본이므로 전체 데이터 noise ratio로 일반화하면 안 된다.
```

---

## 6. Current Best Ensemble 재평가

현재 fixed_v1 기준 best:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/
```

선택 weight:

| Model | Weight |
|---|---:|
| b0_baseline | 0.00 |
| food_lewm_b0 | 0.15 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.25 |
| b0_supervised_seed123_fixed_v1 | 0.25 |
| b2_clean_fixed_v1 | 0.35 |

성능:

| Split | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| calibration | 0.907440 | 0.979762 | 0.907389 |
| evaluation | 0.892857 | 0.969048 | 0.892251 |
| full | 0.900149 | 0.974405 | 0.899900 |

해석:

```text
full 기준으로는 기존 5-model weighted 0.898214보다 개선됐다.
다만 evaluation split에서는 5-model 0.893750보다 6-model 0.892857이 낮아
label review 이후 재검증이 필요하다.
```

---

## 7. Ensemble Weight 안정성

검증 산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip_stability/
```

설정:

```text
cache=reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/logits_cache.pt
weight_step=0.05
calibration_ratio=0.5
seeds=0,1,2,7,42,123
```

선택 weight 범위:

| Model | Min | Mean | Max |
|---|---:|---:|---:|
| b0_baseline | 0.0000 | 0.0167 | 0.1000 |
| food_lewm_b0 | 0.1500 | 0.1833 | 0.2000 |
| b0_supervised_only | 0.0000 | 0.0000 | 0.0000 |
| b0_supervised_seed7_fixed_v1 | 0.1000 | 0.1750 | 0.2500 |
| b0_supervised_seed123_fixed_v1 | 0.2500 | 0.3417 | 0.5000 |
| b2_clean_fixed_v1 | 0.0000 | 0.2833 | 0.3500 |

seed별 성능:

| Seed | Full Top1 | Eval Top1 | Full Macro-F1 |
|---:|---:|---:|---:|
| 0 | 0.900298 | 0.899107 | 0.900050 |
| 1 | 0.900149 | 0.903571 | 0.899961 |
| 2 | 0.900149 | 0.895238 | 0.899897 |
| 7 | 0.898214 | 0.894048 | 0.897979 |
| 42 | 0.900149 | 0.892857 | 0.899900 |
| 123 | 0.900149 | 0.899405 | 0.899900 |

판단:

```text
full top1은 0.898214~0.900298 범위로 안정적이다.
B0 supervised-only 기존 모델은 모든 seed에서 weight 0으로 빠져 pruning 후보다.
B2는 대부분 seed에서 0.30~0.35를 받지만 seed 7에서는 0이라, 유지하되 최종 후보 확정은 label review 이후로 둔다.
```

---

## 8. 운영 후보

현재 임시 운영 후보:

```text
6-model weighted ensemble with B2
```

운영 후보로 바로 확정하지 않는 이유:

```text
1. label review가 아직 미완료다.
2. cleaned_v1 생성 여부가 결정되지 않았다.
3. ensemble은 single model보다 추론 비용이 크다.
4. B2 weight 안정성은 긍정적이지만 완전히 고정적이지는 않다.
```

최종 운영 후보 선택은 다음 조건 이후 진행:

```text
review_sheet_top300.csv 검수 완료
label noise ratio 계산
cleaned_v1 생성 여부 결정
cleaned_v1 또는 fixed_v1 기준 best ensemble 재평가
```

---

## 9. 다음 실제 액션

바로 이어서 할 일:

```text
1. AI draft를 기준으로 cleaned_v1 실험 split 생성 스크립트를 만든다.
2. relabel/remove 대상이 fixed_v1 train/val에 얼마나 걸리는지 먼저 audit한다.
3. 영향 범위가 작고 검증 가능하면 cleaned_v1을 생성한다.
```
