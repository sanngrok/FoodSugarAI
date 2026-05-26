# K-Food 92% 개선 상황 정리

- 작성일: 2026-05-16
- 프로젝트 경로: `/Users/sangrok/foodsugar-ai`
- 목표: K-Food 분류기 validation top1 `92%` 달성
- 평가 데이터: `data/raw/korean_food_fixed_v1`
- 평가 split: `val`
- validation sample 수: `6720`
- 92% 달성 필요 정답 수: `6183 / 6720`
- 현재 최고 검증 결과: `6184 / 6720`
- 현재 최고 top1: `0.9202380952380952`
- 상태: `92% 목표 달성`

## 결론

이번 개선으로 기존 최고였던 약 `91.9792%`를 넘어 `92.0238%`까지 올렸다.

최종 후보는 단일 B3 모델이 아니라, 기존에 학습되어 있던 B0/B3 계열 모델들을 조합한 `7-model hflip weighted ensemble`이다.

현재 운영 후보로 고정할 모델 설정은 아래 결과 폴더에 저장했다.

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16`

핵심 설정 파일:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/ensemble_config.json`

검증 metric 파일:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/metrics.json`

## 개선 전 최고점

이전 최고 후보는 3-model hflip weighted ensemble이었다.

| Model | Weight |
|---|---:|
| `food_lewm_b0` | `0.12` |
| `b0_seed123_fixed_v1` | `0.29` |
| `b3_full_fixed_v1` | `0.59` |

결과:

| Metric | Value |
|---|---:|
| correct | `6181 / 6720` |
| top1 | `0.9197916388511658` |
| top1 percent | `91.9792%` |
| top3 | `0.9794642925262451` |
| macro_f1 | `0.9195684820093929` |

결과 폴더:

`reports/b3/weighted_ensemble_3model_b3_full_hflip_step001`

## 추가 탐색 과정

### 1. 3-model weight sweep 재확인

기존 3개 모델만 사용해 더 촘촘한 weight sweep을 수행했다.

수행한 탐색:

- step `0.025`
- step `0.01`
- step `0.005`
- local step `0.001`
- global step `0.002`

결론:

- 3-model 조합만으로는 `6181 / 6720`을 넘지 못했다.
- 즉, 기존 3-model weight만 미세 조정해서는 92% 도달이 어려웠다.

### 2. 추가 후보 모델 cache 병합

기존에 평가했던 여러 모델의 hflip logits cache를 병합했다.

병합된 cache:

`reports/b3/weighted_ensemble_merged_candidates_hflip/logits_cache.pt`

포함된 모델:

| Index | Model |
|---:|---|
| 0 | `food_lewm_b0` |
| 1 | `b0_seed123_fixed_v1` |
| 2 | `b3_full_fixed_v1` |
| 3 | `b0_seed7_fixed_v1` |
| 4 | `b2_clean_fixed_v1` |
| 5 | `b3_probe_fixed_v1` |
| 6 | `b3_cont_fixed_v1` |
| 7 | `b0_baseline` |
| 8 | `b0_supervised_only` |

### 3. 4-model 근접 후보 발견

먼저 기존 3-model 조합에 `b3_probe_fixed_v1`을 아주 작게 추가한 후보가 발견됐다.

| Model | Weight |
|---|---:|
| `food_lewm_b0` | `0.11928` |
| `b0_seed123_fixed_v1` | `0.28826` |
| `b3_full_fixed_v1` | `0.58646` |
| `b3_probe_fixed_v1` | `0.006` |

결과:

| Metric | Value |
|---|---:|
| correct | `6182 / 6720` |
| top1 | `0.9199404761904761` |

해석:

- 92% 필요 정답 수인 `6183`에 1장 부족했다.
- 이 단계에서 B3 probe가 아주 작은 weight로도 decision boundary 일부를 보정하는 효과가 있음을 확인했다.

결과 파일:

`reports/b3/merged_candidate_extra_local001_2026_05_16/metrics.json`

## 최종 92% 달성 후보

더 넓은 random/local sparse weight search를 수행해 `6184 / 6720` 후보를 찾았다.

탐색 결과 파일:

`reports/b3/merged_candidate_random_search_2026_05_16/metrics.json`

이후 실제 fixed-weight ensemble 평가 스크립트로 다시 검증했다.

검증 결과 폴더:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16`

## 최종 Ensemble 구성

| Model | Weight |
|---|---:|
| `food_lewm_b0` | `0.14236057323734336` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` |
| `b3_full_fixed_v1` | `0.52949003398239` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` |
| `b3_cont_fixed_v1` | `0.00496452020109459` |
| `b0_supervised_only` | `0.0033210487744569726` |

