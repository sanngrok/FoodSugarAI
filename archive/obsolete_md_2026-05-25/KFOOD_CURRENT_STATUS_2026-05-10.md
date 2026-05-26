# K-Food 현재 진행상황 요약

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

## 1. 현재 결론

현재 보수적 기준 best는 `data/raw/korean_food_fixed_v1` 기준 B2 포함 6-model weighted ensemble이다.

| Metric | Value |
|---|---:|
| Top1 | 0.900149 |
| Top3 | 0.974405 |
| Macro-F1 | 0.899900 |
| 92%까지 gap | 약 1.99%p |

다만 high-confidence error top300 AI 검수 결과 label/multi-food noise 후보가 높게 나와서, 다음 우선순위는 추가 학습보다 `cleaned_v1` 생성 및 재평가다.

---

## 2. Split 상태

기존 `korean_food_1000/val`은 old train filename overlap 때문에 낙관적인 평가였음이 확인됐다.

현재 기준 split:

```text
data/raw/korean_food_fixed_v1
```

| Split | Count |
|---|---:|
| train | 49,243 |
| val | 6,720 |
| classes | 56 |

`fixed_v1` 검증:

| Pair | Class+Filename Overlap |
|---|---:|
| old_train -> fixed_v1 val | 0 |
| fixed_v1 train -> fixed_v1 val | 0 |
| old_val -> fixed_v1 val | 6,720 |

---

## 3. 모델 결과

### Best Single

| Model | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| B0 supervised-only seed123 fixed_v1 | hflip | 0.886012 | 0.965327 | 0.885791 |

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
```

### B2 Clean Supervised

B2는 20epoch 계획이었지만 MPS full fine-tuning 속도가 지나치게 느려 epoch 4 best checkpoint를 보존하고 중단했다.

| TTA | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| none | 0.833929 | 0.953125 | 0.833526 |
| hflip | 0.835714 | 0.954762 | 0.835308 |

판단:

```text
B2 단독 모델은 약하다.
하지만 ensemble diversity member로는 소폭 기여한다.
```

---

## 4. 현재 Best Ensemble

산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/
```

구성 weight:

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

주의:

```text
full 기준으로는 5-model ensemble보다 개선됐지만,
evaluation split에서는 5-model보다 낮았다.
따라서 최종 운영 후보 확정은 cleaned_v1 이후로 미룬다.
```

---

## 5. Ensemble 안정성 검증

산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip_stability/
```

검증 설정:

```text
weight_step=0.05
calibration_ratio=0.5
seeds=0,1,2,7,42,123
```

seed별 full top1:

| Seed | Full Top1 |
|---:|---:|
| 0 | 0.900298 |
| 1 | 0.900149 |
| 2 | 0.900149 |
| 7 | 0.898214 |
| 42 | 0.900149 |
| 123 | 0.900149 |

판단:

```text
6-model ensemble은 대체로 0.898~0.900 범위에서 안정적이다.
B0 supervised-only 기존 모델은 모든 stability seed에서 weight 0으로 빠져 pruning 후보다.
B2는 대부분 seed에서 weight를 받지만, seed 7에서는 0으로 빠졌다.
```

---

## 6. Label Review / Noise 분석

검수 대상:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
```

AI draft:

```text
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
```

원본 백업:

```text
reports/error_analysis/final_candidate/review_sheet_top300_unreviewed_backup.csv
```

집계:

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

Noise 후보:

```text
156 / 300 = 52.0%
```

주의:

```text
이 52%는 high-confidence error top300에 대한 biased sample 결과다.
전체 데이터 noise ratio로 일반화하면 안 된다.
하지만 cleaned_v1 실험 split을 만들 근거로는 충분하다.
```

---

## 7. Hard Class / Hard Pair

우선 관리할 hard class:

```text
동태찌개, 김치찌개, 순두부찌개, 된장찌개, 감자탕,
곰탕_설렁탕, 갈비탕, 삼계탕,
갈비구이, 갈비찜, 삼겹살, 보쌈, 족발,
라면, 라볶이, 칼국수, 수제비, 잔치국수,
감자전, 호박전, 파전, 김치전,
물냉면, 비빔냉면
```

대표 hard pair:

```text
곰탕_설렁탕 vs 갈비탕
김치찌개 vs 동태찌개
호박전 vs 감자전
갈비구이 vs 갈비찜
비빔냉면 vs 물냉면
칼국수 vs 수제비
떡볶이 vs 라볶이
족발 vs 보쌈
```

---

## 8. 운영 파일 보호

아래 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

---

## 9. 현재 10단계 상태

| Step | 작업 | 상태 |
|---:|---|---|
| 1 | review_sheet_top300 검수 | AI draft 완료 |
| 2 | label noise 비율 계산 | 완료 |
| 3 | hard class / hard pair 기준 정리 | 완료 |
| 4 | cleaned_v1 생성 여부 결정 | 생성 권장 |
| 5 | fixed_v1 best ensemble 재평가 | 완료 |
| 6 | cleaned_v1 기준 재학습 | 대기 |
| 7 | B2 diversity member 유지 | 완료 |
| 8 | B2 재학습 결정 | cleaned_v1 이후 |
| 9 | ensemble weight 안정성 검증 | 완료 |
| 10 | 운영 후보 선택 | 임시 후보만 선정 |

---

## 10. 다음 액션

추천 순서:

1. AI draft 기준 relabel/remove 대상이 fixed_v1 train/val에 얼마나 걸리는지 audit
2. `korean_food_cleaned_v1` 생성
3. cleaned_v1 기준 현재 best ensemble 재평가
4. cleaned_v1 기준 B0 seed123 / B0 seed ensemble 재학습
5. cleaned_v1 결과 이후 B2 재학습 여부 결정
6. 운영 후보를 single / pruned ensemble / full ensemble 중 선택

---

## 11. 참고 문서

더 상세한 전체 브리프:

```text
KFOOD_CURRENT_PROGRESS_BRIEF_2026-05-10.md
KFOOD_CLEANUP_SEQUENCE_STATUS_2026-05-10.md
KFOOD_92_PROGRESS_SUMMARY_2026-05-10.md
```
