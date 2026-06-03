# FoodSugar AI 프로젝트 전체 진행 보고서 제출용 초안 - 2026-05-27

## 문서 목적

이 문서는 FoodSugar AI 프로젝트의 전체 진행 과정을 제출 서류로 다시 구성하기 위한 장문 정리본이다. 지금까지 진행한 작업은 크게 두 축으로 나뉜다. 첫 번째 축은 음식 이미지를 입력받아 한국 음식 56개 클래스를 분류하는 K-Food 이미지 분류 모델 개발이다. 두 번째 축은 음식 영양성분, 혈당 위험도 점수, OhioT1DM 기반 CGM 시계열 예측, 저혈당/고혈당 가능성 신호, 예측 범위와 불확실성 표시를 연결한 웰니스 혈당 기능 개발이다. 여기에 마지막으로 사용자가 직접 체험할 수 있는 Vite React TypeScript 기반 웹 MVP까지 구현했다.

이 문서는 모델 학습 과정만 나열하는 문서가 아니라, 프로젝트가 왜 시작되었고, 어떤 문제를 풀려고 했으며, 어떤 데이터와 모델을 사용했고, 실험 과정에서 무엇을 발견했으며, 최종적으로 어떤 제품 구조로 발전했는지를 한 흐름으로 설명하기 위해 작성되었다. 제출 서류를 새로 만들 때 이 문서를 기반으로 요약본, 발표 자료, 기술 보고서, 포트폴리오 설명, 공모전 제안서 등을 다시 구성할 수 있도록 최대한 세부적으로 정리했다.

혈당 관련 기능은 본 프로젝트에서 매우 중요한 부분이지만, 이 문서 전체에서 일관되게 강조해야 하는 원칙이 있다. FoodSugar AI의 혈당 기능은 의료 진단, 치료 지침, 인슐린 또는 약물 조절 안내를 제공하는 기능이 아니다. 이 기능은 음식 사진과 영양성분, CGM 데이터가 있는 경우의 혈당 변화 가능성을 참고용으로 보여주는 웰니스 및 식습관 관리 보조 기능이다. 따라서 혈당 관련 결과는 항상 “참고용”, “가능성 신호”, “예측 범위”, “불확실성”이라는 표현과 함께 제시되어야 하며, 사용자는 실제 혈당 측정값과 증상, 의료진의 판단을 우선해야 한다.

---

## 1. 프로젝트 한 줄 정의

FoodSugar AI는 음식 사진을 분석해 음식명을 분류하고, 해당 음식의 영양성분과 혈당 부담을 참고용으로 보여주며, CGM 데이터가 있는 경우 식후 30분, 60분, 90분 뒤 혈당 변화 가능성을 예측 범위와 불확실성 중심으로 제공하는 웰니스 AI 서비스이다.

이 문장을 더 제품적으로 풀어 쓰면 다음과 같다.

```text
FoodSugar AI는 음식 사진을 업로드하면 AI가 음식을 분류하고,
영양성분을 조회한 뒤, 음식 기반 혈당 부담을 참고용으로 계산한다.
사용자가 CGM 데이터를 가지고 있다면 최근 혈당 흐름과 식사/활동 관련 입력을 바탕으로
30분, 60분, 90분 뒤 혈당 변화 가능성을 예측 범위와 위험 가능성 신호로 보여준다.
모든 혈당 결과는 의료 진단이나 치료 목적이 아닌 식습관 관리 참고용이다.
```

프로젝트의 핵심 가치는 “음식 이미지 인식”과 “혈당 변화 참고 정보”를 연결했다는 점이다. 단순히 음식을 분류하는 앱이 아니라, 사용자가 식사 전후에 자신의 식습관이 혈당에 어떤 영향을 줄 수 있는지 이해하도록 돕는 구조를 목표로 했다. 또한 처음부터 실제 서비스 가능성을 고려해 안전 문구, 개인정보/로그 정책, 파일럿 설계, 웹 MVP UX까지 함께 정리했다.

---

## 2. 프로젝트 전체 구조

현재 프로젝트는 다음과 같은 계층으로 구성된다.

```text
음식 이미지 입력
-> K-Food 이미지 분류 모델
-> 음식명 및 confidence
-> K-Food nutrition database
-> 영양성분 조회
-> 음식 기반 혈당 위험도 참고 점수
-> CGM 데이터가 있는 경우 혈당 예측 모델
-> 30/60/90분 예측값
-> 예측 범위와 불확실성
-> 저혈당/고혈당 가능성 신호
-> 웹앱에서 안전 UX로 표시
```

코드 및 데이터 관점에서 보면 다음과 같이 나뉜다.

```text
config/
  kfood_production_ensemble_config.json

src/classifier/
  음식 이미지 분류 모델, ensemble classifier, 학습/평가 관련 코드

src/nutrition/
  음식명과 영양성분 DB 연결

src/predictor/
  영양성분 기반 혈당 위험도 predictor

src/glucose/
  OhioT1DM 파싱, CGM feature engineering, forecasting, safety constants, privacy helper

api/
  FastAPI 기반 endpoint

scripts/
  데이터 준비, 모델 학습, 평가, 검증 스크립트

data/raw/
  K-Food split 및 원천 데이터

data/processed/
  nutrition DB, OhioT1DM 변환 결과, glucose model artifacts

data/models/
  음식 이미지 분류 checkpoint와 관련 metadata

reports/
  실험 결과, 평가 리포트, 안전성 감사 리포트

docs/
  혈당 기능 제품 포지셔닝, 안전 문구, 파일럿 설계, 데이터 거버넌스 문서

frontend/
  Vite React TypeScript 웹 MVP
```

제출용으로 강조할 만한 프로젝트의 특징은 다음과 같다.

1. 음식 이미지 분류 모델은 단일 모델이 아니라 여러 모델의 weighted ensemble로 고도화했다.
2. 56개 한국 음식 class를 대상으로 validation top1 92.02%를 달성했다.
3. 음식 분류 결과를 영양성분 DB와 연결해 음식 기반 혈당 부담 참고 기능을 만들었다.
4. OhioT1DM XML 데이터를 파싱해 CGM 시계열 데이터로 변환했다.
5. 30분, 60분, 90분 horizon별 혈당 예측 모델을 만들었다.
6. low/high glucose 구간 bias를 발견하고 range-aware calibration과 event classifier로 보완했다.
7. 90분 예측은 불확실성이 크다는 점을 제품 UX에 반영했다.
8. 의료 기능이 아니라 웰니스/식습관 관리 보조 기능으로 포지셔닝했다.
9. 실제 사용자 파일럿을 준비하기 위한 동의서, 데이터 스키마, 개인정보/보안/로그 정책을 문서화했다.
10. 최종적으로 사용자가 체험할 수 있는 웹 MVP를 구현했다.

---

## 3. 문제 정의

현대 식생활에서 사용자는 자신이 먹는 음식의 영양성분과 혈당 영향을 직관적으로 이해하기 어렵다. 특히 한국 음식은 국물, 반찬, 밥, 면, 양념, 조리 방식이 복합적으로 섞여 있어 음식명만 알아도 영양성분 추정이 쉽지 않다. 사용자가 매번 직접 영양성분을 검색하거나 탄수화물 양을 계산하는 것도 번거롭다. 또한 CGM을 사용하는 사람이라도 매 식사마다 “이 음식이 이후 혈당 변화에 어떤 가능성을 만들 수 있는지”를 쉽게 해석하기 어렵다.

이 프로젝트는 이 문제를 세 단계로 나누어 접근했다.

첫째, 음식 사진에서 음식명을 자동으로 인식한다. 사용자는 음식을 텍스트로 입력하지 않고 사진을 업로드하는 것만으로 분석을 시작할 수 있어야 한다. 이를 위해 K-Food 56-class 음식 이미지 분류 모델을 구축했다.

둘째, 음식명과 영양성분을 연결한다. 음식명만 표시하는 것은 사용자에게 충분한 정보가 아니다. 탄수화물, 당류, 칼로리, 단백질, 지방, 식이섬유 등 혈당 부담에 관련된 정보를 함께 제공해야 한다. 이를 위해 K-Food class label과 nutrition DB를 연결했다.

셋째, 혈당 변화 가능성을 참고용으로 제시한다. 음식 영양성분 기반 위험도만으로는 개인별 혈당 흐름을 반영하기 어렵다. CGM 데이터가 있는 경우 최근 혈당 흐름과 식사/운동/수면/인슐린 관련 이벤트를 반영해 30분, 60분, 90분 뒤 혈당 변화 가능성을 추정한다. 다만 이것은 의료적 판단이 아니라 웰니스 참고 정보로 제한해야 한다.

이 문제 정의는 프로젝트 전반의 방향을 결정했다. 단순한 정확도 경쟁이 아니라, 실제 사용자가 오해하지 않고 안전하게 사용할 수 있는 AI 서비스 구조를 만드는 것이 중요했다. 그래서 모델 성능 실험뿐 아니라 안전 문구, 예측 불확실성, 개인정보 보호, 파일럿 설계, 웹 UX까지 함께 진행했다.

---

## 4. K-Food 음식 이미지 분류 모델 개발

### 4.1 목표

음식 이미지 분류 파트의 목표는 한국 음식 56개 class에 대해 높은 정확도의 이미지 분류 모델을 만드는 것이었다. 최종적으로는 FastAPI와 웹앱에서 사용할 수 있는 운영 후보 모델을 고정하는 것이 목표였다. 단일 모델을 학습하는 것에서 끝나는 것이 아니라, 여러 모델을 조합한 ensemble을 통해 validation top1 92% 이상을 달성하는 것을 성능 목표로 삼았다.

최종 목표는 다음과 같이 정의되었다.

```text
데이터: data/raw/korean_food_fixed_v1/val
class 수: 56
validation sample 수: 6,720
목표 성능: top1 >= 0.920000
최종 달성 성능: top1 = 0.9202380952380952
정답 수: 6184 / 6720
```

이 목표를 달성하기 위해 초기 데이터 정리, split audit, 모델 실험, self-supervised pretraining 실험, supervised-only seed 실험, B3 장기 학습, hflip TTA, cached logits 기반 ensemble weight search 등 여러 단계를 거쳤다.

### 4.2 데이터

최종 기준 데이터는 다음 경로에 정리되었다.

```text
data/raw/korean_food_fixed_v1
```

구조는 일반적인 ImageFolder 방식이다.

```text
data/raw/korean_food_fixed_v1/
  train/
    class_1/
    class_2/
    ...
  val/
    class_1/
    class_2/
    ...
```

검증 기준 split은 다음과 같다.

```text
validation split: data/raw/korean_food_fixed_v1/val
validation samples: 6,720
classes: 56
```

이 split은 모델 성능 비교의 기준이 되었다. 이후 여러 실험에서 `val_original_fixed`, cleaned candidate, hard pair, label patch 등의 논의가 있었지만, 최종 운영 후보 성능은 `fixed_v1/val` 기준으로 고정했다.

### 4.3 모델 계열

음식 이미지 분류에서는 여러 모델 계열을 실험했다.

1. EfficientNet-B0 계열
2. EfficientNet-B2 계열
3. EfficientNet-B3 계열
4. Food-LeWM B0 계열
5. supervised-only B0 seed 계열
6. B3 probe/continued/full 계열

Food-LeWM은 self-supervised pretraining을 통해 음식 이미지 도메인 representation을 개선하려는 실험이었다. 하지만 실험 결과, LeWM pretraining 자체가 항상 supervised-only보다 우수한 것은 아니었다. 그럼에도 Food-LeWM B0 모델은 최종 ensemble에서 diversity member로 의미가 있었다. 즉, 단일 모델 성능만 보면 압도적이지 않더라도 ensemble에서 다른 모델이 틀리는 샘플을 일부 보완하는 역할을 했다.

### 4.4 Food-LeWM 실험

Food-LeWM 실험의 목적은 음식 이미지 데이터에서 label 없이도 이미지 representation을 학습하고, 이후 supervised fine-tuning을 통해 성능을 높일 수 있는지 확인하는 것이었다.

pretraining 방식은 다음과 같이 구성되었다.

```text
image view A -> encoder -> z_a -> predictor -> z_b_hat
image view B -> encoder -> z_b -> predictor -> z_a_hat

loss = 0.5 * (MSE(z_b_hat, z_b) + MSE(z_a_hat, z_a))
     + lambda_sigreg * SIGReg(z_a, z_b)
```

핵심 요소는 다음과 같다.

- two-view augmentation
- latent prediction
- SIGReg anti-collapse regularization
- EfficientNet encoder

대표 pretraining checkpoint는 다음과 같다.

```text
data/models/food_lewm_b0_pretrain_3ep.pt
```

이후 supervised fine-tuning은 다음 스크립트 계열을 통해 진행되었다.

```text
scripts/train_food_lewm_classifier.py
```

fine-tuning에서는 RandomResizedCrop, HorizontalFlip, ColorJitter, RandomErasing, CrossEntropyLoss with label smoothing, AdamW, cosine scheduler 등을 사용했다. 주요 모델은 다음과 같다.

| 모델 | 설명 | checkpoint |
|---|---|---|
| `food_lewm_b0` | LeWM pretrain 후 fine-tuning | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` |
| `b0_supervised_only` | ImageNet pretrained에서 바로 supervised fine-tuning | `data/models/food_lewm_b0_supervised_only_ft10.pt` |
| `b0_seed123_fixed_v1` | fixed_v1 기준 seed 123 supervised-only | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| `b0_seed7_fixed_v1` | fixed_v1 기준 seed 7 supervised-only | `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |

### 4.5 EfficientNet-B3 full 학습

EfficientNet-B3 full 모델은 최종 ensemble에서 가장 큰 weight를 받은 핵심 모델이다. B0 계열보다 큰 backbone을 사용해 단일 모델 성능과 ensemble diversity를 동시에 확보하고자 했다.

학습 설정은 다음과 같다.

| 항목 | 값 |
|---|---|
| model | `efficientnet_b3` |
| data | `data/raw/korean_food_fixed_v1` |
| image_size | `300` |
| epochs | `25` |
| batch_size | `8` |
| grad_accum_steps | `4` |
| lr | `3e-5` |
| head_lr | `3e-4` |
| warmup_epochs | `2` |
| label_smoothing | `0.05` |
| weight_decay | `0.0001` |
| randaugment | `n=2, m=7` |
| random_erasing_p | `0.1` |
| device | `MPS` |

산출물은 다음과 같다.

```text
checkpoint: data/models/efficientnet_korean_b3_full_fixed_v1.pt
metadata:   data/models/korean_food_model_meta_b3_full_fixed_v1.json
classes:    data/models/korean_food_classes_b3_full_fixed_v1.json
report:     reports/b3/b3_full_fixed_v1
```

성능은 다음과 같이 정리되었다.

| 평가 | top1 | top3 | macro_f1 |
|---|---:|---:|---:|
| train-time val | `0.903423` | `0.973065` | `0.903170` |
| hflip eval | `0.904315` | `0.974554` | `0.904010` |

B3 full은 단일 모델로 90%를 넘겼고, 최종 7-model weighted ensemble에서 약 0.52949의 가장 큰 weight를 받았다. 이는 B3 full이 최종 성능 달성의 중심축이었다는 것을 보여준다.

### 4.6 Ensemble 탐색

최종 성능 달성은 단일 모델이 아니라 여러 모델의 weighted ensemble을 통해 이루어졌다. 처음에는 3-model hflip ensemble을 중심으로 탐색했다.

이전 3-model 후보는 대략 다음 구성이었다.

```text
food_lewm_b0 = 0.12
b0_seed123_fixed_v1 = 0.29
b3_full_fixed_v1 = 0.59
```

이 조합은 `6181 / 6720`, 약 `91.9792%`까지 도달했지만 92% 기준에는 2개 샘플 정도 부족했다. 이후 step `0.025`, `0.01`, `0.005`, local step `0.001`, global step `0.002` 등으로 더 촘촘한 search를 수행했으나 3-model 조합만으로는 92%를 넘기 어려웠다.

그 다음 단계에서는 기존 hflip logits cache를 통합했다. B0, B2, B3 probe, B3 full, B3 continued 등 여러 모델 후보의 logits를 합치고, cached candidate search를 수행했다. 처음에는 `6182 / 6720`까지 도달했으나 여전히 1개 샘플이 부족했다. 이후 broader randomized sparse/local weight search를 수행했고, 최종적으로 7-model hflip weighted ensemble이 `6184 / 6720`으로 92% threshold를 넘었다.

