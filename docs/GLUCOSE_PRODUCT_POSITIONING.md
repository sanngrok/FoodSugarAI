# FoodSugar AI Glucose Product Positioning

- Date: 2026-05-25
- Scope: glucose risk score, CGM forecasting, hypo/hyper possibility signals
- Product position: wellness and dietary management support

## Position

FoodSugar AI의 혈당 기능은 의료 판단 도구가 아니라 식습관 관리와 생활 패턴 이해를 돕는 웰니스 기능이다.

사용자에게 제공하는 것은 다음이다.

- 음식 영양성분 기반 혈당 부담 참고 점수
- CGM 데이터가 있을 때의 30/60/90분 혈당 변화 가능성
- 예측 범위와 불확실성
- 저혈당/고혈당 가능성 신호

제공하지 않는 것은 다음이다.

- 당뇨 진단
- 저혈당/고혈당 확정 판정
- 인슐린 또는 약물 조절 안내
- 치료 결정 지원
- 응급상황 판단

## Horizon Policy

| Horizon | User-facing emphasis | Required safety framing |
|---:|---|---|
| 30m | short-term numeric estimate | 참고용 수치, 실제 측정값 우선 |
| 60m | estimate + range + signal | 범위와 가능성 신호를 함께 표시 |
| 90m | range + uncertainty + signal | 단일 수치 중심 표시 금지, 높은 불확실성 표시 |

## Required Notice

모든 혈당 관련 응답, 화면, 보고서에는 아래 의미가 포함되어야 한다.

```text
이 결과는 식습관 관리를 위한 참고용 정보이며 의료 진단이나 치료 지침이 아닙니다.
혈당 관리와 치료 관련 결정은 앱 결과만으로 하지 말고 의료진과 상의하세요.
```

## Current Readiness

| Use case | Status | Notes |
|---|---|---|
| 교내 발표/공모전/연구 시연 | ready | 안전 문구 포함 시 가능 |
| 팀 내부 베타 | conditionally ready | 로그/동의/삭제 정책 필요 |
| 제한된 사용자 파일럿 | planned | 개인정보/파일럿 프로토콜 필요 |
| 일반 서비스 출시 | not ready | 외부 검증과 실제 사용자 파일럿 필요 |
| 의료 판단/치료 보조 | out of scope | 별도 규제/임상/품질체계 필요 |

## Non-goals

- MAE만 낮추기 위해 안전 문구를 약화하지 않는다.
- 90분 예측을 정확한 혈당값처럼 강조하지 않는다.
- 사용자에게 치료 행동을 지시하지 않는다.
- K-Food classifier, ensemble weights, classifier checkpoints는 이 포지셔닝 작업에서 수정하지 않는다.

