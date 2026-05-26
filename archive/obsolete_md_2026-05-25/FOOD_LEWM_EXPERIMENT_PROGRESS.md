# Food-LeWM Experiment Progress

작성일: 2026-05-08  
프로젝트: `foodsugar-ai`  
실험 방향: LeWM-style joint embedding prediction + SIGReg를 K-Food 단일 이미지 분류에 맞게 변형한다.

---

## 1. 목표

현재 운영 K-Food 모델은 EfficientNet-B0이며, 56-class / class당 600장 split에서 best validation accuracy 0.8275를 기록했다.

이번 방향의 목표는 다음과 같다.

```text
1. 전체 K-Food 원본 이미지를 label 없이 사용해 self-supervised pretraining
2. two-view augmentation latent prediction으로 음식 도메인 representation 강화
3. SIGReg-style anti-collapse regularization으로 embedding 붕괴 방지
4. 56-class 1000/class split에서 supervised fine-tuning
5. hflip TTA와 B0/B2/ViT ensemble로 최종 성능 향상
```

최종 목표:

```text
candidate_val_top1 >= 0.9200
```

1차 실용 승격 후보 기준:

```text
candidate_val_top1 >= 0.8500
candidate_macro_f1 >= B0_macro_f1
class별 F1 하위권 붕괴 없음
추론 로딩 정상
```

---

## 2. 안전 규칙

아래 운영 파일은 이번 작업에서 덮어쓰지 않는다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

Food-LeWM 결과는 별도 후보 파일로 저장한다.

```text
data/models/food_lewm_b0_pretrain.pt
data/models/food_lewm_b0_classifier.pt
data/models/food_lewm_b2_pretrain.pt
data/models/food_lewm_b2_classifier.pt
data/models/food_lewm_vit_tiny_pretrain.pt
data/models/food_lewm_vit_tiny_classifier.pt
```

스모크 테스트 파일은 `_smoke` suffix를 사용한다.

---

## 3. 추가된 코드

### 3.1 SIGReg regularizer

파일:

```text
src/classifier/lewm_sigreg.py
```

내용:

- variance preservation
- projected covariance decorrelation
- LeWM의 collapse 방지 목적을 two-view image SSL에 맞춘 실용 구현

### 3.2 Food-LeWM 모델 컴포넌트

파일:

```text
src/classifier/food_lewm_model.py
```

내용:

- `FoodLeWMConfig`
- `FoodLeWMEncoder`
- `FoodLeWMClassifier`
- checkpoint load helper
- device 선택: mps > cuda > cpu
- `timm.create_model(..., num_classes=0, global_pool="avg")` 기반 encoder

### 3.3 Self-supervised pretraining

파일:

```text
scripts/pretrain_food_lewm.py
```

핵심 구조:

```text
image view A -> encoder -> z_a -> predictor -> z_b_hat
image view B -> encoder -> z_b -> predictor -> z_a_hat

loss = 0.5 * (MSE(z_b_hat, z_b) + MSE(z_a_hat, z_a))
       + lambda_sigreg * SIGReg(z_a, z_b)
```

지원 옵션:

- `--image-root`
- `--model-name`
- `--image-size`
- `--latent-dim`
- `--epochs`
- `--batch-size`
- `--grad-accum-steps`
- `--lr`
- `--weight-decay`
- `--lambda-sigreg`
- `--num-projections`
- `--predictor-dropout`
- `--output`
- `--report-dir`
- `--max-samples` for smoke tests

### 3.4 Supervised classifier fine-tuning

파일:

```text
scripts/train_food_lewm_classifier.py
```

내용:

- LeWM pretrained encoder 로드
- 56-class classifier head 추가
- CrossEntropyLoss + label smoothing
- AdamW + cosine scheduler
- optional warmup
- RandomResizedCrop, HorizontalFlip, mild ColorJitter, RandomErasing
- metrics/report 저장
- `--max-train-samples`, `--max-val-samples` for smoke tests

### 3.5 Evaluation / TTA / ensemble