### 4.7 최종 K-Food 운영 후보

최종 운영 후보는 다음 이름으로 고정되었다.

```text
kfood_92_hflip_7model_weighted_2026_05_16
```

운영 config는 다음 파일이다.

```text
config/kfood_production_ensemble_config.json
```

최종 검증 리포트는 다음 폴더에 있다.

```text
reports/b3/verified_92_hflip_7model_weighted_2026_05_16
```

성능은 다음과 같다.

| Metric | Value |
|---|---:|
| top1 | `0.9202380952380952` |
| top1 percent | `92.02380952380952%` |
| correct | `6184 / 6720` |
| top3 | `0.9794642857142857` |
| macro_f1 | `0.9200379850437458` |
| TTA | `hflip` |

최종 ensemble 구성은 다음과 같다.

| Model | Weight | Checkpoint |
|---|---:|---|
| `food_lewm_b0` | `0.14236057323734336` | `data/models/food_lewm_b0_classifier_3ep_ft10.pt` |
| `b0_seed123_fixed_v1` | `0.2567350687710819` | `data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt` |
| `b3_full_fixed_v1` | `0.52949003398239` | `data/models/efficientnet_korean_b3_full_fixed_v1.pt` |
| `b0_seed7_fixed_v1` | `0.06212042836978825` | `data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt` |
| `b3_probe_fixed_v1` | `0.0010083266638448512` | `data/models/efficientnet_korean_b3_probe_fixed_v1.pt` |
| `b3_cont_fixed_v1` | `0.00496452020109459` | `data/models/efficientnet_korean_b3_cont_fixed_v1.pt` |
| `b0_supervised_only` | `0.0033210487744569726` | `data/models/food_lewm_b0_supervised_only_ft10.pt` |

### 4.8 운영 config와 FastAPI 연결

92% 후보를 단순한 실험 결과로 끝내지 않고 운영 후보로 고정하기 위해 `config/kfood_production_ensemble_config.json`을 생성했다. 이 config에는 ensemble name, status, verified metrics, TTA 방식, 7개 모델 checkpoint 경로, metadata 경로, classes 경로, weight, 운영 확정 전 주의사항이 들어 있다.

또한 config 기반 ensemble classifier를 추가했다.

```text
src/classifier/ensemble_food_classifier.py
```

이 classifier는 JSON config에서 ensemble 구성을 로드하고, checkpoint/metadata/classes 파일 존재 여부를 확인하며, 모델별 class order가 일치하는지 검사한다. 또한 weight normalization과 `none`/`hflip` TTA를 지원한다. 기존 `FoodClassifier.predict(image)`와 같은 형태의 `ClassificationResult`를 반환하도록 만들어 기존 API 코드와 호환되도록 했다.

FastAPI startup에서는 production ensemble config가 있으면 이를 우선 로드하고, 없으면 기존 단일 classifier로 fallback하도록 구성했다. 이 작업은 운영 후보를 실험 리포트에만 묶어두지 않고 실제 API에서 사용할 수 있게 만든 중요한 단계였다.

### 4.9 K-Food 모델 검증

운영 config 검증 스크립트는 다음과 같다.

```text
scripts/validate_kfood_production_config.py
```

검증 항목은 다음과 같다.

- config JSON 존재 여부
- `models` 목록 존재 여부
- `verified_metrics.top1 >= 0.92`
- TTA가 운영 지원 범위인지 확인
- checkpoint/metadata/classes 파일 존재 여부
- class count `56` 확인
- 모든 모델의 class order 동일 여부 확인
- weight 합이 양수인지 확인

실행 결과는 다음과 같이 확인되었다.

```text
status: ok
num_models: 7
num_classes: 56
weight_sum: 1.0
verified_top1: 0.9202380952380952
```

### 4.10 K-Food 파트의 한계와 해석

현재 K-Food 모델은 validation 기준 92.02%를 달성했지만, 이 수치를 해석할 때 중요한 caveat가 있다. 최종 ensemble weight는 `fixed_v1/val`에서 탐색되었고, 최종 성능도 같은 validation split에서 검증되었다. 따라서 이 결과는 현재 기준의 강력한 운영 후보 성능으로 볼 수 있지만, 완전히 독립적인 unseen test 일반화의 최종 증명은 아니다.

제출 서류에서는 이 점을 정직하게 적는 것이 좋다. 과장해서 “실제 모든 사용자 이미지에서 92% 이상을 보장한다”고 표현하면 안 된다. 대신 다음처럼 설명하는 것이 적절하다.

```text
본 프로젝트는 K-Food fixed validation split 6,720장 기준으로 top1 92.02%를 달성한
7-model hflip weighted ensemble 운영 후보를 구축했다.
다만 최종 ensemble weight가 validation split에서 탐색되었으므로,
추후 실제 운영 전에는 별도 holdout 또는 사용자 파일럿 데이터에서 재검증이 필요하다.
```

---

## 5. 음식 영양성분 연결 및 혈당 위험도 기능

### 5.1 목적

음식 이미지 분류 모델이 음식명을 예측하더라도, 사용자가 실제로 궁금해하는 것은 음식명 그 자체만이 아니다. 사용자는 “이 음식이 얼마나 혈당 부담이 있을까”, “탄수화물이나 당류가 많은 음식일까”, “식후 혈당 상승 가능성이 높을까”를 알고 싶어 한다. 따라서 음식명과 영양성분 DB를 연결하고, 이를 기반으로 혈당 위험도 참고 점수를 계산하는 기능을 추가했다.

흐름은 다음과 같다.

```text
음식 이미지
-> K-Food classifier
-> 음식명
-> nutrition lookup
-> calories/carbs/sugar/protein/fat/fiber/GI
-> 혈당 위험도 참고 점수
-> 설명 문구와 serving advice
```

### 5.2 주요 파일

영양성분과 혈당 위험도 기능의 주요 파일은 다음과 같다.

```text
src/nutrition/nutrition_db.py
src/nutrition/nutrition_db_builder.py
src/predictor/sugar_predictor.py
src/predictor/train_predictor.py
src/glucose/risk.py
data/processed/kfood_nutrition_db.json
data/models/xgboost_sugar.pkl
```

### 5.3 K-Food label과 nutrition DB 연결

K-Food 56-class label을 nutrition lookup key로 직접 사용할 수 있도록 연결했다. `data/processed/train_data.csv`에서 exact match 가능한 51개를 생성했고, `곰탕_설렁탕`은 `곰탕`과 `설렁탕`의 평균값으로 구성했다. exact row가 없는 일부 class는 curated alias로 보완했다.

보완한 class 예시는 다음과 같다.

```text
갈비구이
양념치킨
한과
후라이드치킨
```

이 작업의 의미는 크다. 모델이 한국어 label을 반환해도 nutrition DB에서 정보를 찾지 못하면 분석 결과 화면에서 영양성분과 혈당 위험도를 보여줄 수 없다. 따라서 음식 분류와 혈당 기능을 이어주는 연결층이 필요했고, 이 부분을 별도로 구축했다.

### 5.4 XGBoost 기반 혈당 위험도 모델

영양성분 기반 혈당 위험도는 `XGBClassifier` 기반 모델로도 학습할 수 있도록 구성했다.

학습 스크립트:

```text
src/predictor/train_predictor.py
```

모델 파일:

```text
data/models/xgboost_sugar.pkl
```

사용 feature는 다음과 같다.

```text
calories
carbs
sugar
protein
fat
fiber
glycemic_index
```

label은 다음과 같은 3단계 구조이다.

```text
0: 낮음
1: 주의
2: 위험
```

다만 현재 운영 기본값은 XGBoost model eager loading보다 안정성을 우선해 rule-based fallback을 사용하도록 설정했다.

```text
settings.use_xgboost_predictor_model = False
```

이 결정은 특히 macOS Python 3.14 환경에서 XGBoost eager import 또는 trained XGBoost model load가 torch/MPS ensemble inference와 충돌할 수 있다는 점을 고려한 것이다. 즉, 음식 분류 운영 안정성을 먼저 확보하고, XGBoost predictor는 필요할 때 명시적으로 켜서 별도 smoke test를 수행하도록 했다.

### 5.5 rule-based fallback

`SugarPredictor(use_model=False)` 옵션을 추가해 XGBoost model file을 로드하지 않고도 rule-based fallback으로 혈당 위험도를 계산할 수 있게 했다. 이 fallback은 음식 영양성분을 기반으로 혈당 부담을 투명하게 계산한다. 프로젝트의 안전성과 설명 가능성 측면에서 rule-based fallback은 장점이 있다. 모델이 불안정하거나 환경 문제가 있을 때도 API가 멈추지 않고 일관된 참고 정보를 제공할 수 있기 때문이다.

### 5.6 혈당 위험도 기능의 한계

음식 기반 혈당 위험도는 개인별 혈당 반응을 확정하지 않는다. 같은 음식이라도 사람마다 혈당 반응은 다르다. 영향을 주는 요소는 다음과 같다.

- 개인별 인슐린 민감도
- 식사량과 실제 탄수화물 양
- 식사 순서
- 운동 여부
- 수면 상태
- 스트레스
- 약물 또는 인슐린 사용
- 위 배출 속도
- CGM 센서 지연
- 음식 조리 방식과 양념

따라서 음식 기반 위험도는 “이 음식은 혈당 부담 가능성이 상대적으로 높을 수 있다”는 참고 정보로 표현해야 한다. “이 음식을 먹으면 혈당이 반드시 얼마 오른다”라고 표현하면 안 된다.

---

## 6. OhioT1DM CGM 데이터 파이프라인

### 6.1 목적

혈당 기능의 두 번째 핵심은 CGM 기반 혈당 예측이다. 음식 영양성분만으로는 개인의 현재 혈당 상태와 최근 혈당 흐름을 반영하기 어렵다. CGM 데이터가 있다면 현재 혈당, 최근 추세, 식사 이벤트, bolus, basal, 운동, 수면 등을 함께 반영해 30분, 60분, 90분 뒤 혈당 변화 가능성을 예측할 수 있다.

이를 위해 OhioT1DM XML 데이터를 읽고, CGM 시계열 데이터로 변환하는 파이프라인을 구축했다.

원본 데이터 경로:

```text
/Users/sangrok/Downloads/OhioT1DM
```

변환 스크립트:

```text
scripts/prepare_ohiot1dm_cgm.py
```

변환 결과:

```text
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
```

### 6.2 데이터 규모

변환된 데이터의 대략적인 규모는 다음과 같다.

| 항목 | 값 |
|---|---:|
| total rows | 약 `166,533` |
| train rows | 약 `134,790` |
| test rows | 약 `31,743` |
| patients | `12` |
| years | `2018`, `2020` |
| glucose range | `40-400 mg/dL` |

OhioT1DM 데이터는 환자별 CGM 시계열과 다양한 이벤트 정보를 포함한다. 본 프로젝트에서는 이를 연구용 forecasting experiment에 맞게 변환하고, train/test 및 validation 분리, leakage audit, feature enrichment를 수행했다.

### 6.3 XML 파싱과 enriched feature

`src/glucose/ohiot1dm.py`는 OhioT1DM XML 파일에서 glucose level event를 파싱하고, 필요 시 carbs, bolus, basal, exercise, sleep, hypo event, gsr, skin temperature, acceleration 등의 이벤트를 CGM 시계열에 맞춰 결합한다.

기본적으로 CGM 시계열에서 필요한 것은 다음이다.

```text
timestamp
glucose_mg_dl
patient_id
source_file
split
year
```

enriched 데이터에서는 다음과 같은 event feature도 추가된다.

```text
carbs_current
carbs_last_30m
carbs_last_60m
carbs_last_120m
carbs_last_180m
bolus_current
bolus_last_30m
bolus_last_60m
bolus_last_120m
bolus_last_180m
basal_current
basal_mean_60m
basal_mean_120m
exercise_active
exercise_last_60m
exercise_last_120m
sleep_indicator
hypo_event_current
gsr_current
skin_temperature_current
acceleration_current
patient_id_numeric
```

### 6.4 leakage 방지

CGM 예측에서 가장 중요한 점 중 하나는 미래 정보를 feature에 섞지 않는 것이다. 예를 들어 60분 뒤 혈당을 예측할 때 60분 뒤 실제 혈당이나 미래 이벤트가 feature에 들어가면 평가가 의미 없어지고 leakage가 발생한다. 그래서 train/test 분리와 validation selection을 엄격히 구분했다.

최근 validation/test split 구조는 다음과 같이 정리되었다.

```text
train_inner: 107,827
validation: 26,963
groups: 12
time_order_safe: true
test_split_used_for_selection: false
```

즉, 모델/threshold/calibration 선택은 validation을 사용하고, test는 최종 평가에만 사용하도록 했다. 이 점은 추후 제출 서류에서 중요한 신뢰성 근거가 된다.

---

## 7. CGM 혈당 예측 모델

### 7.1 목표

CGM forecasting의 목표는 최근 CGM readings와 식사/활동 관련 feature를 입력받아 30분, 60분, 90분 뒤 혈당을 예측하는 것이다. 이때 30분은 비교적 수치 예측 중심으로 사용할 수 있지만, 60분과 90분은 불확실성이 커지므로 예측 범위와 가능성 신호를 함께 제공하는 방향으로 설계했다.

최신 학습 명령은 다음과 같다.

```bash
python3 scripts/train_glucose_forecaster.py \
  --cgm-csv data/processed/ohiot1dm/cgm_timeseries_enriched.csv \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting \
  --use-validation-selection \
  --long-horizon-upgrade
```

### 7.2 모델 구조

forecasting 모델은 horizon별로 별도 학습했다.

```text
glucose_forecast_30m.joblib
glucose_forecast_60m.joblib
glucose_forecast_90m.joblib
```

모델 타입은 다음과 같이 정리되었다.

```text
enriched_long_horizon
```

기본 회귀 모델은 `HistGradientBoostingRegressor`이다. Horizon별로 다른 예측 난이도와 feature 중요도를 반영하기 위해 30분, 60분, 90분 모델을 분리했다.

### 7.3 feature 구성

CGM 예측 feature는 크게 네 계열로 나뉜다.

첫째, 기본 CGM lag/rolling feature이다.

```text
glucose_mg_dl
lag_1
lag_2
lag_3
lag_6
lag_12
diff_1
diff_3
diff_6
rolling_mean_3
rolling_mean_6
rolling_mean_12
rolling_std_6
rolling_std_12
hour_sin
hour_cos
```

둘째, 식사/인슐린/기저/운동/수면 이벤트 feature이다.

```text
carbs_current
carbs_last_30m
carbs_last_60m
carbs_last_120m
carbs_last_180m
bolus_current
bolus_last_30m
bolus_last_60m
bolus_last_120m
bolus_last_180m
basal_current
basal_mean_60m
basal_mean_120m
exercise_active
exercise_last_60m
exercise_last_120m
sleep_indicator
patient_id_numeric
```

셋째, long-horizon 예측을 위한 proxy feature이다.

```text
time_since_last_meal
time_since_last_bolus
meal_bolus_gap_minutes
carbs_on_board_proxy
insulin_on_board_proxy
carb_insulin_ratio_proxy
net_glucose_pressure_proxy
```

넷째, 장기 혈당 흐름과 volatility를 반영하는 feature이다.

```text
glucose_slope_60m
glucose_slope_120m
glucose_volatility_120m
glucose_volatility_180m
glucose_mean_120m
glucose_mean_180m
recent_low_event_count_180m
recent_high_event_count_180m
time_since_last_low
time_since_last_high
```

여기서 IOB/COB 관련 feature는 의료용 IOB/COB 계산이 아니라 예측용 proxy이다. 제출 서류에서는 이 점을 반드시 명시해야 한다. `insulin_on_board_proxy`나 `carbs_on_board_proxy`라는 이름은 실제 의료용 투약 계산을 의미하지 않는다. 모델이 최근 이벤트의 영향을 예측 feature로 활용하기 위해 만든 근사 feature이다.

### 7.4 최신 성능

long-horizon enriched 모델의 최신 test MAE는 다음과 같다.

| Model | 30m MAE | 60m MAE | 90m MAE |
|---|---:|---:|---:|
| long-horizon enriched raw | `13.027` | `22.704` | `29.721` |
| long-horizon enriched calibrated | `12.998` | `22.633` | `29.606` |

해석은 다음과 같다.

