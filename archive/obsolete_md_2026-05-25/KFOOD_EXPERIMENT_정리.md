# K-Food 실험 진행 상황 정리

- 작성일: 2026-05-10
- 작업 경로: `/Users/sangrok/foodsugar-ai`
- 목적: 지금까지 수행한 K-Food 분류 모델 개선 실험, 검증 결과, 중단 판단, 산출물을 실험 로그 관점에서 정리한다.

## 1. 현재 목표

최종 목표는 K-Food 이미지 분류 모델의 `fixed_v1` 기준 성능을 안정적으로 개선하고, 운영 후보를 선택하는 것이다.

현재 접근은 다음 순서다.

1. 기존 best 기준선을 고정한다.
2. label noise / hard class / hard pair를 분석한다.
3. AI draft와 ensemble scoring으로 검수 우선순위를 만든다.
4. 사람이 확정한 label correction만 cleaned patch로 승격한다.
5. train split 개선 효과가 충분할 때만 `cleaned_v1_candidate`를 만든다.
6. `val_original_fixed` 기준으로 B0 재학습 효과를 확인한다.
7. B0 ensemble이 개선될 때만 B3 probe로 넘어간다.

## 2. 현재 Best Baseline

현재 공정 비교 기준은 `data/raw/korean_food_fixed_v1`의 validation split이다.

### Best Ensemble

- report: `reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip`
- data: `data/raw/korean_food_fixed_v1`
- TTA: `hflip`
- top1: `0.900149`
- top3: `0.974405`
- macro_f1: `0.899900`

ensemble weights:

| Model | Weight |
|---|---:|
| b0_baseline | 0.00 |
| food_lewm_b0 | 0.15 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.25 |
| b0_supervised_seed123_fixed_v1 | 0.25 |
| b2_clean_fixed_v1 | 0.35 |

