# Confidence 0.70+ AI Visual Draft Review

- 작성일: 2026-05-10
- 입력: `reports/cleaned_v1/train_hard_review/prioritized_subsets/train_hard_disagree_conf70_15.csv`
- contact sheet: `reports/cleaned_v1/train_hard_review/prioritized_subsets/contact_conf70/review_sheet_001.jpg`
- 출력: `reports/cleaned_v1/train_hard_review/conf70_ai_visual_review.csv`

## 주의

이 검토는 사람이 확정한 결과가 아니라 AI visual draft다. 운영용 `cleaned_v1` 또는 human-reviewed patch로 바로 승격하면 안 된다.

## 결과 요약

- total reviewed: 15
- proposed relabel: 8
- proposed remove: 3
- proposed keep/model_error: 4
- apply_to_ai_candidate=yes: 11
- apply_to_ai_candidate=no: 4

## 중요한 수정

기존 AI draft와 ensemble이 틀릴 수 있음을 확인했다.

- `족발/Img_131_0545.jpg`: ensemble은 닭갈비, 하지만 visual review는 족발 유지.
- `갈비구이/Img_000_0261.jpg`: ensemble은 떡갈비, 하지만 visual review는 갈비구이 유지.
- `물냉면/Img_052_0792.jpg`: ensemble은 잔치국수, 하지만 visual review는 물냉면 유지.

## 현재 판단

0.70 이상 불일치 15개 중 11개가 correction/remove 후보로 보이지만, 전체 train 49,243장 대비 여전히 작은 규모다. 이 단계는 B0/B3 재학습 시작 근거라기보다, 사람이 확정할 우선 검수 목록을 만든 것으로 보는 게 맞다.