```text
30분: 비교적 수치 예측 중심으로 시연 가능
60분: 수치 + 범위 + 위험 가능성 + 불확실성 표시 필요
90분: 단일 수치보다 범위 + 불확실성 + 가능성 신호 중심이 적절
```

90분 horizon에서는 MAE 자체도 더 크고 prediction interval width도 넓기 때문에, UI에서 90분 point estimate를 크게 강조하면 사용자가 과신할 수 있다. 따라서 90분은 범위와 불확실성 중심으로 보여주도록 제품 설계를 바꾸었다.

### 7.5 prediction interval

예측값만 제공하면 사용자는 이를 실제 미래 혈당처럼 받아들일 수 있다. 이를 방지하기 위해 validation residual 기반 prediction interval을 추가했다.

최근 interval 성능은 다음과 같다.

| Horizon | Observed Coverage | Mean Interval Width | Uncertainty |
|---:|---:|---:|---|
| 30m | `0.919` | `64.487` | high |
| 60m | `0.915` | `107.109` | high |
| 90m | `0.912` | `136.114` | high |

coverage는 약 91% 수준이지만, interval width가 넓다. 특히 90분은 평균 interval width가 약 136 mg/dL 수준으로 넓기 때문에 “정확한 예측”처럼 표현하면 안 된다. 제품적으로는 90분 예측을 “정확한 혈당 수치”가 아니라 “가능성 범위”로 표시하는 것이 맞다.

### 7.6 low/high glucose bias

초기 enriched CGM 모델은 전체 MAE는 개선했지만 low/high glucose 구간에서 bias가 있었다.

관찰된 경향은 다음과 같다.

```text
low glucose 구간: 실제보다 높게 예측하는 경향
high glucose 구간: 실제보다 낮게 예측하는 경향
```

이 문제는 혈당 예측 모델에서 특히 중요하다. 전체 평균 MAE가 좋아도 저혈당 또는 고혈당 구간을 놓치면 실제 사용자에게 위험하게 해석될 수 있기 때문이다. 따라서 단순히 MAE만 낮추는 방향보다 위험 구간을 별도로 감지하고, 사용자가 이를 가능성 신호로 이해하도록 만드는 방향으로 개선했다.

추가한 대응은 다음과 같다.

- range-aware calibration
- hypo event classifier
- hyper event classifier
- event threshold validation selection
- patient-specific evaluation
- prediction interval
- uncertainty message
- leakage audit

---

## 8. Hypo/Hyper Event Classifier

### 8.1 목적

혈당 수치 예측만으로 저혈당/고혈당 위험을 표현하면 bias 문제의 영향을 받을 수 있다. 예를 들어 실제 저혈당이 될 가능성이 있는 구간에서 회귀 모델이 평균으로 끌려 올라가면, 저혈당 가능성을 놓칠 수 있다. 반대로 고혈당 구간에서 회귀 모델이 평균으로 끌려 내려가면 고혈당 가능성을 약하게 볼 수 있다.

이를 보완하기 위해 hypo/hyper event classifier를 별도로 학습했다. 이 classifier는 “저혈당입니다” 또는 “고혈당입니다”라고 확정하는 것이 아니라, horizon별 저혈당/고혈당 가능성 신호를 제공한다.

### 8.2 산출물

event classifier 모델 파일은 다음과 같다.

```text
data/processed/glucose_models_enriched/glucose_event_hypo_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hypo_90m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_30m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_60m.joblib
data/processed/glucose_models_enriched/glucose_event_hyper_90m.joblib
```

선택/평가 리포트는 다음과 같다.

```text
reports/glucose_forecasting/test_final_event_classifier_metrics.csv
reports/glucose_forecasting/validation_hypo_classifier_model_comparison.csv
reports/glucose_forecasting/validation_hypo_threshold_selection.json
```

### 8.3 학습 및 선택 원칙

event classifier는 다음 원칙으로 학습/평가했다.

```text
train_inner로 모델 학습
validation으로 모델 family와 threshold 선택
test는 최종 평가에만 사용
```

이 원칙은 leakage 방지를 위해 중요하다. test set에서 threshold를 고르면 test performance가 과대평가될 수 있다. 따라서 validation에서 선택하고 test에서 최종 확인하는 구조를 유지했다.

### 8.4 API 표현 원칙

event classifier 결과는 API와 UI에서 다음처럼 표현해야 한다.

허용 표현:

```text
저혈당 가능성 신호
고혈당 가능성 신호
실제 혈당 측정값과 증상을 우선 확인하세요.
```

금지 표현:

```text
저혈당입니다.
고혈당입니다.
인슐린을 조절하세요.
치료가 필요합니다.
```

현재 API의 `risk_messages`는 “가능성 신호”라는 표현을 사용하도록 정리했다. 웹앱에서도 `RiskSignalCard`에서 “저혈당 가능성 신호”, “고혈당 가능성 신호”로 표시한다.

---

## 9. 혈당 기능의 안전성, 개인정보, 웰니스 포지셔닝

### 9.1 왜 안전 UX가 중요한가

혈당 예측 기능은 사용자가 의료 정보처럼 받아들일 가능성이 있다. 특히 “저혈당”, “고혈당”, “예측”이라는 단어는 매우 민감하다. 앱이 실제로 의료기기 수준의 임상 검증과 규제 체계를 갖추지 않은 상태에서 치료 의사결정처럼 보이는 표현을 쓰면 위험하다.

따라서 프로젝트 후반부에서는 모델 성능을 조금 더 높이는 것보다, 사용자가 오해하지 않도록 안전한 제품 포지션을 확정하는 것이 더 중요하다고 판단했다. 이 판단에 따라 Safe Wellness Pilot 방향으로 전환했다.

### 9.2 제품 포지셔닝

혈당 기능의 포지션은 다음과 같이 고정했다.

```text
FoodSugar AI 혈당 기능은 의료 판단 도구가 아니라
식습관 관리와 생활 패턴 이해를 돕는 웰니스 기능이다.
```

이 기능이 제공하는 것은 다음이다.

- 음식 영양성분 기반 혈당 부담 참고 점수
- CGM 데이터가 있을 때의 30/60/90분 혈당 변화 가능성
- 예측 범위와 불확실성
- 저혈당/고혈당 가능성 신호

제공하지 않는 것은 다음이다.

- 당뇨 진단
- 저혈당/고혈당 확정 판정
- 인슐린 또는 약물 조절 안내
- 치료 결정 지원
- 응급상황 판단

### 9.3 안전 문구

모든 혈당 관련 기능에는 다음 의미의 문구가 들어가야 한다.

```text
이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다.
혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요.
```

현재 코드에서는 `src/glucose/constants.py`의 안전 문구를 강화했다. 웹앱에서는 `SafetyNotice` 컴포넌트가 모든 혈당 관련 화면에 표시된다.

### 9.4 파일럿 설계

실제 사용자 파일럿을 준비하기 위해 다음 문서를 생성했다.

```text
docs/PILOT_STUDY_PROTOCOL.md
docs/PILOT_USER_CONSENT_DRAFT.md
docs/PILOT_DATA_SCHEMA.md
reports/pilot/pilot_metric_plan.md
```

파일럿 설계는 다음을 기준으로 했다.

```text
대상: 10~30명
기간: 2~4주
수집 데이터:
- 식사 사진
- 음식명
- 예상 탄수화물
- CGM readings
- 식사 시간
- 운동 여부
- 수면 여부
- 사용자 피드백
```

파일럿에서 확인할 질문은 다음과 같다.

1. 사용자가 식사 사진을 꾸준히 입력하는가?
2. 음식분류 결과를 신뢰할 수 있는가?
3. 영양성분 추정이 실제 식사량과 크게 어긋나지 않는가?
4. 30/60/90분 예측이 실제 CGM과 어느 정도 맞는가?
5. 저혈당/고혈당 가능성 신호를 사용자가 오해하지 않는가?
6. 오경고가 너무 많아 사용자가 앱을 꺼버리지는 않는가?

### 9.5 데이터 거버넌스와 개인정보

CGM, 식사, 운동, 인슐린 관련 데이터는 민감한 건강정보에 가깝다. 실제 파일럿 또는 서비스로 발전하려면 수집 데이터, 저장 기간, 삭제 요청, 로그 마스킹, 사용자 ID 분리 저장, 연구 데이터와 운영 데이터 분리 원칙이 필요하다.

이를 위해 다음 문서를 생성했다.

```text
docs/GLUCOSE_DATA_GOVERNANCE.md
docs/GLUCOSE_PRIVACY_SECURITY_CHECKLIST.md
docs/GLUCOSE_LOGGING_POLICY.md
```

또한 로그 마스킹 helper를 추가했다.

```text
src/glucose/privacy.py
```

이 helper는 raw CGM sequence, insulin/bolus values, basal rate, exact timestamp, patient id 등이 로그에 직접 남지 않도록 마스킹하는 역할을 한다.

### 9.6 robustness 테스트

실제 사용자는 데이터를 완벽하게 입력하지 않는다. 식사 입력이 누락될 수 있고, bolus/basal 정보가 없을 수 있으며, CGM readings가 부족할 수도 있고, timestamp가 잘못될 수도 있다. 따라서 missing input robustness를 확인했다.

생성한 리포트는 다음과 같다.

```text
reports/glucose_forecasting/robustness_missing_input_report.csv
reports/glucose_forecasting/timestamp_error_robustness_report.csv
reports/glucose_forecasting/low_confidence_food_handling_report.md
```

테스트 파일도 추가했다.

```text
tests/test_glucose_safety_wording.py
tests/test_glucose_uncertainty_response.py
tests/test_glucose_robustness_inputs.py
tests/test_glucose_privacy_logging.py
```

검증 결과:

```text
python3 -m pytest tests/ -q
72 passed
```

---

## 10. FastAPI API 구조

현재 프로젝트는 FastAPI 기반 API를 제공한다. 핵심 endpoint는 다음과 같다.

```text
/predict/classify
/predict/analyze
/predict/risk
/predict/glucose-risk
/predict/cgm-forecast
/predict/cgm-forecast-enriched
/predict/cgm-forecast-enriched-events
```

각 endpoint의 역할은 다음과 같다.

### 10.1 `/predict/classify`

음식 이미지를 입력받아 음식 분류 결과를 반환한다.

반환 정보:

```text
food_key
food_name_ko
confidence
top5
```

### 10.2 `/predict/analyze`

음식 이미지를 입력받아 분류, 영양성분 조회, 혈당 위험도 예측을 한 번에 수행한다.

흐름:

```text
image upload
-> classifier.predict(image)
-> get_nutrition(food_key)
-> predictor.predict(nutrition_info)
-> FullAnalysisResponse
```

웹 MVP의 음식 분석 화면은 이 endpoint를 우선 호출한다. backend가 꺼져 있거나 실패하면 mock data로 fallback한다.

### 10.3 `/predict/glucose-risk`

영양성분 입력을 바탕으로 0~100 참고용 혈당 위험도 점수를 계산한다.

### 10.4 `/predict/cgm-forecast`

최근 5분 간격 CGM readings를 입력받아 30/60/90분 뒤 혈당을 예측한다. 기존 baseline endpoint이며, 기존 동작을 깨지 않도록 유지했다.

### 10.5 `/predict/cgm-forecast-enriched`

최근 CGM readings와 aggregated event feature를 입력받아 enriched glucose forecast를 수행한다. range-aware calibration, event probability, prediction interval, uncertainty message를 반환할 수 있다.

### 10.6 `/predict/cgm-forecast-enriched-events`

raw CGM readings와 meal/bolus/basal/exercise/sleep event를 입력받고, API 내부에서 feature engineering을 수행한 뒤 enriched forecast를 반환한다. 웹 MVP에서는 이 endpoint를 우선 사용한다.

반환하는 주요 필드:

```text
predictions_mg_dl
calibrated_predictions_mg_dl
prediction_intervals_mg_dl
uncertainty_level
uncertainty_message
event_probabilities
risk_flags
risk_messages
horizons_minutes
reference_notice
risk_interpretation
safety_warning
```

---

## 11. 웹 MVP 구현

### 11.1 목표

웹 MVP의 목표는 기존 모델과 API를 활용해 사용자가 FoodSugar AI의 핵심 흐름을 체험할 수 있게 만드는 것이었다. 이번 작업은 모델 학습이 아니라 frontend/demo integration 작업이었다. 기존 classifier, checkpoint, ensemble, glucose training code는 수정하지 않았다.

웹 MVP는 다음을 보여준다.

1. 음식 사진 업로드
2. 음식 분석 결과
3. 영양성분 표시
4. 혈당 부담 참고 점수
5. CGM 기반 30/60/90분 예측
6. 예측 범위와 불확실성
7. 저혈당/고혈당 가능성 신호
8. 기록/리포트 mock
9. 설정/소개 및 안전 문구

### 11.2 기술 스택

```text
Vite
React
TypeScript
Tailwind CSS
Recharts
lucide-react
```

주요 파일:

```text
frontend/package.json
frontend/index.html
frontend/vite.config.ts
frontend/tsconfig.json
frontend/tailwind.config.js
frontend/postcss.config.js
```

### 11.3 frontend 구조

핵심 구조는 다음과 같다.

```text
frontend/
├── package.json
├── index.html
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── styles.css
    ├── vite-env.d.ts
    ├── lib/
    │   └── api.ts
    ├── data/
    │   └── mockData.ts
    ├── components/
    │   ├── AppShell.tsx
    │   ├── BottomNav.tsx
    │   ├── HeaderBar.tsx
    │   ├── SafetyNotice.tsx
    │   ├── UploadPanel.tsx
    │   ├── FoodPreviewCard.tsx
    │   ├── NutritionCard.tsx
    │   ├── GlucoseRiskCard.tsx
    │   ├── GlucosePredictionCards.tsx
    │   ├── GlucoseChart.tsx
    │   ├── RiskSignalCard.tsx
    │   └── HistoryList.tsx
    └── pages/
        ├── HomePage.tsx
        ├── AnalysisPage.tsx
        ├── PredictionPage.tsx
        ├── HistoryPage.tsx
        └── SettingsPage.tsx
```

### 11.4 페이지 구성

웹앱은 5개 페이지로 구성된다.

```text
home
analysis
prediction
history
settings
```

라우팅은 React Router를 사용하지 않고, `App.tsx`의 local state로 간단히 처리했다.

```ts
type PageKey = "home" | "analysis" | "prediction" | "history" | "settings";
```

이 방식은 MVP에 적합하다. 별도 URL routing이 필요한 단계가 아니고, 빠르게 데모 흐름을 확인하는 것이 목적이었기 때문에 상태 기반 페이지 전환으로 충분했다.

### 11.5 HomePage

`HomePage`는 음식 사진 업로드 화면이다. 사용자는 이미지를 드래그하거나 파일 선택 버튼으로 업로드할 수 있다. 업로드 후 preview가 표시되고, “분석 시작하기” 버튼을 누르면 backend `/predict/analyze` 호출을 시도한다.

주요 컴포넌트:

```text
UploadPanel
```

표시 내용:

- FoodSugar AI 소개 문장
- 음식 사진 업로드 안내
- 촬영 팁
- 이미지 preview
- 분석 시작 버튼
- 업로드 데이터 안내

### 11.6 AnalysisPage

`AnalysisPage`는 음식 분석 결과 화면이다. 음식명, classification confidence, 영양성분, 혈당 부담 참고 점수, 예상 혈당 상승 가능성, 피크 예상 시간을 표시한다.

사용 컴포넌트:

```text
FoodPreviewCard
NutritionCard
GlucoseRiskCard
SafetyNotice
```

여기서 중요한 UX는 confidence가 낮을 때 사용자 확인을 유도하는 것이다. 음식명과 섭취량은 혈당 위험도에 직접 영향을 주기 때문에, 낮은 confidence 상황에서는 결과를 확정적으로 보여주지 않고 음식명 확인을 권장해야 한다.

### 11.7 PredictionPage

`PredictionPage`는 CGM 기반 혈당 변화 가능성 화면이다. 현재 혈당 기준값, 30분/60분/90분 예측, prediction interval, uncertainty, Recharts 기반 그래프, 저혈당/고혈당 가능성 신호, 안전 문구를 표시한다.

사용 컴포넌트:

```text
GlucosePredictionCards
GlucoseChart
RiskSignalCard
SafetyNotice
```

핵심 설계 원칙은 다음이다.

```text
30분: 숫자 중심
60분: 숫자 + 범위
90분: 범위 + 불확실성 중심
```