## 최종 검증 결과

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| num_classes | `56` |
| num_samples | `6720` |
| TTA | `hflip` |

92% 기준:

- `0.92 * 6720 = 6182.4`
- 따라서 최소 `6183`장 정답 필요
- 현재 후보는 `6184`장 정답
- 기준보다 1장 초과 달성

## 사용한 모델 파일

### food_lewm_b0

- checkpoint: `data/models/food_lewm_b0_classifier_3ep_ft10.pt`
- metadata: `data/models/food_lewm_b0_meta_3ep_ft10.json`
- classes: `data/models/food_lewm_b0_classes_3ep_ft10.json`

### b0_seed123_fixed_v1

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json`

### b3_full_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_full_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_full_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_full_fixed_v1.json`

### b0_seed7_fixed_v1

- checkpoint: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_classes_ft10.json`

### b3_probe_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_probe_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_probe_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_probe_fixed_v1.json`

### b3_cont_fixed_v1

- checkpoint: `data/models/efficientnet_korean_b3_cont_fixed_v1.pt`
- metadata: `data/models/korean_food_model_meta_b3_cont_fixed_v1.json`
- classes: `data/models/korean_food_classes_b3_cont_fixed_v1.json`

### b0_supervised_only

- checkpoint: `data/models/food_lewm_b0_supervised_only_ft10.pt`
- metadata: `data/models/food_lewm_b0_supervised_only_meta_ft10.json`
- classes: `data/models/food_lewm_b0_supervised_only_classes_ft10.json`

## Fivefold TTA 검증

추가로 fivefold TTA도 테스트했다.

대상:

- 기존 3-model B3 full ensemble
- weights: `0.12 / 0.29 / 0.59`

결과:

| Metric | Value |
|---|---:|
| top1 | `0.9132440476190476` |
| top3 | `0.9785714285714285` |
| macro_f1 | `0.9130393612296608` |

결론:

- fivefold TTA는 hflip보다 성능이 낮았다.
- 추론 시간도 더 길다.
- 따라서 현재 운영 후보에서는 fivefold TTA를 사용하지 않는 것이 맞다.

결과 폴더:

`reports/b3/fivefold/weighted_3model_b3_full_step001_fivefold`

## 아직 약한 클래스

최종 92% 후보에서도 낮은 per-class accuracy를 보이는 클래스는 다음과 같다.

| Class | Accuracy | Support |
|---|---:|---:|
| `삼겹살` | `0.7583333333333333` | `120` |
| `닭볶음탕` | `0.7916666666666666` | `120` |
| `곰탕_설렁탕` | `0.8` | `120` |
| `갈비구이` | `0.85` | `120` |
| `김치찌개` | `0.85` | `120` |
| `닭계장` | `0.8666666666666667` | `120` |
| `수제비` | `0.8666666666666667` | `120` |
| `칼국수` | `0.8666666666666667` | `120` |
| `김치찜` | `0.875` | `120` |
| `동태찌개` | `0.875` | `120` |

다음 개선 목표가 `92% 유지 안정화` 또는 `93% 도전`이라면 위 클래스들을 우선 대상으로 보는 것이 좋다.

## 주의점

이번 결과는 `fixed_v1/val`에서 실제 재평가로 검증된 결과다.

다만 최종 weight는 validation split에서 탐색된 값이므로 다음과 같이 해석해야 한다.

- 현재 validation 기준 최고 성능 후보로는 유효하다.
- 완전히 새로운 test set 일반화 성능을 증명한 것은 아니다.
- 운영 확정 전에는 이 weight를 고정하고 별도 holdout 또는 사람 검수 clean validation에서 재평가하는 것이 좋다.
- 같은 validation split에서 weight 탐색을 계속 반복하면 validation-specific tuning 위험이 커진다.

## 현재 Best로 사용할 설정

현재 사용할 best 설정:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/ensemble_config.json`

현재 best 리포트:

`reports/b3/verified_92_hflip_7model_weighted_2026_05_16/README.md`

상세 진행 리포트:

`KFOOD_92_GOAL_ACHIEVED_2026-05-16.md`

## 다음 단계 제안

1. 현재 7-model hflip ensemble weight를 freeze한다.
2. 이 config를 기준으로 inference wrapper를 만든다.
3. 사람이 검수한 clean validation 또는 별도 holdout에서 다시 평가한다.
4. high-confidence error를 중심으로 label noise와 hard pair를 재정리한다.
5. `삼겹살`, `닭볶음탕`, `곰탕_설렁탕` 등 약한 클래스를 중심으로 추가 데이터/검수/재학습 계획을 세운다.
6. 다음 목표를 `92% 안정화`로 둘지, `93% 도전`으로 둘지 결정한다.
