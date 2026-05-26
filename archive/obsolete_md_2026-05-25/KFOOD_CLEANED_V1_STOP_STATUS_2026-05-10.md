# K-Food Cleaned_v1 Candidate 중단 상태 요약

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

## 1. 현재 상태

`Cleaned_v1 Candidate → B0 재학습 → B3 Probe` 계획을 실행하다가, patch impact audit 단계에서 stop 조건에 걸려 중단했다.

중단 위치:

```text
Phase 2.3 fixed_v1 train/val 영향 audit
```

진행하지 않은 단계:

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

## 2. 중단 이유

AI draft 기반 label patch가 `fixed_v1 train`보다 `fixed_v1 val`에 더 많이 걸렸다.

Patch impact 결과:

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
train 정제량이 너무 작아서 B0 재학습 효과를 기대하기 어렵다.
val_cleaned에서 성능이 오르면 모델 개선이 아니라 validation label correction 효과일 가능성이 크다.
```

따라서 이 상태로 B0 재학습이나 B3 probe를 진행하면 compute를 쓰고도 실제 모델 개선 여부를 분리하기 어렵다.

---

## 3. 완료한 작업

### Preflight

```text
fixed_v1 train: 49,243
fixed_v1 val: 6,720
classes: 56
class_order_match: True
MPS available: True
```

### AI Draft Label Review 요약

입력:

```text
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
```

결과:

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
이 52%는 high-confidence error top300 AI draft 기준이다.
전체 데이터 noise ratio가 아니고, 운영 확정용 human review도 아니다.
```

### Label Patch / Exclude 생성

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

### Patch Impact Audit

산출물:

```text
reports/cleaned_v1/patch_impact_audit/
```

주요 파일:

```text
reports/cleaned_v1/patch_impact_audit/README.md
reports/cleaned_v1/patch_impact_audit/patch_impact_summary.json
reports/cleaned_v1/patch_impact_audit/train_affected.csv
reports/cleaned_v1/patch_impact_audit/val_affected.csv
reports/cleaned_v1/patch_impact_audit/per_class_impact.csv
```

---

## 4. 보호된 파일

아래 운영/기준 파일은 덮어쓰지 않았다.

```text
data/models/efficientnet_korean.pt
data/models/korean_food_classes.json
data/models/korean_food_model_meta.json
data/models/efficientnet_korean_b0_val08275.pt
```

아래 원본 split도 삭제/수정하지 않았다.

```text
data/raw/korean_food
data/raw/korean_food_1000
data/raw/korean_food_fixed_v1
```

`data/raw/korean_food_cleaned_v1_candidate`는 생성하지 않았다.

---

## 5. 현재 Best 기준은 그대로 유지

현재 fixed_v1 기준 best:

```text
Data: data/raw/korean_food_fixed_v1
Ensemble: B0-family + B2 clean weighted ensemble
TTA: hflip
Top1: 0.900149
Top3: 0.974405
Macro-F1: 0.899900
```

현재 best single:

```text
B0 supervised-only seed123 fixed_v1
Top1: 0.886012
Top3: 0.965327
Macro-F1: 0.885791
```

---

## 6. 검증

테스트:

```bash
python3 -m pytest tests/ -q
```

결과:

```text
18 passed in 2.11s
```

스크립트 문법 확인:

```text
py_compile 통과
```

---

## 7. 다음 선택지

### Option A. 사람 검수본 확정

AI draft가 아니라 사람이 직접 확인한 최종 파일을 만든다.

권장 경로:

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

그 뒤 patch/exclude와 impact audit을 다시 수행한다.

### Option B. Train 중심 hard-class label audit

현재 top300은 val error 중심이라 train 정제량이 작다.  
재학습 효과를 보려면 train 쪽 hard class / hard pair 후보를 더 찾아야 한다.

권장 방향:

```text
1. fixed_v1 train에서 hard class별 suspicious sample 추출
2. train 중심 label review sheet 생성
3. train_affected가 충분한 patch 생성
4. 그때 cleaned train 재학습
```

### Option C. val_cleaned 진단만 별도 수행

`val_cleaned`를 만들어 corrected-label 기준 점수를 볼 수는 있다.

단, 이 수치는 기존 fixed_v1 current best와 공정 비교하면 안 된다.

---

## 8. 최종 판단

현재 상태에서 B0 재학습이나 B3 probe로 넘어가는 것은 권장하지 않는다.

이유:

```text
cleaned train에 실제로 반영되는 샘플이 너무 적다.
성능 상승이 발생해도 train 개선 효과와 val correction 효과를 분리하기 어렵다.
```

따라서 다음 우선순위는 `사람 검수본 확정` 또는 `train 중심 hard-class label audit`이다.
