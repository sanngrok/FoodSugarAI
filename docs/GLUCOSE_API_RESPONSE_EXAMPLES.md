# Glucose API Response Examples

- Date: 2026-05-25

## Enriched Forecast Example

```json
{
  "predictions_mg_dl": {"30": 132.4, "60": 151.8, "90": 160.2},
  "calibrated_predictions_mg_dl": {"30": 130.9, "60": 149.3, "90": 158.0},
  "prediction_intervals_mg_dl": {
    "30": [101.0, 165.5],
    "60": [96.0, 203.1],
    "90": [89.4, 225.5]
  },
  "uncertainty_level": {"30": "low", "60": "medium", "90": "high"},
  "uncertainty_message": {
    "30": "30분 예측의 불확실성은 낮음 수준이며, 범위는 최근 validation 오차를 바탕으로 한 참고용 범위입니다.",
    "60": "60분 예측의 불확실성은 중간 수준이며, 범위는 최근 validation 오차를 바탕으로 한 참고용 범위입니다.",
    "90": "90분 예측은 불확실성이 높으므로 참고용 범위와 가능성 신호로만 확인하세요."
  },
  "risk_messages": {
    "60": ["60분 뒤 고혈당 가능성 신호가 감지되었습니다. 실제 혈당 측정값과 증상을 우선 확인하세요."]
  },
  "reference_notice": "이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다. 혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요."
}
```

## UI Mapping

| API field | UI use |
|---|---|
| `predictions_mg_dl.30` | 30m short-term estimate |
| `prediction_intervals_mg_dl.60` | 60m primary display |
| `prediction_intervals_mg_dl.90` | 90m primary display |
| `uncertainty_message.90` | mandatory 90m warning copy |
| `risk_messages` | possibility signal, not diagnosis |
| `reference_notice` | shown near result area |

