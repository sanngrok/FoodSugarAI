# K-Food / Food-LeWM Progress Summary

작성일: 2026-05-09  
프로젝트: `/Users/sangrok/foodsugar-ai`  
목표: K-Food 56-class 음식 분류 모델을 개선하고, 92% top-1 accuracy에 가까워지기 위한 검증/ablation/ensemble/error-analysis 흐름을 정리한다.

---

## 1. 현재 결론

현재까지의 최고 성능은 단일 모델이 아니라 ensemble에서 나왔다.

```text
Best single:
  B0 supervised-only ft10 + hflip
  top1     = 0.879757
  top3     = 0.962212
  macro_f1 = 0.879561

Best overall:
  B0 baseline + Food-LeWM B0 + B0 supervised-only ensemble + hflip
  top1     = 0.899232
  top3     = 0.976059
  macro_f1 = 0.899126
```

92%까지 남은 gap:

```text
0.920000 - 0.899232 = 0.020768
약 2.08%p
```

가장 중요한 해석:

```text
1. 기존 B0 0.8275와 Food-LeWM 0.8695를 직접 비교하면 안 된다.
2. 기존 B0 0.8275는 data/raw/korean_food/val 기준이다.
3. Food-LeWM 0.8695는 data/raw/korean_food_1000/val 기준이다.
4. 같은 korean_food_1000/val에서 기존 B0는 hflip 기준 0.8735로 매우 강하다.
5. 현재 3epoch LeWM pretraining은 supervised-only 대비 이득을 주지 못했다.
6. 지금까지의 실질적 개선은 1000/class split, fine-tuning recipe, wrapper head, TTA, ensemble에서 나왔다.
```

---

## 2. 안전 규칙

아래 운영 파일은 아직 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

운영 승격은 아직 하지 않았다.  
현재 결과는 후보 모델/리포트 상태다.

---

## 3. 데이터 상태

### 3.1 기존 K-Food 600 split

```text
path: data/raw/korean_food
classes: 56
train: 26,880
val: 6,720
class당 총 600장 제한
```

### 3.2 K-Food 1000 split

```text
path: data/raw/korean_food_1000
classes: 56
train: 44,769
val: 11,194
```

정확히 56,000장이 아닌 이유:

```text
일부 class의 원본 이미지가 1000장보다 적어서 총 55,963장이다.
```

### 3.3 Smoke split

```text
path: data/raw/korean_food_smoke
classes: 56
train: 1,344
val: 336
```

---

## 4. 주요 모델 파일

### 4.1 기존 운영/B0 계열

```text
data/models/efficientnet_korean.pt
data/models/efficientnet_korean_b0_val08275.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
```

기존 기록:

```text
model: efficientnet_b0
image_size: 224
classes: 56
old val_acc on data/raw/korean_food/val: 0.8275
```

### 4.2 Food-LeWM B0 후보

```text
pretrain checkpoint:
  data/models/food_lewm_b0_pretrain_3ep.pt

classifier:
  data/models/food_lewm_b0_classifier_3ep_ft10.pt
  data/models/food_lewm_b0_classes_3ep_ft10.json
  data/models/food_lewm_b0_meta_3ep_ft10.json
```

Food-LeWM B0 결과:

```text
data: data/raw/korean_food_1000
pretrain: 3 epochs on original K-Food root, 150,513 images
fine-tune: 10 epochs
hflip top1: 0.869484
hflip macro_f1: 0.869524
```

### 4.3 B0 supervised-only 후보

```text
data/models/food_lewm_b0_supervised_only_ft10.pt
data/models/food_lewm_b0_supervised_only_classes_ft10.json
data/models/food_lewm_b0_supervised_only_meta_ft10.json
```

결과:

```text
data: data/raw/korean_food_1000
pretrain: ImageNet only, no LeWM checkpoint
fine-tune: 10 epochs
hflip top1: 0.879757
hflip macro_f1: 0.879561
```

현재 best single model이다.

### 4.4 B2 기존 후보

```text
data/models/efficientnet_korean_b2_val07549.pt
data/models/efficientnet_korean_b2_opt.pt
data/models/korean_food_model_meta_b2_opt.json
data/models/korean_food_classes_b2_opt.json
```

