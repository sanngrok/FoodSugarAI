# Glucose Safety Wording Guide

- Date: 2026-05-25
- Purpose: 혈당 관련 문구를 웰니스/참고용 표현으로 통일

## Core Rule

FoodSugar AI는 혈당 변화를 확정하지 않는다. 항상 “참고용”, “가능성”, “신호”, “범위”, “불확실성”을 함께 표현한다.

## Recommended Phrases

| Context | Recommended wording |
|---|---|
| general notice | 이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다. |
| risk score | 영양성분 기준 혈당 부담 가능성을 참고용 점수로 보여줍니다. |
| 30m forecast | 30분 뒤 혈당 변화 가능성을 참고용 수치로 보여줍니다. |
| 60m forecast | 60분 예측은 범위와 가능성 신호를 함께 확인하세요. |
| 90m forecast | 90분 예측은 불확실성이 높으므로 단일 수치보다 범위와 주의 신호 중심으로 확인하세요. |
| event signal | 저혈당/고혈당 가능성 신호가 감지되었습니다. 실제 측정값과 증상을 우선 확인하세요. |
| safety | 증상이 있거나 실제 측정값이 우려되면 앱 예측에 의존하지 말고 의료진에게 문의하세요. |

## Forbidden Phrases

아래 표현은 사용자에게 진단/치료 기능처럼 보일 수 있으므로 product copy와 API 메시지에서 사용하지 않는다.

```text
혈당을 정확히 예측합니다.
저혈당입니다.
고혈당입니다.
인슐린을 조절하세요.
치료 결정을 도와줍니다.
당뇨를 진단합니다.
약을 조절하세요.
응급 여부를 판단합니다.
```

## API Message Requirements

- `reference_notice`는 모든 혈당 관련 response에 포함한다.
- `safety_warning`은 실제 측정값과 의료진 확인을 우선하도록 표현한다.
- `risk_messages`는 “가능성 신호”로 표현한다.
- 90분 horizon에는 `uncertainty_message`가 있어야 한다.
- 90분 horizon은 화면에서 `prediction_intervals_mg_dl`을 우선 표시한다.

## UX Requirements

- 혈당 위험도 색상은 경고처럼 보일 수 있으므로 “가능성” 라벨을 함께 둔다.
- 90분 값은 큰 숫자 카드 하나로 표시하지 않는다.
- 오경고/미경고 가능성을 사용자가 볼 수 있게 짧은 안내를 붙인다.
- 결과 화면 하단이 아니라 결과 바로 근처에 참고용 문구를 둔다.