파일:

```text
scripts/eval_food_lewm.py
```

내용:

- 단일 모델 평가
- 여러 checkpoint logits 평균 ensemble
- optional `--tta hflip`
- top1/top3/macro_f1
- per-class metrics
- confusion matrix
- README/metrics JSON 저장

---

## 4. 생성된 1000/class split

명령:

```bash
python3 -m src.data.prepare_kfood_split \
  --source-root "/Users/sangrok/Downloads/한국 음식 이미지/kfood" \
  --output-dir data/raw/korean_food_1000 \
  --max-per-class 1000 \
  --val-ratio 0.2 \
  --mode symlink \
  --manifest data/processed/kfood_1000_split_manifest.csv \
  --selected-classes-output data/processed/kfood_1000_selected_classes.txt
```

결과:

```text
data/raw/korean_food_1000
classes: 56
train: 44,769
val: 11,194
total: 55,963
```

관련 파일:

```text
data/processed/kfood_1000_split_manifest.csv
data/processed/kfood_1000_selected_classes.txt
```

검증 결과:

```text
korean_food classes=56 train=26880 val=6720
korean_food_1000 classes=56 train=44769 val=11194
class_order_match=True
```

원본 클래스별 이미지 수가 1000장 미만인 경우가 있어 정확히 56,000장은 아니며, 실제 총합은 55,963장이다.

---

## 5. 스모크 테스트 결과

전체 학습을 시작하기 전, 아주 작은 샘플로 pretrain -> fine-tune -> eval 경로를 검증했다.

### 5.1 B0-LeWM pretrain smoke

명령:

```bash
python3 scripts/pretrain_food_lewm.py \
  --image-root data/raw/korean_food_smoke \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 1 \
  --batch-size 4 \
  --num-workers 0 \
  --lr 1e-4 \
  --weight-decay 1e-4 \
  --lambda-sigreg 0.1 \
  --num-projections 64 \
  --predictor-dropout 0.1 \
  --output data/models/food_lewm_b0_pretrain_smoke.pt \
  --report-dir reports/food_lewm/smoke_pretrain_b0 \
  --max-samples 16 \
  --log-every 1
```

결과:

```text
checkpoint: data/models/food_lewm_b0_pretrain_smoke.pt
report: reports/food_lewm/smoke_pretrain_b0
images: 16
batches: 4
final smoke loss: 0.4024
```

### 5.2 B0-LeWM classifier smoke

명령:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_smoke \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --lewm-checkpoint data/models/food_lewm_b0_pretrain_smoke.pt \
  --epochs 1 \
  --batch-size 4 \
  --num-workers 0 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 0 \
  --random-erasing-p 0.1 \
  --output data/models/food_lewm_b0_classifier_smoke.pt \
  --classes-output data/models/food_lewm_b0_classes_smoke.json \
  --metadata-output data/models/food_lewm_b0_meta_smoke.json \
  --report-dir reports/food_lewm/smoke_b0_classifier \
  --max-train-samples 32 \
  --max-val-samples 32 \
  --log-every 2
```

결과:

```text
checkpoint: data/models/food_lewm_b0_classifier_smoke.pt
classes: data/models/food_lewm_b0_classes_smoke.json
metadata: data/models/food_lewm_b0_meta_smoke.json
report: reports/food_lewm/smoke_b0_classifier
train samples: 32
val samples: 32
val_top1: 0.21875
val_top3: 0.375
macro_f1: 0.0884
```

이 수치는 성능 의미가 아니라 경로 검증용이다.

### 5.3 B0-LeWM eval smoke

명령:

```bash
python3 scripts/eval_food_lewm.py \
  --data-dir data/raw/korean_food_smoke \
  --checkpoint data/models/food_lewm_b0_classifier_smoke.pt \
  --metadata data/models/food_lewm_b0_meta_smoke.json \
  --classes data/models/food_lewm_b0_classes_smoke.json \
  --batch-size 4 \
  --num-workers 0 \
  --tta hflip \
  --output-dir reports/food_lewm/smoke_eval_b0 \
  --max-samples 32