기존 기록:

```text
B2 first experiment best: 0.7549
B2 opt experiment best: 0.8082
B2 opt metadata image_size: 224
```

B2 clean 1000 / B2-LeWM은 아직 진행하지 않았다.

---

## 5. 추가/수정된 코드

### 5.1 Food-LeWM 모델 구성

```text
src/classifier/lewm_sigreg.py
src/classifier/food_lewm_model.py
```

역할:

```text
FoodLeWMEncoder
FoodLeWMClassifier
SIGReg-style anti-collapse regularizer
checkpoint load helper
```

### 5.2 학습 스크립트

```text
scripts/pretrain_food_lewm.py
scripts/train_food_lewm_classifier.py
```

`train_food_lewm_classifier.py`는 이제 두 모드를 모두 지원한다.

```text
1. --lewm-checkpoint 있음:
   LeWM pretrained encoder를 로드해서 fine-tuning

2. --lewm-checkpoint 없음:
   ImageNet pretrained encoder로 supervised-only fine-tuning
```

### 5.3 평가 스크립트

```text
scripts/eval_kfood_any_model.py
scripts/eval_kfood_ensemble.py
scripts/eval_food_lewm.py
```

역할:

```text
eval_kfood_any_model.py:
  plain timm checkpoint와 Food-LeWM checkpoint를 모두 평가
  top1/top3/macro_f1/per-class/confusion/high-confidence errors 저장

eval_kfood_ensemble.py:
  여러 checkpoint logits 평균 ensemble
  model별 image_size transform 지원
  hflip TTA 지원
  per-class/confusion/high-confidence errors 저장
```

### 5.4 오류 분석 스크립트

```text
scripts/analyze_kfood_errors.py
```

출력:

```text
low_f1_classes.csv
low_recall_classes.csv
low_precision_classes.csv
top_confusion_pairs.csv
high_confidence_errors_top300.csv
samples_to_review.csv
suggested_data_actions.md
README.md
```

### 5.5 추론 로더 호환

파일:

```text
src/classifier/food_classifier.py
```

변경 내용:

```text
FoodClassifier(model_path=...) 로 Food-LeWM classifier checkpoint 직접 로드 가능
기존 timm classifier checkpoint 로드 유지
model_type 자동 판별
companion classes/meta 파일 자동 탐색
```

검증:

```text
FoodClassifier(model_path="data/models/food_lewm_b0_classifier_3ep_ft10.pt")
model_type=food_lewm_classifier
model_name=efficientnet_b0
image_size=224
classes=56
predict(top_k=5) 정상 동작
```

---

## 6. 실험 타임라인

### 6.1 Food-LeWM B0 pretraining

실행:

```text
model: efficientnet_b0
image_size: 224
latent_dim: 192
pretrain data: original K-Food root
images: 150,513
epochs: 3
checkpoint: data/models/food_lewm_b0_pretrain_3ep.pt
```

pretraining loss:

```text
epoch 1: loss=0.0754169677
epoch 2: loss=0.0366920503
epoch 3: loss=0.0296942468
```

### 6.2 Food-LeWM B0 10epoch fine-tuning

```text
checkpoint: data/models/food_lewm_b0_classifier_3ep_ft10.pt
best epoch: 9
non-TTA top1: 0.867965
hflip top1: 0.869484
hflip macro_f1: 0.869524
```

### 6.3 Same-validation B0 재평가

`data/raw/korean_food_1000/val` 기준으로 기존 B0를 재평가했다.

```text
B0 baseline none:
  top1     = 0.867876
  top3     = 0.962301
  macro_f1 = 0.867653

B0 baseline hflip:
  top1     = 0.873504
  top3     = 0.964713
  macro_f1 = 0.873296
```

결론:

```text
기존 B0는 korean_food_1000/val에서 0.8735까지 나온다.
따라서 old 0.8275와 Food-LeWM 0.8695를 직접 비교하면 안 된다.
```

### 6.4 B0 supervised-only ablation