90분은 단일 숫자를 크게 강조하지 않는다. 대신 `104~205 mg/dL`처럼 범위를 먼저 보여주고, “불확실성 높음”, “참고용 범위와 가능성 신호로만 확인”이라는 문구를 강조한다.

### 11.8 HistoryPage

`HistoryPage`는 mock 기록/리포트 화면이다. 현재 backend history API가 없으므로 mock data를 사용한다.

표시 내용:

- 주간 평균 혈당
- 혈당 변동성
- 가장 높은 시간대
- 최근 식사 기록 리스트
- 음식명
- 칼로리
- 혈당 영향 수준
- 예상 피크 혈당

### 11.9 SettingsPage

`SettingsPage`는 서비스 소개와 안전 안내 화면이다.

표시 내용:

- FoodSugar AI 소개
- CGM 연결 상태 mock
- 데이터 처리 안내
- 개인정보/로그 원칙
- 모델 한계
- 안전 문구

이 화면은 제출/발표 시 프로젝트가 단순 기능 구현을 넘어 제품 안전성과 한계를 고려했다는 점을 보여줄 수 있는 페이지다.

---

## 12. 웹 MVP API fallback 구조

### 12.1 `frontend/src/lib/api.ts`

웹앱의 API 연결은 `frontend/src/lib/api.ts`에서 처리한다.

기본 API 주소:

```ts
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";
```

구현된 함수:

```ts
analyzeFoodImage(file: File): Promise<AnalysisResult>
predictGlucose(payload: CGMForecastPayload): Promise<GlucosePredictionResult>
getMockAnalysis(imageUrl?: string): AnalysisResult
getMockPrediction(): GlucosePredictionResult
```

### 12.2 음식 분석 fallback

`analyzeFoodImage(file)`는 먼저 FastAPI backend의 `/predict/analyze`를 호출한다.

```text
POST /predict/analyze
```

성공하면 backend response를 frontend의 `AnalysisResult` 형태로 변환한다. 실패하면 `getMockAnalysis(imageUrl)`를 반환한다.

이 fallback이 중요한 이유는 데모 상황에서 backend가 꺼져 있어도 사용자가 UI 흐름을 볼 수 있어야 하기 때문이다. 제출이나 발표 중 backend 실행 문제가 있어도 웹 MVP는 mock data로 기능 흐름을 보여줄 수 있다.

### 12.3 혈당 예측 fallback

`predictGlucose(payload)`는 backend의 `/predict/cgm-forecast-enriched-events`를 호출한다.

```text
POST /predict/cgm-forecast-enriched-events
```

성공하면 다음 field를 frontend 구조로 변환한다.

```text
calibrated_predictions_mg_dl
predictions_mg_dl
prediction_intervals_mg_dl
uncertainty_level
uncertainty_message
```

실패하면 `getMockPrediction()`을 반환한다.

### 12.4 mock data

mock 음식 분석 데이터:

```text
음식명: 비빔밥
신뢰도: 92%
칼로리: 560 kcal
탄수화물: 85g
당류: 8g
단백질: 22g
지방: 15g
식이섬유: 6g
혈당 위험도: 높음
예상 혈당 상승 가능성: +48 mg/dL
피크 예상 시간: 식후 60분
```

mock 혈당 예측 데이터:

```text
현재 혈당: 112 mg/dL
30분: 138 mg/dL, 범위 120~152
60분: 160 mg/dL, 범위 126~176
90분: 142 mg/dL, 범위 104~205, 불확실성 높음
```

---

## 13. 검증 결과

### 13.1 backend/model 검증

K-Food production config 검증:

```text
python3 scripts/validate_kfood_production_config.py
status: ok
verified_top1: 0.9202380952380952
num_models: 7
num_classes: 56
weight_sum: 1.0
```

Glucose artifact 검증:

```text
python3 scripts/validate_glucose_artifacts.py \
  --model-dir data/processed/glucose_models_enriched \
  --report-dir reports/glucose_forecasting

artifact_validation: pass
leakage_audit: pass
```

전체 backend/model test:

```text
python3 -m pytest tests/ -q
72 passed
```

### 13.2 frontend 검증

frontend 설치:

```text
npm install --cache ./.npm-cache
success
```

frontend build:

```text
npm run build
success
```

dev server:

```text
npm run dev -- --port 5173
VITE ready
Local: http://127.0.0.1:5173/
```

HTTP 확인:

```text
curl -I http://127.0.0.1:5173/
HTTP/1.1 200 OK
```

주의점:

```text
npm install 시 moderate vulnerability 2개가 보고됨.
Recharts 포함으로 build 시 500KB chunk size warning이 있음.
현재 MVP 실행과 빌드를 막지는 않으므로 force fix는 하지 않음.
```

---

## 14. 제출 서류에서 강조할 성과

제출 서류에서 가장 강조할 만한 성과는 다음이다.

### 14.1 음식 이미지 분류 92% 달성

K-Food 56-class 음식 이미지 분류에서 fixed validation split 6,720장 기준 top1 92.02%를 달성했다. 단일 모델이 아니라 B0, Food-LeWM, B3 full, seed ensemble 등을 조합한 7-model hflip weighted ensemble을 통해 목표를 달성했다.

### 14.2 이미지 분류와 영양성분 연결

단순히 이미지를 분류하는 데서 끝나지 않고, 분류 결과를 nutrition DB와 연결해 사용자에게 실제로 의미 있는 영양성분 정보를 제공할 수 있게 했다. 이는 FoodSugar AI가 “이미지 인식 모델”이 아니라 “식습관 관리 서비스”로 확장되는 핵심 연결점이다.

### 14.3 CGM 기반 혈당 예측

OhioT1DM XML 데이터를 CGM 시계열로 변환하고, enriched long-horizon forecasting 모델을 학습했다. 30분, 60분, 90분 horizon별 모델을 구성했고, 최신 calibrated MAE는 30분 약 12.998, 60분 약 22.633, 90분 약 29.606이다.

### 14.4 위험 구간 bias 대응

전체 MAE만 보는 것이 아니라 low/high glucose 구간 bias를 발견하고, range-aware calibration과 hypo/hyper event classifier를 추가했다. 이는 프로젝트가 단순 점수 개선이 아니라 안전한 해석을 고려했다는 중요한 근거다.

### 14.5 안전한 웰니스 포지셔닝

혈당 기능을 의료 진단/치료가 아니라 웰니스/식습관 관리 참고용으로 제한했다. 안전 문구, 파일럿 동의서 초안, 데이터 거버넌스, 로그 마스킹, 개인정보 체크리스트까지 정리했다.

### 14.6 웹 MVP 구현

사용자가 직접 체험할 수 있는 웹 MVP를 구현했다. 음식 업로드, 분석 결과, 혈당 예측, 기록, 설정 화면까지 구성했고, backend가 꺼져 있어도 mock fallback으로 데모 흐름이 유지된다.

---

## 15. 제출 서류용 기술 요약 문장

아래 문단은 제출 서류의 “기술 구현 요약”에 사용할 수 있다.

```text
본 프로젝트는 음식 이미지 기반 식습관 관리와 CGM 기반 혈당 변화 참고 기능을 결합한 FoodSugar AI 시스템을 구현했다. 음식 이미지 분류에서는 K-Food 56-class fixed validation split 6,720장을 기준으로 EfficientNet-B0/B3, Food-LeWM, supervised seed 모델을 조합한 7-model hflip weighted ensemble을 구축해 top1 92.02%를 달성했다. 이후 음식 분류 결과를 한국 음식 영양성분 DB와 연결하여 칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유 등의 정보를 제공하고, 영양성분 기반 혈당 부담 참고 점수를 계산했다. 혈당 예측 파트에서는 OhioT1DM XML 데이터를 CGM 시계열로 변환하고, 30분/60분/90분 horizon별 HistGradientBoostingRegressor 모델을 학습했다. 또한 low/high glucose 구간의 bias를 보완하기 위해 range-aware calibration, hypo/hyper event classifier, prediction interval, uncertainty message, patient-specific evaluation을 추가했다. 모든 혈당 관련 결과는 의료 진단이나 치료 지침이 아닌 웰니스 및 식습관 관리 참고용으로 제한했으며, 안전 문구, 개인정보/로그 정책, 파일럿 설계 문서를 함께 구축했다. 마지막으로 Vite React TypeScript 기반 웹 MVP를 구현하여 음식 사진 업로드, 영양성분 확인, 혈당 부담 점수, CGM 기반 혈당 변화 가능성, 예측 범위와 불확실성을 사용자가 직접 확인할 수 있게 했다.
```

---

## 16. 제출 서류용 문제 해결 과정 요약

프로젝트는 단번에 완성된 것이 아니라 여러 번의 실험과 방향 전환을 거쳐 발전했다. 초기에는 음식 이미지 분류 성능을 높이는 것이 가장 큰 목표였다. K-Food 데이터 split을 정리하고, EfficientNet-B0/B2/B3 모델을 학습했으며, Food-LeWM이라는 self-supervised pretraining 실험도 수행했다. 이후 모델별 성능과 diversity를 확인하면서 hflip TTA와 ensemble weight search를 통해 목표였던 92%를 달성했다.

그 다음 단계에서는 음식 분류 결과를 실제 사용자 가치로 연결하기 위해 영양성분 DB를 구축했다. 음식명만 보여주는 앱은 정보 가치가 제한적이므로, 칼로리와 탄수화물, 당류, 단백질, 지방, 식이섬유를 함께 보여주는 구조를 만들었다. 여기서 혈당 부담 참고 점수 기능이 추가되었다.

이후 프로젝트는 CGM 기반 혈당 예측으로 확장되었다. OhioT1DM XML 데이터를 파싱하고, CGM 시계열로 변환한 뒤, 30분/60분/90분 뒤 혈당을 예측하는 모델을 만들었다. 이 과정에서 단순 MAE 개선만으로는 충분하지 않다는 점을 발견했다. 특히 low glucose 구간은 높게 예측하고 high glucose 구간은 낮게 예측하는 경향이 있어, 위험 구간 해석에 문제가 생길 수 있었다. 이에 따라 range-aware calibration, event classifier, prediction interval, uncertainty message를 추가했다.

마지막으로 모델 기능을 실제 사용자가 오해 없이 사용할 수 있도록 safe wellness pilot 방향으로 정리했다. 혈당 기능은 의료 목적이 아니라 참고용이라는 점을 명확히 했고, 파일럿 설계와 개인정보/로그 정책을 문서화했다. 웹 MVP에서는 90분 예측을 단일 숫자로 강조하지 않고 범위와 불확실성 중심으로 보여주도록 구현했다.

---

## 17. 프로젝트의 차별점

FoodSugar AI의 차별점은 다음과 같다.

첫째, 한국 음식 이미지 분류에 특화되어 있다. 일반적인 Food-101 같은 서양 음식 중심 분류가 아니라 한국 음식 56개 class를 대상으로 모델을 구성했다.

둘째, 이미지 분류 성능을 목표 수치까지 체계적으로 끌어올렸다. 단일 모델 학습에 그치지 않고, 여러 모델의 diversity를 활용한 weighted ensemble과 hflip TTA로 92% validation top1을 달성했다.

셋째, 음식명에서 끝나지 않고 영양성분과 혈당 부담으로 연결했다. 사용자가 실제로 식습관을 관리하는 데 필요한 정보는 음식명보다 영양성분과 혈당 영향 가능성이다.

넷째, CGM 시계열 예측 기능을 포함한다. 음식 기반 위험도만 제공하는 것이 아니라, CGM 데이터가 있는 경우 개인의 최근 혈당 흐름을 반영해 30/60/90분 예측을 제공한다.

다섯째, 안전한 해석을 제품 설계에 반영했다. 혈당 예측은 의료적으로 민감하기 때문에, 예측 범위, 불확실성, 가능성 신호, 참고용 문구를 필수로 포함했다.

여섯째, 실제 웹 MVP까지 구현했다. 모델과 API만 있는 프로젝트가 아니라 사용자가 실제로 체험할 수 있는 화면을 만들었다.

---

## 18. 현재 한계

프로젝트의 한계도 명확히 정리해야 한다.

### 18.1 K-Food validation tuning 한계

최종 92.02% ensemble weight는 fixed validation split에서 탐색되었다. 따라서 별도 holdout 또는 실제 사용자 이미지에서 동일 성능을 보장한다고 말할 수 없다. 운영 전에는 독립 holdout 평가가 필요하다.

### 18.2 영양성분 추정 한계

한국 음식은 조리법, 양념, 식사량, 반찬 구성에 따라 영양성분이 크게 달라진다. 현재 nutrition DB는 class-level 참고값에 가깝다. 실제 식사량이나 조리법을 완벽히 반영하지 못한다.

### 18.3 CGM 데이터 일반화 한계

CGM 모델은 OhioT1DM 기반으로 학습/검증되었다. 한국 사용자, 한국 음식, 실제 앱 입력 상황을 대표한다고 보기 어렵다. 외부 데이터셋 또는 한국 사용자 파일럿으로 추가 검증이 필요하다.

### 18.4 90분 예측 불확실성

90분 horizon은 interval width가 넓고 불확실성이 크다. 따라서 정확한 단일 숫자로 제공하면 안 된다. 현재 웹 MVP에서는 범위와 불확실성 중심으로 표시하지만, 실제 사용자 테스트에서 오해 여부를 확인해야 한다.

### 18.5 의료기기 아님

FoodSugar AI는 현재 의료기기가 아니다. 진단, 치료, 약물 조절, 응급 판단에 사용하면 안 된다. 이 점은 제출 서류와 발표에서 반드시 명확히 해야 한다.

---

## 19. 향후 계획

향후 계획은 다음과 같이 정리할 수 있다.

### 19.1 웹 MVP 고도화

- 실제 backend와 연결한 end-to-end 테스트
- 이미지 업로드 후 실제 모델 inference 확인
- `/predict/cgm-forecast-enriched-events` 실제 응답 연결
- loading, error, fallback UX 개선
- 모바일 화면 시각 검수
- 90분 예측 UI 사용자 테스트

### 19.2 독립 검증

- K-Food holdout set 평가
- 사람이 검수한 clean validation subset 평가
- 실제 사용자 음식 사진 테스트
- low-confidence class 분석

### 19.3 혈당 파일럿

- 10~30명 소규모 파일럿
- 2~4주 식사 사진/CGM 기록 수집
- 예측 MAE와 interval coverage 측정
- hypo/hyper possibility signal 오해 여부 조사
- 사용자 피드백 수집

### 19.4 외부 데이터 검증

- OhioT1DM 외 CGM dataset 탐색
- 한국 사용자 데이터 수집 설계
- 한국 음식 사진 -> 영양성분 -> CGM 반응 연결 검증

### 19.5 개인정보/보안

- 배포 환경 storage encryption 확인
- 사용자 ID와 건강 데이터 분리 저장
- 삭제 요청 처리 프로세스 구현
- 로그 마스킹 실제 적용
- 데이터 보존 기간 정책 확정

---

## 20. 제출용 결론

FoodSugar AI는 음식 이미지 분류, 영양성분 분석, 혈당 부담 참고 점수, CGM 기반 혈당 변화 가능성 예측, 안전한 웰니스 UX, 웹 MVP 구현까지 연결한 통합 AI 프로젝트이다. 단순히 모델 하나를 학습한 프로젝트가 아니라, 데이터 정리, 모델 학습, ensemble 최적화, API 구성, 혈당 시계열 모델링, 안전성 문구, 개인정보 정책, 사용자 파일럿 설계, 프론트엔드 MVP까지 실제 서비스 형태를 고려해 확장한 프로젝트라는 점이 핵심이다.

음식 이미지 분류에서는 K-Food 56-class validation 기준 top1 92.02%를 달성했다. 혈당 예측에서는 OhioT1DM 기반 enriched CGM forecasting 모델을 구축하고, 30분/60분/90분 horizon별 예측과 prediction interval, uncertainty message, hypo/hyper possibility signal을 제공하도록 했다. 또한 웹 MVP에서는 음식 사진 업로드부터 혈당 변화 가능성 표시까지 사용자가 직접 확인할 수 있는 흐름을 구현했다.

가장 중요한 점은 혈당 기능을 의료적 판단으로 포장하지 않았다는 것이다. 프로젝트는 혈당 예측의 한계와 불확실성을 인정하고, 이를 제품 UX에 반영했다. 90분 예측은 단일 숫자보다 범위와 불확실성 중심으로 보여주고, 모든 혈당 결과는 식습관 관리 참고용임을 명시했다. 이는 실제 사용자에게 안전하게 전달될 수 있는 AI 서비스로 발전하기 위한 중요한 기반이다.

