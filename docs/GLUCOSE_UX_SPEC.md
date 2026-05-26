# Glucose UX Spec

- Date: 2026-05-25
- Product stance: wellness and dietary management support

## Result Hierarchy

1. Food name and nutrition estimate
2. Glucose burden reference score
3. CGM-based 30m estimate
4. 60m/90m prediction range
5. Hypo/hyper possibility signals
6. Reference-only notice

## Horizon Display

### 30m

- Show numeric estimate.
- Show “참고용” label near the number.
- Do not show treatment advice.

### 60m

- Show interval first when available.
- Show calibrated estimate second.
- Show hypo/hyper possibility signal as low/medium/high or yes/no.

### 90m

- Show interval first.
- Mark uncertainty as high when reported.
- Avoid using a large single-number card.
- Required copy: `90분 예측은 불확실성이 높으므로 참고용 범위와 가능성 신호로만 확인하세요.`

## Event Signal Copy

Use:

```text
고혈당 가능성 신호가 있습니다.
저혈당 가능성 신호가 있습니다.
실제 측정값과 증상을 우선 확인하세요.
```

Avoid:

```text
고혈당입니다.
저혈당입니다.
치료가 필요합니다.
```

## Error States

- Missing CGM readings: ask for at least 13 recent 5-minute readings.
- Missing meal/bolus/basal events: continue with defaults and mark the prediction as context-limited.
- Invalid timestamp: ask the user to confirm device time/timezone.
- Low food confidence: ask user to confirm food name before showing nutrition/risk.