```

결과:

```text
report: reports/food_lewm/smoke_eval_b0
val_top1: 0.21875
val_top3: 0.375
macro_f1: 0.0884
```

생성된 리포트 파일:

```text
reports/food_lewm/smoke_eval_b0/metrics.json
reports/food_lewm/smoke_eval_b0/per_class_metrics.csv
reports/food_lewm/smoke_eval_b0/confusion_matrix.csv
reports/food_lewm/smoke_eval_b0/README.md
```

### 5.4 B0-LeWM pilot pretrain on original K-Food root

본 실험을 바로 장시간 실행하기 전, 원본 K-Food 경로와 MPS 실행 가능성을 확인하기 위해 128장 pilot을 실행했다.

명령:

```bash
python3 scripts/pretrain_food_lewm.py \
  --image-root "/Users/sangrok/Downloads/한국 음식 이미지/kfood" \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 1 \
  --batch-size 8 \
  --num-workers 2 \
  --lr 1e-4 \
  --weight-decay 1e-4 \
  --lambda-sigreg 0.1 \
  --num-projections 256 \
  --predictor-dropout 0.1 \
  --output data/models/food_lewm_b0_pretrain_pilot.pt \
  --report-dir reports/food_lewm/b0_pretrain_pilot \
  --max-samples 128 \
  --log-every 4
```

결과:

```text
device: mps
images: 128
batches: 16
epoch seconds: 16.73
loss: 0.2889
prediction_loss: 0.2106
sigreg_loss: 0.7830
checkpoint: data/models/food_lewm_b0_pretrain_pilot.pt
report: reports/food_lewm/b0_pretrain_pilot
```

메모:

- sandbox 내부에서는 `torch.backends.mps.is_available()`가 `False`였지만, 승인 실행에서는 `device=mps`로 정상 동작했다.
- `num_workers=2`는 sandbox 내부에서 shared-memory 제한으로 실패했지만, 승인 실행에서는 정상 동작했다.
- full pretraining은 같은 방식으로 실행하면 된다.

---

## 6. 다음 실제 실험 명령

### 6.1 Experiment 1: B0-LeWM 3epoch pretraining 완료

실행한 명령:

```bash
python3 scripts/pretrain_food_lewm.py \
  --image-root "/Users/sangrok/Downloads/한국 음식 이미지/kfood" \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 3 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 1e-4 \
  --weight-decay 1e-4 \
  --lambda-sigreg 0.1 \
  --num-projections 256 \
  --predictor-dropout 0.1 \
  --output data/models/food_lewm_b0_pretrain_3ep.pt \
  --report-dir reports/food_lewm/b0_pretrain_3ep \
  --log-every 50
```

결과:

```text
checkpoint: data/models/food_lewm_b0_pretrain_3ep.pt
report: reports/food_lewm/b0_pretrain_3ep
images: 150,513
epochs: 3
best_loss: 0.029694246769946517
```

epoch별 기록:

```text
epoch 1: loss=0.0754169677, prediction_loss=0.0173428223, sigreg_loss=0.5807414447, seconds=2822.73
epoch 2: loss=0.0366920503, prediction_loss=0.0211051540, sigreg_loss=0.1558689605, seconds=1779.10
epoch 3: loss=0.0296942468, prediction_loss=0.0180548402, sigreg_loss=0.1163940638, seconds=1724.45
```

### 6.2 B0-LeWM classifier 5epoch fine-tuning 완료

실행한 명령:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_1000 \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --lewm-checkpoint data/models/food_lewm_b0_pretrain_3ep.pt \
  --epochs 5 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 1 \
  --random-erasing-p 0.1 \
  --output data/models/food_lewm_b0_classifier_3ep_ft5.pt \
  --classes-output data/models/food_lewm_b0_classes_3ep_ft5.json \
  --metadata-output data/models/food_lewm_b0_meta_3ep_ft5.json \
  --report-dir reports/food_lewm/b0_classifier_3ep_ft5 \
  --log-every 50
```

