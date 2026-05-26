# K-Food Train 중심 Hard-Class Review 다음 단계 결과

작성일: 2026-05-10  
작업 경로: `/Users/sangrok/foodsugar-ai`

## 1. 진행 배경

이전 `cleaned_v1_candidate` 계획은 patch impact audit에서 중단됐다.

중단 이유:

```text
AI draft patch 156건 중 fixed_v1 train에는 49건만 걸렸고,
fixed_v1 val에는 107건이 걸렸다.
```

따라서 B0 재학습/B3 probe로 바로 넘어가지 않고, `fixed_v1 train`에서 hard class / hard pair 중심 검수 후보를 새로 만드는 방향으로 전환했다.

---

## 2. 이번에 생성한 산출물

Train 중심 review sheet:

```text
reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv
```

Contact sheets:

```text
reports/cleaned_v1/train_hard_review/contact_sheets/
```

요약 리포트:

```text
reports/cleaned_v1/train_hard_review/README.md
```

생성 스크립트:

```text
scripts/build_train_hard_review_sheet.py
```

---

## 3. Review Sheet 구성

총 샘플:

```text
500 rows
```

Source별 구성:

| Source | Count |
|---|---:|
| existing_ai_patch_train_affected | 49 |
| hard_pair_true_side | 177 |
| hard_pair_pred_side | 178 |
| hard_class_extra | 96 |

의미:

```text
existing_ai_patch_train_affected:
  기존 AI draft patch가 fixed_v1 train에 실제로 걸린 49건.
  사람이 확인해서 relabel/remove로 확정할 후보.

hard_pair_true_side / hard_pair_pred_side:
  hard pair 양쪽 class에서 샘플링한 boundary 검수 후보.
  모델 prediction 결과가 아니라 class boundary 확인용이다.

hard_class_extra:
  low-F1 hard class에서 추가 샘플링한 후보.
```

---

## 4. 주요 Class 분포

상위 class:

| Class | Count |
|---|---:|
| 갈비구이 | 43 |
| 곰탕_설렁탕 | 33 |
| 김치찌개 | 28 |
| 동태찌개 | 27 |
| 칼국수 | 26 |
| 삼겹살 | 23 |
| 갈비찜 | 22 |
| 라면 | 19 |
| 불고기 | 18 |
| 호박전 | 18 |
| 라볶이 | 18 |
| 닭볶음탕 | 16 |

이 구성은 기존 hard class / hard pair 리포트에 기반한다.

---

## 5. 검수 방법

CSV:

```text
reports/cleaned_v1/train_hard_review/train_hard_review_sheet.csv
```

이미지 보기:

```text
reports/cleaned_v1/train_hard_review/contact_sheets/review_sheet_001.jpg
...
reports/cleaned_v1/train_hard_review/contact_sheets/review_sheet_020.jpg
```

검수 컬럼:

| Column | 입력값 |
|---|---|
| `review_status` | `correct`, `wrong_label`, `ambiguous`, `multi_food`, `bad_crop`, `unclear`, `class_definition_overlap` |
| `corrected_label` | `wrong_label`일 때 올바른 class |
| `review_note` | 판단 근거 |
| `action` | `keep`, `relabel`, `remove`, `needs_class_definition`, `needs_more_data` |

주의:

```text
hard_pair_* 샘플의 pred_label은 실제 모델 예측값이 아니다.
비교해야 할 candidate class로만 사용한다.
```

---

## 6. 다음 판단 기준

사람 검수 또는 AI 보조 검수 후 patch를 다시 만들고 impact audit을 다시 실행한다.

권장 threshold:

```text
train_affected >= 300:
  cleaned train 재학습을 진행할 만한 최소 근거가 생김.

train_affected >= 500:
  B0 seed123 cleaned 재학습을 강하게 권장.

train_affected < 150:
  아직 재학습보다 train review 후보를 더 늘리는 것이 우선.
```

재개 순서:

```text
1. train_hard_review_sheet.csv 검수 완료
2. build_kfood_label_patch.py로 patch/exclude 재생성
3. audit_label_patch_impact.py 재실행
4. train_affected가 충분하면 cleaned_v1_candidate 생성
5. B0 seed123 cleaned 재학습
6. 조건 충족 시 B0 seed7 / B3 probe 진행
```

---

## 7. 현재 결론

현재는 B0 재학습이나 B3 probe를 재개하지 않았다.

대신 train 정제량을 실제로 늘릴 수 있는 hard-class review sheet 500개를 생성했다.

이제 다음 병목은 `train_hard_review_sheet.csv`의 검수 결과다.
