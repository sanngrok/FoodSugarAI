# Glucose UX Safety Review

- Date: 2026-05-25
- Result: safe wellness pilot UX direction documented

## Review Result

| UX item | Decision |
|---|---|
| 30m display | numeric estimate allowed with reference-only label |
| 60m display | range + calibrated estimate + possibility signal |
| 90m display | range-first with high uncertainty copy |
| event flags | possibility signal only |
| treatment wording | not allowed |
| actual readings | users should prioritize CGM/glucose measurement and symptoms |

## API Fields To Surface

- `prediction_intervals_mg_dl`
- `uncertainty_level`
- `uncertainty_message`
- `risk_messages`
- `reference_notice`
- `safety_warning`

## UI Copy Requirement

For 90m horizon, show:

```text
90분 예측은 불확실성이 높으므로 참고용 범위와 가능성 신호로만 확인하세요.
```