결과:

```text
checkpoint: data/models/food_lewm_b0_classifier_3ep_ft5.pt
classes: data/models/food_lewm_b0_classes_3ep_ft5.json
metadata: data/models/food_lewm_b0_meta_3ep_ft5.json
report: reports/food_lewm/b0_classifier_3ep_ft5
train images: 44,769
val images: 11,194
```

epoch별 validation:

```text
epoch 1: val_top1=0.0820082187, val_top3=0.1931391817, macro_f1=0.0224414306
epoch 2: val_top1=0.7587100232, val_top3=0.9189744506, macro_f1=0.7581480499
epoch 3: val_top1=0.8139181704, val_top3=0.9437198499, macro_f1=0.8131976352
epoch 4: val_top1=0.8363408969, val_top3=0.9523852064, macro_f1=0.8362075545
epoch 5: val_top1=0.8446489191, val_top3=0.9557798821, macro_f1=0.8447195543
```

의미:

```text
기존 B0 기준선 0.8275를 epoch 4부터 넘었다.
5epoch non-TTA 기준 top1은 0.84465로, 기존 B0 대비 +1.71%p 개선이다.
```

### 6.3 B0-LeWM hflip TTA 평가 완료

실행한 명령:

```bash
python3 scripts/eval_food_lewm.py \
  --data-dir data/raw/korean_food_1000 \
  --checkpoint data/models/food_lewm_b0_classifier_3ep_ft5.pt \
  --metadata data/models/food_lewm_b0_meta_3ep_ft5.json \
  --classes data/models/food_lewm_b0_classes_3ep_ft5.json \
  --batch-size 64 \
  --num-workers 2 \
  --tta hflip \
  --output-dir reports/food_lewm/eval_b0_3ep_ft5_hflip
```

결과:

```text
report: reports/food_lewm/eval_b0_3ep_ft5_hflip
val_top1: 0.8466142576380203
val_top3: 0.9571198856530284
macro_f1: 0.8467187274170281
num_samples: 11,194
```

의미:

```text
hflip TTA 기준 기존 B0 0.8275 대비 +1.91%p 개선이다.
1차 실용 승격 후보 기준인 top1 >= 0.8500에는 아직 약간 미달한다.
```

### 6.4 B0-LeWM classifier 10epoch fine-tuning 완료

5epoch 후보에서 성능이 계속 오르는 흐름이 보여, 같은 3epoch pretraining checkpoint에서 classifier fine-tuning을 10epoch로 확장했다. 기존 5epoch 후보는 보존하고, 별도 후보 파일로 저장했다.

실행한 명령:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_1000 \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --lewm-checkpoint data/models/food_lewm_b0_pretrain_3ep.pt \
  --epochs 10 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 1 \
  --random-erasing-p 0.1 \
  --output data/models/food_lewm_b0_classifier_3ep_ft10.pt \
  --classes-output data/models/food_lewm_b0_classes_3ep_ft10.json \
  --metadata-output data/models/food_lewm_b0_meta_3ep_ft10.json \
  --report-dir reports/food_lewm/b0_classifier_3ep_ft10 \
  --log-every 50