### Best Single

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`
- top1: `0.886012`
- top3: `0.965327`
- macro_f1: `0.885791`

### B2 역할

- checkpoint: `data/models/efficientnet_korean_b2_clean_fixed_v1.pt`
- hflip top1: `0.835714`
- hflip top3: `0.954762`
- macro_f1: `0.835308`
- 판단: 단독 후보가 아니라 ensemble diversity member로 유지한다.

## 3. Fixed_v1 Split 상태

확인된 split 상태:

| Split | Count |
|---|---:|
| train | 49,243 |
| val | 6,720 |
| classes | 56 |

확인 내용:

- fixed_v1 class order 유지
- old_train -> fixed_v1 val class+filename overlap: 0
- fixed_v1 train -> fixed_v1 val class+filename overlap: 0
- MPS 사용 가능

## 4. 기존 평가/학습 스크립트 호환 작업

cleaned split 실험을 위해 스크립트 호환 작업을 진행했다.

수정/추가된 주요 기능:

- `--val-subdir` 지원
- `--train-subdir` 지원
- `--head-lr` 지원
- `efficientnet_korean_*` companion metadata/classes path lookup 보강

관련 파일:

- `scripts/eval_kfood_any_model.py`
- `scripts/eval_kfood_ensemble.py`
- `scripts/eval_weighted_ensemble_sweep.py`
- `scripts/train_food_lewm_classifier.py`
- `src/classifier/train_classifier_korean.py`
- `src/classifier/food_classifier.py`
- `src/data/prepare_kfood_cleaned_split.py`

검증:

- `python3 -m py_compile` 통과
- `python3 -m pytest tests/ -q` 통과
- 최근 결과: `18 passed`

## 5. AI Draft 기반 Top300 Error Review

초기 label correction 후보는 high-confidence error top300에서 만들었다.

입력:

- `reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv`

AI draft review summary:

| Status | Count |
|---|---:|
| model_error | 144 |
| wrong_label | 126 |
| multi_food | 30 |

noise 후보:

- wrong_label + multi_food = 156 / 300
- 비율: 52.0%

주의:

- 이 52.0%는 high-confidence error top300 기준이다.
- 전체 train/val 데이터셋의 label noise 비율이 아니다.
- 사람이 확정한 운영용 review가 아니다.

생성 산출물:

- `data/processed/kfood_label_patch_v1.csv`
- `data/processed/kfood_exclude_list_v1.csv`
- `reports/error_analysis/final_candidate/label_patch_v1_summary.md`

patch action:

| Action | Count |
|---|---:|
| relabel | 126 |
| remove | 30 |
| total | 156 |

검증:

- patch rows: 156
- unique class+filename keys: 156
- duplicates: 0

## 6. Patch Impact Audit

AI draft patch가 fixed_v1 train/val에 얼마나 영향을 주는지 audit했다.

script:

- `scripts/audit_label_patch_impact.py`

출력:

- `reports/cleaned_v1/patch_impact_audit/README.md`
- `reports/cleaned_v1/patch_impact_audit/patch_impact_summary.json`
- `reports/cleaned_v1/patch_impact_audit/train_affected.csv`
- `reports/cleaned_v1/patch_impact_audit/val_affected.csv`
- `reports/cleaned_v1/patch_impact_audit/per_class_impact.csv`

결과:

| Split | Relabel | Remove | Total | Ratio |
|---|---:|---:|---:|---:|
| train | 42 | 7 | 49 | 약 0.10% |
| val | 84 | 23 | 107 | 약 1.59% |

중단 판단:

- patch가 train보다 val에 훨씬 많이 걸렸다.
- `cleaned_v1_candidate`를 만들면 재학습 개선 실험보다 validation correction 실험에 가까워진다.
- `val_cleaned`만 좋아지는 결과가 나올 위험이 크다.
- 따라서 split 생성, B0 재학습, B3 probe를 중단했다.

중단 상태 기록:

- `KFOOD_CLEANED_V1_STOP_STATUS_2026-05-10.md`
- `reports/cleaned_v1/cleaned_v1_b3_roadmap_result.md`

## 7. Cleaned_v1_candidate 생성 보류

아직 생성하지 않은 것:

- `data/raw/korean_food_cleaned_v1_candidate`
- `val_original_fixed`
- `val_cleaned`
- cleaned candidate 기준 기존 모델 재평가
- B0 seed123 cleaned 재학습
- B0 seed7 cleaned 재학습
- B3 probe
- B3 full / CutMix / 5-fold TTA

보류 이유:

- train correction 규모가 너무 작다.
- 현재 patch는 val correction 효과가 더 크다.
- 사람이 확정한 patch가 아니다.
- 이 상태에서 학습하면 결과 해석이 애매해진다.

## 8. Train-Focused Hard Review 생성

중단 사유를 해소하기 위해 train split 중심의 hard review 후보를 만들었다.

script:

- `scripts/build_train_hard_review_sheet.py`

산출물:

- `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- `reports/cleaned_v1/train_hard_review/README.md`
- `reports/cleaned_v1/train_hard_review/contact_sheets/`

구성:

| Source | Count |
|---|---:|
| existing_ai_patch_train_affected | 49 |
| hard_pair_true_side | 177 |
| hard_pair_pred_side | 178 |
| hard_class_extra | 96 |
| total | 500 |

목적:

- train split에서 실제 label correction 후보를 더 찾는다.
- hard class / hard pair 중심으로 사람이 검수할 우선순위를 만든다.
- 학습 전에 train 개선량을 확보한다.

## 9. Train Hard Review 500개 Ensemble Scoring

500개 후보를 현재 best weighted ensemble로 scoring했다.

script:

- `scripts/score_review_sheet_with_ensemble.py`

입력:

- `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`

출력:

- `reports/cleaned_v1/train_hard_review/train_hard_review_scored.csv`
- `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`
- `reports/cleaned_v1/train_hard_review/ensemble_scoring_README.md`

설정:

- TTA: `hflip`
- suspect threshold: `0.80`
- ensemble: current best 6-model weighted ensemble

결과:

| Condition | Count |
|---|---:|
| total scored rows | 500 |
| ensemble disagrees with current train label | 51 |
| disagreement confidence >= 0.60 | 22 |
| disagreement confidence >= 0.70 | 15 |
| disagreement confidence >= 0.80 | 7 |
| disagreement confidence >= 0.90 | 1 |

해석:

- ensemble scoring은 검수 우선순위 생성에는 유용하다.
- 하지만 ensemble prediction 자체를 label correction으로 자동 승격하면 안 된다.
- 실제로 뒤의 visual draft에서 ensemble이 틀린 hard-boundary 사례가 확인됐다.

## 10. Contact Sheet 개선

검수 편의를 위해 contact sheet 생성 스크립트를 수정했다.

파일:

- `scripts/build_label_review_contact_sheets.py`

수정 내용:

- 기존에는 `confidence` 컬럼만 읽어 suspect contact sheet에 `conf 0.000`으로 표시되는 문제가 있었다.
- `ensemble_confidence`와 `ensemble_pred_label`을 우선 사용하도록 수정했다.

재생성된 contact sheets:

- `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/review_sheet_001.jpg`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf60/review_sheet_001.jpg`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_all_disagree/`

## 11. Suspect 7 AI Visual Draft Review

confidence `>= 0.80` suspect 7개를 먼저 visual draft로 검토했다.

입력:

- `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`

출력:

- `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review.csv`
- `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review_README.md`

결과:

| Decision | Count |
|---|---:|
| proposed remove | 2 |
| proposed relabel | 4 |
| proposed keep/model_error | 1 |

주요 판단:

- `후라이드치킨/Img_028_0432.jpg`는 후라이드치킨과 양념치킨이 같이 중심에 있어 relabel보다 remove가 적절해 보인다.
- `갈비구이/Img_000_0065.JPG`는 갈비찜 후보로 보인다.
- `김치찌개/Img_119_0156.jpg`, `김치찌개/Img_119_0141.jpg`는 순두부찌개 후보로 보인다.
- `족발/Img_131_0545.jpg`는 ensemble/기존 draft와 달리 current label `족발` 유지가 더 타당해 보인다.

주의:

- 이 검토는 AI visual draft다.
- 운영 확정용 human review가 아니다.

## 12. Confidence 0.70+ Visual Draft Review

confidence `>= 0.70` ensemble-disagree 15개까지 검토 범위를 확장했다.

입력:

- `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf70_15.csv`

출력:

- `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review.csv`
- `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review_README.md`
- contact sheet: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`

결과:

| Decision | Count |
|---|---:|
| proposed relabel | 8 |
| proposed remove | 3 |
| proposed keep/model_error | 4 |
| apply_to_ai_candidate=yes | 11 |
| apply_to_ai_candidate=no | 4 |

중요한 발견:

- `족발/Img_131_0545.jpg`: ensemble은 `닭갈비`, visual draft는 `족발` 유지.
- `물냉면/Img_052_0792.jpg`: ensemble은 `잔치국수`, visual draft는 `물냉면` 유지.
- `갈비구이/Img_000_0261.jpg`: ensemble은 `떡갈비`, visual draft는 `갈비구이` 유지.

해석:

- current best ensemble도 hard boundary에서는 틀릴 수 있다.
- 따라서 model disagreement는 label error 후보일 뿐, 확정값이 아니다.
- 최종 cleaned patch에는 human confirmation이 필요하다.

## 13. Prioritized Review Subsets

ensemble disagreement 기준으로 사람이 볼 우선 검수 묶음을 만들었다.

생성 파일:

- `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf70_15.csv`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf60_22.csv`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_all_51.csv`

contact sheets:

- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf60/`
- `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_all_disagree/`

추천 검수 순서:

1. confidence `>= 0.70` 15개
2. confidence `>= 0.60` 22개
3. ensemble disagreement 전체 51개
4. 필요 시 train hard review 전체 500개

## 14. 현재 실험 결론

현재까지의 실험 결과, 바로 학습을 재개하지 않는 것이 맞다.

이유:

- AI draft patch는 train보다 val에 많이 걸렸다.
- train affected는 49장뿐이었다.
- train hard review 500개를 ensemble scoring해도 high-confidence suspect는 7개뿐이었다.
- confidence 0.70 이상까지 넓혀도 correction/remove 후보는 11개 수준이다.
- 전체 train 49,243장 대비 매우 작다.
- 현 단계에서 B0/B3를 학습하면 개선 가능성보다 결과 해석 리스크가 크다.

현재 보류:

- `cleaned_v1_candidate` 생성
- B0 seed123 cleaned 재학습
- B0 seed7 cleaned 재학습
- B3 probe
- B3 full
- CutMix
- 5-fold TTA 운영 후보 반영

## 15. 다음 실험 조건

다음 실험은 human-reviewed train patch가 생긴 뒤 진행한다.

필요 조건:

- 사람이 `conf70_ai_visual_review.csv`의 후보를 확정한다.
- 부족하면 `conf60`, `all_disagree_51`, hard class 추가 mining으로 확장한다.
- 확정된 항목만 human-reviewed patch로 저장한다.
- patch impact audit을 다시 수행한다.
- train affected가 의미 있게 커졌는지 확인한다.

cleaned candidate 생성 조건:

- class+filename 충돌 없음
- train/val overlap 없음
- class order fixed_v1과 일치
- 운영/원본 파일 덮어쓰기 없음
- `val_original_fixed`와 `val_cleaned` 분리

B0 seed123 cleaned 재학습 조건:

- `data/raw/korean_food_cleaned_v1_candidate` 생성 완료
- train subdir: `train`
- validation subdir: `val_original_fixed`
- 기존 seed123 recipe 유지

성공 판단:

| Result | Interpretation |
|---|---|
| `> 0.886012` | cleaned train 효과 가능성 있음 |
| `>= 0.890` | 긍정적, ensemble 진행 가능 |
| `< 0.886012` | patch 품질 또는 train 영향 부족 재검토 |

B3 probe 조건:

- cleaned candidate 생성 후
- B0 seed123 cleaned 재학습 후
- B0-family ensemble 확인 후
- 10epoch probe만 먼저 수행

B3 full 조건:

- B3 probe hflip `>= 0.87`, 또는
- B3가 ensemble weight `>= 0.10`을 받고 evaluation split도 개선, 또는
- hard class에서 B0/B2보다 명확히 우수

## 16. 생성/수정한 주요 스크립트

추가:

- `scripts/build_kfood_label_patch.py`
- `scripts/audit_label_patch_impact.py`
- `src/data/prepare_kfood_cleaned_split.py`
- `scripts/build_train_hard_review_sheet.py`
- `scripts/score_review_sheet_with_ensemble.py`

수정:

- `scripts/eval_kfood_any_model.py`
- `scripts/eval_kfood_ensemble.py`
- `scripts/eval_weighted_ensemble_sweep.py`
- `scripts/train_food_lewm_classifier.py`
- `src/classifier/train_classifier_korean.py`
- `src/classifier/food_classifier.py`
- `scripts/build_label_review_contact_sheets.py`

## 17. 주요 MD 산출물

- `KFOOD_CLEANED_V1_STOP_STATUS_2026-05-10.md`
- `KFOOD_TRAIN_HARD_REVIEW_STATUS_2026-05-10.md`
- `KFOOD_CLEANED_V1_DIRECTION_SUMMARY_2026-05-10.md`
- `reports/cleaned_v1/cleaned_v1_b3_roadmap_result.md`
- `reports/cleaned_v1/patch_impact_audit/README.md`
- `reports/cleaned_v1/train_hard_review/README.md`
- `reports/cleaned_v1/train_hard_review/ensemble_scoring_README.md`
- `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review_README.md`
- `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review_README.md`

## 18. 검증 상태

최근 검증:

```bash
python3 -m py_compile ...
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

## 19. 최종 요약

현재까지의 실험은 “학습을 더 돌리는 단계”가 아니라 “학습 전에 train label correction 근거를 확보하는 단계”다.

핵심 결론:

- current best fixed_v1 ensemble은 `top1=0.900149`다.
- AI draft 기반 cleaned patch는 val에 치우쳐 있어 그대로 학습하면 안 된다.
- train-focused hard review 500개를 만들고 ensemble scoring까지 완료했다.
- high-confidence suspect는 적고, ensemble도 hard boundary에서 틀리는 사례가 있다.
- 따라서 human review 확정 없이 cleaned split / B0 재학습 / B3 probe로 넘어가면 안 된다.
- 다음 액션은 `conf70` -> `conf60` -> `all_disagree_51` 순서의 human review 확정이다.
