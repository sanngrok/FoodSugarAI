# K-Food Cleaned_v1 / B0 / B3 진행 방향 정리

- 작성일: 2026-05-10
- 작업 경로: `/Users/sangrok/foodsugar-ai`
- 목적: 현재까지의 실험 흐름, 중단 판단, label review 방향, 다음 실행 조건을 한 문서로 정리한다.

## 1. 현재 최종 기준선

현재 비교 기준은 `fixed_v1` 기준 best ensemble이다.

- data: `data/raw/korean_food_fixed_v1`
- validation 기준: fixed_v1 `val`
- TTA: `hflip`
- current best ensemble: `reports/weighted_ensemble/b0_family_plus_b2_clean_fixed_v1_hflip`
- top1: `0.900149`
- top3: `0.974405`
- macro_f1: `0.899900`

현재 best single은 B0 seed123 fixed_v1 모델이다.

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`
- top1: `0.886012`
- top3: `0.965327`
- macro_f1: `0.885791`

B2는 단독 운영 후보라기보다 diversity member로 유지한다.

- checkpoint: `data/models/efficientnet_korean_b2_clean_fixed_v1.pt`
- hflip top1: `0.835714`
- current weighted ensemble에서 weight: `0.35`

## 2. 중요한 원칙

이번 방향의 핵심은 단순히 학습을 더 돌리는 것이 아니라, label noise와 hard pair를 정리한 뒤 공정한 validation 기준에서 개선이 반복되는지 확인하는 것이다.

원칙:

- `val_original_fixed` 기준 성능을 공정 비교 기준으로 둔다.
- `val_cleaned` 성능은 corrected-label 진단 수치로만 본다.
- AI visual draft는 운영 확정용 cleaned split의 근거가 아니다.
- 사람이 확정하지 않은 label patch는 `candidate` 또는 `ai_visual_draft`로 격리한다.
- train split 개선량이 충분하지 않으면 B0/B3 재학습으로 넘어가지 않는다.

보호 대상:

- `data/models/efficientnet_korean.pt`
- `data/models/korean_food_classes.json`
- `data/models/korean_food_model_meta.json`
- `data/models/efficientnet_korean_b0_val08275.pt`
- `data/raw/korean_food`
- `data/raw/korean_food_1000`
- `data/raw/korean_food_fixed_v1`

현재까지 위 운영/기준 파일은 덮어쓰지 않았다.

## 3. 왜 cleaned_v1_candidate 생성을 중단했는가

초기 계획은 다음 흐름이었다.

1. AI draft 기반 label patch 생성
2. `cleaned_v1_candidate` split 생성
3. 기존 모델 재평가
4. B0 seed123 cleaned 재학습
5. 조건부 B0 seed ensemble
6. 조건부 B3 probe

하지만 patch impact audit에서 stop 조건에 걸렸다.

입력 검수 파일:

- `reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv`

생성된 patch:

- `data/processed/kfood_label_patch_v1.csv`
- `data/processed/kfood_exclude_list_v1.csv`

AI draft 요약:

| Status | Count |
|---|---:|
| model_error | 144 |
| wrong_label | 126 |
| multi_food | 30 |

noise 후보:

- `wrong_label + multi_food = 156 / 300 = 52.0%`

주의:

- 이 52%는 high-confidence error top300 AI draft 기준이다.
- 전체 데이터 label noise 비율이 아니다.
- 운영 확정용 human review도 아니다.

patch impact 결과:

| Split | Relabel | Remove | Total | Ratio |
|---|---:|---:|---:|---:|
| train | 42 | 7 | 49 | 약 0.10% |
| val | 84 | 23 | 107 | 약 1.59% |

중단 판단:

- patch가 train보다 val에 훨씬 많이 걸렸다.
- 이 상태에서 `cleaned_v1_candidate`를 만들면 재학습 개선 실험보다 validation correction 실험에 가까워진다.
- `val_cleaned` 성능이 올라가더라도 실제 모델 개선인지 label correction 효과인지 분리하기 어렵다.
- 따라서 split 생성, B0 재학습, B3 probe를 보류했다.

관련 파일:

- `KFOOD_CLEANED_V1_STOP_STATUS_2026-05-10.md`
- `reports/cleaned_v1/patch_impact_audit/README.md`
- `reports/cleaned_v1/patch_impact_audit/patch_impact_summary.json`

## 4. 개선 방향: Train-Focused Hard Review

중단 사유를 해소하기 위해 train split에서 실제로 correction 후보를 더 찾는 방향으로 전환했다.

목표:

- train label correction 후보를 늘린다.
- hard class / hard pair 중심으로 사람이 검수할 우선순위를 만든다.
- 사람이 확정한 항목만 cleaned patch로 승격한다.
- train affected가 충분해진 뒤에만 cleaned candidate split을 만든다.

생성한 review sheet:

- script: `scripts/build_train_hard_review_sheet.py`
- review CSV: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- summary: `reports/cleaned_v1/train_hard_review/README.md`
- contact sheets: `reports/cleaned_v1/train_hard_review/contact_sheets/`

구성:

| Source | Count |
|---|---:|
| existing_ai_patch_train_affected | 49 |
| hard_pair_true_side | 177 |
| hard_pair_pred_side | 178 |
| hard_class_extra | 96 |
| total | 500 |

## 5. Current Best Ensemble로 500개 후보 점수화

500개 train hard 후보를 현재 best weighted ensemble로 scoring했다.

scoring:

- script: `scripts/score_review_sheet_with_ensemble.py`
- input: `reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv`
- output: `reports/cleaned_v1/train_hard_review/train_hard_review_scored.csv`
- suspects: `reports/cleaned_v1/train_hard_review/train_hard_review_suspects.csv`
- report: `reports/cleaned_v1/train_hard_review/ensemble_scoring_README.md`
- TTA: `hflip`
- suspect threshold: `0.80`

사용한 weighted ensemble:

| Model | Weight |
|---|---:|
| b0_baseline | 0.00 |
| food_lewm_b0 | 0.15 |
| b0_supervised_only | 0.00 |
| b0_supervised_seed7_fixed_v1 | 0.25 |
| b0_supervised_seed123_fixed_v1 | 0.25 |
| b2_clean_fixed_v1 | 0.35 |

결과:

| Condition | Count |
|---|---:|
| total scored rows | 500 |
| ensemble disagrees with current train label | 51 |
| disagreement confidence >= 0.60 | 22 |
| disagreement confidence >= 0.70 | 15 |
| disagreement confidence >= 0.80 | 7 |
| disagreement confidence >= 0.90 | 1 |

중요:

- `model_suspect`는 확정 label error가 아니다.
- ensemble이 높은 confidence로 틀릴 수 있다.
- 이미지 확인 없이 자동 relabel/remove하면 안 된다.

## 6. Suspect / Conf70 Visual Draft 검토

먼저 confidence `>= 0.80` suspect 7개를 검토했다.

파일:

- `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review.csv`
- `reports/cleaned_v1/train_hard_review/suspect_ai_visual_review_README.md`
- contact sheet: `reports/cleaned_v1/train_hard_review/suspect_contact_sheets/review_sheet_001.jpg`

suspect 7 결과:

| Decision | Count |
|---|---:|
| proposed remove | 2 |
| proposed relabel | 4 |
| proposed keep/model_error | 1 |

이후 confidence `>= 0.70` ensemble-disagree 15개까지 확장했다.

파일:

- `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review.csv`
- `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review_README.md`
- source CSV: `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf70_15.csv`
- contact sheet: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`

