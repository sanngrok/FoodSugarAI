# B3 Next Stage After Probe Result

작성일: 2026-05-13  
기준 데이터: `data/raw/korean_food_fixed_v1`  
기준 validation: `val`  
목표: B3 probe 이후 continuation, ensemble, TTA로 92% 접근 가능성 검증

## 1. 결론

B3 continuation은 성공이다.

- B3 probe hflip: `top1=0.888839`
- B3 continuation epoch 6 hflip: `top1=0.895982`
- B3 probe 3-model weighted ensemble: `top1=0.911310`
- B3 continuation 3-model weighted ensemble: `top1=0.913095`

다만 fivefold TTA는 개선이 아니라 악화였다.

- B3 continuation hflip ensemble: `top1=0.913095`
- B3 continuation fivefold ensemble: `top1=0.907292`

따라서 현재 운영 후보는 fivefold가 아니라 hflip weighted ensemble이다.

## 2. B3 Continuation 학습 상태

원래 10epoch continuation을 계획했지만, 2026-05-12에 epoch 6 validation까지 수행한 뒤 사용자가 요청해 중단했다.

best checkpoint는 epoch 6에서 저장되었다.

| checkpoint | epoch | val_top1 | val_top3 | macro_f1 |
|---|---:|---:|---:|---:|
| `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` | 6 | 0.893155 | 0.972470 | 0.892909 |

관련 파일:

- `data/models/efficientnet_korean_b3_cont_fixed_v1.pt`
- `data/models/korean_food_classes_b3_cont_fixed_v1.json`
- `data/models/korean_food_model_meta_b3_cont_fixed_v1.json`
- `reports/b3/b3_cont_fixed_v1/train_log.csv`

## 3. 단일 모델 평가

| model | TTA | top1 | top3 | macro_f1 | report |
|---|---|---:|---:|---:|---|
| B3 continuation | none | 0.893155 | 0.972470 | 0.892909 | `reports/b3/eval_b3_cont_fixed_v1_none` |
| B3 continuation | hflip | 0.895982 | 0.974107 | 0.895791 | `reports/b3/eval_b3_cont_fixed_v1_hflip` |

판단:

- probe hflip `0.888839` 대비 `+0.007143`
- 계획서 기준 `B3 continuation hflip >= 0.895` 조건을 충족
- single 기준으로도 continuation은 유효

## 4. 3-Model Weighted Ensemble

구성:

