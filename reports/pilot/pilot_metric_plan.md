# Pilot Metric Plan

- Date: 2026-05-25
- Pilot size: 10-30 users
- Duration: 2-4 weeks

## Model Metrics

| Metric | Horizon | Purpose |
|---|---|---|
| MAE | 30/60/90m | overall forecast error |
| interval coverage | 30/60/90m | uncertainty calibration |
| interval width | 30/60/90m | usability of range |
| hypo signal recall | 30/60/90m | missed low-risk signal check |
| hyper signal recall | 30/60/90m | missed high-risk signal check |
| per-user MAE spread | all | fairness/personalization need |

## Product Metrics

| Metric | Target observation |
|---|---|
| meal logging adherence | whether users continue logging meals |
| food correction rate | classifier/nutrition trust proxy |
| reference-only comprehension | users understand non-medical status |
| 90m misunderstanding rate | users do not treat 90m as exact |
| false alarm fatigue | event signals do not cause app abandonment |

## Safety Metrics

- users who interpreted a signal as diagnosis
- users who considered medication/insulin changes because of app output
- reports of missing actual symptoms due to app output
- privacy complaints or deletion requests