conf70 결과:

| Decision | Count |
|---|---:|
| proposed relabel | 8 |
| proposed remove | 3 |
| proposed keep/model_error | 4 |
| apply_to_ai_candidate=yes | 11 |
| apply_to_ai_candidate=no | 4 |

중요한 발견:

- `족발/Img_131_0545.jpg`: ensemble은 `닭갈비`, visual draft는 current label `족발` 유지.
- `물냉면/Img_052_0792.jpg`: ensemble은 `잔치국수`, visual draft는 current label `물냉면` 유지.
- `갈비구이/Img_000_0261.jpg`: ensemble은 `떡갈비`, visual draft는 current label `갈비구이` 유지.

즉, 현재 best ensemble도 hard boundary에서는 충분히 틀릴 수 있다. 따라서 ensemble prediction을 label correction으로 자동 승격하면 안 된다.

## 7. 현재 판단

현재 방향은 타당하다.

- 먼저 label/hard-pair 정리를 진행한다.
- AI draft와 ensemble scoring을 이용해 검수 우선순위를 만든다.
- 사람이 확정한 후에만 cleaned patch를 만든다.
- 공정 비교는 `val_original_fixed`로 한다.
- B3 장기학습은 아직 이르다.

하지만 아직 학습 시작 조건은 충족하지 못했다.