---

## 부록 A. 핵심 파일 목록

### 음식 분류

```text
config/kfood_production_ensemble_config.json
src/classifier/ensemble_food_classifier.py
data/models/food_lewm_b0_classifier_3ep_ft10.pt
data/models/food_lewm_b0_supervised_only_seed123_fixed_v1_ft10.pt
data/models/efficientnet_korean_b3_full_fixed_v1.pt
data/models/food_lewm_b0_supervised_only_seed7_fixed_v1_ft10.pt
data/models/efficientnet_korean_b3_probe_fixed_v1.pt
data/models/efficientnet_korean_b3_cont_fixed_v1.pt
data/models/food_lewm_b0_supervised_only_ft10.pt
reports/b3/verified_92_hflip_7model_weighted_2026_05_16
```

### 영양성분/혈당 위험도

```text
src/nutrition/nutrition_db.py
src/predictor/sugar_predictor.py
src/glucose/risk.py
data/processed/kfood_nutrition_db.json
data/models/xgboost_sugar.pkl
```

### CGM 예측

```text
scripts/prepare_ohiot1dm_cgm.py
scripts/train_glucose_forecaster.py
scripts/validate_glucose_artifacts.py
src/glucose/ohiot1dm.py
src/glucose/forecasting.py
data/processed/ohiot1dm/cgm_timeseries_enriched.csv
data/processed/glucose_models_enriched/
reports/glucose_forecasting/
```

### 안전/파일럿/개인정보

```text
docs/GLUCOSE_PRODUCT_POSITIONING.md
docs/GLUCOSE_SAFETY_WORDING_GUIDE.md
docs/PILOT_STUDY_PROTOCOL.md
docs/PILOT_USER_CONSENT_DRAFT.md
docs/PILOT_DATA_SCHEMA.md
docs/GLUCOSE_DATA_GOVERNANCE.md
docs/GLUCOSE_PRIVACY_SECURITY_CHECKLIST.md
docs/GLUCOSE_LOGGING_POLICY.md
src/glucose/privacy.py
```

### 웹 MVP

```text
frontend/package.json
frontend/src/App.tsx
frontend/src/lib/api.ts
frontend/src/data/mockData.ts
frontend/src/pages/HomePage.tsx
frontend/src/pages/AnalysisPage.tsx
frontend/src/pages/PredictionPage.tsx
frontend/src/pages/HistoryPage.tsx
frontend/src/pages/SettingsPage.tsx
frontend/src/components/
```

---

## 부록 B. 제출 서류 재구성 가이드

이 장문 문서를 실제 제출 서류로 줄일 때는 다음 순서로 구성하는 것이 좋다.

1. 프로젝트 개요
2. 문제 정의와 필요성
3. 전체 시스템 구조
4. 음식 이미지 분류 모델
5. 영양성분 및 혈당 위험도
6. CGM 기반 혈당 예측
7. 안전성/개인정보/웰니스 포지셔닝
8. 웹 MVP 구현
9. 검증 결과
10. 한계와 향후 계획

발표 자료로 줄일 때는 다음 메시지를 중심으로 구성하면 좋다.

```text
우리는 음식 사진을 단순히 분류하는 것을 넘어,
그 음식이 사용자의 식습관과 혈당 변화 가능성에 어떤 참고 정보를 줄 수 있는지 연결했다.
이미지 분류 모델은 K-Food 56-class에서 92.02% validation top1을 달성했고,
CGM 기반 혈당 예측은 30/60/90분 horizon별 예측과 불확실성 표시를 제공한다.
단, 혈당 기능은 의료 진단이 아니라 웰니스 참고용으로 제한했고,
이를 웹 MVP에서 안전하게 표시하도록 구현했다.
```

---

## 부록 C. 상세 서술 확장본: 개발 단계별 진행 과정

### C.1 초기 단계: 음식 이미지 분류 문제로 시작

프로젝트의 초기 단계는 음식 이미지 분류 문제였다. 사용자가 음식 사진을 업로드하면 모델이 음식명을 예측하고, 그 결과를 바탕으로 영양성분과 혈당 부담을 계산하는 전체 시스템을 상상했다. 따라서 가장 먼저 필요한 것은 충분히 신뢰할 수 있는 음식 이미지 분류 모델이었다.

초기에는 단일 EfficientNet-B0 또는 B2 모델로 접근했지만, validation 기준으로 목표 성능에 도달하기 위해서는 데이터 split 정리, augmentation, seed 변경, 더 큰 backbone, TTA, ensemble이 필요하다는 점을 확인했다. 특히 한국 음식은 시각적으로 비슷한 class가 많다. 예를 들어 국물 요리, 찌개류, 탕류, 면류는 음식의 색상과 그릇 형태가 비슷할 수 있고, 고기류도 조리 방식과 촬영 각도에 따라 구분이 어렵다. 따라서 단일 모델만으로 높은 정확도를 안정적으로 확보하는 데 한계가 있었다.

이 문제를 해결하기 위해 모델 diversity를 확보하는 방향으로 진행했다. Food-LeWM pretraining, supervised-only seed 모델, B3 probe, B3 continuation, B3 full 25epoch 등 다양한 모델을 만들고, 각 모델의 hflip logits를 저장한 뒤 ensemble weight search를 수행했다. 최종적으로 B3 full이 가장 큰 비중을 차지하면서도, B0 seed 모델과 Food-LeWM 모델이 보조적인 diversity를 제공하는 7-model ensemble이 가장 좋은 결과를 냈다.

### C.2 중간 단계: label noise와 hard class 검토

모델 성능이 90%를 넘어서면서 단순 학습 epoch 증가만으로는 성능 향상이 제한적이라는 점이 드러났다. 이때부터는 hard class, hard pair, label noise, 검수 sheet, patch/exclude 후보 등을 검토했다. 특히 validation에서 반복적으로 틀리는 class를 확인하고, 해당 class가 실제로 모델이 어려워하는 visual boundary인지, 아니면 label 자체가 애매하거나 잘못되어 있는지를 분리하려고 했다.

이 과정에서 cleaned_v1 candidate, AI draft review, human review 필요성, train hard-pair candidates, label boundary noise 비율 등의 논의가 있었다. 최종적으로는 사람이 확정하지 않은 AI draft를 운영용 cleaned split으로 바로 사용하지 않고, candidate 실험으로 격리해야 한다는 판단을 세웠다. 이 판단은 데이터 품질 개선에서 중요한 원칙이다. label correction은 성능 향상에 도움이 될 수 있지만, 검수 기준이 불명확하면 오히려 validation-specific improvement 또는 잘못된 relabeling으로 이어질 수 있기 때문이다.

이 경험은 프로젝트의 방향에 영향을 주었다. 단순히 데이터를 많이 바꾸고 모델을 더 학습시키는 것보다, 기준 split을 유지하고 비교 가능한 실험을 하는 것이 중요하다는 점을 확인했다. 이 원칙은 이후 혈당 모델에서도 validation/test 분리와 leakage audit로 이어졌다.

### C.3 92% 달성 단계: ensemble search

K-Food 모델이 91% 후반까지 올라간 뒤 가장 어려웠던 지점은 92% threshold를 넘기는 것이었다. validation sample이 6,720장이므로 92%를 넘기려면 최소 6,183개 이상의 정답이 필요했다. 이전 best 3-model ensemble은 6,181개 정답으로 매우 근접했지만 목표에 2개 부족했다.

이후 여러 step size로 weight search를 수행했지만 3-model 조합만으로는 한계가 있었다. 그래서 기존에 만들어 둔 여러 모델의 logits cache를 합치고, sparse/random/local search 방식으로 후보를 확장했다. 최종적으로 7개 모델을 매우 불균형한 weight로 조합한 ensemble이 6,184개 정답을 달성했다. 이 결과는 목표를 1개 샘플 차이로 넘긴 것이며, 성능 향상이 얼마나 촘촘한 탐색과 다양성 확보에 의존했는지를 보여준다.

이 단계에서 얻은 교훈은 다음과 같다. 첫째, 고성능 구간에서는 단일 모델을 조금 더 학습하는 것보다 서로 다른 오류 패턴을 가진 모델을 조합하는 것이 효과적일 수 있다. 둘째, validation split에서 weight를 탐색한 결과는 반드시 caveat와 함께 보고해야 한다. 셋째, 운영 후보로 고정하려면 config와 preflight 검증이 필요하다. 그래서 최종적으로 production ensemble config와 validation script를 만들었다.

### C.4 영양성분 연결 단계: 모델 결과를 사용자 가치로 바꾸기

음식 분류 성능이 일정 수준에 도달한 뒤, 다음 문제는 “분류 결과를 사용자에게 어떻게 의미 있게 보여줄 것인가”였다. 음식명만 표시하면 사용자는 “그래서 이 음식이 내 식습관에 어떤 의미가 있지?”라는 질문을 하게 된다. 따라서 음식명과 영양성분을 연결하는 작업이 필요했다.

K-Food 56개 class label을 nutrition DB와 연결하면서 exact match가 가능한 항목과 그렇지 않은 항목을 나누었다. exact row가 없는 class는 curated alias 또는 평균값으로 보완했다. 예를 들어 `곰탕_설렁탕`은 하나의 음식만을 가리키는 class가 아니라 두 음식이 묶인 class이므로, 곰탕과 설렁탕 영양성분을 평균내는 방식으로 처리했다. 이러한 처리는 완벽한 영양성분 추정은 아니지만, class-level 참고 정보를 제공하는 데에는 충분한 출발점이 된다.

이후 영양성분 기반 혈당 위험도 점수를 추가했다. 여기서도 중요한 점은 의료적 확정 표현을 피하는 것이다. 같은 탄수화물 양이라도 개인별 반응은 다르며, 실제 식사량도 사진만으로 완벽히 알기 어렵다. 따라서 위험도는 “혈당 부담 가능성”으로 표현하고, 사용자에게 식습관 관리 참고 정보로 제공해야 한다.

### C.5 CGM 예측 단계: 시계열 문제로 확장

프로젝트가 더 발전하면서 음식 기반 위험도만으로는 충분하지 않다는 점을 고려했다. 실제 혈당 변화는 음식뿐 아니라 현재 혈당, 최근 추세, 활동, 수면, 인슐린, 시간대 등에 영향을 받는다. 따라서 CGM 데이터가 있는 경우 시계열 예측을 추가하는 방향으로 확장했다.

OhioT1DM 데이터는 XML 형태였고, 이를 분석 가능한 tabular time series로 변환해야 했다. 이 과정에서 CGM readings뿐 아니라 carbs, bolus, basal, exercise, sleep 등 이벤트 정보를 time-aligned feature로 변환했다. 모델은 30분, 60분, 90분 horizon별로 미래 glucose target을 구성했고, 현재와 과거 feature만 사용하도록 했다.

초기 모델은 baseline CGM feature만 사용했지만, 이후 enriched event feature, range-aware calibration, event classifier, long-horizon proxy feature, prediction interval, patient-specific evaluation 등이 추가되었다. 특히 60분/90분 horizon에서는 단순 회귀 예측의 불확실성이 커지기 때문에 point estimate보다 range와 uncertainty가 중요해졌다.

### C.6 안전성 전환 단계: 모델 프로젝트에서 제품 프로젝트로

혈당 예측 모델이 어느 정도 작동한 뒤, 다음 질문은 “이 결과를 사용자에게 어떻게 보여줘야 하는가”였다. 이 질문은 모델 정확도와는 다른 문제다. 모델이 MAE를 어느 정도 낮추더라도 사용자가 결과를 의료 판단으로 오해하면 위험하다. 특히 90분 예측처럼 불확실성이 큰 값을 큰 숫자로 보여주면 사용자는 그것을 확정적 미래 혈당으로 받아들일 수 있다.

그래서 프로젝트는 Safe Wellness Pilot 방향으로 전환했다. 이는 단순한 문구 수정이 아니라 제품 전략의 전환이었다. 혈당 기능을 의료 기능이 아니라 웰니스/식습관 관리 보조 기능으로 제한하고, 모든 혈당 결과에 참고용/비의료 문구를 포함하도록 했다. 또한 사용자 파일럿을 준비하기 위해 동의서 초안, 데이터 스키마, 개인정보/보안 체크리스트, 로그 마스킹 정책을 작성했다.

이 단계는 제출 서류에서 매우 중요하게 다룰 수 있다. 많은 AI 프로젝트는 모델 성능만 보여주고 끝나지만, FoodSugar AI는 실제 사용자에게 전달될 때의 안전성까지 고려했다. 특히 의료에 가까운 도메인에서는 이런 안전한 포지셔닝이 핵심이다.

### C.7 웹 MVP 단계: 체험 가능한 제품으로 만들기

마지막으로 웹 MVP를 구현했다. 사용자가 음식 사진을 업로드하고, 음식 분석 결과를 보고, 혈당 예측 화면으로 이동해 30분/60분/90분 결과와 그래프를 확인할 수 있도록 만들었다. backend가 꺼져 있어도 mock fallback으로 흐름이 유지되도록 했다. 이는 발표나 제출 시 매우 유용하다. 실제 모델 서버가 즉시 켜지지 않아도 제품 컨셉과 UX를 보여줄 수 있기 때문이다.

웹 MVP는 따뜻한 크림 배경과 그린 포인트를 사용해 병원/의료기기 느낌이 아니라 건강한 식습관 앱 느낌을 주도록 설계했다. 90분 예측은 큰 단일 숫자보다 범위와 불확실성 메시지를 강조했다. 모든 혈당 관련 화면에는 SafetyNotice를 표시했다.

이렇게 프로젝트는 “모델 실험”에서 “사용자 체험 가능한 안전한 웰니스 MVP”로 발전했다.

---

## 부록 D. 제출용 상세 문단 모음

### D.1 프로젝트 배경 문단

현대인은 식사 선택이 건강에 미치는 영향을 알고 싶어 하지만, 매번 음식의 영양성분을 직접 검색하고 자신의 혈당 변화를 예측하기는 어렵다. 특히 한국 음식은 밥, 면, 국물, 반찬, 양념이 복합적으로 구성되어 있어 단순한 음식명만으로 영양성분과 혈당 부담을 직관적으로 판단하기 어렵다. FoodSugar AI는 이러한 문제를 해결하기 위해 음식 사진 분석과 CGM 기반 혈당 변화 참고 기능을 결합한 웰니스 AI 시스템으로 개발되었다.

### D.2 기술 목표 문단

본 프로젝트의 기술 목표는 세 가지였다. 첫째, 한국 음식 56개 class를 높은 정확도로 분류하는 이미지 분류 모델을 구축하는 것이다. 둘째, 음식 분류 결과를 영양성분 DB와 연결하여 음식 기반 혈당 부담 참고 점수를 제공하는 것이다. 셋째, CGM 데이터가 있는 경우 최근 혈당 흐름과 식사 관련 이벤트를 반영해 30분, 60분, 90분 뒤 혈당 변화 가능성을 예측 범위와 불확실성 중심으로 제공하는 것이다.

### D.3 이미지 분류 성과 문단

음식 이미지 분류 모델은 K-Food fixed validation split 6,720장을 기준으로 평가되었다. EfficientNet-B0/B3, Food-LeWM, supervised seed 모델, B3 probe/full 모델 등 다양한 모델을 학습한 뒤, hflip TTA와 cached logits 기반 weighted ensemble search를 수행했다. 최종적으로 7-model hflip weighted ensemble이 top1 0.920238, top3 0.979464, macro_f1 0.920038을 달성했다. 이는 6,720개 validation sample 중 6,184개를 맞춘 결과이며, 목표였던 92% validation top1을 넘긴 성과다.

### D.4 혈당 예측 성과 문단

혈당 예측 파트에서는 OhioT1DM XML 데이터를 CGM 시계열 데이터로 변환하고, 30분/60분/90분 horizon별 enriched long-horizon forecasting 모델을 학습했다. 최신 calibrated MAE는 30분 12.998, 60분 22.633, 90분 29.606으로 확인되었다. 또한 단순 point prediction의 한계를 보완하기 위해 prediction interval, uncertainty level, range-aware calibration, hypo/hyper event classifier를 추가했다. 90분 예측은 불확실성이 크기 때문에 단일 숫자가 아니라 범위와 가능성 신호 중심으로 제공하도록 설계했다.

### D.5 안전성 문단

