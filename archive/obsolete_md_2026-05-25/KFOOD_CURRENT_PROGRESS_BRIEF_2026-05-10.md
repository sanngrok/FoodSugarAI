# K-Food 92% 프로젝트 최신 진행상황 브리프

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`  
목표: K-Food 56-class 분류 성능을 보수적 fixed split 기준 92%에 가깝게 개선

---

## 1. 현재 한 줄 요약

현재 보수적 기준 best는 `data/raw/korean_food_fixed_v1`에서 B2를 포함한 6-model weighted ensemble이며, hflip TTA 기준 `top1=0.900149`, `macro_f1=0.899900`이다.

다만 92%까지는 아직 약 `1.99%p` gap이 남아 있고, high-confidence error top300 AI visual draft에서 noise 후보가 `52.0%`로 높게 나와서 다음 핵심은 추가 학습보다 `cleaned_v1` 실험 split 생성이다.

---

## 2. 데이터 / Split 상태

초기에는 `data/raw/korean_food_1000/val` 전체 기준 ensemble top1 `0.900661`까지 확인했지만, split audit에서 old train filename overlap이 성능을 부풀리는 문제가 확인됐다.

중요 발견:

```text
korean_food_1000/val 11,194장은 class+filename 기준으로
old_train overlap 4,474장 + old_val overlap 6,720장으로 구성되어 있었다.
```

그래서 새 보수 split을 만들었다.

| Dataset | Train | Val | Classes | Notes |
|---|---:|---:|---:|---|
| `data/raw/korean_food_fixed_v1` | 49,243 | 6,720 | 56 | old_train overlap 제거 val |

`fixed_v1` audit:

| Pair | Class+Filename Overlap |
|---|---:|
| old_train -> fixed_v1 val | 0 |
| fixed_v1 train -> fixed_v1 val | 0 |
| old_val -> fixed_v1 val | 6,720 |

해석:

```text
fixed_v1은 기존 full-val보다 보수적이다.
다만 fixed_v1 val은 old_val에서 온 샘플이므로 완전 신규 검증셋은 아니다.
```

---

## 3. 현재 모델 실험 요약

### 3.1 Best Single

현재 best single:

```text
B0 supervised-only seed123 fixed_v1
```

| Data | TTA | Top1 | Top3 | Macro-F1 |
|---|---|---:|---:|---:|
| fixed_v1 | hflip | 0.886012 | 0.965327 | 0.885791 |

Checkpoint:

```text
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
```

---

### 3.2 B2 Clean Supervised

Plan:

```text
/Users/sangrok/Desktop/CODEX_B2_CLEAN_SUPERVISED_FIXED_V1_PLAN.md
```

Checkpoint:

```text
data/models/efficientnet_korean_b2_clean_fixed_v1.pt
```

학습은 20epoch 계획이었지만 MPS full fine-tuning 속도가 지나치게 느려져 epoch 4 best checkpoint를 보존하고 중단했다.

| Epoch | Val Top1 | Val Top3 | Macro-F1 | Seconds |
|---:|---:|---:|---:|---:|
| 1 | 0.096577 | 0.219048 | 0.094726 | 210.83 |
| 2 | 0.222619 | 0.408036 | 0.214998 | 211.07 |
| 3 | 0.786458 | 0.926339 | 0.786383 | 2248.29 |
| 4 | 0.833929 | 0.953125 | 0.833526 | 16772.22 |

평가:

| TTA | Top1 | Top3 | Macro-F1 |
|---|---:|---:|---:|
| none | 0.833929 | 0.953125 | 0.833526 |
| hflip | 0.835714 | 0.954762 | 0.835308 |

판단:

```text
B2 단독 모델로는 약하다.
하지만 ensemble diversity member로는 소폭 기여했다.
```

---

## 4. 현재 Best Ensemble

현재 best:

```text
6-model weighted ensemble with B2
```

산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip/
```

구성 모델:

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

비교:

| Candidate | Full Top1 | Full Macro-F1 |
|---|---:|---:|
| 5-model weighted ensemble | 0.898214 | 0.897979 |
| 6-model weighted ensemble | 0.900149 | 0.899900 |
| 6-model diagnostic full-best | 0.900744 | 0.900487 |

주의:

```text
6-model은 full 기준으로 개선됐지만, evaluation split top1은 5-model보다 낮았다.
따라서 현재 best로 기록하되, 최종 운영 후보 확정은 cleaned_v1 이후로 미룬다.
```

---

## 5. Ensemble Weight 안정성 검증

산출물:

```text
reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip_stability/
```

설정:

```text
weight_step=0.05
calibration_ratio=0.5
seeds=0,1,2,7,42,123
num_weight_candidates=53,130
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
full top1은 0.898214~0.900298 범위로 비교적 안정적이다.
B0 supervised-only 기존 모델은 모든 stability seed에서 weight 0으로 빠져 pruning 후보다.
B2는 대부분 seed에서 0.30~0.35를 받지만 seed 7에서는 0이라, 유지하되 최종 확정은 cleaned_v1 이후로 둔다.
```

---

## 6. Label Review / Noise 분석

검수 대상:

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
```

검수용 contact sheet:

```text
reports/error_analysis/final_candidate/contact_sheets/
```

AI visual draft 작성 결과:

```text
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
```

원본 백업:

```text
reports/error_analysis/final_candidate/review_sheet_top300_unreviewed_backup.csv
```

집계 산출물:

```text
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

Noise ratio:

```text
noisy_label_count = 156 / 300
noisy_label_ratio = 0.520000
```

중요한 해석:

```text
이 52%는 전체 데이터 noise ratio가 아니다.
high-confidence error top300만 본 biased sample의 AI draft 결과다.
하지만 cleaned_v1 실험 split을 만들 근거로는 충분하다.
```

