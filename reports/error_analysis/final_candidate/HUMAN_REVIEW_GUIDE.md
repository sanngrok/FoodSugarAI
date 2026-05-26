# K-Food Human Label Review Guide

작성일: 2026-05-10

## 목적

`review_sheet_top300.csv`는 high-confidence error 300개를 검수하기 위한 파일이다.  
현재 `reviewed_top300_ai_draft.csv`는 AI visual draft이므로, 운영 확정용 cleaned split을 만들기 전에는 사람이 한 번 더 확인하는 것이 안전하다.

## 검수 파일

```text
reports/error_analysis/final_candidate/review_sheet_top300.csv
reports/error_analysis/final_candidate/reviewed_top300_ai_draft.csv
reports/error_analysis/final_candidate/contact_sheets/
```

사람 검수 최종본 권장 경로:

```text
reports/error_analysis/final_candidate/reviewed_top300.csv
```

## 컬럼 규칙

| Column | 설명 |
|---|---|
| `review_status` | 최종 판정 |
| `corrected_label` | `wrong_label`일 때 올바른 class |
| `review_note` | 판단 근거 |
| `action` | 데이터 처리 방식 |

권장 `review_status`:

```text
correct
wrong_label
ambiguous
multi_food
bad_crop
unclear
class_definition_overlap
```

권장 `action`:

```text
keep
relabel
remove
needs_class_definition
needs_more_data
```

## Hard Pair 기준

### 곰탕_설렁탕 vs 갈비탕

- 갈비뼈/갈비 형태가 명확하면 `갈비탕`.
- 고기국물 중심이고 갈비뼈가 명확하지 않으면 `곰탕_설렁탕`.

### 김치찌개 vs 동태찌개

- 생선/동태 살 또는 생선 조각이 명확하면 `동태찌개`.
- 김치/돼지고기/두부 중심이면 `김치찌개`.
- 생선이 보이지 않는 빨간 국물 이미지는 `ambiguous`.

### 호박전 vs 감자전

- 호박 형태/색/조각이 명확하면 `호박전`.
- 감자 질감 중심이면 `감자전`.
- 재료 texture가 보이지 않으면 `ambiguous`.

### 갈비구이 vs 갈비찜

- 양념된 구운 고기/석쇠/불판이면 `갈비구이`.
- 국물/찜 양념/그릇 안 조리 형태면 `갈비찜`.
- 고기 close-up만 있고 조리방식이 불명확하면 `ambiguous`.

### 비빔냉면 vs 물냉면

- 육수 없이 양념장 중심이면 `비빔냉면`.
- 육수가 명확하면 `물냉면`.

### 칼국수 vs 수제비

- 긴 면발이 명확하면 `칼국수`.
- 뜯은 반죽 조각 형태가 명확하면 `수제비`.

### 떡볶이 vs 라볶이

- 라면/면이 명확하면 `라볶이`.
- 떡 중심이면 `떡볶이`.

### 족발 vs 보쌈

- 껍질/족발 특유의 진한 색과 형태가 명확하면 `족발`.
- 삶은 돼지고기 슬라이스 중심이면 `보쌈`.

## 판정 원칙

```text
운영 확정용 clean은 보수적으로.
확실한 wrong_label만 relabel.
multi_food, bad_crop, class_definition_overlap은 remove 또는 needs_class_definition으로 둔다.
애매하면 relabel하지 말고 ambiguous로 둔다.
```