FoodSugar AI의 혈당 기능은 의료 진단이나 치료 지침이 아니다. 본 프로젝트는 혈당 예측 기능이 사용자의 치료 행동에 직접 영향을 주지 않도록 안전한 웰니스 포지셔닝을 명확히 했다. 모든 혈당 결과에는 참고용 문구를 포함하고, 저혈당/고혈당은 확정 판정이 아니라 가능성 신호로 표현한다. 또한 사용자 파일럿을 준비하기 위해 동의서 초안, 데이터 거버넌스, 개인정보/보안 체크리스트, 로그 마스킹 정책을 문서화했다.

### D.6 웹 MVP 문단

웹 MVP는 Vite, React, TypeScript, Tailwind CSS, Recharts, lucide-react를 사용해 구현했다. 사용자는 음식 사진을 업로드하고, 음식 분석 결과와 영양성분, 혈당 부담 참고 점수를 확인할 수 있다. 이후 CGM 예측 화면에서 30분/60분/90분 혈당 변화 가능성과 예측 범위, 불확실성, 저혈당/고혈당 가능성 신호를 확인할 수 있다. backend API 연결에 실패해도 mock fallback으로 데모가 계속 동작하도록 설계했다. 이는 발표나 제출 상황에서 안정적으로 프로젝트 흐름을 보여줄 수 있게 한다.

---

## 부록 E. 장문 제출 서술 확장: 시스템별 상세 설명

### E.1 음식 이미지 분류 시스템 상세 설명

음식 이미지 분류 시스템은 FoodSugar AI의 첫 번째 관문이다. 사용자가 앱을 사용할 때 가장 먼저 하는 행동은 음식 사진을 업로드하는 것이다. 이 사진이 어떤 음식인지 정확히 예측해야 이후 영양성분 조회와 혈당 부담 계산이 가능하다. 따라서 음식 이미지 분류 모델의 신뢰도는 전체 시스템의 기초 품질을 결정한다.

K-Food 음식 이미지는 일반적인 이미지 분류보다 어려운 지점이 있다. 한국 음식은 같은 음식이라도 지역, 조리법, 그릇, 고명, 양념, 촬영 각도에 따라 시각적 차이가 크다. 반대로 서로 다른 음식이라도 시각적으로 매우 비슷하게 보일 수 있다. 예를 들어 탕류와 찌개류는 국물 색과 재료가 비슷하게 나타날 수 있고, 면류는 그릇과 국물, 고명이 비슷하게 보일 수 있다. 고기류 역시 구이, 찜, 볶음, 양념 여부에 따라 구분이 애매할 수 있다.

이러한 특성 때문에 프로젝트에서는 단일 모델 학습만으로 끝내지 않았다. 여러 모델 계열을 학습하고, 각 모델이 다른 오류 패턴을 갖도록 seed와 architecture, pretraining 여부를 다르게 구성했다. Food-LeWM B0는 self-supervised pretraining 실험을 통해 representation 다양성을 확보하는 데 사용되었고, supervised-only B0 seed 모델은 ImageNet pretrained 기반의 안정적인 baseline 역할을 했다. EfficientNet-B3 full은 더 큰 backbone을 통해 단일 모델 성능을 끌어올리는 역할을 했다.

최종 ensemble에서 B3 full이 가장 큰 weight를 받은 것은 자연스러운 결과다. B3 full은 단일 모델 성능이 높았고, hflip 평가에서도 90% 이상의 top1을 보였다. 그러나 B3 full만으로는 92%에 도달하지 못했기 때문에, B0 seed 모델과 Food-LeWM 모델을 함께 조합했다. 이 ensemble은 각 모델의 장점을 결합해 validation에서 6,184개 정답을 달성했다.

### E.2 영양성분 연결 시스템 상세 설명

음식 분류 모델이 예측한 label은 그 자체로도 의미가 있지만, FoodSugar AI의 핵심 가치는 그 label을 영양성분과 연결하는 데 있다. 사용자는 “비빔밥”이라는 이름보다 “비빔밥이 탄수화물 85g, 당류 8g, 단백질 22g, 지방 15g 정도의 참고값을 가지고 있으며, 식후 혈당 상승 가능성이 상대적으로 높을 수 있다”는 정보를 더 필요로 한다.

이를 위해 K-Food 56개 class label과 nutrition DB를 연결했다. exact match가 가능한 음식은 DB의 값을 그대로 사용했고, exact match가 어려운 class는 alias 또는 평균값을 적용했다. 이 작업은 단순히 데이터를 붙이는 작업처럼 보일 수 있지만, 실제 서비스에서는 매우 중요하다. 모델이 예측한 class와 nutrition DB key가 맞지 않으면 API는 영양성분을 반환할 수 없고, 사용자는 분석 결과를 제대로 볼 수 없다.

영양성분 기반 혈당 위험도는 완전한 개인화 모델이 아니라 참고용 점수다. 이 점은 중요하다. 음식의 탄수화물과 당류가 높으면 혈당 상승 가능성이 높을 수 있지만, 개인마다 반응은 다르다. 또한 실제 섭취량과 사진 속 음식량은 다를 수 있다. 따라서 FoodSugar AI는 이 기능을 “혈당 부담 참고 점수”로 표현하고, 의료적 판단으로 보이지 않게 했다.

### E.3 CGM forecasting 시스템 상세 설명

CGM forecasting 시스템은 프로젝트의 두 번째 핵심 AI 기능이다. 음식 사진과 영양성분만으로는 사용자의 현재 혈당 상태를 알 수 없다. 예를 들어 같은 음식을 먹더라도 식전 혈당이 낮은지 높은지, 최근 혈당이 상승 중인지 하락 중인지, 운동을 했는지, bolus가 있었는지에 따라 이후 혈당 변화는 달라질 수 있다. CGM forecasting은 이러한 시계열 정보를 반영하기 위한 기능이다.

OhioT1DM 데이터는 XML 형식이므로, 먼저 이를 분석 가능한 CSV 시계열로 변환했다. 변환 과정에서는 glucose_level event를 중심으로 timestamp와 glucose_mg_dl 값을 추출했고, 환자 ID, 연도, split, source_file 정보를 함께 유지했다. 이후 식사, bolus, basal, 운동, 수면 등의 이벤트를 현재 시점 기준 rolling window feature로 변환했다.

모델은 30분, 60분, 90분 horizon별로 분리했다. 30분 예측은 최근 혈당 추세의 연장선으로 비교적 안정적인 편이지만, 60분과 90분은 식사 흡수, 인슐린 작용, 활동 변화 등 더 많은 요인에 영향을 받는다. 따라서 장기 horizon에서는 long-window feature와 IOB/COB proxy feature를 추가했다.

하지만 long-horizon upgrade 이후에도 MAE 개선은 매우 크지 않았다. 이는 중요한 발견이다. 장기 혈당 예측은 feature를 더 추가한다고 무조건 좋아지지 않는다. 개인별 차이와 이벤트 기록의 불완전성, CGM 센서 지연, 식사량 추정 오차가 모두 영향을 준다. 그래서 프로젝트는 단일 point estimate를 더 정밀하게 맞추는 것보다 prediction interval과 uncertainty를 함께 제공하는 방향으로 전환했다.

### E.4 calibration과 event classifier 상세 설명

회귀 모델은 평균적인 오차를 줄이는 방향으로 학습되기 때문에 극단 구간에서 bias가 생길 수 있다. 실제 혈당이 낮은 구간에서는 예측값이 평균으로 끌려 올라가고, 실제 혈당이 높은 구간에서는 예측값이 평균으로 끌려 내려가는 현상이 발생할 수 있다. 이는 전체 MAE만 보면 잘 드러나지 않지만, 안전한 해석에서는 매우 중요하다.

이를 보완하기 위해 range-aware calibration을 적용했다. 예측값이 low, normal, high range 중 어디에 있는지에 따라 validation에서 관찰된 mean error를 보정하는 방식이다. 또한 저혈당/고혈당 가능성을 회귀값 하나로만 판단하지 않고 별도 classifier로 예측했다. 이 classifier의 threshold는 validation에서 선택하고 test에서 최종 평가하도록 했다.

event classifier는 사용자에게 확정 판정을 주기 위한 것이 아니다. “저혈당 가능성 신호”, “고혈당 가능성 신호”를 보여주기 위한 것이다. 이 distinction은 제품 안전성에서 매우 중요하다. 가능성 신호는 사용자가 실제 측정값과 증상을 확인하도록 돕는 참고 정보이며, 치료 행동을 지시하지 않는다.

### E.5 웹 MVP UX 상세 설명

웹 MVP는 사용자가 프로젝트의 전체 흐름을 체험할 수 있게 한다. 홈 화면에서 음식 사진을 업로드하면 preview가 표시되고, 분석 버튼을 누르면 backend `/predict/analyze`를 호출한다. backend가 없으면 mock data가 표시된다. 분석 결과 화면에서는 음식명, 신뢰도, 영양성분, 혈당 부담 참고 점수가 나타난다. 사용자는 여기서 혈당 변화 보기 버튼을 눌러 prediction page로 이동할 수 있다.

Prediction page에서는 현재 혈당 112 mg/dL 기준 mock prediction이 표시된다. 30분은 138 mg/dL처럼 숫자 중심으로 보여주지만, 60분과 90분은 범위를 함께 보여준다. 특히 90분은 104~205 mg/dL 범위와 “불확실성 높음” 메시지를 강조한다. 이는 프로젝트의 safety principle을 UI에 구현한 것이다.

웹앱 디자인은 따뜻한 크림 배경과 그린 포인트를 사용했다. 이는 병원/의료기기처럼 딱딱한 느낌보다, 식습관 관리와 웰니스 앱에 가까운 느낌을 주기 위한 선택이다. UI에서 사용되는 모든 혈당 관련 문구는 참고용/가능성 신호 중심으로 작성했다.

---

## 부록 F. 최종 제출용 아주 짧은 요약

FoodSugar AI는 음식 사진 분석과 CGM 기반 혈당 변화 가능성 예측을 결합한 웰니스 AI 프로젝트이다. K-Food 56-class 음식 이미지 분류에서는 7-model hflip weighted ensemble을 구축해 fixed validation split 기준 top1 92.02%를 달성했다. 이후 음식 분류 결과를 nutrition DB와 연결하여 영양성분과 혈당 부담 참고 점수를 제공했다. CGM 파트에서는 OhioT1DM XML 데이터를 시계열 CSV로 변환하고, 30분/60분/90분 horizon별 혈당 예측 모델을 학습했다. 또한 low/high glucose bias를 고려해 range-aware calibration, hypo/hyper event classifier, prediction interval, uncertainty message를 추가했다. 혈당 기능은 의료 진단이나 치료 지침이 아니라 식습관 관리 참고용으로 제한했으며, 안전 문구와 개인정보/로그 정책, 파일럿 설계 문서를 함께 구축했다. 마지막으로 Vite React TypeScript 기반 웹 MVP를 구현해 사용자가 음식 사진 업로드, 영양성분 확인, 혈당 부담 점수, CGM 기반 혈당 변화 가능성, 예측 범위와 불확실성을 직접 확인할 수 있도록 했다.

---

## 부록 G. 제출용 확장 서술: 기획 의도와 사용자 시나리오

### G.1 기획 의도

FoodSugar AI의 기획 의도는 단순히 음식 이미지를 맞히는 기술 데모를 만드는 것이 아니었다. 프로젝트의 출발점은 “사용자가 매일 먹는 음식이 건강 관리와 어떤 관계가 있는지를 더 쉽게 이해할 수 있게 만들 수 있을까”라는 질문이었다. 음식 사진 인식 기술은 이미 다양한 형태로 존재하지만, 그 결과가 음식명 하나로 끝나면 실제 사용자의 행동 변화로 이어지기 어렵다. 사용자는 “이 음식이 무엇인가”보다 “이 음식을 먹으면 내 식습관 관리에 어떤 의미가 있는가”를 알고 싶어 한다.

특히 혈당 관리는 음식 선택과 매우 밀접한 영역이다. 탄수화물과 당류가 많은 음식은 식후 혈당 변화를 크게 만들 수 있지만, 일반 사용자가 매번 음식의 탄수화물 함량을 계산하기는 어렵다. CGM을 사용하는 사람도 혈당 그래프를 볼 수는 있지만, 특정 식사와 이후 혈당 흐름을 직관적으로 연결해 이해하는 것은 쉽지 않다. FoodSugar AI는 이 지점을 연결하려고 했다. 즉, 음식 사진이라는 쉬운 입력을 시작점으로 삼고, 음식명, 영양성분, 혈당 부담, CGM 기반 변화 가능성까지 이어지는 하나의 사용자 경험을 만드는 것이 목표였다.

기획 과정에서 가장 중요하게 고려한 것은 “편리함”과 “안전함”의 균형이었다. 사용자가 음식을 찍기만 하면 결과를 볼 수 있어야 하지만, 혈당 관련 결과가 의료적 판단처럼 보이면 안 된다. 따라서 프로젝트는 기술적으로는 이미지 분류와 시계열 예측을 결합했지만, 제품적으로는 웰니스와 식습관 관리 보조라는 경계를 명확히 했다. 이 경계를 지키기 위해 모델 성능뿐 아니라 안전 문구, prediction interval, uncertainty, 가능성 신호, 개인정보 정책까지 함께 정리했다.

### G.2 사용자 시나리오 1: 음식 사진 기반 기본 분석

첫 번째 사용자 시나리오는 CGM 데이터가 없는 일반 사용자가 음식 사진만 업로드하는 상황이다. 사용자는 점심 식사 전 음식 사진을 찍어 웹앱에 업로드한다. 웹앱은 이미지를 preview로 보여주고, 사용자가 분석 시작 버튼을 누르면 backend의 `/predict/analyze` endpoint를 호출한다. backend가 정상 동작 중이면 K-Food classifier가 음식명을 예측하고, nutrition DB에서 영양성분을 조회한 뒤, 혈당 부담 참고 점수를 계산한다. backend가 꺼져 있거나 네트워크 문제가 있으면 mock fallback을 사용해 데모 데이터로 흐름을 유지한다.

결과 화면에서는 음식명, 신뢰도, 칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유가 표시된다. 사용자는 이 정보를 통해 음식의 대략적인 영양 구성을 이해할 수 있다. 이어서 혈당 부담 참고 점수가 낮음, 보통, 높음 중 하나로 표시된다. 이때 앱은 “이 결과는 음식 영양성분 기반 참고용 분석이며 의료 진단이나 치료 지침이 아니다”라는 문구를 함께 보여준다. 사용자는 앱 결과를 식사 선택의 참고 정보로 사용할 수 있지만, 이를 의학적 판단으로 받아들이면 안 된다.

이 시나리오에서 중요한 UX는 confidence 처리이다. 음식 인식 confidence가 낮으면 앱은 사용자에게 음식명을 확인하도록 유도해야 한다. 왜냐하면 영양성분과 혈당 부담은 음식명에 크게 의존하기 때문이다. 예를 들어 비슷한 색과 형태의 찌개류가 잘못 분류되면 탄수화물이나 나트륨, 칼로리 추정이 달라질 수 있다. 따라서 낮은 confidence 상황에서는 결과를 확정적으로 보여주기보다 “음식명을 확인하세요”라는 안내가 필요하다.

### G.3 사용자 시나리오 2: CGM 데이터가 있는 사용자

두 번째 사용자 시나리오는 CGM 데이터를 가진 사용자가 식후 혈당 변화 가능성을 확인하는 상황이다. 사용자는 음식 사진 분석 후 “혈당 변화 보기” 버튼을 누른다. 웹앱은 sample CGM payload 또는 실제 CGM readings를 바탕으로 `/predict/cgm-forecast-enriched-events` endpoint를 호출한다. backend가 정상 동작하면 calibrated prediction, prediction interval, uncertainty, risk flags, risk messages를 받아온다. backend가 없으면 mockPrediction을 사용한다.

Prediction 화면에서는 현재 혈당과 30분, 60분, 90분 결과가 표시된다. 30분은 비교적 단기 예측이므로 숫자 중심으로 보여줄 수 있다. 하지만 60분은 범위와 가능성 신호를 함께 보여주고, 90분은 단일 숫자보다 예측 범위와 불확실성 메시지를 강조한다. 예를 들어 90분 결과는 “142 mg/dL”을 크게 보여주는 대신 “104~205 mg/dL, 불확실성 높음, 참고용 범위와 가능성 신호로만 확인”과 같이 표시한다.

