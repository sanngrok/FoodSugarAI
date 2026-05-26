# K-Food Classification 진행 상황 및 사용 모델 결정 - 2026-05-15

## 결론

현재 사용할 모델은 **3-model weighted hflip ensemble**로 결정한다.

이 조합이 지금까지 실험 중 가장 높은 성능을 냈다.

| Candidate | top1 | top3 | macro_f1 | 판단 |
|---|---:|---:|---:|---|
| 기존 current best 3-model hflip | 0.913095 | 0.979613 | 0.912846 | 이전 최고 |
| B3 full single, no TTA | 0.903423 | 0.973065 | 0.903170 | 강한 단일 모델 |
| B3 full single, hflip | 0.904315 | 0.974554 | 0.904010 | 단일 모델 기준 최고 |
| **B3 full 포함 3-model hflip ensemble** | **0.919196** | **0.979613** | **0.919031** | **현재 최고 / 사용 후보** |
| B3 continuation + B3 full 4-model hflip ensemble | 0.917857 | 0.979911 | 0.917632 | 3-model보다 낮음 |

최종 운영/실험 후보:

```text
food_lewm_b0              weight 0.20
b0_seed123_fixed_v1       weight 0.25
b3_full_fixed_v1          weight 0.55
TTA                       hflip
```

결과 경로:

```text
reports/b3/weighted_ensemble_3model_b3_full_hflip
```

## 사용할 모델 구성

### 1. Food-LeWM B0

```text
checkpoint: data/models/food_lewm_b0_classifier_3ep_ft10.pt
metadata:   data/models/food_lewm_b0_meta_3ep_ft10.json
classes:    data/models/food_lewm_b0_classes_3ep_ft10.json
image_size: 224
weight:     0.20
```

### 2. B0 seed123 fixed_v1

```text
checkpoint: data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
metadata:   data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_meta_ft10.json
classes:    data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_classes_ft10.json
image_size: 224
weight:     0.25
```

### 3. B3 full fixed_v1 25epoch

```text
checkpoint: data/models/efficientnet_korean_b3_full_fixed_v1.pt
metadata:   data/models/korean_food_model_meta_b3_full_fixed_v1.json
classes:    data/models/korean_food_classes_b3_full_fixed_v1.json
image_size: 300
weight:     0.55
```

## 현재 최고 성능

3-model weighted hflip ensemble:

```text
top1:     0.919196
top3:     0.979613
macro_f1: 0.919031
```

이전 current best 대비:

```text
previous top1: 0.913095
new top1:      0.919196
gain:          +0.006101
```

92% 목표까지 남은 gap:

```text
0.920000 - 0.919196 = 0.000804
약 0.0804%p
```

## 지금까지 진행 흐름

### 1. Fixed_v1 기준 실험 체계 정리

- 기준 데이터는 `data/raw/korean_food_fixed_v1`로 고정했다.
- 공정 비교 기준은 fixed_v1 validation split으로 유지했다.
- 기존 운영/기준 모델 파일은 덮어쓰지 않고, 새 실험은 별도 checkpoint와 report directory에 저장했다.

### 2. 검수 및 label noise 방향 정리

- high-confidence top300 검수 파일을 저장했다.
- train hard-pair candidate 검수 파일을 저장했다.
- label boundary noise와 hard-pair 기반 patch/exclude 방향을 정리했다.
- train patch/exclude audit를 수행했다.

주요 audit 결과:

```text
high-confidence label boundary noise: 62.67%
train patch rows: 23
train affected: 23
val affected: 0
relabel: 14
remove/exclude: 9
```

관련 산출물:

```text
reports/current_best/error_analysis/reviewed_current_best_high_conf_top300.csv
reports/current_best/hard_class_report/reviewed_train_hard_pair_candidates.csv
data/processed/kfood_train_hard_pair_patch_v2.csv
data/processed/kfood_train_hard_pair_exclude_v2.csv
reports/current_best/current_best_review_patch_audit_result_2026-05-14.md
```

### 3. B3 probe / continuation 계열

- B3 probe와 continuation 실험을 통해 B3가 B0 계열과 다른 diversity를 줄 수 있음을 확인했다.
- 기존 best는 B3 continuation을 포함한 3-model hflip ensemble이었다.

이전 current best:

```text
path: reports/current_best/fixed_weight_3model_hflip
top1: 0.913095
macro_f1: 0.912846
```

### 4. B3 full fixed_v1 25epoch 학습

