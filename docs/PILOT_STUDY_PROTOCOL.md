# FoodSugar AI Wellness Pilot Study Protocol

- Date: 2026-05-25
- Study type: small wellness usability and model-observation pilot
- Target size: 10-30 participants
- Duration: 2-4 weeks

## Objective

실제 사용자가 식사 사진, 음식명 확인, 영양성분 참고, CGM 기반 혈당 변화 가능성 신호를 오해 없이 사용할 수 있는지 확인한다.

이 파일럿은 의료 효과 검증이나 치료 보조 검증이 아니다.

## Participants

권장 대상:

- CGM 데이터를 자발적으로 제공할 수 있는 성인
- 식사 사진 기록에 동의한 사용자
- 앱 결과가 의료 조언이 아니라 참고용이라는 점을 이해한 사용자

제외 권장:

- 앱 결과를 치료 결정에 사용할 가능성이 높은 사용자
- 연구/파일럿 동의 내용을 이해하기 어려운 사용자
- 응급 혈당 관리가 필요한 상황의 사용자

## Collected Data

| Category | Fields |
|---|---|
| meal | meal timestamp, food image, user-confirmed food name, portion estimate |
| nutrition | estimated calories, carbs, sugar, protein, fat, fiber, GI if available |
| CGM | timestamp, glucose_mg_dl, device/source label if available |
| context | exercise flag, sleep flag, optional notes |
| model output | food prediction, glucose risk score, 30/60/90m forecast, intervals, event signals |
| feedback | understood/not understood, trusted/not trusted, action taken outside app |

## Metrics

Model observation metrics:

- 30/60/90m MAE
- prediction interval coverage
- hypo/hyper signal precision and recall
- per-user error distribution
- missing input rate

UX/safety metrics:

- percentage of users who understand “reference only”
- percentage who interpret signal as diagnosis
- false alarm fatigue feedback
- unclear wording reports
- cases where users considered changing medication due to the app

## Safety Event Reporting

Record a safety review item when a user reports any of the following.

- The user interpreted the app as diagnosis.
- The user considered medication/insulin changes because of the app.
- The user ignored symptoms or actual CGM readings because of the app.
- The user was confused by 90m prediction precision.

## Stop Criteria

Pause pilot review if any of the following occurs.

- Repeated misunderstanding of event signals as diagnosis
- Any medication/treatment decision influenced by app output
- Raw health data appears in logs
- Deletion request cannot be fulfilled