LeWM checkpoint 없이 같은 wrapper/recipe로 학습했다.

```text
checkpoint: data/models/food_lewm_b0_supervised_only_ft10.pt
data: data/raw/korean_food_1000
epochs: 10
hflip top1: 0.879757
hflip top3: 0.962212
hflip macro_f1: 0.879561
```

결론:

```text
Food-LeWM 3ep pretraining은 supervised-only보다 낮았다.
LeWM effect vs supervised-only = -1.0273%p top1
```

### 6.5 Ensemble

조합:

```text
B0 baseline
+ Food-LeWM B0 3ep ft10
+ B0 supervised-only ft10
+ hflip TTA
```

결과:

```text
top1     = 0.899232
top3     = 0.976059
macro_f1 = 0.899126
```

개선폭:

```text
vs same-validation B0 hflip:
  0.899232 - 0.873504 = +0.025728
  약 +2.57%p

vs best single supervised-only:
  0.899232 - 0.879757 = +0.019475
  약 +1.95%p
```

현재 best overall이다.

---

## 7. 성능 표

| Experiment | Model | Pretrain | Data | TTA | Ensemble | Top1 | Top3 | Macro-F1 |
|---|---|---|---|---|---|---:|---:|---:|
| B0 baseline on 1000val | efficientnet_b0 | none | old 600 train / 1000 val | hflip | no | 0.873504 | 0.964713 | 0.873296 |
| B0 supervised-only | B0 Food-LeWM arch | ImageNet | korean_food_1000 | hflip | no | 0.879757 | 0.962212 | 0.879561 |
| B0-LeWM 3ep ft10 | B0 Food-LeWM | LeWM 3ep | korean_food_1000 | hflip | no | 0.869484 | 0.961408 | 0.869524 |
| Best ensemble | B0/B0-LeWM/Supervised | mixed | korean_food_1000 | hflip | yes | 0.899232 | 0.976059 | 0.899126 |
| B2 clean | efficientnet_b2 | none | korean_food_1000 | hflip | no | TBD | TBD | TBD |
| B2-LeWM | B2 Food-LeWM | LeWM 3ep | korean_food_1000 | hflip | no | TBD | TBD | TBD |

---

## 8. Error Analysis

대상:

```text
reports/ensemble/b0_baseline_plus_food_lewm_b0_plus_supervised_only_hflip
```

출력:

```text
reports/error_analysis/final_candidate/
```

생성 파일:

```text
README.md
low_f1_classes.csv
low_recall_classes.csv
low_precision_classes.csv
top_confusion_pairs.csv
high_confidence_errors_top300.csv
samples_to_review.csv
suggested_data_actions.md
```

high-confidence 검수 후보:

```text
300 images
```

최종 ensemble 하위 F1 class:

| class | F1 | Precision | Recall | Support |
|---|---:|---:|---:|---:|
| 동태찌개 | 0.798165 | 0.737288 | 0.870000 | 200 |
| 갈비찜 | 0.816626 | 0.799043 | 0.835000 | 200 |
| 김치찌개 | 0.817955 | 0.815920 | 0.820000 | 200 |
| 갈비구이 | 0.824691 | 0.814634 | 0.835000 | 200 |
| 삼겹살 | 0.827586 | 0.876404 | 0.783920 | 199 |
| 라면 | 0.834646 | 0.873626 | 0.798995 | 199 |
| 닭볶음탕 | 0.835897 | 0.857895 | 0.815000 | 200 |
| 곰탕_설렁탕 | 0.839895 | 0.883978 | 0.800000 | 200 |
| 닭갈비 | 0.842365 | 0.830097 | 0.855000 | 200 |
| 불고기 | 0.843434 | 0.852041 | 0.835000 | 200 |
| 칼국수 | 0.846348 | 0.852792 | 0.840000 | 200 |
| 김치찜 | 0.851385 | 0.857868 | 0.845000 | 200 |
| 수제비 | 0.860825 | 0.883598 | 0.839196 | 199 |
| 닭계장 | 0.861538 | 0.884211 | 0.840000 | 200 |
| 감자탕 | 0.865672 | 0.861386 | 0.870000 | 200 |