이 시나리오의 핵심은 사용자가 예측값을 실제 미래 혈당으로 오해하지 않도록 만드는 것이다. 혈당 예측은 CGM 센서 오차, 식사량 차이, 운동, 수면, 인슐린, 스트레스 등 다양한 요인에 영향을 받는다. 따라서 앱은 예측값을 확정적으로 제시하지 않고, 실제 측정값과 증상을 우선 확인하라고 안내한다. 이 원칙은 SafetyNotice와 uncertainty message에 반영되어 있다.

### G.4 사용자 시나리오 3: 기록과 회고

세 번째 사용자 시나리오는 사용자가 자신의 식사 기록과 혈당 영향 요약을 확인하는 상황이다. 현재 MVP에서는 backend history API가 없으므로 mock data를 사용하지만, 향후 실제 앱에서는 사용자가 기록한 식사 사진, 음식명, 영양성분, 혈당 부담, CGM 반응, 사용자 피드백을 시간순으로 보여줄 수 있다.

기록 화면은 사용자가 단일 식사 결과를 넘어 패턴을 이해하도록 돕는다. 예를 들어 “주간 평균 혈당”, “혈당 변동성”, “가장 높은 시간대”, “혈당 영향이 높았던 음식” 등을 보여줄 수 있다. 이 화면은 사용자가 반복적으로 어떤 음식에서 혈당 변동이 커지는지 회고하는 데 도움이 된다. 다만 여기서도 의료적 판단을 제공하면 안 되며, 식습관 관리 참고용으로 제한해야 한다.

### G.5 사용자 시나리오 4: 설정과 안전 안내

설정/소개 화면은 프로젝트의 신뢰성과 안전성을 설명하는 역할을 한다. 사용자는 이 화면에서 FoodSugar AI가 어떤 서비스인지, CGM 연결 상태가 무엇인지, 데이터가 어떻게 처리되는지, 모델의 한계가 무엇인지 확인할 수 있다. 특히 “본 결과는 의료 진단이나 치료 지침이 아니다”라는 문구가 명확히 표시되어야 한다.

제출 서류나 발표에서 이 화면은 매우 중요하다. 기술 구현만 보여주는 것이 아니라, 프로젝트가 실제 사용 상황에서 발생할 수 있는 오해와 위험을 고려했다는 점을 보여주기 때문이다. AI 서비스가 건강 관련 정보를 다룰 때는 모델 성능뿐 아니라 사용자 커뮤니케이션과 안전한 제품 경계 설정이 필수적이다.

---

## 부록 H. 제출용 확장 서술: 데이터와 평가 설계의 의미

### H.1 K-Food 데이터 split의 의미

K-Food 이미지 분류에서 `data/raw/korean_food_fixed_v1` split은 프로젝트의 기준점이다. 모델 실험이 많아질수록 기준 split이 흔들리면 성능 비교가 어려워진다. 예를 들어 어떤 모델은 원래 validation에서 평가하고, 다른 모델은 cleaned candidate validation에서 평가하면 두 결과를 직접 비교할 수 없다. 따라서 프로젝트에서는 fixed_v1 validation split을 기준으로 성능 비교를 유지했다.

validation sample 수는 6,720장이며 class는 56개다. 이 수치는 class당 일정 수의 validation sample이 확보되어 있음을 의미한다. top1 92%를 넘기기 위해서는 최소 6,183개 이상의 정답이 필요했다. 최종 ensemble은 6,184개 정답을 달성했다. 즉 목표를 매우 촘촘하게 넘긴 결과이며, 이 수치는 제출 서류에서 프로젝트의 성능 목표 달성 근거로 사용할 수 있다.

하지만 동시에 이 validation split에서 ensemble weight를 탐색했다는 점도 정직하게 언급해야 한다. 최종 weight가 validation에 최적화되었을 가능성이 있기 때문이다. 따라서 향후 별도 holdout 또는 실제 사용자 데이터에서 추가 검증이 필요하다. 이 caveat는 프로젝트의 신뢰성을 낮추는 것이 아니라, 오히려 연구자로서 성능을 정직하게 해석하고 있음을 보여준다.

### H.2 OhioT1DM 데이터의 의미

OhioT1DM 데이터는 CGM forecasting 실험을 가능하게 만든 핵심 데이터다. 이 데이터는 환자별 CGM readings와 여러 event 정보를 포함한다. 하지만 이 데이터가 FoodSugar AI의 실제 목표 사용자 전체를 대표한다고 볼 수는 없다. 특히 한국 음식, 한국 사용자, 실제 식사 사진 기반 영양 추정과는 차이가 있다.

따라서 OhioT1DM은 “혈당 예측 파이프라인과 모델링 방법을 검증하기 위한 연구용 benchmark”로 사용하는 것이 적절하다. 프로젝트에서는 OhioT1DM만으로 일반 사용자 서비스 성능을 주장하지 않고, 외부 데이터와 한국 사용자 파일럿 검증 계획을 따로 세웠다. 이 점은 제출 서류에서 한계와 향후 계획으로 명확히 적는 것이 좋다.

### H.3 validation/test 분리의 의미

혈당 예측에서는 validation/test 분리가 특히 중요하다. 모델 선택, threshold 선택, calibration strategy 선택에 test를 사용하면 최종 test 성능이 과대평가된다. 프로젝트에서는 train_inner와 validation을 분리해 모델과 threshold를 선택하고, test는 최종 평가에만 사용하도록 했다. 또한 leakage audit을 수행해 threshold selection과 calibration safety가 문서화되었는지 확인했다.

이 구조는 제출 서류에서 “평가 신뢰성”을 보여주는 핵심 근거다. 단순히 MAE 수치만 제시하는 것보다, 어떤 split으로 모델을 선택했고 어떤 split으로 최종 평가했는지를 설명하는 것이 더 중요하다. 특히 건강 관련 예측에서는 leakage가 있으면 실제 사용 가능성을 과대평가하게 되므로, 이 부분을 명확히 적어야 한다.

### H.4 MAE와 interval을 함께 보는 이유

CGM 예측에서 MAE는 중요한 지표지만 충분하지 않다. 예를 들어 90분 MAE가 29.606이라고 해도, 개별 사용자 또는 특정 glucose range에서는 오차가 훨씬 클 수 있다. 또한 저혈당/고혈당 구간에서 평균으로 회귀하는 bias가 있으면 전체 MAE는 괜찮아도 위험 신호를 놓칠 수 있다.

그래서 prediction interval과 event classifier를 함께 사용했다. Prediction interval은 사용자가 예측값의 불확실성을 이해하도록 돕는다. Event classifier는 회귀값 하나만으로 위험 가능성을 판단하지 않도록 보완한다. 이 설계는 “정확한 혈당 예측”을 주장하기보다 “불확실성을 포함한 참고 정보”를 제공한다는 프로젝트 철학과 일치한다.

### H.5 사용자 이해도 지표의 필요성

향후 파일럿에서는 모델 성능 지표뿐 아니라 사용자 이해도 지표도 필요하다. 예를 들어 사용자가 “가능성 신호”를 “확정 진단”으로 이해한다면 UI 문구를 수정해야 한다. 사용자가 90분 예측 범위를 보고도 단일 수치처럼 받아들인다면 표시 방식이 잘못된 것이다. 또한 오경고가 많아 사용자가 앱을 신뢰하지 않게 되는지도 확인해야 한다.

따라서 파일럿 metric plan에는 MAE, interval coverage, event recall/precision뿐 아니라 reference-only comprehension, perceived-as-medical-advice, false alarm fatigue, unclear wording report 같은 UX/safety metric이 포함되어야 한다. FoodSugar AI는 모델 성능과 사용자 안전을 함께 평가해야 하는 프로젝트이다.

---

## 부록 I. 제출용 확장 서술: 모델별 역할과 앙상블 해석

### I.1 왜 단일 모델이 아니라 ensemble인가

음식 이미지 분류에서 단일 모델은 특정 데이터 분포와 class boundary에 맞춰 학습된다. 하지만 음식 이미지는 촬영 조건, 조리 방식, 배경, 그릇, 조명, 음식 배치에 따라 다양하게 나타난다. 단일 모델이 모든 상황을 안정적으로 맞히기는 어렵다. Ensemble은 서로 다른 모델이 가진 오류 패턴을 결합해 전체 정확도를 높이는 방법이다.

FoodSugar AI에서는 B0 계열, Food-LeWM 계열, B3 계열, seed가 다른 supervised-only 모델을 조합했다. 각 모델은 architecture, initialization, training recipe, pretraining 여부가 다르기 때문에 서로 다른 샘플에서 강점을 보일 수 있다. 최종 weight가 높은 모델은 B3 full이지만, weight가 낮은 모델도 특정 샘플에서 ensemble decision에 기여할 수 있다.

### I.2 B3 full의 역할

B3 full은 최종 ensemble에서 0.52949의 가장 큰 weight를 받았다. 이는 B3 full이 전체적으로 가장 강한 기반 모델임을 의미한다. B3 full은 image size 300, 25epoch, head_lr와 backbone lr 분리, label smoothing, randaugment, random erasing 등 비교적 강한 supervised training recipe를 사용했다. 단일 hflip eval에서도 top1 0.904315를 달성했다.

하지만 B3 full만으로 92%에 도달하지는 못했다. 이는 강한 단일 모델도 일부 hard class와 boundary case에서 한계가 있음을 보여준다. Ensemble은 이러한 한계를 보완했다.

### I.3 B0 seed 모델의 역할

`b0_seed123_fixed_v1`과 `b0_seed7_fixed_v1`은 같은 계열이지만 seed가 다르다. seed 차이는 모델이 학습하는 local optimum과 일부 decision boundary에 영향을 줄 수 있다. 성능이 높은 B3 full과 다른 seed B0 모델을 조합하면 일부 샘플에서 예측이 보완될 수 있다. 특히 최종 ensemble에서 `b0_seed123_fixed_v1`은 0.256735라는 큰 weight를 받았고, 이는 B3 full 다음으로 중요한 구성원이다.

### I.4 Food-LeWM의 역할

Food-LeWM은 self-supervised pretraining을 통해 음식 이미지 representation을 학습하려는 실험이었다. 최종적으로 LeWM pretraining이 항상 supervised-only보다 우월하다고 결론내리기는 어렵다. 하지만 최종 ensemble에서 `food_lewm_b0`는 0.14236의 weight를 받았다. 이는 모델이 단일 성능만으로는 평가하기 어려운 ensemble diversity를 제공했음을 의미한다.

### I.5 낮은 weight 모델의 의미

최종 ensemble에는 `b3_probe_fixed_v1`, `b3_cont_fixed_v1`, `b0_supervised_only`처럼 weight가 매우 낮은 모델도 포함되었다. 이 모델들은 전체 decision에 큰 영향을 주지는 않지만, 특정 validation sample에서 tie-breaking 또는 confidence 조정에 기여했을 가능성이 있다. 92% threshold를 1개 샘플 차이로 넘긴 결과였기 때문에, 낮은 weight 모델도 최종 후보에서 완전히 무의미하다고 볼 수 없다.

### I.6 ensemble의 한계

Ensemble은 정확도를 높일 수 있지만, inference cost가 증가한다. 7개 모델을 hflip TTA로 돌리면 단일 모델보다 latency와 compute cost가 커진다. 운영 서비스에서는 성능과 latency의 균형을 다시 검토해야 한다. 제출 서류에서는 “현재 운영 후보는 정확도 중심의 7-model ensemble이며, 실제 제품 배포 전 latency 측정과 경량화 검토가 필요하다”고 적는 것이 좋다.

---

## 부록 J. 제출용 확장 서술: 웹 MVP 화면별 상세 설명

### J.1 홈 화면

홈 화면은 사용자가 처음 만나는 화면이므로 프로젝트의 성격을 명확히 전달해야 한다. FoodSugar AI가 의료 앱이 아니라 웰니스 AI 데모라는 점을 보여주면서도, 음식 사진 업로드라는 핵심 행동을 바로 할 수 있어야 한다. 현재 홈 화면은 왼쪽에 서비스 설명과 촬영 팁을 두고, 오른쪽에 큰 upload box를 배치했다.

업로드 박스는 드래그 앤 드롭과 파일 선택을 모두 지원한다. 사용자가 이미지를 선택하면 preview가 표시되고, 분석 시작 버튼이 활성화된다. 이 흐름은 사용자가 앱을 처음 접해도 쉽게 이해할 수 있도록 설계되었다. 배경은 pure white가 아니라 크림색을 사용했고, 포인트 컬러는 세이지/포레스트 그린 계열로 구성했다.

### J.2 음식 분석 화면

음식 분석 화면은 사용자가 업로드한 음식과 AI 분석 결과를 확인하는 공간이다. FoodPreviewCard는 음식명과 confidence를 보여준다. NutritionCard는 칼로리, 탄수화물, 당류, 단백질, 지방, 식이섬유를 카드 형태로 보여준다. GlucoseRiskCard는 혈당 부담 참고 점수와 예상 혈당 상승 가능성, 피크 예상 시간을 표시한다.

이 화면에서 중요한 점은 결과가 과도하게 확정적으로 보이지 않도록 하는 것이다. 음식명은 AI 예측이며, confidence가 낮을 경우 사용자 확인이 필요하다. 혈당 부담도 음식 영양성분 기반 참고 정보이므로 SafetyNotice를 함께 표시한다.

### J.3 혈당 예측 화면

혈당 예측 화면은 프로젝트의 안전 UX가 가장 중요하게 드러나는 화면이다. 30분, 60분, 90분을 동일한 방식으로 보여주지 않고 horizon별로 다르게 표현했다. 30분은 단기 예측이므로 숫자를 비교적 크게 보여준다. 60분은 범위와 참고 수치를 함께 표시한다. 90분은 범위와 불확실성을 중심으로 보여주고, “범위 우선” badge를 추가했다.

그래프에서는 현재, 30분, 60분, 90분, 120분 흐름을 보여준다. 목표 범위 70~180 mg/dL 영역을 표시해 사용자가 혈당 변화 가능성을 시각적으로 이해할 수 있게 했다. RiskSignalCard는 저혈당/고혈당 가능성 신호를 표시한다. 여기서도 확정 표현을 피하고 가능성 신호라는 표현을 사용한다.

### J.4 기록 화면

기록 화면은 현재 mock 데이터 기반이지만, 향후 실제 서비스에서 중요한 역할을 할 수 있다. 사용자는 단일 식사 분석보다 자신의 반복 패턴을 확인하고 싶어 한다. 어떤 음식에서 혈당 영향이 컸는지, 하루 중 어떤 시간대가 높았는지, 주간 평균과 변동성이 어떤지 볼 수 있어야 한다. 현재 MVP는 이를 보여주는 기초 구조를 제공한다.

### J.5 설정 화면

설정 화면은 서비스 소개와 안전 안내를 담당한다. CGM 연결 상태, 데이터 처리 안내, 개인정보 원칙, 모델 한계를 설명한다. 특히 혈당 기능이 의료 진단이나 치료 지침이 아니라는 문구를 명확히 표시한다. 제출용 시연에서는 이 화면을 보여주면 프로젝트가 안전성과 책임 있는 AI 사용을 고려했다는 점을 강조할 수 있다.

---

## 부록 K. 제출용 확장 서술: 리스크 관리와 개선 계획

### K.1 기술 리스크

첫 번째 기술 리스크는 K-Food ensemble의 validation-specific tuning이다. 최종 92.02%는 fixed validation에서 weight search를 통해 얻은 결과이므로, 실제 외부 데이터에서 동일한 성능이 나올지는 확인이 필요하다. 이를 해결하기 위해 별도 holdout set, human-reviewed clean validation subset, 실제 사용자 이미지 평가가 필요하다.

두 번째 기술 리스크는 웹 MVP의 backend 연동 상태다. 현재 frontend는 backend API를 호출하되 실패하면 mock fallback을 사용한다. 이는 데모 안정성에는 좋지만, 실제 서비스 검증을 위해서는 backend를 켠 상태에서 end-to-end 테스트가 필요하다. 특히 `/predict/analyze`와 `/predict/cgm-forecast-enriched-events`가 실제 응답을 반환할 때 frontend mapping이 의도대로 되는지 확인해야 한다.

세 번째 기술 리스크는 CGM prediction의 일반화다. OhioT1DM 데이터에서 얻은 모델이 한국 사용자와 한국 음식 환경에서도 잘 작동한다는 보장은 없다. 외부 데이터셋과 한국 사용자 파일럿이 필요하다.

### K.2 제품 리스크

