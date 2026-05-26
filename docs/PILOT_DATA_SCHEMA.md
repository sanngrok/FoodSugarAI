# Pilot Data Schema

- Date: 2026-05-25
- Scope: limited wellness pilot data, not production medical records

## Tables

### users

| Field | Type | Notes |
|---|---|---|
| user_id | string | pseudonymous id |
| consent_version | string | accepted consent draft version |
| created_at | timestamp | signup time |
| withdrawal_at | timestamp/null | set when user withdraws |

### meal_events

| Field | Type | Notes |
|---|---|---|
| meal_id | string | generated id |
| user_id | string | pseudonymous id |
| timestamp | timestamp | user-local time and timezone required |
| image_ref | string | storage pointer, not raw image in logs |
| user_confirmed_food_name | string | user correction allowed |
| portion_estimate_g | float/null | optional |

### nutrition_estimates

| Field | Type | Notes |
|---|---|---|
| meal_id | string | joins meal_events |
| calories | float | estimated |
| carbs | float | estimated |
| sugar | float | estimated |
| protein | float | estimated |
| fat | float | estimated |
| fiber | float | estimated |

### cgm_readings

| Field | Type | Notes |
|---|---|---|
| user_id | string | pseudonymous id |
| timestamp | timestamp | timezone normalized |
| glucose_mg_dl | float | raw value, sensitive |
| source | string | device/import route |

### glucose_predictions

| Field | Type | Notes |
|---|---|---|
| prediction_id | string | generated id |
| user_id | string | pseudonymous id |
| created_at | timestamp | prediction time |
| model_version | string | glucose model version |
| horizon_minutes | int | 30/60/90 |
| prediction_mg_dl | float | reference-only |
| interval_low_mg_dl | float/null | preferred for 60/90 |
| interval_high_mg_dl | float/null | preferred for 60/90 |
| uncertainty_level | string | low/medium/high |
| hypo_signal | bool | possibility signal |
| hyper_signal | bool | possibility signal |

### user_feedback

| Field | Type | Notes |
|---|---|---|
| feedback_id | string | generated id |
| user_id | string | pseudonymous id |
| prediction_id | string/null | optional |
| understood_reference_only | bool | safety metric |
| perceived_as_medical_advice | bool | safety metric |
| free_text | string/null | redact before analysis |

## Logging Rule

Application logs must store counts, request ids, model versions, latency, and error classes. They must not store raw CGM sequences, food images, insulin values, exact meal timestamps, or user identifiers.