주요 confusion pair:

```text
곰탕_설렁탕 -> 갈비탕
김치찌개 -> 동태찌개
호박전 -> 감자전
감자전 -> 호박전
갈비구이 -> 갈비찜
곰탕_설렁탕 -> 삼계탕
비빔냉면 -> 물냉면
삼겹살 -> 갈비구이
칼국수 -> 수제비
김치찜 -> 김치찌개
수제비 -> 칼국수
잔치국수 -> 칼국수
```

해석:

```text
오류 병목은 주로 국/찌개/탕 계열, 전 계열, 유사 면/고기 class에서 발생한다.
92%까지 남은 약 2.08%p는 모델만이 아니라 라벨/데이터/class confusion 정리가 중요해 보인다.
```

---

## 9. 검증 상태

테스트:

```text
python3 -m pytest tests/ -q
18 passed
```

문법 확인:

```text
py_compile 통과:
- scripts/eval_kfood_any_model.py
- scripts/eval_kfood_ensemble.py
- scripts/analyze_kfood_errors.py
- scripts/train_food_lewm_classifier.py
- src/classifier/food_classifier.py
```

---

## 10. 생성된 주요 리포트

```text
reports/production_validation/README.md
reports/ablation/b0_lewm_ablation_summary.md
reports/ensemble/b0_baseline_plus_food_lewm_b0_plus_supervised_only_hflip/
reports/error_analysis/final_candidate/
reports/food_lewm_92_next_steps_summary.md
```

이번 종합 문서:

```text
KFOOD_LEWM_PROGRESS_SUMMARY.md
```

---

## 11. 다음 선택지

### Option A. 데이터/라벨 검수 우선

가장 추천하는 다음 액션:

```text
reports/error_analysis/final_candidate/high_confidence_errors_top300.csv
reports/error_analysis/final_candidate/samples_to_review.csv
```

위 300개를 우선 검수한다.

검수 기준:

```text
1. 라벨이 틀렸는가?
2. 이미지에 여러 음식이 섞였는가?
3. 음식이 너무 작거나 가려졌는가?
4. class 정의가 겹치는가?
5. 국/찌개/탕처럼 시각적으로 구분이 어려운가?
```

### Option B. B2 clean 추가

목적:

```text
B2가 B0 계열과 다른 오답 패턴을 만들면 ensemble 성능을 더 올릴 수 있다.
```

후보 파일:

```text
data/models/efficientnet_korean_b2_clean_1000.pt
data/models/korean_food_classes_b2_clean_1000.json
data/models/korean_food_model_meta_b2_clean_1000.json
```

주의:

```text
B2는 이전에 단독 성능이 B0보다 낮았다.
단일 성능보다 ensemble 다양성 관점에서 보는 것이 좋다.
```

### Option C. B2-LeWM 추가

목적:

```text
B2 + LeWM이 B0 계열과 다른 representation을 만들 수 있는지 확인한다.
```

비용:

```text
B2 pretraining/fine-tuning은 시간이 더 오래 걸릴 수 있다.
```

### Option D. 운영 승격 준비

현재 운영 승격은 아직 하지 않았다.

가능한 운영 방식:

```text
1. Best single supervised-only 모델을 운영 후보로 지정
2. Best ensemble을 별도 inference wrapper로 운영 후보화
3. 기존 B0 운영 모델은 유지하고 shadow/evaluation mode로 새 모델을 비교
```

추천:

```text
바로 운영 파일 덮어쓰기보다, ensemble inference wrapper를 만든 뒤 shadow 테스트하는 것이 안전하다.
```

---

## 12. 최종 한 줄 결론

현재 best는 `B0 baseline + Food-LeWM B0 + B0 supervised-only` hflip ensemble이며, same-validation 기준 top1 `0.899232`, macro_f1 `0.899126`이다. 기존 B0 same-validation hflip `0.873504` 대비 `+2.57%p` 개선했고, 92%까지는 약 `2.08%p` 남았다. 현재 병목은 3epoch LeWM pretraining이 아니라 데이터/라벨/class confusion 정리와 모델 다양성 확보다.