---

## 7. Hard Class / Hard Pair 기준

우선 검토할 hard class:

| Group | Classes |
|---|---|
| 찌개/탕 | 동태찌개, 김치찌개, 순두부찌개, 된장찌개, 감자탕 |
| 곰탕류 | 곰탕_설렁탕, 갈비탕, 삼계탕 |
| 고기류 | 갈비구이, 갈비찜, 삼겹살, 보쌈, 족발 |
| 면류 | 라면, 라볶이, 칼국수, 수제비, 잔치국수 |
| 전류 | 감자전, 호박전, 파전, 김치전 |
| 냉면류 | 물냉면, 비빔냉면 |

우선 boundary rule이 필요한 pair:

| Pair | 기준 |
|---|---|
| 곰탕_설렁탕 vs 갈비탕 | 갈비뼈/갈비 형태가 보이면 갈비탕 |
| 김치찌개 vs 동태찌개 | 생선 살/동태 단서가 보이면 동태찌개 |
| 호박전 vs 감자전 | 호박 단면/초록 테두리 visible이면 호박전 |
| 갈비구이 vs 갈비찜 | 구이 자국이면 갈비구이, 국물/찜 양념이면 갈비찜 |
| 비빔냉면 vs 물냉면 | 빨간 양념 비빔 상태면 비빔냉면, 육수 중심이면 물냉면 |
| 칼국수 vs 수제비 | 긴 면이면 칼국수, 뜯은 반죽 조각이면 수제비 |
| 떡볶이 vs 라볶이 | 라면 사리가 명확하면 라볶이 |
| 족발 vs 보쌈 | 껍질/윤기/족발 형태면 족발, 수육 단면 중심이면 보쌈 |

---

## 8. 운영 파일 보호 상태

다음 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

새 모델/리포트는 별도 경로에 저장했다.

---

## 9. 추가/수정된 주요 스크립트

최근 추가:

| Script | Purpose |
|---|---|
| `scripts/build_label_review_contact_sheets.py` | review CSV를 이미지 contact sheet로 변환 |
| `scripts/check_cached_ensemble_stability.py` | cached logits 기반 weight stability 검증 |

최근 수정:

| File | Change |
|---|---|
| `scripts/summarize_label_review.py` | noisy status에 `low_quality`, `out_of_scope` 포함 |
| `src/classifier/food_classifier.py` | `efficientnet_korean_*` companion class/meta 파일 탐색 보강 |

기존 핵심 스크립트:

| Script | Purpose |
|---|---|
| `scripts/audit_kfood_splits.py` | split leakage audit |
| `scripts/build_kfood_fixed_split.py` | fixed_v1 생성 |
| `scripts/eval_kfood_any_model.py` | single model 평가 |
| `scripts/eval_kfood_ensemble.py` | ensemble 평가 |
| `scripts/append_model_to_logits_cache.py` | 기존 cache에 모델 logits 추가 |
| `scripts/sweep_cached_ensemble_weights.py` | cached logits weight sweep |

---

## 10. 현재 10단계 작업 상태

| Step | 작업 | 상태 |
|---:|---|---|
| 1 | `review_sheet_top300.csv` 수동/AI draft 검수 | AI draft 완료 |
| 2 | label noise 비율 계산 | 완료, 52.0% |
| 3 | hard class / hard pair 기준 정리 | 완료 |
| 4 | cleaned_v1 생성 여부 결정 | 생성 권장 |
| 5 | fixed_v1 현재 best ensemble 재평가 | 완료 |
| 6 | cleaned_v1이 생기면 B0 seed123 / seed ensemble 재학습 | 대기 |
| 7 | B2 현재 checkpoint diversity member 유지 | 완료 |
| 8 | B2 재학습/fine-tuning 결정 | cleaned_v1 이후 |
| 9 | ensemble weight 안정성 검증 | 완료 |
| 10 | 운영 후보 선택 | 임시 후보만 선정 |

임시 운영 후보:

```text
6-model weighted ensemble with B2
```

최종 운영 후보로 확정하지 않는 이유:

```text
1. AI draft label review 기준 noisy candidate가 높다.
2. cleaned_v1 실험이 아직 없다.
3. ensemble은 추론 비용이 single보다 크다.
4. B2는 대체로 도움 되지만 모든 calibration seed에서 고정적으로 선택되지는 않는다.
```

---

## 11. 테스트

최근 테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.44s
```

---

## 12. 다음 액션

추천 다음 순서:

1. `reviewed_top300_ai_draft.csv` 기준으로 fixed_v1 train/val에 걸리는 relabel/remove 대상 audit
2. 영향 범위가 확인되면 `korean_food_cleaned_v1` 생성
3. cleaned_v1 기준 현재 best 6-model ensemble 재평가
4. cleaned_v1 기준 B0 seed123 또는 B0 seed ensemble 재학습
5. cleaned_v1 결과가 좋아지면 B2 재학습 여부 결정
6. 운영 후보를 single / pruned ensemble / full ensemble 중 선택

바로 다음에 만들면 좋은 산출물:

```text
reports/cleaned_v1_candidate_audit/
data/raw/korean_food_cleaned_v1/
reports/weighted_ensemble/*cleaned_v1*/
```

---

## 13. 현재 결론

현재 모델링만으로는 fixed_v1 기준 `90.01%`까지 도달했다.

하지만 high-confidence error top300에서 wrong label / multi-food 후보가 매우 많아, 남은 92% gap은 단순 backbone 확장보다 데이터 정제가 더 효율적으로 보인다.

따라서 다음 핵심 단계는 `cleaned_v1` 생성 및 재평가다.