- `food_lewm_b0`: `data/models/food_lewm_b0_classifier_3ep_ft10.pt`
- `b0_seed123_fixed_v1`: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`
- `b3_cont_fixed_v1`: `data/models/efficientnet_korean_b3_cont_fixed_v1.pt`

seed42, weight step 0.05 결과:

| metric | value |
|---|---:|
| top1 | 0.913095 |
| top3 | 0.979613 |
| macro_f1 | 0.912846 |
| weights | `0.20 / 0.25 / 0.55` |

Best weights:

```text
food_lewm_b0        0.20
b0_seed123_fixed_v1 0.25
b3_cont_fixed_v1    0.55
```

비교:

| candidate | top1 | macro_f1 |
|---|---:|---:|
| B3 probe weighted ensemble | 0.911310 | 0.911089 |
| B3 continuation weighted ensemble | 0.913095 | 0.912846 |

개선폭:

- top1: `+0.001786`
- macro_f1: `+0.001756`

## 5. Ensemble Stability

같은 logits cache를 사용해 calibration seed만 바꿔 안정성을 확인했다.

| seed | weight step | weights | full top1 | full top3 | macro_f1 |
|---:|---:|---|---:|---:|---:|
| 42 | 0.05 | `0.20 / 0.25 / 0.55` | 0.913095 | 0.979613 | 0.912846 |
| 7 | 0.05 | `0.20 / 0.25 / 0.55` | 0.913095 | 0.979613 | 0.912846 |
| 123 | 0.05 | `0.25 / 0.30 / 0.45` | 0.912202 | 0.978869 | 0.911994 |
| 42 | 0.025 | `0.225 / 0.20 / 0.575` | 0.912500 | 0.979018 | 0.912272 |

판단:

- B3 continuation weight는 `0.45~0.575`로 안정적으로 높다.
- 모든 seed 결과가 probe ensemble `0.911310` 이상 또는 근접 상회 수준이다.
- 0.025 step은 최고점을 갱신하지 못했다.
- 현재 best는 seed42/seed7의 `0.20 / 0.25 / 0.55` 조합이다.

## 6. Fivefold TTA

Best hflip weights `0.20 / 0.25 / 0.55`를 고정하고 fivefold TTA를 적용했다.

| candidate | TTA | top1 | top3 | macro_f1 |
|---|---|---:|---:|---:|
| B3 continuation ensemble | hflip | 0.913095 | 0.979613 | 0.912846 |
| B3 continuation ensemble | fivefold | 0.907292 | 0.979018 | 0.907179 |

판단:

- fivefold는 top1 기준 `-0.005804` 악화
- 92% 돌파 실패
- 현재 fivefold 구현은 운영 후보에서 제외
- hflip weighted ensemble을 유지하는 것이 맞다.

## 7. Plus4 추가 학습 시도

epoch 6 continuation checkpoint에서 `lr=3e-6`, 4epoch 추가 fine-tuning을 별도 경로로 시도했다.

보호를 위해 기존 best checkpoint는 덮어쓰지 않았다.

출력:

- `data/models/efficientnet_korean_b3_cont_plus4_fixed_v1.pt`
- `data/models/korean_food_model_meta_b3_cont_plus4_fixed_v1.json`
- `reports/b3/b3_cont_plus4_fixed_v1`

epoch 1 결과:

| run | epoch | val_top1 | val_top3 | macro_f1 |
|---|---:|---:|---:|---:|
| B3 cont plus4 | 1 | 0.891220 | 0.971577 | 0.890778 |

판단:

- 원본 epoch 6 checkpoint `0.893155`보다 낮다.
- 추가 continuation은 개선 신호가 약해 조기 중단했다.
- 운영 후보는 plus4가 아니라 epoch 6 B3 continuation이다.

## 8. 현재 Best 후보

현재 best 운영 후보:

```text
3-model weighted ensemble, hflip
top1     0.913095
top3     0.979613
macro_f1 0.912846
weights  food_lewm_b0=0.20, b0_seed123_fixed_v1=0.25, b3_cont_fixed_v1=0.55
```

이전 전체 best `0.900149` 대비:

- top1 개선폭: `+0.012946`

92%까지 남은 gap:

- `0.920000 - 0.913095 = 0.006905`

94%까지 남은 gap:

- `0.940000 - 0.913095 = 0.026905`

## 9. B3 Full Run 여부

현재 B3 full 25epoch는 아직 시작하지 않았다.

이유:

- B3 continuation은 성공했지만 92%까지는 아직 `0.0069` gap이 남아 있다.
- fivefold TTA가 악화되어 단순 TTA 확대만으로는 해결 가능성이 낮다.
- 현재 환경에서 epoch 시간이 길고, 25epoch full run은 장시간 점유가 예상된다.
- 따라서 full run은 다음 장시간 실험으로 분리하는 것이 안전하다.

다음 실행 후보:

1. B3 full 25epoch fixed_v1 장시간 실험
2. B3/B0/B2 포함 4~6 model ensemble에서 continuation member 재조합
3. hard class 중심 오류 분석 후 label/hard-pair cleaning 재개

## 10. 검증

실행 완료:

```bash
python3 -m py_compile scripts/eval_fixed_weight_ensemble.py scripts/eval_weighted_ensemble_sweep.py scripts/eval_kfood_any_model.py src/classifier/train_classifier_korean.py
python3 -m pytest tests/ -q
```

결과:

```text
18 passed
```

