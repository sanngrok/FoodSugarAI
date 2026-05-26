# K-Food Train Hard Review 진행상황

- 작성일: 2026-05-10
- 목적: `cleaned_v1_candidate`를 바로 만들기 전에, 실제 train split에 충분한 label correction 효과가 있는지 검증한다.
- 기준 baseline: fixed_v1 hflip 6-model weighted ensemble `top1=0.900149`
- 현 결론: 아직 B0/B3 추가 학습으로 넘어가지 않는다. 현재 patch는 train보다 val에 많이 걸리므로, train label 개선 근거를 더 확보해야 한다.

## 1. 이전 중단 사유

AI visual draft 기반 patch를 만들고 impact audit을 수행했다.

- 입력 검수 파일: `reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv`
- patch: `data/processed/kfood_label_patch_v1.csv`
- exclude: `data/processed/kfood_exclude_list_v1.csv`
- audit report: `reports/cleaned_v1/patch_impact_audit/README.md`

영향 범위:

- fixed_v1 train affected: 49 / 49,243, 약 0.10%
- fixed_v1 val affected: 107 / 6,720, 약 1.59%
- action summary:
  - train: relabel 42, remove 7
  - val: relabel 84, remove 23

중단 판단:

- patch가 mostly val 쪽에 걸렸다.
- 이 상태로 `cleaned_v1_candidate`를 만들면, 재학습 개선 실험이라기보다 val correction 실험이 될 가능성이 높다.
- 따라서 split 생성, B0 재학습, B3 probe는 보류했다.

## 2. 개선 방향

중단 사유를 해소하기 위해 train-focused hard review를 생성했다.

- 생성 스크립트: `scripts/build_train_hard_review_sheet.py`
- 출력 CSV: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- 전체 contact sheets: `reports/cleaned_v1/train_hard_review/contact_sheets/`
- 요약: `reports/cleaned_v1/train_hard_review/README.md`

구성:

- total rows: 500
- existing_ai_patch_train_affected: 49
- hard_pair_true_side: 177
- hard_pair_pred_side: 178
- hard_class_extra: 96

상위 포함 class 예:

- 갈비구이
- 곰탕_설렁탕
- 김치찌개
- 동태찌개
- 칼국수
- 삼겹살
- 갈비찜
- 라면

## 3. Current Best Ensemble로 Review Sheet 점수화

500개 train hard review 후보를 현재 best weighted ensemble로 scoring했다.

- scoring script: `scripts/score_review_sheet_with_ensemble.py`
- input: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- scored output: `reports/cleaned_v1/train_hard_review/train_hard_review_scored.csv`
- suspects output: `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`
- scoring report: `reports/cleaned_v1/train_hard_review/ensemble_scoring_README.md`
- TTA: `hflip`
- suspect threshold: `0.80`

사용한 ensemble:

- `b0_baseline`: weight 0.00
- `food_lewm_b0`: weight 0.15
- `b0_supervised_only`: weight 0.00
- `b0_supervised_seed7_fixed_v1`: weight 0.25
- `b0_supervised_seed123_fixed_v1`: weight 0.25
- `b2_clean_fixed_v1`: weight 0.35

결과:

- total scored rows: 500
- ensemble disagrees with current train label: 51
- confidence >= 0.60 disagreement: 22
- confidence >= 0.70 disagreement: 15
- confidence >= 0.80 disagreement: 7
- confidence >= 0.90 disagreement: 1
- auto-prefilled `model_suspect`: 2

중요:

- `model_suspect`는 확정 label error가 아니다.
- 모델 앙상블의 고신뢰 불일치일 뿐이므로, 이미지 확인 없이 자동 relabel/remove하면 안 된다.

## 4. Suspect Contact Sheet

상위 suspect 7장을 별도 contact sheet로 만들었다.

- suspect contact sheet dir: `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/`
- sheet: `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/review_sheet_001.jpg`
- index: `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/README.md`

확인 대상 7개:

| rank | current label | ensemble label | confidence | status |
|---:|---|---|---:|---|
| 37 | 양념치킨 | 족발 | 0.9678 | existing AI draft remove 후보 |
| 250 | 후라이드치킨 | 양념치킨 | 0.8973 | model_suspect |
| 1 | 갈비구이 | 갈비찜 | 0.8593 | existing AI draft relabel 후보 |
| 35 | 약식 | 잡곡밥 | 0.8310 | existing AI draft relabel 후보 |
| 41 | 족발 | 닭갈비 | 0.8284 | existing AI draft relabel 후보 |
| 12 | 김치찌개 | 순두부찌개 | 0.8164 | existing AI draft relabel 후보 |
| 163 | 김치찌개 | 순두부찌개 | 0.8009 | model_suspect |

## 5. 현재 판단

현재까지 자동/AI 기반으로 train split에서 강하게 의심되는 신규 후보는 많지 않다.

- 이미 AI draft train patch에 잡힌 항목: 49
- ensemble scoring으로 새롭게 강하게 의심된 항목: 2
- 합산해도 train correction 규모는 약 51장 수준이다.

따라서 지금 바로 `cleaned_v1_candidate` 생성 후 B0 재학습을 돌리면, 학습 데이터 개선 효과가 매우 작을 가능성이 높다.

## 6. 권장 다음 단계

1. `suspect_contact_sheets/review_sheet_001.jpg`의 7개를 사람이 먼저 확인한다.
2. `train_hard_review_sheet.csv` 전체 500개 중 hard class/pair 중심으로 사람이 추가 확정한다.
3. 확정된 항목만 별도 human-reviewed patch로 승격한다.
4. train affected가 충분히 커졌을 때만 `cleaned_v1_candidate`를 만든다.
5. 이후 `val_original_fixed` 기준으로 B0 seed123 cleaned 재학습을 시작한다.

## 7. 보류 중인 작업

- `data/raw/korean_food_cleaned_v1_candidate` 생성: 보류
- B0 seed123 cleaned 재학습: 보류
- B0 seed7 cleaned 재학습: 보류
- B3 probe: 보류
- B3 full / CutMix / 5-fold TTA: 보류

보류 이유는 명확하다. 현재 correction 후보가 val 쪽에 치우쳐 있고, train 쪽 개선량이 아직 작아서 재학습 효과 검증으로 보기 어렵다.

## 8. 2026-05-10 추가 진행

이 파일의 권장 다음 단계에 따라 suspect 7개를 먼저 visual draft로 검토했고, 이후 confidence 0.70 이상 ensemble-disagree 15개까지 우선 검수 묶음을 확장했다.

생성 파일:

- suspect 7 AI visual draft: `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review.csv`
- suspect 7 요약: `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review_README.md`
- confidence 0.70+ AI visual draft: `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review.csv`
- confidence 0.70+ 요약: `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review_README.md`
- confidence 0.70+ review CSV: `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf70_15.csv`
- confidence 0.60+ review CSV: `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf60_22.csv`
- all ensemble-disagree CSV: `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_all_51.csv`
- confidence 0.70+ contact sheet: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`
- confidence 0.60+ contact sheet: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf60/review_sheet_001.jpg`
- all ensemble-disagree contact sheets: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_all_disagree/`

검토 결과:

- suspect 7:
  - proposed remove: 2
  - proposed relabel: 4
  - proposed keep/model_error: 1
- confidence 0.70+ 15:
  - proposed remove: 3
  - proposed relabel: 8
  - proposed keep/model_error: 4

중요한 발견:

- `족발/Img_131_0545.jpg`는 기존 AI draft와 ensemble이 `닭갈비`로 의심했지만, 확대 확인상 current label `족발` 유지가 더 타당하다.
- `물냉면/Img_052_0792.jpg`는 ensemble이 `잔치국수`로 의심했지만, current label `물냉면` 유지가 더 타당하다.
- `갈비구이/Img_000_0261.jpg`는 ensemble이 `떡갈비`로 의심했지만, current label `갈비구이` 유지가 더 타당하다.

현재 판단:

- 우선 검수 후보는 정리됐지만, 여전히 운영 확정용 human review가 아니다.
- confidence 0.70 이상에서도 correction/remove 후보는 11개 수준이다.
- 따라서 아직 `cleaned_v1_candidate` 생성과 B0/B3 재학습은 보류한다.
- 다음으로는 사람이 `conf70_ai_visual_review.csv` 또는 contact sheet를 보고 `apply_to_ai_candidate=yes` 항목을 확정해야 한다.
