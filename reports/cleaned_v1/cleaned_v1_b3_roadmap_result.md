# Cleaned_v1 Candidate / B3 Roadmap 실행 중단 리포트

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

## 1. 현재 결론

로드맵의 Phase 2 `patch impact audit`에서 stop 조건에 걸려, `cleaned_v1_candidate` split 생성 / B0 재학습 / B3 probe는 진행하지 않았다.

핵심 이유:

```text
patch 영향이 fixed_v1 train보다 val에 훨씬 많이 걸렸고,
train 영향은 전체 train 49,243장 중 49장(약 0.10%)뿐이다.
```

따라서 지금 상태에서 B0 seed123을 재학습해도 `cleaned train` 효과를 기대하기 어렵다.  
반대로 `val_cleaned`에서 점수가 오르면 모델 개선이 아니라 validation label correction 효과일 가능성이 크다.

---

## 2. 완료한 작업

### Preflight

```text
fixed_v1 train: 49,243
fixed_v1 val: 6,720
classes: 56
class_order_match: True
MPS available: True
```

### Label Review Summary

입력:

```text
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
```

집계:

| Status | Count |
|---|---:|
| model_error | 144 |
| wrong_label | 126 |
| multi_food | 30 |

Noise 후보:

```text
wrong_label + multi_food = 156 / 300 = 52.0%
```

주의:

```text
이 값은 high-confidence error top300 AI draft 기준이다.
전체 데이터 noise ratio가 아니며, 운영 확정용 human review도 아니다.
```

### Label Patch 생성

산출물:

```text
data/processed/kfood_label_patch_v1.csv
data/processed/kfood_exclude_list_v1.csv
reports/error_analysis/final_candidate/label_patch_v1_summary.md
```

Patch:

| Action | Count |
|---|---:|
| relabel | 126 |
| remove | 30 |

검증:

```text
patch_rows: 156
unique class+filename keys: 156
duplicates: 0
```

---

## 3. Stop 조건에 걸린 지점

Patch impact audit:

```text
reports/cleaned_v1/patch_impact_audit/
```

결과:

| Split | Relabel | Remove | Total |
|---|---:|---:|---:|
| train | 42 | 7 | 49 |
| val | 84 | 23 | 107 |

비율:

```text
train affected: 49 / 49,243 = 약 0.10%
val affected:   107 / 6,720 = 약 1.59%
```

판단:

```text
patch가 주로 validation correction에 영향을 준다.
train 정제량이 너무 작아 B0 재학습 효과를 검증하기 어렵다.
```

따라서 아래 단계는 진행하지 않았다.

```text
- data/raw/korean_food_cleaned_v1_candidate 생성
- cleaned_v1_candidate 기준 기존 모델 재평가
- B0 seed123 cleaned 재학습
- B0 seed7 cleaned 재학습
- B3 probe
- B3 full run
- CutMix / 5-fold TTA
```

---

## 4. 현재 Best 기준

기존 current best는 유지한다.

```text
Data: data/raw/korean_food_fixed_v1
Ensemble: B0-family + B2 clean weighted ensemble
TTA: hflip
Top1: 0.900149
Top3: 0.974405
Macro-F1: 0.899900
```

B0 seed123 fixed_v1 single:

```text
Top1: 0.886012
Top3: 0.965327
Macro-F1: 0.885791
```

B2 clean fixed_v1 single:

```text
Top1: 0.835714
Top3: 0.954762
Macro-F1: 0.835308
```

---

## 5. 운영 파일 보호

아래 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

원본 split도 삭제/수정하지 않았다.

```text
data/raw/korean_food
data/raw/korean_food_1000
data/raw/korean_food_fixed_v1
```

---

## 6. 권장 다음 액션

지금 바로 B0 재학습이나 B3 probe로 넘어가는 것은 권장하지 않는다.

대신 다음 중 하나를 먼저 진행해야 한다.

### Option A. Human Review 확정

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

사람 검수본을 확정한 뒤 patch impact를 다시 계산한다.

판단:

```text
AI draft는 빠른 후보 검수로는 유용하지만,
운영용 cleaned split 근거로는 부족하다.
```

### Option B. Train 중심 hard-class review 추가

현재 top300은 val error 중심이라 train 정제에 거의 영향을 주지 않는다.  
따라서 train 쪽 hard class / hard pair 후보를 별도로 샘플링해야 한다.

권장:

```text
1. fixed_v1 train에서 hard class별 샘플 추출
2. class+filename 기준 suspicious / duplicate / visually ambiguous 후보 생성
3. train 중심 label patch 생성
4. train_affected가 충분해진 뒤 cleaned train 재학습
```

### Option C. val_cleaned 진단만 별도 수행

`val_cleaned`를 만들어 corrected-label diagnostic을 볼 수는 있다.  
단, 이 수치는 기존 fixed_v1 current best와 공정 비교하면 안 된다.

---

## 7. 최종 판단

로드맵의 방향은 맞지만, 현재 AI draft top300 patch만으로는 `cleaned train 재학습 → B3 probe`로 넘어가기에는 근거가 약하다.

이 상태에서 재학습을 진행하면 compute를 쓰고도 모델 개선 여부를 분리하기 어렵다.  
따라서 현재 단계에서는 stop 조건에 따라 멈추고, 사람 검수 확정 또는 train 중심 label audit을 먼저 진행하는 것이 맞다.
