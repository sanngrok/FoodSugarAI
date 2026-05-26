# Low-confidence Food Handling Report

- Date: 2026-05-25
- Scope: food image -> nutrition -> glucose risk UX

## Current Policy

Food classification confidence is already returned by the classifier response. For the wellness pilot, low-confidence food predictions should not flow silently into nutrition and glucose-risk interpretation.

## Recommended Handling

| Condition | UX behavior |
|---|---|
| confidence >= 0.80 | show food result and nutrition estimate |
| 0.50 <= confidence < 0.80 | ask user to confirm the food name |
| confidence < 0.50 | require manual food selection before glucose-risk display |

## Safety Copy

```text
음식 인식 신뢰도가 낮습니다. 혈당 위험도는 음식명과 섭취량에 민감하므로 먼저 음식명을 확인하세요.
```

## Current Status

This is documented as pilot UX policy. A frontend implementation should block or de-emphasize glucose-risk display until the user confirms the food label when confidence is low.