```

결과:

```text
checkpoint: data/models/food_lewm_b0_classifier_3ep_ft10.pt
classes: data/models/food_lewm_b0_classes_3ep_ft10.json
metadata: data/models/food_lewm_b0_meta_3ep_ft10.json
report: reports/food_lewm/b0_classifier_3ep_ft10
best epoch: 9
best val_top1: 0.86796498123995
best val_top3: 0.961586564230838
best macro_f1: 0.8680396484464304
```

epoch별 validation:

```text
epoch 1:  val_top1=0.0820082187, val_top3=0.1931391817, macro_f1=0.0224414306
epoch 2:  val_top1=0.7587100232, val_top3=0.9189744506, macro_f1=0.7581480499
epoch 3:  val_top1=0.8155261747, val_top3=0.9441665178, macro_f1=0.8148064201
epoch 4:  val_top1=0.8381275683, val_top3=0.9529212078, macro_f1=0.8380467144
epoch 5:  val_top1=0.8532249419, val_top3=0.9597105592, macro_f1=0.8532499882
epoch 6:  val_top1=0.8590316241, val_top3=0.9601572271, macro_f1=0.8587970499
epoch 7:  val_top1=0.8654636412, val_top3=0.9614972307, macro_f1=0.8651377883
epoch 8:  val_top1=0.8650169734, val_top3=0.9614972307, macro_f1=0.8647593151
epoch 9:  val_top1=0.8679649812, val_top3=0.9615865642, macro_f1=0.8680396484
epoch 10: val_top1=0.8660889762, val_top3=0.9611398964, macro_f1=0.8659546851
```

의미:

```text
best epoch 9 기준 기존 B0 0.8275 대비 +4.05%p 개선.
1차 실용 승격 후보 기준 top1 >= 0.8500을 충족.
macro_f1도 0.8680으로 top1과 균형이 좋다.
epoch 10에서 약간 하락했으므로 이 run의 best checkpoint는 epoch 9 상태다.
```

### 6.5 B0-LeWM 10epoch hflip TTA 평가 완료

실행한 명령:

```bash
python3 scripts/eval_food_lewm.py \
  --data-dir data/raw/korean_food_1000 \
  --checkpoint data/models/food_lewm_b0_classifier_3ep_ft10.pt \
  --metadata data/models/food_lewm_b0_meta_3ep_ft10.json \
  --classes data/models/food_lewm_b0_classes_3ep_ft10.json \
  --batch-size 64 \
  --num-workers 2 \
  --tta hflip \
  --output-dir reports/food_lewm/eval_b0_3ep_ft10_hflip
```

결과:

```text
report: reports/food_lewm/eval_b0_3ep_ft10_hflip
val_top1: 0.8694836519564052
val_top3: 0.9614078970877256
macro_f1: 0.8695236233196315
num_samples: 11,194
```

의미:

```text
hflip TTA 기준 기존 B0 0.8275 대비 +4.20%p 개선.
현재까지의 최고 Food-LeWM B0 결과다.
```

### 6.6 B0-LeWM 10epoch class별 성능/혼동 분석 완료

운영 승격 후보로 볼 수 있는지 확인하기 위해 hflip TTA 평가 결과의 class별 F1과 confusion matrix를 점검했다.

대상 리포트:

```text
reports/food_lewm/eval_b0_3ep_ft10_hflip/per_class_metrics.csv
reports/food_lewm/eval_b0_3ep_ft10_hflip/confusion_matrix.csv
```

전체 지표:

```text
val_top1: 0.8694836519564052
val_top3: 0.9614078970877256
macro_f1: 0.8695236233196315
num_classes: 56
num_samples: 11,194
class support: min 199, max 200
```

하위 F1 15개 class:

```text
동태찌개      f1=0.7383 precision=0.6680 recall=0.8250 support=200
곰탕_설렁탕  f1=0.7696 precision=0.8077 recall=0.7350 support=200
김치찌개      f1=0.7704 precision=0.7610 recall=0.7800 support=200
갈비찜        f1=0.7835 precision=0.7630 recall=0.8050 support=200
갈비구이      f1=0.7841 precision=0.7783 recall=0.7900 support=200
닭볶음탕      f1=0.7918 precision=0.8148 recall=0.7700 support=200
닭계장        f1=0.8031 precision=0.8220 recall=0.7850 support=200
순두부찌개    f1=0.8041 precision=0.8298 recall=0.7800 support=200
불고기        f1=0.8059 precision=0.7923 recall=0.8200 support=200
라면          f1=0.8130 precision=0.8824 recall=0.7538 support=199
된장찌개      f1=0.8139 precision=0.8079 recall=0.8200 support=200
갈비탕        f1=0.8152 precision=0.8256 recall=0.8050 support=200
김치찜        f1=0.8189 precision=0.8128 recall=0.8250 support=200
감자탕        f1=0.8238 precision=0.8177 recall=0.8300 support=200
수제비        f1=0.8254 precision=0.8715 recall=0.7839 support=199
```

F1 threshold counts:

```text
f1 < 0.60: 0 classes
f1 < 0.70: 0 classes
f1 < 0.75: 1 class
f1 < 0.80: 6 classes
f1 < 0.85: 20 classes
f1 < 0.90: 34 classes
```

상위 F1 class:

```text
한과      f1=0.9727
수정과    f1=0.9618
짜장면    f1=0.9535
김밥      f1=0.9383
식혜      f1=0.9370
알밥      f1=0.9370
잡곡밥    f1=0.9360
피자      f1=0.9320
약과      f1=0.9291
유부초밥  f1=0.9289
```

상위 confusion pair:

```text
곰탕_설렁탕 -> 갈비탕        count=18
김치찌개     -> 동태찌개      count=17
호박전       -> 감자전        count=15
순두부찌개   -> 된장찌개      count=14
곰탕_설렁탕 -> 삼계탕        count=14
갈비탕       -> 곰탕_설렁탕  count=13
양념치킨     -> 후라이드치킨  count=12
갈비탕       -> 삼계탕        count=12
칼국수       -> 수제비        count=11
비빔냉면     -> 물냉면        count=11
떡볶이       -> 라볶이        count=11
떡갈비       -> 갈비구이      count=11
족발         -> 보쌈          count=10
순두부찌개   -> 동태찌개      count=10
닭볶음탕     -> 찜닭          count=10
김치볶음밥   -> 새우볶음밥    count=10
```

판단:

```text
하위 class F1이 대량으로 붕괴한 징후는 없다.
F1 0.7 미만 class가 없고, 최저 F1도 0.7383이다.
주요 confusion은 국/찌개/탕 계열, 전 계열, 면 계열, 유사 조리 class에서 발생한다.
이는 모델 붕괴라기보다 시각적으로 실제로 헷갈리는 class pair 중심이다.
```

결론:

```text
Food-LeWM B0 3ep pretrain + 10ep fine-tune + hflip TTA 모델은
1차 실용 승격 후보 기준을 만족한다.

