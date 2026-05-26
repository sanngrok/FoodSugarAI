# External Validation Plan

- Date: 2026-05-25

## Why

OhioT1DM은 연구용 CGM 데이터로 유용하지만 FoodSugar AI의 실제 한국 사용자, 한국 음식 사진, 식사량 추정, 앱 입력 누락 상황을 충분히 대표하지 않는다.

## Candidate Data Sources

| Candidate | Use | Limitation |
|---|---|---|
| OhioT1DM | current benchmark | limited users, not Korean-food specific |
| publicly available CGM challenge datasets | external CGM pattern check | event schema mismatch likely |
| internal consented pilot | product realism | requires privacy/governance readiness |
| Korean user pilot | target validation | needs recruitment and consent |

## Evaluation Targets

- external 30/60/90m MAE
- interval coverage
- hypo/hyper signal precision/recall
- missing input robustness
- per-user performance spread
- food image to nutrition to CGM response linkage

## Decision Rule

Do not claim broad generalization until at least one external or pilot dataset confirms the safety/UX conclusions.