요청대로 중단 조건 없이 25epoch까지 완료했다.

학습 설정:

```text
model: efficientnet_b3
data_dir: data/raw/korean_food_fixed_v1
image_size: 300
epochs: 25
batch_size: 8
grad_accum_steps: 4
lr: 3e-5
head_lr: 3e-4
warmup_epochs: 2
device: MPS
```

출력:

```text
checkpoint: data/models/efficientnet_korean_b3_full_fixed_v1.pt
metadata:   data/models/korean_food_model_meta_b3_full_fixed_v1.json
classes:    data/models/korean_food_classes_b3_full_fixed_v1.json
report:     reports/b3/b3_full_fixed_v1
```

중요 epoch:

| Epoch | val_top1 | top3 | macro_f1 | 메모 |
|---:|---:|---:|---:|---|
| 10 | 0.886607 | 0.970089 | 0.886431 | 중간 기준 |
| 16 | 0.898958 | 0.972619 | 0.898693 | 90% 직전 |
| 19 | 0.900446 | 0.974851 | 0.900224 | single 90% 첫 돌파 |
| 20 | 0.902381 | 0.972619 | 0.902122 | 큰 폭 갱신 |
| 21 | 0.903274 | 0.974405 | 0.903046 | 기존 best 갱신 |
| 25 | 0.903423 | 0.973065 | 0.903170 | 최종 best 저장 |

### 5. B3 full hflip 단일 평가

```text
path: reports/b3/eval_b3_full_fixed_v1_hflip
top1: 0.904315
top3: 0.974554
macro_f1: 0.904010
```

### 6. Ensemble sweep

#### 3-model hflip ensemble

```text
path: reports/b3/weighted_ensemble_3model_b3_full_hflip
weights:
  food_lewm_b0:        0.20
  b0_seed123_fixed_v1: 0.25
  b3_full_fixed_v1:    0.55
full top1:             0.919196
full top3:             0.979613
full macro_f1:         0.919031
```

#### 4-model hflip ensemble

```text
path: reports/b3/weighted_ensemble_4model_b3_cont_full_hflip
weights:
  food_lewm_b0:        0.15
  b0_seed123_fixed_v1: 0.20
  b3_cont_fixed_v1:    0.25
  b3_full_fixed_v1:    0.40
full top1:             0.917857
full top3:             0.979911
full macro_f1:         0.917632
```

4-model은 top3는 약간 높지만 top1과 macro_f1이 3-model보다 낮다. 따라서 현재 운영 후보로는 3-model이 더 적합하다.

## 현재 결정

현재 사용할 모델:

```text
reports/b3/weighted_ensemble_3model_b3_full_hflip
```

운영/데모 기준 추천:

```text
3-model weighted hflip ensemble
food_lewm_b0 0.20 + b0_seed123_fixed_v1 0.25 + b3_full_fixed_v1 0.55
```

선택 이유:

- 지금까지의 full validation top1 최고.
- macro_f1도 최고.
- B3 full 단일 모델이 충분히 강해졌고, B0 계열과 ensemble 시 상승 폭이 큼.
- 4-model보다 단순하면서도 성능이 높음.

## 남은 작업

1. 새 current best 기준으로 high-confidence error analysis 재생성.
2. hard class / hard pair report를 새 best 기준으로 갱신.
3. top300 사람 검수 결과를 새 best 기준으로 재검토.
4. 운영 적용 전 latency 점검.
5. 필요하면 92% 돌파를 위해 다음 후보 실험 진행.

## 다음 실험 후보

현재 92%까지 약 0.0804%p만 남았다.

우선순위:

1. 새 best ensemble 기준 error analysis.
2. 남은 hard class 집중 검수.
3. patch/exclude 반영 cleaned 또는 corrected train split 생성 여부 결정.
4. B3 full을 seed variation으로 한 번 더 학습하거나, B0 seed ensemble을 추가 검토.
5. weight step을 `0.025` 또는 `0.01`로 더 촘촘히 sweep.

## 참고 파일

```text
reports/b3/B3_FULL_FIXED_V1_25E_RESULT_2026-05-15.md
reports/b3/b3_full_fixed_v1/metrics.json
reports/b3/eval_b3_full_fixed_v1_hflip/metrics.json
reports/b3/weighted_ensemble_3model_b3_full_hflip/metrics.json
reports/b3/weighted_ensemble_4model_b3_cont_full_hflip/metrics.json
reports/current_best/current_best_review_patch_audit_result_2026-05-14.md
```