이유:

- 초기 AI patch는 train보다 val에 많이 걸렸다.
- train affected는 49장뿐이었다.
- conf70 visual draft까지 포함해도 correction/remove 후보는 11개 수준이다.
- 전체 train 49,243장 대비 매우 작은 규모다.
- 이 상태로 B0 재학습을 해도 개선이 반복될 가능성이 낮고, compute 대비 정보량이 작다.

따라서 현재 결론은 다음과 같다.

```text
cleaned_v1_candidate 생성: 아직 보류
B0 seed123 cleaned 재학습: 아직 보류
B0 seed7 cleaned 재학습: 아직 보류
B3 probe: 아직 보류
B3 full/CutMix/5-fold TTA: 아직 보류
```

## 8. 다음 실행 조건

다음 단계는 사람이 확정한 train label patch를 만드는 것이다.

우선순위:

1. `conf70_ai_visual_review.csv`의 `apply_to_ai_candidate=yes` 항목을 사람이 확인한다.
2. `train_hard_disagree_conf60_22.csv`까지 확장해서 사람이 확인한다.
3. 필요하면 `train_hard_disagree_all_51.csv` 전체를 확인한다.
4. 확정된 항목만 human-reviewed patch로 만든다.
5. train affected 규모가 충분한지 다시 audit한다.

cleaned candidate 생성 조건:

- human-reviewed train correction/remove 후보가 충분히 모였을 것
- class+filename 충돌이 없을 것
- train/val overlap이 없을 것
- class order가 fixed_v1과 일치할 것
- 원본 split과 운영 모델 파일을 덮어쓰지 않을 것

B0 seed123 cleaned 재학습 조건:

- `data/raw/korean_food_cleaned_v1_candidate`가 안전하게 생성됐을 것
- train은 cleaned candidate `train`
- validation은 반드시 `val_original_fixed`
- 기존 seed123 recipe 유지
- 성공 기준:
  - `> 0.886012`: cleaned train 효과 가능성 있음
  - `>= 0.890`: 긍정적, ensemble 진행 가능
  - `< 0.886012`: patch 품질 또는 train 영향 부족 재검토

B0 seed ensemble 조건:

- seed123 cleaned가 기존과 같거나 높을 때만 seed7 cleaned도 진행
- B0-family weighted ensemble sweep 수행
- current best `0.900149` 초과 여부 확인

B3 probe 조건:

- cleaned candidate 생성
- B0 seed123 cleaned 재학습
- B0-family ensemble 확인
- 위 과정을 통과한 뒤에만 10 epoch probe 수행

B3 full run 조건:

- B3 probe hflip `>= 0.87`, 또는
- B3가 ensemble weight `>= 0.10`을 받고 evaluation split도 개선, 또는
- hard class에서 B0/B2보다 명확히 우수

## 9. 추천 다음 액션

가장 좋은 다음 액션은 학습이 아니라 human review 확정이다.

추천 순서:

1. `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`를 보고 15개를 사람이 확정한다.
2. 확정 결과를 별도 CSV로 저장한다.
3. 확정 CSV 기준으로 human-reviewed train patch를 만든다.
4. patch impact audit을 다시 수행한다.
5. train affected가 충분하지 않으면 `conf60`, `all_disagree_51`, 또는 hard class 추가 mining으로 확장한다.
6. train correction 규모가 의미 있게 커진 뒤 cleaned candidate split을 만든다.

## 10. 검증 상태

최근 검증:

```bash
python3 -m py_compile ...
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

## 11. 한 줄 결론

현재 방향은 “더 큰 모델을 더 오래 학습”이 아니라 “train label/hard pair를 먼저 확정 정리한 뒤, `val_original_fixed` 기준으로 B0 개선이 반복되는지 확인하고, 그 다음에 B3를 probe로만 진입”하는 방향이다.