가장 큰 제품 리스크는 사용자가 혈당 예측을 의료 판단으로 오해하는 것이다. 이를 줄이기 위해 SafetyNotice, reference_notice, uncertainty_message, possibility signal wording을 적용했다. 하지만 실제 사용자 테스트에서 문구가 충분히 이해되는지는 별도로 확인해야 한다.

두 번째 제품 리스크는 오경고 피로다. 저혈당/고혈당 가능성 신호가 너무 자주 뜨면 사용자는 앱을 불편하게 느끼거나 신뢰하지 않을 수 있다. 반대로 너무 적게 뜨면 위험 구간을 놓칠 수 있다. 파일럿에서 precision/recall뿐 아니라 사용자 피드백을 함께 봐야 한다.

세 번째 제품 리스크는 음식량 추정이다. 현재 웹 MVP는 음식 사진으로 섭취량을 정확히 추정하지 않는다. `portion_g`는 기본값 또는 사용자 입력에 의존한다. 실제 서비스에서는 사용자에게 섭취량 확인 UX를 제공해야 한다.

### K.3 개인정보 리스크

CGM 데이터, 식사 사진, 인슐린/bolus/basal 정보는 민감한 데이터다. 실제 파일럿에서는 데이터 수집 동의, 저장 기간, 삭제 요청, 암호화, 접근 권한, 로그 마스킹이 필요하다. 현재 문서와 helper는 준비되어 있지만, 실제 배포 환경에서 정책이 제대로 적용되는지는 별도 점검해야 한다.

### K.4 개선 계획

개선 계획은 단계별로 진행하는 것이 좋다.

1. 웹 MVP end-to-end 연결 확인
2. K-Food holdout 평가
3. 실제 음식 사진 사용자 테스트
4. 파일럿 동의서/개인정보 정책 검토
5. 소규모 CGM 파일럿
6. CGM 모델 patient-specific calibration 개선
7. 웹앱 기록/리포트 기능 실제화
8. 배포 환경 보안 점검

---

## 부록 L. 제출용 확장 서술: 평가 지표 상세

### L.1 음식 이미지 분류 지표

음식 이미지 분류에서는 top1, top3, macro_f1, per-class accuracy, confusion matrix를 사용했다. Top1은 모델이 가장 높은 확률로 예측한 class가 정답인지 보는 지표다. Top3는 상위 3개 후보 안에 정답이 있는지 보는 지표로, 사용자가 후보 중에서 음식명을 선택하거나 수정할 수 있는 UX에서는 의미가 있다. Macro F1은 class별 성능 균형을 확인하는 데 유용하다.

최종 후보의 주요 지표:

```text
top1: 0.9202380952380952
top3: 0.9794642857142857
macro_f1: 0.9200379850437458
correct: 6184 / 6720
```

이 수치는 음식 분류 파트의 정량적 성과를 보여준다. 다만 weak class와 hard pair는 여전히 존재하므로, per-class metric 분석이 필요하다.

### L.2 혈당 예측 지표

혈당 예측에서는 horizon별 MAE를 기본 지표로 사용했다.

```text
30m MAE: 12.998
60m MAE: 22.633
90m MAE: 29.606
```

하지만 MAE만으로는 충분하지 않다. Prediction interval coverage와 interval width를 함께 봐야 한다.

```text
30m coverage: 0.919, width: 64.487
60m coverage: 0.915, width: 107.109
90m coverage: 0.912, width: 136.114
```

또한 low/high glucose 구간별 error, hypo/hyper event classifier precision/recall, patient별 성능 편차도 중요하다.

### L.3 UX/safety 지표

파일럿에서는 다음 UX/safety 지표를 봐야 한다.

- 사용자가 참고용 문구를 이해했는지
- 가능성 신호를 진단으로 오해했는지
- 90분 예측을 정확한 수치로 받아들였는지
- 오경고가 불편했는지
- 앱 결과 때문에 치료/약물 행동을 바꾸려고 했는지
- 삭제 요청이나 개인정보 우려가 있었는지

이 지표들은 모델 성능 지표와 함께 봐야 한다. FoodSugar AI는 건강 관련 웰니스 기능이므로, 사용자가 결과를 안전하게 해석하는지가 매우 중요하다.

---

## 부록 M. 제출용 확장 서술: 최종 메시지

FoodSugar AI 프로젝트의 핵심 메시지는 “음식 사진을 건강 관리 맥락으로 연결하는 AI”이다. 단순히 음식 이미지를 맞히는 데서 끝나지 않고, 영양성분과 혈당 부담, CGM 기반 혈당 변화 가능성까지 연결했다. 모델 개발 과정에서는 K-Food 56-class 이미지 분류에서 92.02% validation top1을 달성했고, 혈당 예측 과정에서는 OhioT1DM 기반 30/60/90분 forecasting 모델과 event classifier, prediction interval을 구축했다.

동시에 이 프로젝트는 혈당 예측의 한계를 인정한다. 90분 예측은 불확실성이 크며, 음식 기반 혈당 위험도는 개인별 반응을 확정할 수 없다. 그래서 FoodSugar AI는 의료 진단이나 치료 지침이 아니라 식습관 관리 참고용 웰니스 서비스로 포지셔닝했다. 이 점을 제품 문구, API response, 테스트, 웹앱 UX에 반영했다.

최종적으로 FoodSugar AI는 모델 성능, 데이터 파이프라인, API, 안전성 문서, 웹 MVP까지 갖춘 통합 프로젝트로 발전했다. 제출 서류에서는 이 통합성을 강조하는 것이 좋다. 하나의 알고리즘 성능만이 아니라, 실제 사용자가 접할 수 있는 서비스 형태로 발전시켰다는 점이 프로젝트의 가장 큰 강점이다.

---

## 부록 N. 제출 서류 재작성용 목차 제안

실제 제출 서류를 새로 작성할 때는 이 장문 문서를 그대로 제출하기보다, 평가 기준에 맞춰 압축하는 것이 좋다. 아래는 공모전, 교내 프로젝트, 캡스톤디자인, 연구 보고서, 포트폴리오 제출 등에 맞게 재구성할 수 있는 목차 제안이다.

### N.1 10페이지 내외 제출 보고서 목차

```text
1. 프로젝트 개요
   - FoodSugar AI 한 줄 소개
   - 음식 이미지 분석과 혈당 변화 참고 기능의 결합
   - 웰니스/식습관 관리 보조 서비스라는 포지션

2. 문제 정의
   - 사용자가 음식의 혈당 영향을 직관적으로 이해하기 어려움
   - 한국 음식의 복합성
   - CGM 데이터 해석의 어려움

3. 전체 시스템 구조
   - 음식 이미지 -> classifier -> nutrition DB -> glucose risk
   - CGM readings -> forecasting model -> interval/uncertainty/signal
   - FastAPI backend와 React frontend

4. 음식 이미지 분류 모델
   - K-Food 56-class dataset
   - EfficientNet-B0/B3, Food-LeWM, seed 실험
   - 7-model hflip weighted ensemble
   - validation top1 92.02%

5. 영양성분 및 혈당 부담 점수
   - K-Food label과 nutrition DB 연결
   - 영양성분 기반 참고용 risk score
   - rule-based fallback과 XGBoost predictor

6. CGM 기반 혈당 예측
   - OhioT1DM XML 파싱
   - enriched CGM feature engineering
   - 30/60/90분 horizon별 forecasting
   - calibrated MAE와 prediction interval

7. 안전성 설계
   - 의료 진단/치료 아님
   - reference notice와 safety warning
   - hypo/hyper possibility signal
   - 개인정보/로그 마스킹 정책

8. 웹 MVP 구현
   - Vite React TypeScript
   - 음식 업로드, 분석 결과, 혈당 예측, 기록, 설정
   - mock fallback
   - 90분 예측 UX

9. 검증 결과
   - K-Food config validation
   - glucose artifact validation
   - pytest 72 passed
   - frontend build success

10. 한계와 향후 계획
   - validation-tuned ensemble caveat
   - OhioT1DM-only limitation
   - 사용자 파일럿 필요
   - 외부 데이터 검증 계획
```

### N.2 3분 발표용 구성

3분 발표에서는 모든 기술 세부사항을 설명하기 어렵다. 다음 흐름이 가장 좋다.

```text
1. 문제 제기
   우리는 매일 음식을 먹지만, 그 음식이 혈당에 어떤 영향을 줄 수 있는지 쉽게 알기 어렵습니다.

2. 해결 아이디어
   FoodSugar AI는 음식 사진을 분석해 음식명과 영양성분을 보여주고,
   CGM 데이터가 있으면 식후 혈당 변화 가능성을 참고용으로 예측합니다.

3. 핵심 기술
   K-Food 56-class 이미지 분류에서 7-model ensemble으로 92.02%를 달성했고,
   OhioT1DM 기반 CGM forecasting으로 30/60/90분 예측을 구현했습니다.

4. 안전 설계
   혈당 결과는 의료 진단이 아니라 웰니스 참고용입니다.
   특히 90분 예측은 단일 수치가 아니라 범위와 불확실성 중심으로 보여줍니다.

5. 결과물
   FastAPI backend와 React web MVP를 구현해
   음식 업로드부터 혈당 변화 가능성 확인까지 데모로 체험할 수 있습니다.
```

### N.3 10분 발표용 구성

10분 발표에서는 기술 과정과 결과를 더 자세히 보여줄 수 있다.

```text
1분: 문제와 서비스 컨셉
1분: 전체 아키텍처
2분: K-Food 이미지 분류 모델과 92% 달성 과정
1분: nutrition DB와 음식 기반 혈당 부담 점수
2분: OhioT1DM CGM forecasting, calibration, event classifier
1분: 안전성/웰니스 포지셔닝
1분: 웹 MVP 시연
1분: 한계와 향후 계획
```

---

## 부록 O. 심사위원 예상 질문과 답변

### O.1 “혈당 예측이면 의료기기 아닌가요?”

답변 초안:

```text
본 프로젝트는 의료 진단이나 치료 결정을 위한 도구가 아니라
식습관 관리 참고용 웰니스 서비스로 설계했습니다.
앱은 저혈당이나 고혈당을 확정적으로 판단하지 않고,
가능성 신호와 예측 범위, 불확실성을 함께 제공합니다.
또한 모든 혈당 관련 화면에 참고용 문구와 의료진 상담 안내를 포함했습니다.
의료기기 수준으로 확장하려면 별도의 임상 검증, 규제 검토, 품질 관리 체계가 필요하다고 보고 있습니다.
```

### O.2 “92.02% 성능은 실제 서비스에서도 보장되나요?”

답변 초안:

```text
현재 92.02%는 K-Food fixed validation split 6,720장 기준으로 검증한 수치입니다.
최종 ensemble weight도 해당 validation 기준으로 탐색되었기 때문에,
이를 실제 모든 사용자 이미지에서 보장되는 성능으로 말하지는 않습니다.
운영 전에는 별도 holdout set, 사람 검수 clean validation subset,
실제 사용자 이미지 기반 검증이 필요합니다.
다만 현재 결과는 프로젝트 내부 기준에서 목표였던 92%를 달성한 운영 후보 모델이라는 의미가 있습니다.
```

### O.3 “왜 90분 예측을 숫자로 크게 보여주지 않나요?”

답변 초안:

```text
90분 horizon은 30분보다 불확실성이 훨씬 큽니다.
현재 90분 calibrated MAE는 약 29.606이고,
prediction interval 평균 width도 약 136 mg/dL 수준입니다.
따라서 90분 값을 큰 단일 숫자로 보여주면 사용자가 정확한 미래 혈당처럼 오해할 수 있습니다.
그래서 웹 MVP에서는 90분을 범위와 불확실성 중심으로 표시했습니다.
```

### O.4 “음식 사진만으로 혈당을 예측할 수 있나요?”

답변 초안:

```text
음식 사진만으로 개인의 혈당을 정확히 예측하는 것은 어렵습니다.
FoodSugar AI는 음식 사진만 있는 경우에는 음식명, 영양성분, 혈당 부담 참고 점수를 제공합니다.
CGM 데이터가 있는 경우에만 최근 혈당 흐름과 이벤트 feature를 바탕으로 30/60/90분 혈당 변화 가능성을 예측합니다.
즉, 음식 사진 단독 예측과 CGM 기반 예측을 구분하고 있습니다.
```

### O.5 “영양성분은 얼마나 정확한가요?”

답변 초안:

```text
현재 nutrition DB는 K-Food class label 기준의 참고값입니다.
실제 식사량, 조리법, 양념, 반찬 구성에 따라 영양성분은 달라질 수 있습니다.
따라서 앱은 이를 정확한 영양 분석값이 아니라 식습관 관리 참고 정보로 제공합니다.
향후에는 사용자 portion 입력, 음식명 확인, 한국 음식별 실제 섭취량 데이터 보강이 필요합니다.
```

### O.6 “왜 backend 실패 시 mock data를 보여주나요?”

답변 초안:

```text
웹 MVP는 제출과 시연 상황에서도 사용 흐름을 안정적으로 보여주는 것이 중요합니다.
backend가 꺼져 있거나 API 연결이 실패하면 UI가 멈추는 대신 mock fallback을 사용해
음식 분석과 혈당 예측 화면을 계속 보여줍니다.
mock data 사용 시 데모 데이터 배지를 표시해 실제 분석 결과와 구분하도록 했습니다.
```

### O.7 “개인정보는 어떻게 보호하나요?”

답변 초안:

```text
CGM readings, 식사 사진, 인슐린/bolus/basal 정보는 민감한 건강 관련 데이터로 분류했습니다.
이를 위해 데이터 거버넌스 문서, 개인정보/보안 체크리스트, 로그 정책을 작성했고,
raw glucose나 insulin 값이 로그에 직접 남지 않도록 masking helper를 추가했습니다.
실제 파일럿 전에는 저장 암호화, 접근 권한, 삭제 요청 처리, 사용자 ID 분리 저장을 배포 환경에서 확인해야 합니다.
```

---

## 부록 P. 제출용 핵심 수치 모음

```text
K-Food class 수: 56
K-Food validation sample 수: 6,720
최종 음식 분류 top1: 0.9202380952380952
최종 음식 분류 top1 percent: 92.02380952380952%
최종 음식 분류 top3: 0.9794642857142857
최종 음식 분류 macro_f1: 0.9200379850437458
최종 음식 분류 correct: 6184 / 6720
최종 ensemble model 수: 7
TTA 방식: hflip
CGM total rows: 약 166,533
CGM train rows: 약 134,790
CGM test rows: 약 31,743
CGM patients: 12
CGM glucose range: 40-400 mg/dL
CGM feature count: 66
30m calibrated MAE: 12.998
60m calibrated MAE: 22.633
90m calibrated MAE: 29.606
30m interval coverage: 0.919
60m interval coverage: 0.915
90m interval coverage: 0.912
30m mean interval width: 64.487
60m mean interval width: 107.109
90m mean interval width: 136.114
backend/model tests: 72 passed
frontend build: success
frontend local URL: http://127.0.0.1:5173/
```

---

## 부록 Q. 최종 제출 문장 후보

아래 문장은 제출서의 마지막 결론 문단으로 사용할 수 있다.

```text
FoodSugar AI는 음식 이미지 인식 기술을 식습관 관리와 혈당 변화 이해라는 실제 사용자 문제에 연결한 프로젝트이다. 본 프로젝트는 K-Food 56-class 음식 이미지 분류에서 92.02% validation top1을 달성한 7-model ensemble을 구축했고, 이를 영양성분 DB와 연결해 음식 기반 혈당 부담 참고 점수를 제공했다. 또한 OhioT1DM 기반 CGM forecasting 모델을 통해 30분, 60분, 90분 혈당 변화 가능성을 예측하고, prediction interval과 uncertainty, hypo/hyper possibility signal을 함께 제공하도록 설계했다. 혈당 기능은 의료 진단이나 치료 지침이 아니라 웰니스 및 식습관 관리 참고용으로 제한했으며, 안전 문구와 개인정보/로그 정책, 파일럿 설계를 함께 마련했다. 마지막으로 Vite React TypeScript 기반 웹 MVP를 구현해 사용자가 음식 사진 업로드부터 혈당 변화 가능성 확인까지 직접 체험할 수 있게 했다. 향후에는 독립 holdout 평가, 한국 사용자 파일럿, 외부 CGM 데이터 검증, 개인정보 보호 체계 고도화를 통해 실제 서비스 가능성을 더 검증할 계획이다.
```