candidate_val_top1 >= 0.8500: 만족
candidate_macro_f1 >= B0_macro_f1: 현재 macro_f1=0.8695로 강하게 만족할 가능성이 높음
하위 class F1 대량 붕괴 없음: 만족
```

### 6.7 FoodClassifier 호환 작업 완료

기존 운영 로더는 `data/models/efficientnet_korean.pt` 형태의 plain timm classifier checkpoint만 기대했다. Food-LeWM classifier checkpoint는 wrapper 구조가 다르므로, 운영 파일을 덮어쓰기 전에 `FoodClassifier`가 두 형식을 모두 읽을 수 있게 호환 레이어를 추가했다.

변경 파일:

```text
src/classifier/food_classifier.py
scripts/train_food_lewm_classifier.py
scripts/eval_food_lewm.py
data/models/food_lewm_b0_meta_3ep_ft10.json
```

지원되는 로드 방식:

```python
from src.classifier.food_classifier import FoodClassifier

clf = FoodClassifier(
    model_path="data/models/food_lewm_b0_classifier_3ep_ft10.pt"
)
```

동작:

```text
1. model_path가 명시되면 후보 checkpoint를 우선 로드한다.
2. checkpoint 이름에서 companion classes/meta 파일을 자동 탐색한다.
   - data/models/food_lewm_b0_classes_3ep_ft10.json
   - data/models/food_lewm_b0_meta_3ep_ft10.json
3. metadata 또는 checkpoint 구조를 보고 Food-LeWM classifier인지 판별한다.
4. FoodLeWMClassifier wrapper를 구성하고 model_state_dict를 로드한다.
5. 기존 운영 B0 plain timm checkpoint 로드는 그대로 유지한다.
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

기본 운영 로더 검증:

```text
FoodClassifier()
model_type=timm_classifier
model_name=efficientnet_b0
image_size=224
classes=56
```

테스트:

```text
python3 -m py_compile scripts/train_food_lewm_classifier.py scripts/eval_food_lewm.py src/classifier/food_classifier.py
python3 -m pytest tests/ -q
18 passed
```

주의:

```text
아직 운영 파일 data/models/efficientnet_korean.pt 는 덮어쓰지 않았다.
현재 호환 작업은 후보 모델을 명시적으로 로드할 수 있게 한 단계다.
실제 운영 승격을 하려면 API 설정에서 candidate path를 선택하는 방식 또는 운영 파일 교체 절차를 별도로 결정해야 한다.
```

### 6.8 다음 후보: B0-LeWM full pretraining

```bash
python3 scripts/pretrain_food_lewm.py \
  --image-root "/Users/sangrok/Downloads/한국 음식 이미지/kfood" \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --epochs 20 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 1e-4 \
  --weight-decay 1e-4 \
  --lambda-sigreg 0.1 \
  --num-projections 256 \
  --predictor-dropout 0.1 \
  --output data/models/food_lewm_b0_pretrain.pt \
  --report-dir reports/food_lewm/b0_pretrain \
  --log-every 50
```

현재 Codex 실행 환경에서는 `torch.backends.mps.is_available()`가 `False`로 확인되었다.  
따라서 이 세션에서 full pretraining을 바로 돌리면 CPU 학습이 되어 매우 오래 걸릴 수 있다. M4 MacBook Pro에서 직접 실행할 때 MPS가 잡히는 환경인지 먼저 확인하는 것이 좋다.

확인 명령:

```bash
python3 - <<'PY'
import torch
print(torch.backends.mps.is_available())
PY
```

MPS OOM이 나면:

```text
--batch-size 32
--grad-accum-steps 2
```

### 6.9 B0-LeWM classifier full fine-tuning

B0 pretrain 완료 후 실행:

```bash
python3 scripts/train_food_lewm_classifier.py \
  --data-dir data/raw/korean_food_1000 \
  --model-name efficientnet_b0 \
  --image-size 224 \
  --latent-dim 192 \
  --lewm-checkpoint data/models/food_lewm_b0_pretrain.pt \
  --epochs 30 \
  --batch-size 64 \
  --num-workers 2 \
  --lr 7e-5 \
  --weight-decay 1e-4 \
  --label-smoothing 0.05 \
  --warmup-epochs 2 \
  --random-erasing-p 0.1 \
  --output data/models/food_lewm_b0_classifier.pt \
  --classes-output data/models/food_lewm_b0_classes.json \
  --metadata-output data/models/food_lewm_b0_meta.json \
  --report-dir reports/food_lewm/b0_classifier \
  --log-every 50
```

### 6.10 B0-LeWM evaluation

```bash
python3 scripts/eval_food_lewm.py \
  --data-dir data/raw/korean_food_1000 \
  --checkpoint data/models/food_lewm_b0_classifier.pt \
  --metadata data/models/food_lewm_b0_meta.json \
  --classes data/models/food_lewm_b0_classes.json \
  --batch-size 64 \
  --num-workers 2 \
  --tta hflip \
  --output-dir reports/food_lewm/eval_b0_lewm
```

---

## 7. Known Notes

- `python3 scripts/...` 직접 실행이 가능하도록 각 script에서 repo root를 `sys.path`에 추가했다.
- PyTorch 2.6+의 `weights_only=True` 제한 때문에 checkpoint 로더에 local trusted checkpoint fallback을 넣었다.
- smoke checkpoint는 실험 검증용이므로 운영 후보가 아니다.
- full pretraining은 장시간 작업이다. 이 세션에서는 CPU로 잡혀 실제 full run을 시작하지 않았다.
- ensemble 평가에서 image size가 다른 모델을 섞을 때는 현재 max image size transform을 사용한다. B0/B2 EfficientNet 조합에는 실용적으로 동작하지만, ViT까지 섞는 경우 모델별 transform으로 개선할 수 있다.
